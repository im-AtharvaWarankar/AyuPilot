from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q, Count
from django.utils import timezone
from datetime import date, timedelta
from atomicloops.viewsets import AtomicViewSet
from django.db import transaction
import logging
from rest_framework import serializers
import base64
import mimetypes

from .permissions import (
    AyuPilotBasePermission, PatientDataPermission, IsPatientDoctorOnly,
    IsImageAnalysisOwner, IsDocumentAnalysisOwner, IsClinicalReportOwner,
    IsChatMessageOwner, IsAppointmentParticipant, CanUploadFiles,
    CanGenerateReports, filter_by_patient_access
)
from .filters import (
    PatientFilter, MedicineFilter, AppointmentFilter, ImageAnalysisFilter,
    DocumentAnalysisFilter, ClinicalReportFilter, SNLPrescriptionFilter,
    KnowledgeReferenceFilter, ChatMessageFilter
)

from .models import (
    Patient, Medicine, Appointment, ImageAnalysis, 
    DocumentAnalysis, ClinicalReport, SNLPrescription, 
    KnowledgeReference, ChatMessage, Prescription
)
from .serializers import (
    PatientSerializer, PatientCreateSerializer, MedicineSerializer,
    AppointmentSerializer, ImageAnalysisSerializer, DocumentAnalysisSerializer,
    ClinicalReportSerializer, SNLPrescriptionSerializer, KnowledgeReferenceSerializer,
    ChatMessageSerializer, ImageUploadSerializer, DocumentUploadSerializer,
    GenerateReportSerializer, ChatRequestSerializer, DashboardStatsSerializer,
    PrescriptionSerializer
)
from .tasks import (
    analyze_image_task, analyze_document_task, generate_clinical_report_task,
    generate_snl_prescription_task, generate_knowledge_references_task,
    process_ai_chat_task
)
# Import the synchronous helper so the view can fall back when Celery/broker is unavailable
from .tasks import analyze_document_sync

logger = logging.getLogger(__name__)


def get_user_or_default_doctor(request):
    """Return the authenticated user or fall back to the first doctor user.

    This mirrors the fallback behavior used elsewhere in the views so that
    endpoints can be called in development without authentication.
    """
    user = request.user if getattr(request, 'user', None) and request.user.is_authenticated else None
    if not user:
        # Import here to avoid circular imports at module import time
        from users.models import Users, UserLevel
        user = Users.objects.filter(level=UserLevel.DOCTOR).first()
    return user


def get_user_or_default_doctor(request):
    """Return request.user if authenticated, otherwise return the first doctor user.

    This helper centralizes the fallback logic used across several views so
    unauthenticated requests in development can still operate against a test
    doctor. It mirrors the behavior used in DashboardStatsView.
    """
    user = None
    try:
        if getattr(request, 'user', None) and request.user.is_authenticated:
            user = request.user
    except Exception:
        user = None
    if not user:
        # Import here to avoid circular imports at module import time
        from users.models import Users, UserLevel
        user = Users.objects.filter(level=UserLevel.DOCTOR).first()

    return user


class PatientViewSet(AtomicViewSet):
    """ViewSet for Patient CRUD operations"""
    
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [PatientDataPermission]
    filterset_class = PatientFilter
    ordering_fields = ('createdAt', 'name', 'age', 'lastVisit')
    ordering = ('-createdAt',)
    
    def get_queryset(self):
        """Filter patients by current doctor. If unauthenticated, fall back to a
        default doctor user so development/demo requests can still return
        patients (mirrors behavior used by dashboard endpoints)."""
        # Prefer the authenticated user when available
        user = None
        try:
            if getattr(self.request, 'user', None) and self.request.user.is_authenticated:
                user = self.request.user
        except Exception:
            user = None

        # Fall back to the first doctor user for unauthenticated/dev requests
        if not user:
            user = get_user_or_default_doctor(self.request)
            if not user:
                # No doctor available -> return empty queryset
                return Patient.objects.none()

        return super().get_queryset().filter(doctorId=user)
    
    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_authenticated:
            logger.error("Attempt to create patient without authentication.")
            raise PermissionError("Authentication required.")
        try:
            serializer.save(doctorId=user)
        except Exception as e:
            logger.error(f"Error creating patient: {e}")
            raise serializers.ValidationError({'error': 'Failed to create patient.'})
    
    def perform_update(self, serializer):
        try:
            serializer.save()
        except Exception as e:
            logger.error(f"Error updating patient: {e}")
            raise serializers.ValidationError({'error': 'Failed to update patient.'})
    
    def perform_destroy(self, instance):
        try:
            instance.delete()
        except Exception as e:
            logger.error(f"Error deleting patient: {e}")
            raise serializers.ValidationError({'error': 'Failed to delete patient.'})
    
    def get_serializer_class(self):
        """Use different serializer for create/update"""
        if self.action in ['create', 'update', 'partial_update']:
            return PatientCreateSerializer
        return PatientSerializer
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent patients for dashboard (paginated)"""
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset[:5], many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_medication(self, request, pk=None):
        """Add medicine to patient"""
        patient = self.get_object()
        serializer = MedicineSerializer(data=request.data)
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    serializer.save(patientId=patient)
                    logger.info(f"Medicine added for patient {patient.id}")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                logger.error(f"Error adding medication: {e}")
                return Response({'error': 'Failed to add medication.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        logger.warning(f"Invalid medication data: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MedicineViewSet(AtomicViewSet):
    """ViewSet for Medication CRUD operations"""
    
    queryset = Medicine.objects.all()
    serializer_class = MedicineSerializer
    permission_classes = [PatientDataPermission]
    filterset_class = MedicineFilter
    ordering_fields = ('createdAt', 'name')
    ordering = ('-createdAt',)
    
    def get_queryset(self):
        """Return all medicines (no patient filtering)"""
        queryset = super().get_queryset()
        return queryset
    
    def perform_create(self, serializer):
        try:
            serializer.save()
        except Exception as e:
            logger.error(f"Error creating medication: {e}")
            raise serializers.ValidationError({'error': 'Failed to create medication.'})
    
    def perform_update(self, serializer):
        try:
            serializer.save()
        except Exception as e:
            logger.error(f"Error updating medication: {e}")
            raise serializers.ValidationError({'error': 'Failed to update medication.'})
    
    def perform_destroy(self, instance):
        try:
            instance.delete()
        except Exception as e:
            logger.error(f"Error deleting medication: {e}")
            raise serializers.ValidationError({'error': 'Failed to delete medication.'})


class AppointmentViewSet(AtomicViewSet):
    """ViewSet for Appointment CRUD operations"""
    
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsAppointmentParticipant]
    filterset_class = AppointmentFilter
    ordering_fields = ('appointmentDate', 'appointmentTime', 'createdAt')
    ordering = ('appointmentDate', 'appointmentTime')
    
    def get_queryset(self):
        """Filter appointments by current doctor"""
        queryset = super().get_queryset()
        
        # Get user - use first doctor if not authenticated (testing)
        user = self.request.user if self.request.user.is_authenticated else None
        if not user:
            from users.models import Users, UserLevel
            user = Users.objects.filter(level=UserLevel.DOCTOR).first()
            if not user:
                return queryset.none()
        
        return queryset.filter(doctorId=user).select_related('patientId')
    
    def perform_create(self, serializer):
        # Set doctorId from request.user if not provided
        doctor = self.request.user if self.request.user.is_authenticated else None
        validated_data = serializer.validated_data
        if not validated_data.get('doctorId'):
            if not doctor:
                from users.models import Users, UserLevel
                doctor = Users.objects.filter(level=UserLevel.DOCTOR).first()
            serializer.save(doctorId=doctor)
        else:
            serializer.save()
    
    def perform_update(self, serializer):
        try:
            serializer.save()
        except Exception as e:
            logger.error(f"Error updating appointment: {e}")
            raise serializers.ValidationError({'error': 'Failed to update appointment.'})
    
    def perform_destroy(self, instance):
        try:
            instance.delete()
        except Exception as e:
            logger.error(f"Error deleting appointment: {e}")
            raise serializers.ValidationError({'error': 'Failed to delete appointment.'})
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's appointments for dashboard"""
        today_appointments = self.get_queryset().filter(appointmentDate=date.today())
        serializer = self.get_serializer(today_appointments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_completed(self, request, pk=None):
        """Mark appointment as completed"""
        appointment = self.get_object()
        appointment.status = Appointment.StatusChoices.COMPLETED
        appointment.save()
        return Response({'status': 'completed'})
    
    @action(detail=True, methods=['post'])
    def reschedule(self, request, pk=None):
        """Reschedule appointment"""
        appointment = self.get_object()
        new_date = request.data.get('appointmentDate')
        new_time = request.data.get('appointmentTime')
        
        if new_date:
            appointment.appointmentDate = new_date
        if new_time:
            appointment.appointmentTime = new_time
        
        appointment.save()
        serializer = self.get_serializer(appointment)
        return Response(serializer.data)


class ImageAnalysisViewSet(AtomicViewSet):
    """ViewSet for ImageAnalysis CRUD operations"""
    
    queryset = ImageAnalysis.objects.all()
    serializer_class = ImageAnalysisSerializer
    permission_classes = [IsImageAnalysisOwner]
    filterset_class = ImageAnalysisFilter
    ordering_fields = ('createdAt', 'imageType')
    ordering = ('-createdAt',)
    
    def get_queryset(self):
        """Filter by current doctor's patients"""
        queryset = super().get_queryset()
        if self.request.user.is_authenticated:
            return queryset.filter(patientId__doctorId=self.request.user).select_related('patientId')
        else:
            # For anonymous users, use the first doctor
            from users.models import Users, UserLevel
            first_doctor = Users.objects.filter(level=UserLevel.DOCTOR).first()
            if first_doctor:
                return queryset.filter(patientId__doctorId=first_doctor).select_related('patientId')
            return queryset.none()


class DocumentAnalysisViewSet(AtomicViewSet):
    """ViewSet for DocumentAnalysis CRUD operations"""
    
    queryset = DocumentAnalysis.objects.all()
    serializer_class = DocumentAnalysisSerializer
    permission_classes = [IsDocumentAnalysisOwner]
    filterset_class = DocumentAnalysisFilter
    ordering_fields = ('createdAt', 'documentType')
    ordering = ('-createdAt',)
    
    def get_queryset(self):
        """Filter by current doctor's patients"""
        queryset = super().get_queryset()
        if self.request.user.is_authenticated:
            return queryset.filter(patientId__doctorId=self.request.user).select_related('patientId')
        else:
            # For anonymous users, use the first doctor
            from users.models import Users, UserLevel
            first_doctor = Users.objects.filter(level=UserLevel.DOCTOR).first()
            if first_doctor:
                return queryset.filter(patientId__doctorId=first_doctor).select_related('patientId')
            return queryset.none()


class ClinicalReportViewSet(AtomicViewSet):
    """ViewSet for ClinicalReport CRUD operations"""
    
    queryset = ClinicalReport.objects.all()
    serializer_class = ClinicalReportSerializer
    permission_classes = [IsClinicalReportOwner]
    filterset_class = ClinicalReportFilter
    ordering_fields = ('createdAt',)
    ordering = ('-createdAt',)
    
    def get_queryset(self):
        """Filter by current doctor's patients"""
        queryset = super().get_queryset()
        if self.request.user.is_authenticated:
            return queryset.filter(patientId__doctorId=self.request.user).select_related('patientId')
        else:
            # For anonymous users, use the first doctor
            from users.models import Users, UserLevel
            first_doctor = Users.objects.filter(level=UserLevel.DOCTOR).first()
            if first_doctor:
                return queryset.filter(patientId__doctorId=first_doctor).select_related('patientId')
            return queryset.none()


class SNLPrescriptionViewSet(AtomicViewSet):
    """ViewSet for SNLPrescription CRUD operations"""
    
    queryset = SNLPrescription.objects.all()
    serializer_class = SNLPrescriptionSerializer
    permission_classes = [IsPatientDoctorOnly]
    filterset_class = SNLPrescriptionFilter
    ordering_fields = ('createdAt',)
    ordering = ('-createdAt',)
    
    def get_queryset(self):
        """Filter by current doctor's patients"""
        queryset = super().get_queryset()
        if self.request.user.is_authenticated:
            return queryset.filter(patientId__doctorId=self.request.user).select_related('patientId')
        else:
            # For anonymous users, use the first doctor
            from users.models import Users, UserLevel
            first_doctor = Users.objects.filter(level=UserLevel.DOCTOR).first()
            if first_doctor:
                return queryset.filter(patientId__doctorId=first_doctor).select_related('patientId')
            return queryset.none()


class KnowledgeReferenceViewSet(AtomicViewSet):
    """ViewSet for KnowledgeReference CRUD operations"""
    
    queryset = KnowledgeReference.objects.all()
    serializer_class = KnowledgeReferenceSerializer
    permission_classes = [IsPatientDoctorOnly]
    filterset_class = KnowledgeReferenceFilter
    ordering_fields = ('createdAt',)
    ordering = ('-createdAt',)
    
    def get_queryset(self):
        """Filter by current doctor's patients"""
        queryset = super().get_queryset()
        if self.request.user.is_authenticated:
            return queryset.filter(patientId__doctorId=self.request.user).select_related('patientId')
        else:
            # For anonymous users, use the first doctor
            from users.models import Users, UserLevel
            first_doctor = Users.objects.filter(level=UserLevel.DOCTOR).first()
            if first_doctor:
                return queryset.filter(patientId__doctorId=first_doctor).select_related('patientId')
            return queryset.none()


class ChatMessageViewSet(AtomicViewSet):
    """ViewSet for ChatMessage CRUD operations"""
    
    queryset = ChatMessage.objects.all()
    serializer_class = ChatMessageSerializer
    permission_classes = [IsChatMessageOwner]
    filterset_class = ChatMessageFilter
    ordering_fields = ('createdAt',)
    ordering = ('createdAt',)
    
    def get_queryset(self):
        """Filter by current user"""
        queryset = super().get_queryset()
        if self.request.user.is_authenticated:
            return queryset.filter(userId=self.request.user).select_related('patientId', 'userId')
        else:
            # For anonymous users, show all messages (for testing)
            return queryset.select_related('patientId', 'userId')


# API Views for specific frontend functionality

class ImageUploadView(APIView):
    """API endpoint for uploading and analyzing images"""
    
    permission_classes = [CanUploadFiles]
    action = 'create'  # Required for AtomicSerializer
    
    def post(self, request):
        if not request.user.is_authenticated:
            logger.error("Unauthenticated image upload attempt.")
            return Response({'error': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)
        serializer = ImageUploadSerializer(data=request.data)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            try:
                patient = Patient.objects.get(
                    id=validated_data['patientId'],
                    doctorId=request.user
                )
            except Patient.DoesNotExist:
                logger.warning(f"Patient not found or access denied for user {request.user.id}")
                return Response({'error': 'Patient not found or access denied'}, status=status.HTTP_404_NOT_FOUND)
            try:
                with transaction.atomic():
                    image_analysis = ImageAnalysis.objects.create(
                        patientId=patient,
                        imageType=validated_data['imageType'],
                        imageData=validated_data['imageData'],
                        fileName=validated_data['fileName'],
                        status=ImageAnalysis.StatusChoices.ANALYZING
                    )
                    analyze_image_task.delay(image_analysis.id)
                    logger.info(f"Image analysis created for patient {patient.id}")
                serializer = ImageAnalysisSerializer(image_analysis, context={'request': request, 'view': self})
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                logger.error(f"Error creating image analysis: {e}")
                return Response({'error': 'Failed to create image analysis.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        logger.warning(f"Invalid image upload data: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DocumentUploadView(APIView):
    """API endpoint for uploading and analyzing documents"""
    
    permission_classes = [CanUploadFiles]
    action = 'create'  # Required for AtomicSerializer
    
    def post(self, request):
        # Support two upload contracts:
        # 1) JSON body with `documentData` (base64) + fileName/fileType (existing)
        # 2) multipart/form-data with a File under key `document` (frontend FormData)
        data = request.data.copy()
        # If client uploaded a file via multipart, convert to base64 data URI
        uploaded_file = None
        try:
            uploaded_file = request.FILES.get('document')
        except Exception:
            uploaded_file = None

        if uploaded_file:
            try:
                file_bytes = uploaded_file.read()
                b64 = base64.b64encode(file_bytes).decode('ascii')
                # Determine mime type: prefer content_type, fall back by extension
                mime = getattr(uploaded_file, 'content_type', None)
                if not mime:
                    mime, _ = mimetypes.guess_type(uploaded_file.name)
                if not mime:
                    mime = 'application/octet-stream'
                data['documentData'] = f"data:{mime};base64,{b64}"
                data['fileName'] = uploaded_file.name
                data['fileType'] = mime
            except Exception as e:
                logger.error(f"Failed to read uploaded file: {e}")
                return Response({'error': 'Failed to read uploaded file.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = DocumentUploadSerializer(data=data)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            
            # Verify patient belongs to current doctor
            try:
                patient = Patient.objects.get(
                    id=validated_data['patientId'],
                    doctorId=get_user_or_default_doctor(request)
                )
            except Patient.DoesNotExist:
                return Response(
                    {'error': 'Patient not found or access denied'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Create document analysis record
            document_analysis = DocumentAnalysis.objects.create(
                patientId=patient,
                documentType=validated_data['documentType'],
                documentData=validated_data['documentData'],
                fileName=validated_data['fileName'],
                fileType=validated_data['fileType'],
                status=DocumentAnalysis.StatusChoices.ANALYZING
            )
            
            # Trigger async analysis task (enqueue on 'celery' queue so worker picks it up)
            try:
                analyze_document_task.apply_async(args=(str(document_analysis.id),), queue='celery')
            except Exception:
                # If enqueue fails (broker down, misconfigured), run analysis synchronously so
                # the UI doesn't remain stuck on ANALYZING. This is a safe dev-mode fallback.
                try:
                    analyze_document_sync(str(document_analysis.id))
                except Exception as e:
                    logger.error(f"Synchronous document analysis fallback failed: {e}")
                    # As a last resort, try the normal delay() which may still work
                    try:
                        analyze_document_task.delay(document_analysis.id)
                    except Exception:
                        logger.exception("Failed to enqueue document analysis task and fallback failed")
            
            serializer = DocumentAnalysisSerializer(document_analysis, context={'request': request, 'view': self})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GenerateClinicalReportView(APIView):
    """API endpoint for generating clinical intelligence reports"""
    
    permission_classes = [CanGenerateReports]
    action = 'create'  # Required for AtomicSerializer
    
    def post(self, request):
        serializer = GenerateReportSerializer(data=request.data)
        if serializer.is_valid():
            patient_id = serializer.validated_data['patientId']
            
            # Verify patient belongs to current doctor
            try:
                patient = Patient.objects.get(
                    id=patient_id,
                    doctorId=get_user_or_default_doctor(request)
                )
            except Patient.DoesNotExist:
                return Response(
                    {'error': 'Patient not found or access denied'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Create clinical report record
            clinical_report = ClinicalReport.objects.create(
                patientId=patient,
                status=ClinicalReport.StatusChoices.GENERATING
            )
            
            # Trigger async report generation task
            generate_clinical_report_task.delay(clinical_report.id)
            
            serializer = ClinicalReportSerializer(clinical_report, context={'request': request, 'view': self})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GenerateSNLPrescriptionView(APIView):
    """API endpoint for generating SNL prescriptions"""
    
    permission_classes = [CanGenerateReports]
    action = 'create'  # Required for AtomicSerializer
    
    def post(self, request):
        serializer = GenerateReportSerializer(data=request.data)
        if serializer.is_valid():
            patient_id = serializer.validated_data['patientId']
            
            # Verify patient belongs to current doctor
            try:
                patient = Patient.objects.get(
                    id=patient_id,
                    doctorId=get_user_or_default_doctor(request)
                )
            except Patient.DoesNotExist:
                return Response(
                    {'error': 'Patient not found or access denied'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Create SNL prescription record
            snl_prescription = SNLPrescription.objects.create(
                patientId=patient,
                prescriptionContent="",
                status=SNLPrescription.StatusChoices.GENERATING
            )
            
            # Trigger async prescription generation task
            generate_snl_prescription_task.delay(snl_prescription.id)
            
            serializer = SNLPrescriptionSerializer(snl_prescription, context={'request': request, 'view': self})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GenerateKnowledgeReferencesView(APIView):
    """API endpoint for generating knowledge base references"""
    
    permission_classes = [CanGenerateReports]
    action = 'create'  # Required for AtomicSerializer
    
    def post(self, request):
        serializer = GenerateReportSerializer(data=request.data)
        if serializer.is_valid():
            patient_id = serializer.validated_data['patientId']
            
            # Verify patient belongs to current doctor
            try:
                patient = Patient.objects.get(
                    id=patient_id,
                    doctorId=get_user_or_default_doctor(request)
                )
            except Patient.DoesNotExist:
                return Response(
                    {'error': 'Patient not found or access denied'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Create knowledge reference record
            knowledge_reference = KnowledgeReference.objects.create(
                patientId=patient,
                referencesContent="",
                status=KnowledgeReference.StatusChoices.GENERATING
            )
            
            # Trigger async reference generation task
            generate_knowledge_references_task.delay(knowledge_reference.id)
            
            serializer = KnowledgeReferenceSerializer(knowledge_reference, context={'request': request, 'view': self})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AIChatView(APIView):
    """API endpoint for AI assistant chat with polling support"""
    
    permission_classes = [AyuPilotBasePermission]
    action = 'create'  # Required for AtomicSerializer
    
    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        if serializer.is_valid():
            message = serializer.validated_data['message']
            patient_id = serializer.validated_data.get('patientId')
            
            # Get user - use first doctor if not authenticated (testing)
            user = request.user if request.user.is_authenticated else None
            if not user:
                # For testing without auth, use first available doctor
                from users.models import Users, UserLevel
                user = Users.objects.filter(
                    level=UserLevel.DOCTOR
                ).first()
                if not user:
                    return Response(
                        {'error': 'No doctor user available for testing'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            
            patient = None
            if patient_id:
                try:
                    patient = Patient.objects.get(
                        id=patient_id,
                        doctorId=user
                    )
                except Patient.DoesNotExist:
                    return Response(
                        {'error': 'Patient not found or access denied'},
                        status=status.HTTP_404_NOT_FOUND
                    )
            
            # Create user message
            user_message = ChatMessage.objects.create(
                userId=user,
                patientId=patient,
                role=ChatMessage.RoleChoices.USER,
                content=message
            )
            
            # Create assistant message placeholder
            assistant_message = ChatMessage.objects.create(
                userId=user,
                patientId=patient,
                role=ChatMessage.RoleChoices.ASSISTANT,
                content="Thinking..."
            )
            
            # Trigger async AI processing
            process_ai_chat_task.delay(
                str(user_message.id),
                str(assistant_message.id)
            )
            
            # Poll for response (wait up to 30 seconds)
            import time
            max_wait = 30
            poll_interval = 0.5
            waited = 0
            
            while waited < max_wait:
                time.sleep(poll_interval)
                waited += poll_interval
                
                # Refresh assistant message from database
                assistant_message.refresh_from_db()
                
                # Check if response is ready
                if (assistant_message.content and
                        assistant_message.content != "Thinking..."):
                    return Response({
                        'response': assistant_message.content
                    }, status=status.HTTP_200_OK)
            
            # Timeout - return what we have
            return Response({
                'response': (
                    assistant_message.content
                    if assistant_message.content != "Thinking..."
                    else "I'm still processing your request. "
                         "Please try again in a moment."
                )
            }, status=status.HTTP_200_OK)
        
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class DashboardStatsView(APIView):
    """API endpoint for dashboard statistics"""
    
    permission_classes = [AyuPilotBasePermission]
    
    def get(self, request):
        # Get user - use first doctor if not authenticated (testing)
        user = request.user if request.user.is_authenticated else None
        if not user:
            # For testing without auth, use first available doctor
            from users.models import Users, UserLevel
            user = Users.objects.filter(
                level=UserLevel.DOCTOR
            ).first()
            if not user:
                # Return empty stats if no doctor exists
                return Response({
                    'totalPatients': 0,
                    'todayAppointments': 0,
                    'pendingAnalyses': 0,
                    'upcomingAppointments': 0
                }, status=status.HTTP_200_OK)
        
        # Calculate statistics for current doctor
        active_cases = Patient.objects.filter(
            doctorId=user,
            status=Patient.StatusChoices.ACTIVE
        ).count()
        
        today_appointments = Appointment.objects.filter(
            doctorId=user,
            appointmentDate=date.today()
        ).count()
        
        pending_reviews = Patient.objects.filter(
            doctorId=user,
            status=Patient.StatusChoices.REVIEW
        ).count()
        
        remaining_appointments = Appointment.objects.filter(
            doctorId=user,
            appointmentDate=date.today(),
            status=Appointment.StatusChoices.SCHEDULED,
            appointmentTime__gt=timezone.now().time()
        ).count()
        
        stats_data = {
            'totalPatients': active_cases,
            'todayAppointments': today_appointments,
            'pendingAnalyses': pending_reviews,
            'completedReports': remaining_appointments
        }
        
        serializer = DashboardStatsSerializer(stats_data)
        return Response(serializer.data)


class PrescriptionViewSet(AtomicViewSet):
    """ViewSet for Prescription CRUD operations"""
    queryset = Prescription.objects.all()
    serializer_class = PrescriptionSerializer
    permission_classes = [AyuPilotBasePermission]
    filterset_fields = [
        "patientId",
        "medicineId"
    ]
    ordering_fields = (
        "createdAt",
        "updatedAt"
    )
    ordering = ("-createdAt",)

    def get_queryset(self):
        return super().get_queryset()

    def perform_create(self, serializer):
        with transaction.atomic():
            serializer.save()

from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q, Count
from django.utils import timezone
from datetime import date, timedelta
from atomicloops.viewsets import AtomicViewSet

from .permissions import (
    AyuPilotBasePermission, PatientDataPermission, IsPatientDoctorOnly,
    IsImageAnalysisOwner, IsDocumentAnalysisOwner, IsClinicalReportOwner,
    IsChatMessageOwner, IsAppointmentParticipant, CanUploadFiles,
    CanGenerateReports, filter_by_patient_access
)
from .filters import (
    PatientFilter, MedicationFilter, AppointmentFilter, ImageAnalysisFilter,
    DocumentAnalysisFilter, ClinicalReportFilter, SNLPrescriptionFilter,
    KnowledgeReferenceFilter, ChatMessageFilter
)

from .models import (
    Patient, Medication, Appointment, ImageAnalysis, 
    DocumentAnalysis, ClinicalReport, SNLPrescription, 
    KnowledgeReference, ChatMessage
)
from .serializers import (
    PatientSerializer, PatientCreateSerializer, MedicationSerializer,
    AppointmentSerializer, ImageAnalysisSerializer, DocumentAnalysisSerializer,
    ClinicalReportSerializer, SNLPrescriptionSerializer, KnowledgeReferenceSerializer,
    ChatMessageSerializer, ImageUploadSerializer, DocumentUploadSerializer,
    GenerateReportSerializer, ChatRequestSerializer, DashboardStatsSerializer
)
from .tasks import (
    analyze_image_task, analyze_document_task, generate_clinical_report_task,
    generate_snl_prescription_task, generate_knowledge_references_task,
    process_ai_chat_task
)


class PatientViewSet(AtomicViewSet):
    """ViewSet for Patient CRUD operations"""
    
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [PatientDataPermission]
    filterset_class = PatientFilter
    ordering_fields = ('createdAt', 'name', 'age', 'lastVisit')
    ordering = ('-createdAt',)
    
    def get_queryset(self):
        """Filter patients by current doctor"""
        queryset = super().get_queryset()
        return queryset.filter(doctorId=self.request.user).prefetch_related('medications')
    
    def get_serializer_class(self):
        """Use different serializer for create/update"""
        if self.action in ['create', 'update', 'partial_update']:
            return PatientCreateSerializer
        return PatientSerializer
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent patients for dashboard"""
        recent_patients = self.get_queryset()[:5]
        serializer = self.get_serializer(recent_patients, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_medication(self, request, pk=None):
        """Add medication to patient"""
        patient = self.get_object()
        serializer = MedicationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(patientId=patient)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MedicationViewSet(AtomicViewSet):
    """ViewSet for Medication CRUD operations"""
    
    queryset = Medication.objects.all()
    serializer_class = MedicationSerializer
    permission_classes = [PatientDataPermission]
    filterset_class = MedicationFilter
    ordering_fields = ('createdAt', 'name')
    ordering = ('-createdAt',)
    
    def get_queryset(self):
        """Filter by current doctor's patients"""
        queryset = super().get_queryset()
        return queryset.filter(patientId__doctorId=self.request.user).select_related('patientId')


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
        return queryset.filter(doctorId=self.request.user).select_related('patientId')
    
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
        return queryset.filter(patientId__doctorId=self.request.user).select_related('patientId')


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
        return queryset.filter(patientId__doctorId=self.request.user).select_related('patientId')


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
        return queryset.filter(patientId__doctorId=self.request.user).select_related('patientId')


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
        return queryset.filter(patientId__doctorId=self.request.user).select_related('patientId')


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
        return queryset.filter(patientId__doctorId=self.request.user).select_related('patientId')


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
        return queryset.filter(userId=self.request.user).select_related('patientId', 'userId')


# API Views for specific frontend functionality

class ImageUploadView(APIView):
    """API endpoint for uploading and analyzing images"""
    
    permission_classes = [CanUploadFiles]
    action = 'create'  # Required for AtomicSerializer
    
    def post(self, request):
        serializer = ImageUploadSerializer(data=request.data)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            
            # Verify patient belongs to current doctor
            try:
                patient = Patient.objects.get(
                    id=validated_data['patientId'],
                    doctorId=request.user
                )
            except Patient.DoesNotExist:
                return Response(
                    {'error': 'Patient not found or access denied'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Create image analysis record
            image_analysis = ImageAnalysis.objects.create(
                patientId=patient,
                imageType=validated_data['imageType'],
                imageData=validated_data['imageData'],
                fileName=validated_data['fileName'],
                status=ImageAnalysis.StatusChoices.ANALYZING
            )
            
            # Trigger async analysis task
            analyze_image_task.delay(image_analysis.id)
            
            serializer = ImageAnalysisSerializer(image_analysis, context={'request': request, 'view': self})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DocumentUploadView(APIView):
    """API endpoint for uploading and analyzing documents"""
    
    permission_classes = [CanUploadFiles]
    action = 'create'  # Required for AtomicSerializer
    
    def post(self, request):
        serializer = DocumentUploadSerializer(data=request.data)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            
            # Verify patient belongs to current doctor
            try:
                patient = Patient.objects.get(
                    id=validated_data['patientId'],
                    doctorId=request.user
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
            
            # Trigger async analysis task
            analyze_document_task.delay(document_analysis.id)
            
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
                    doctorId=request.user
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
                    doctorId=request.user
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
                    doctorId=request.user
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
    """API endpoint for AI assistant chat"""
    
    permission_classes = [AyuPilotBasePermission]
    action = 'create'  # Required for AtomicSerializer
    
    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        if serializer.is_valid():
            message = serializer.validated_data['message']
            patient_id = serializer.validated_data.get('patientId')
            
            patient = None
            if patient_id:
                try:
                    patient = Patient.objects.get(
                        id=patient_id,
                        doctorId=request.user
                    )
                except Patient.DoesNotExist:
                    return Response(
                        {'error': 'Patient not found or access denied'},
                        status=status.HTTP_404_NOT_FOUND
                    )
            
            # Create user message
            user_message = ChatMessage.objects.create(
                userId=request.user,
                patientId=patient,
                role=ChatMessage.RoleChoices.USER,
                content=message
            )
            
            # Create assistant message placeholder
            assistant_message = ChatMessage.objects.create(
                userId=request.user,
                patientId=patient,
                role=ChatMessage.RoleChoices.ASSISTANT,
                content=""
            )
            
            # Trigger async AI processing
            process_ai_chat_task.delay(user_message.id, assistant_message.id)
            
            # Return both messages
            user_serializer = ChatMessageSerializer(user_message, context={'request': request, 'view': self})
            assistant_serializer = ChatMessageSerializer(assistant_message, context={'request': request, 'view': self})
            
            return Response({
                'user_message': user_serializer.data,
                'assistant_message': assistant_serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DashboardStatsView(APIView):
    """API endpoint for dashboard statistics"""
    
    permission_classes = [AyuPilotBasePermission]
    
    def get(self, request):
        # Calculate statistics for current doctor
        active_cases = Patient.objects.filter(
            doctorId=request.user,
            status=Patient.StatusChoices.ACTIVE
        ).count()
        
        today_appointments = Appointment.objects.filter(
            doctorId=request.user,
            appointmentDate=date.today()
        ).count()
        
        pending_reviews = Patient.objects.filter(
            doctorId=request.user,
            status=Patient.StatusChoices.REVIEW
        ).count()
        
        remaining_appointments = Appointment.objects.filter(
            doctorId=request.user,
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

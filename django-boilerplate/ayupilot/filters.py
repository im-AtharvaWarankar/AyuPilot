import django_filters
from django_filters import rest_framework as filters
from django.db.models import Q, F
from atomicloops.filters import AtomicDateFilter
from .models import (
    Patient, Medicine, Appointment, ImageAnalysis,
    DocumentAnalysis, ClinicalReport, SNLPrescription,
    KnowledgeReference, ChatMessage
)


class PatientFilter(AtomicDateFilter):
    """Filter for Patient model with comprehensive search options"""
    
    # Text search filters
    name = filters.CharFilter(lookup_expr='icontains')
    phone = filters.CharFilter(lookup_expr='icontains')
    abhaNumber = filters.CharFilter(lookup_expr='icontains')
    
    # Status filters
    status = filters.ChoiceFilter(choices=Patient.StatusChoices.choices)
    gender = filters.ChoiceFilter(choices=Patient.GenderChoices.choices)
    
    # Age range filters
    ageMin = filters.NumberFilter(field_name='age', lookup_expr='gte')
    ageMax = filters.NumberFilter(field_name='age', lookup_expr='lte')
    
    # Date filters
    lastVisitAfter = filters.DateFilter(field_name='lastVisit', lookup_expr='gte')
    lastVisitBefore = filters.DateFilter(field_name='lastVisit', lookup_expr='lte')
    
    # Dosha filters (for advanced filtering)
    primaryDosha = filters.CharFilter(method='filter_primary_dosha')
    
    # Search across multiple fields
    search = filters.CharFilter(method='filter_search')
    
    class Meta:
        model = Patient
        fields = [
            'createdAt', 'updatedAt', 'name', 'phone', 'abhaNumber',
            'status', 'gender', 'ageMin', 'ageMax', 'doctorId',
            'lastVisitAfter', 'lastVisitBefore', 'primaryDosha', 'search'
        ]
    
    def filter_primary_dosha(self, queryset, name, value):
        """Filter by primary dosha based on highest percentage"""
        # Simplified approach to avoid syntax issues
        if value.lower() == 'vata':
            return queryset.filter(prakritiVata__gte=34)  # Assuming >33% is dominant
        elif value.lower() == 'pitta':
            return queryset.filter(prakritiPitta__gte=34)
        elif value.lower() == 'kapha':
            return queryset.filter(prakritiKapha__gte=34)
        return queryset
    
    def filter_search(self, queryset, name, value):
        """Search across multiple patient fields"""
        return queryset.filter(
            Q(name__icontains=value) |
            Q(phone__icontains=value) |
            Q(abhaNumber__icontains=value) |
            Q(chiefComplaints__icontains=value)
        )


class MedicineFilter(AtomicDateFilter):
    """Filter for Medicine model"""

    name = filters.CharFilter(lookup_expr='icontains')
    dosage = filters.CharFilter(lookup_expr='icontains')
    frequency = filters.CharFilter(lookup_expr='icontains')
    patientName = filters.CharFilter(field_name='patientId__name', lookup_expr='icontains')
    
    class Meta:
        model = Medicine
        fields = [
            'createdAt', 'updatedAt', 'name', 'dosage',
            'frequency', 'patientName'
        ]


class AppointmentFilter(AtomicDateFilter):
    """Filter for Appointment model with date and status options"""
    
    # Date filters
    appointmentDate = filters.DateFilter(field_name='appointmentDate')
    appointmentDateAfter = filters.DateFilter(field_name='appointmentDate', lookup_expr='gte')
    appointmentDateBefore = filters.DateFilter(field_name='appointmentDate', lookup_expr='lte')
    
    # Time filters
    appointmentTimeAfter = filters.TimeFilter(field_name='appointmentTime', lookup_expr='gte')
    appointmentTimeBefore = filters.TimeFilter(field_name='appointmentTime', lookup_expr='lte')
    
    # Status and type filters
    status = filters.ChoiceFilter(choices=Appointment.StatusChoices.choices)
    appointmentType = filters.ChoiceFilter(choices=Appointment.TypeChoices.choices)
    
    # Patient and doctor filters
    patientName = filters.CharFilter(field_name='patientId__name', lookup_expr='icontains')
    doctorName = filters.CharFilter(field_name='doctorId__firstName', lookup_expr='icontains')
    
    # Today's appointments
    today = filters.BooleanFilter(method='filter_today')
    
    # This week's appointments
    thisWeek = filters.BooleanFilter(method='filter_this_week')
    
    class Meta:
        model = Appointment
        fields = [
            'createdAt', 'updatedAt', 'appointmentDate', 'appointmentDateAfter',
            'appointmentDateBefore', 'appointmentTime', 'appointmentTimeAfter',
            'appointmentTimeBefore', 'appointmentType', 'status', 'patientId',
            'doctorId', 'patientName', 'doctorName', 'today', 'thisWeek'
        ]
    
    def filter_today(self, queryset, name, value):
        """Filter appointments for today"""
        if value:
            from datetime import date
            return queryset.filter(appointmentDate=date.today())
        return queryset
    
    def filter_this_week(self, queryset, name, value):
        """Filter appointments for this week"""
        if value:
            from datetime import date, timedelta
            today = date.today()
            start_week = today - timedelta(days=today.weekday())
            end_week = start_week + timedelta(days=6)
            return queryset.filter(appointmentDate__range=[start_week, end_week])
        return queryset


class ImageAnalysisFilter(AtomicDateFilter):
    """Filter for ImageAnalysis model"""
    
    imageType = filters.ChoiceFilter(choices=ImageAnalysis.ImageTypeChoices.choices)
    status = filters.ChoiceFilter(choices=ImageAnalysis.StatusChoices.choices)
    fileName = filters.CharFilter(field_name='fileName', lookup_expr='icontains')
    patientName = filters.CharFilter(field_name='patientId__name', lookup_expr='icontains')
    
    # Filter by completion status
    completed = filters.BooleanFilter(method='filter_completed')
    pending = filters.BooleanFilter(method='filter_pending')
    
    class Meta:
        model = ImageAnalysis
        fields = [
            'createdAt', 'updatedAt', 'imageType', 'status', 'patientId',
            'fileName', 'patientName', 'completed', 'pending'
        ]
    
    def filter_completed(self, queryset, name, value):
        """Filter completed analyses"""
        if value:
            return queryset.filter(status=ImageAnalysis.StatusChoices.COMPLETED)
        return queryset
    
    def filter_pending(self, queryset, name, value):
        """Filter pending analyses"""
        if value:
            return queryset.filter(status__in=[
                ImageAnalysis.StatusChoices.PENDING,
                ImageAnalysis.StatusChoices.ANALYZING
            ])
        return queryset


class DocumentAnalysisFilter(AtomicDateFilter):
    """Filter for DocumentAnalysis model"""
    
    document_type = filters.ChoiceFilter(choices=DocumentAnalysis.DocumentTypeChoices.choices)
    status = filters.ChoiceFilter(choices=DocumentAnalysis.StatusChoices.choices)
    file_name = filters.CharFilter(field_name='fileName', lookup_expr='icontains')
    file_type = filters.CharFilter(field_name='fileType', lookup_expr='icontains')
    patient_name = filters.CharFilter(field_name='patientId__name', lookup_expr='icontains')
    
    # Filter by completion status
    completed = filters.BooleanFilter(method='filter_completed')
    pending = filters.BooleanFilter(method='filter_pending')
    
    class Meta:
        model = DocumentAnalysis
        fields = [
            'createdAt', 'updatedAt', 'documentType', 'status', 'patientId',
            'file_name', 'file_type', 'patient_name', 'completed', 'pending'
        ]
    
    def filter_completed(self, queryset, name, value):
        """Filter completed analyses"""
        if value:
            return queryset.filter(status=DocumentAnalysis.StatusChoices.COMPLETED)
        return queryset
    
    def filter_pending(self, queryset, name, value):
        """Filter pending analyses"""
        if value:
            return queryset.filter(status__in=[
                DocumentAnalysis.StatusChoices.PENDING,
                DocumentAnalysis.StatusChoices.ANALYZING
            ])
        return queryset


class ClinicalReportFilter(AtomicDateFilter):
    """Filter for ClinicalReport model"""
    
    status = filters.ChoiceFilter(choices=ClinicalReport.StatusChoices.choices)
    patient_name = filters.CharFilter(field_name='patientId__name', lookup_expr='icontains')
    
    # Filter by completion status
    completed = filters.BooleanFilter(method='filter_completed')
    generating = filters.BooleanFilter(method='filter_generating')
    
    class Meta:
        model = ClinicalReport
        fields = [
            'createdAt', 'updatedAt', 'status', 'patientId',
            'patient_name', 'completed', 'generating'
        ]
    
    def filter_completed(self, queryset, name, value):
        """Filter completed reports"""
        if value:
            return queryset.filter(status=ClinicalReport.StatusChoices.COMPLETED)
        return queryset
    
    def filter_generating(self, queryset, name, value):
        """Filter reports being generated"""
        if value:
            return queryset.filter(status=ClinicalReport.StatusChoices.GENERATING)
        return queryset


class SNLPrescriptionFilter(AtomicDateFilter):
    """Filter for SNLPrescription model"""
    
    status = filters.ChoiceFilter(choices=SNLPrescription.StatusChoices.choices)
    patient_name = filters.CharFilter(field_name='patientId__name', lookup_expr='icontains')
    content_search = filters.CharFilter(field_name='prescriptionContent', lookup_expr='icontains')
    
    # Filter by completion status
    completed = filters.BooleanFilter(method='filter_completed')
    generating = filters.BooleanFilter(method='filter_generating')
    
    class Meta:
        model = SNLPrescription
        fields = [
            'createdAt', 'updatedAt', 'status', 'patientId',
            'patient_name', 'content_search', 'completed', 'generating'
        ]
    
    def filter_completed(self, queryset, name, value):
        """Filter completed prescriptions"""
        if value:
            return queryset.filter(status=SNLPrescription.StatusChoices.COMPLETED)
        return queryset
    
    def filter_generating(self, queryset, name, value):
        """Filter prescriptions being generated"""
        if value:
            return queryset.filter(status=SNLPrescription.StatusChoices.GENERATING)
        return queryset


class KnowledgeReferenceFilter(AtomicDateFilter):
    """Filter for KnowledgeReference model"""
    
    status = filters.ChoiceFilter(choices=KnowledgeReference.StatusChoices.choices)
    patient_name = filters.CharFilter(field_name='patientId__name', lookup_expr='icontains')
    content_search = filters.CharFilter(field_name='referencesContent', lookup_expr='icontains')
    
    # Filter by completion status
    completed = filters.BooleanFilter(method='filter_completed')
    generating = filters.BooleanFilter(method='filter_generating')
    
    class Meta:
        model = KnowledgeReference
        fields = [
            'createdAt', 'updatedAt', 'status', 'patientId',
            'patient_name', 'content_search', 'completed', 'generating'
        ]
    
    def filter_completed(self, queryset, name, value):
        """Filter completed references"""
        if value:
            return queryset.filter(status=KnowledgeReference.StatusChoices.COMPLETED)
        return queryset
    
    def filter_generating(self, queryset, name, value):
        """Filter references being generated"""
        if value:
            return queryset.filter(status=KnowledgeReference.StatusChoices.GENERATING)
        return queryset


class ChatMessageFilter(AtomicDateFilter):
    """Filter for ChatMessage model"""
    
    role = filters.ChoiceFilter(choices=ChatMessage.RoleChoices.choices)
    content_search = filters.CharFilter(field_name='content', lookup_expr='icontains')
    patient_name = filters.CharFilter(field_name='patientId__name', lookup_expr='icontains')
    user_email = filters.CharFilter(field_name='userId__email', lookup_expr='icontains')
    
    # Filter by message type
    user_messages = filters.BooleanFilter(method='filter_user_messages')
    assistant_messages = filters.BooleanFilter(method='filter_assistant_messages')
    
    # Filter by date range
    today = filters.BooleanFilter(method='filter_today')
    this_week = filters.BooleanFilter(method='filter_this_week')
    
    class Meta:
        model = ChatMessage
        fields = [
            'createdAt', 'updatedAt', 'role', 'patientId', 'userId',
            'content_search', 'patient_name', 'user_email',
            'user_messages', 'assistant_messages', 'today', 'this_week'
        ]
    
    def filter_user_messages(self, queryset, name, value):
        """Filter user messages only"""
        if value:
            return queryset.filter(role=ChatMessage.RoleChoices.USER)
        return queryset
    
    def filter_assistant_messages(self, queryset, name, value):
        """Filter assistant messages only"""
        if value:
            return queryset.filter(role=ChatMessage.RoleChoices.ASSISTANT)
        return queryset
    
    def filter_today(self, queryset, name, value):
        """Filter messages from today"""
        if value:
            from datetime import date
            return queryset.filter(createdAt__date=date.today())
        return queryset
    
    def filter_this_week(self, queryset, name, value):
        """Filter messages from this week"""
        if value:
            from datetime import date, timedelta
            today = date.today()
            start_week = today - timedelta(days=today.weekday())
            return queryset.filter(createdAt__date__gte=start_week)
        return queryset


# Utility filter functions for common use cases

def filter_by_doctor_patients(queryset, user):
    """Filter any patient-related queryset by doctor's patients"""
    return queryset.filter(patientId__doctorId=user)


def filter_by_doctor_appointments(queryset, user):
    """Filter appointments by doctor"""
    return queryset.filter(doctorId=user)


def filter_by_user_messages(queryset, user):
    """Filter chat messages by user"""
    return queryset.filter(userId=user)


def get_recent_items(queryset, days=7):
    """Get items from the last N days"""
    from datetime import date, timedelta
    cutoff_date = date.today() - timedelta(days=days)
    return queryset.filter(createdAt__date__gte=cutoff_date)


def get_pending_items(queryset, status_field='status', pending_values=None):
    """Get items with pending status"""
    if pending_values is None:
        pending_values = ['PENDING', 'ANALYZING', 'GENERATING']
    
    filter_kwargs = {f"{status_field}__in": pending_values}
    return queryset.filter(**filter_kwargs)

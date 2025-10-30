from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from atomicloops.models import AtomicBaseModel

User = get_user_model()


class Patient(AtomicBaseModel):
    """Patient model for storing Ayurvedic patient information"""
    
    class StatusChoices(models.TextChoices):
        ACTIVE = 'ACTIVE', _('Active')
        INACTIVE = 'INACTIVE', _('Inactive')
        REVIEW = 'REVIEW', _('Review')
    
    class GenderChoices(models.TextChoices):
        MALE = 'MALE', _('Male')
        FEMALE = 'FEMALE', _('Female')
        OTHER = 'OTHER', _('Other')
    
    doctorId = models.ForeignKey(User, verbose_name=_('Doctor'), related_name='ayupilot_patients', db_column='doctor_id', on_delete=models.CASCADE)
    name = models.CharField(verbose_name=_('Patient Name'), max_length=255, db_column='name')
    age = models.IntegerField(verbose_name=_('Age'), db_column='age')
    gender = models.CharField(verbose_name=_('Gender'), max_length=10, choices=GenderChoices.choices, db_column='gender')
    phone = models.CharField(verbose_name=_('Phone Number'), max_length=20, db_column='phone')
    abhaNumber = models.CharField(verbose_name=_('ABHA Number'), max_length=20, db_column='abha_number', null=True)
    chiefComplaints = models.TextField(verbose_name=_('Chief Complaints'), db_column='chief_complaints', null=True)
    medicalHistory = models.TextField(verbose_name=_('Medical History'), db_column='medical_history', null=True)
    familyHistory = models.TextField(verbose_name=_('Family History'), db_column='family_history', null=True)
    surgicalHistory = models.TextField(verbose_name=_('Surgical History'), db_column='surgical_history', null=True)
    prakritiVata = models.IntegerField(verbose_name=_('Prakriti Vata %'), default=33, db_column='prakriti_vata')
    prakritiPitta = models.IntegerField(verbose_name=_('Prakriti Pitta %'), default=33, db_column='prakriti_pitta')
    prakritiKapha = models.IntegerField(verbose_name=_('Prakriti Kapha %'), default=34, db_column='prakriti_kapha')
    vikritiVata = models.IntegerField(verbose_name=_('Vikriti Vata %'), default=33, db_column='vikriti_vata')
    vikritiPitta = models.IntegerField(verbose_name=_('Vikriti Pitta %'), default=33, db_column='vikriti_pitta')
    vikritiKapha = models.IntegerField(verbose_name=_('Vikriti Kapha %'), default=34, db_column='vikriti_kapha')
    agniStatus = models.CharField(verbose_name=_('Agni Status'), max_length=100, db_column='agni_status', null=True)
    amaLevel = models.CharField(verbose_name=_('Ama Level'), max_length=50, db_column='ama_level', null=True)
    ojasLevel = models.CharField(verbose_name=_('Ojas Level'), max_length=50, db_column='ojas_level', null=True)
    dhatuStatus = models.CharField(verbose_name=_('Dhatu Status'), max_length=200, db_column='dhatu_status', null=True)
    status = models.CharField(verbose_name=_('Status'), max_length=20, choices=StatusChoices.choices, default=StatusChoices.ACTIVE, db_column='status')
    lastVisit = models.DateField(verbose_name=_('Last Visit'), db_column='last_visit', null=True)

    class Meta:
        db_table = 'ayupilot_patient'
        verbose_name = _('Patient')
        verbose_name_plural = _('Patients')
        managed = True
        indexes = [
            models.Index(fields=['doctorId', 'createdAt']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['doctorId', 'phone'], name='unique_patient_doctor_phone'),
        ]

    def __str__(self):
        return f"{self.name} - {self.age}y"



class Medicine(AtomicBaseModel):
    """Master table for all medicines"""
    name = models.CharField(verbose_name=_('Medicine Name'), max_length=255, db_column='name', unique=True)
    description = models.TextField(verbose_name=_('Description'), db_column='description', null=True)
    # Add more fields as needed (e.g., manufacturer, type)

    class Meta:
        db_table = 'ayupilot_medicine'
        verbose_name = _('Medicine')
        verbose_name_plural = _('Medicines')
        managed = True

    def __str__(self):
        return self.name


class Prescription(AtomicBaseModel):
    """Link table for Patient-Medicine M-M relationship with extra fields"""
    patientId = models.ForeignKey(Patient, verbose_name=_('Patient'), related_name='prescriptions', db_column='patient_id', on_delete=models.CASCADE)
    medicineId = models.ForeignKey(Medicine, verbose_name=_('Medicine'), related_name='prescriptions', db_column='medicine_id', on_delete=models.CASCADE)
    dosage = models.CharField(verbose_name=_('Dosage'), max_length=100, db_column='dosage')
    frequency = models.CharField(verbose_name=_('Frequency'), max_length=100, db_column='frequency')
    duration = models.CharField(verbose_name=_('Duration'), max_length=100, db_column='duration', null=True)
    instructions = models.TextField(verbose_name=_('Instructions'), db_column='instructions', null=True)

    class Meta:
        db_table = 'ayupilot_prescription'
        verbose_name = _('Prescription')
        verbose_name_plural = _('Prescriptions')
        managed = True
        constraints = [
            models.UniqueConstraint(fields=['patientId', 'medicineId'], name='unique_prescription_per_patient_medicine'),
        ]

    def __str__(self):
        return f"{self.patientId.name} - {self.medicineId.name}"


class Appointment(AtomicBaseModel):
    """Appointment scheduling model"""
    
    class TypeChoices(models.TextChoices):
        NEW_CASE = 'NEW_CASE', _('New Case')
        FOLLOW_UP = 'FOLLOW_UP', _('Follow-up')
        CONSULTATION = 'CONSULTATION', _('Consultation')
    
    class StatusChoices(models.TextChoices):
        SCHEDULED = 'SCHEDULED', _('Scheduled')
        COMPLETED = 'COMPLETED', _('Completed')
        CANCELLED = 'CANCELLED', _('Cancelled')
        NO_SHOW = 'NO_SHOW', _('No Show')
    
    patientId = models.ForeignKey(Patient, verbose_name=_('Patient'), related_name='appointments', db_column='patient_id', on_delete=models.CASCADE)
    doctorId = models.ForeignKey(User, verbose_name=_('Doctor'), related_name='ayupilot_appointments', db_column='doctor_id', on_delete=models.CASCADE)
    appointmentDate = models.DateField(verbose_name=_('Appointment Date'), db_column='appointment_date')
    appointmentTime = models.TimeField(verbose_name=_('Appointment Time'), db_column='appointment_time')
    appointmentType = models.CharField(verbose_name=_('Appointment Type'), max_length=20, choices=TypeChoices.choices, db_column='appointment_type')
    reason = models.TextField(verbose_name=_('Reason for Visit'), db_column='reason', null=True)
    notes = models.TextField(verbose_name=_('Notes'), db_column='notes', null=True)
    status = models.CharField(verbose_name=_('Status'), max_length=20, choices=StatusChoices.choices, default=StatusChoices.SCHEDULED, db_column='status')
    
    class Meta:
        db_table = 'ayupilot_appointment'
        verbose_name = _('Appointment')
        verbose_name_plural = _('Appointments')
        managed = True
        indexes = [
            models.Index(fields=['doctorId', 'appointmentDate']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['patientId', 'doctorId', 'appointmentDate', 'appointmentTime'], name='unique_appointment_per_patient_doctor_time'),
        ]
    
    def __str__(self):
        return f"{self.patientId.name} - {self.appointmentDate} {self.appointmentTime}"


class ImageAnalysis(AtomicBaseModel):
    """Model for storing image analysis results"""
    
    class ImageTypeChoices(models.TextChoices):
        TONGUE = 'TONGUE', _('Tongue')
        IRIS = 'IRIS', _('Iris')
        NAILS = 'NAILS', _('Nails')
        SKIN = 'SKIN', _('Skin')
    
    class StatusChoices(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        ANALYZING = 'ANALYZING', _('Analyzing')
        COMPLETED = 'COMPLETED', _('Completed')
        FAILED = 'FAILED', _('Failed')
    
    patientId = models.ForeignKey(Patient, verbose_name=_('Patient'), related_name='image_analyses', db_column='patient_id', on_delete=models.CASCADE)
    imageType = models.CharField(verbose_name=_('Image Type'), max_length=10, choices=ImageTypeChoices.choices, db_column='image_type')
    imageUrl = models.URLField(verbose_name=_('Image URL'), db_column='image_url', null=True)
    imageData = models.TextField(verbose_name=_('Base64 Image Data'), db_column='image_data', null=True)
    fileName = models.CharField(verbose_name=_('File Name'), max_length=255, db_column='file_name', null=True)
    analysisResult = models.TextField(verbose_name=_('Analysis Result'), db_column='analysis_result', null=True)
    status = models.CharField(verbose_name=_('Analysis Status'), max_length=20, choices=StatusChoices.choices, default=StatusChoices.PENDING, db_column='status')
    
    class Meta:
        db_table = 'ayupilot_image_analysis'
        verbose_name = _('Image Analysis')
        verbose_name_plural = _('Image Analyses')
        managed = True
    
    def __str__(self):
        return f"{self.patientId.name} - {self.imageType}"


class DocumentAnalysis(AtomicBaseModel):
    """Model for storing document analysis results"""
    
    class DocumentTypeChoices(models.TextChoices):
        BLOOD_REPORTS = 'BLOOD_REPORTS', _('Blood Reports')
        LAB_REPORTS = 'LAB_REPORTS', _('Lab Reports')
        OTHER_DOCUMENTS = 'OTHER_DOCUMENTS', _('Other Documents')
    
    class StatusChoices(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        ANALYZING = 'ANALYZING', _('Analyzing')
        COMPLETED = 'COMPLETED', _('Completed')
        FAILED = 'FAILED', _('Failed')
    
    patientId = models.ForeignKey(Patient, verbose_name=_('Patient'), related_name='document_analyses', db_column='patient_id', on_delete=models.CASCADE)
    documentType = models.CharField(verbose_name=_('Document Type'), max_length=20, choices=DocumentTypeChoices.choices, db_column='document_type')
    documentUrl = models.URLField(verbose_name=_('Document URL'), db_column='document_url')
    documentData = models.TextField(verbose_name=_('Base64 Document Data'), db_column='document_data', null=True)
    fileName = models.CharField(verbose_name=_('File Name'), max_length=255, db_column='file_name')
    fileType = models.CharField(verbose_name=_('File Type'), max_length=100, db_column='file_type')
    analysisResult = models.TextField(verbose_name=_('Analysis Result'), db_column='analysis_result', null=True)
    status = models.CharField(verbose_name=_('Analysis Status'), max_length=20, choices=StatusChoices.choices, default=StatusChoices.PENDING, db_column='status')
    
    class Meta:
        db_table = 'ayupilot_document_analysis'
        verbose_name = _('Document Analysis')
        verbose_name_plural = _('Document Analyses')
        managed = True
    
    def __str__(self):
        return f"{self.patientId.name} - {self.fileName}"


class ClinicalReport(AtomicBaseModel):
    """Model for storing AI-generated clinical intelligence reports"""
    
    class StatusChoices(models.TextChoices):
        GENERATING = 'GENERATING', _('Generating')
        COMPLETED = 'COMPLETED', _('Completed')
        FAILED = 'FAILED', _('Failed')
    
    patientId = models.ForeignKey(Patient, verbose_name=_('Patient'), related_name='clinical_reports', db_column='patient_id', on_delete=models.CASCADE)
    patientOverview = models.TextField(verbose_name=_('Patient Overview'), db_column='patient_overview', null=True)
    keyClinicalFindings = models.JSONField(verbose_name=_('Key Clinical Findings'), db_column='key_clinical_findings', null=True)
    currentHealthStatus = models.TextField(verbose_name=_('Current Health Status'), db_column='current_health_status', null=True)
    followUpRecommendation = models.TextField(verbose_name=_('Follow-up Recommendation'), db_column='follow_up_recommendation', null=True)
    primaryDoshaImbalance = models.JSONField(verbose_name=_('Primary Dosha Imbalance'), db_column='primary_dosha_imbalance', null=True)
    impactedSrotas = models.JSONField(verbose_name=_('Impacted Srotas'), db_column='impacted_srotas', null=True)
    suggestedCondition = models.JSONField(verbose_name=_('Suggested Condition'), db_column='suggested_condition', null=True)
    prakritiAssessment = models.JSONField(verbose_name=_('Prakriti Assessment'), db_column='prakriti_assessment', null=True)
    vikritiAssessment = models.JSONField(verbose_name=_('Vikriti Assessment'), db_column='vikriti_assessment', null=True)
    diagnosticSummary = models.JSONField(verbose_name=_('Diagnostic Summary'), db_column='diagnostic_summary', null=True)
    recommendedActions = models.JSONField(verbose_name=_('Recommended Actions'), db_column='recommended_actions', null=True)
    status = models.CharField(verbose_name=_('Generation Status'), max_length=20, choices=StatusChoices.choices, default=StatusChoices.GENERATING, db_column='status')
    
    class Meta:
        db_table = 'ayupilot_clinical_report'
        verbose_name = _('Clinical Report')
        verbose_name_plural = _('Clinical Reports')
        managed = True
    
    def __str__(self):
        return f"Clinical Report - {self.patientId.name} - {self.createdAt.date()}"


class SNLPrescription(AtomicBaseModel):
    """Model for storing SNL (Supplements, Nutrition, Lifestyle) prescriptions"""
    
    class StatusChoices(models.TextChoices):
        GENERATING = 'GENERATING', _('Generating')
        COMPLETED = 'COMPLETED', _('Completed')
        FAILED = 'FAILED', _('Failed')
    
    patientId = models.ForeignKey(Patient, verbose_name=_('Patient'), related_name='snl_prescriptions', db_column='patient_id', on_delete=models.CASCADE)
    prescriptionContent = models.TextField(verbose_name=_('Prescription Content'), db_column='prescription_content')
    status = models.CharField(verbose_name=_('Generation Status'), max_length=20, choices=StatusChoices.choices, default=StatusChoices.GENERATING, db_column='status')
    
    class Meta:
        db_table = 'ayupilot_snl_prescription'
        verbose_name = _('SNL Prescription')
        verbose_name_plural = _('SNL Prescriptions')
        managed = True
    
    def __str__(self):
        return f"SNL Prescription - {self.patientId.name} - {self.createdAt.date()}"


class KnowledgeReference(AtomicBaseModel):
    """Model for storing knowledge base references"""
    
    class StatusChoices(models.TextChoices):
        GENERATING = 'GENERATING', _('Generating')
        COMPLETED = 'COMPLETED', _('Completed')
        FAILED = 'FAILED', _('Failed')
    
    patientId = models.ForeignKey(Patient, verbose_name=_('Patient'), related_name='knowledge_references', db_column='patient_id', on_delete=models.CASCADE)
    referencesContent = models.TextField(verbose_name=_('References Content'), db_column='references_content')
    status = models.CharField(verbose_name=_('Generation Status'), max_length=20, choices=StatusChoices.choices, default=StatusChoices.GENERATING, db_column='status')
    
    class Meta:
        db_table = 'ayupilot_knowledge_reference'
        verbose_name = _('Knowledge Reference')
        verbose_name_plural = _('Knowledge References')
        managed = True
    
    def __str__(self):
        return f"Knowledge References - {self.patientId.name} - {self.createdAt.date()}"


class ChatMessage(AtomicBaseModel):
    """Model for storing AI assistant chat messages"""
    
    class RoleChoices(models.TextChoices):
        USER = 'USER', _('User')
        ASSISTANT = 'ASSISTANT', _('Assistant')
    
    patientId = models.ForeignKey(Patient, verbose_name=_('Patient'), related_name='chat_messages', db_column='patient_id', on_delete=models.CASCADE, null=True)
    userId = models.ForeignKey(User, verbose_name=_('User'), related_name='ayupilot_chat_messages', db_column='user_id', on_delete=models.CASCADE)
    role = models.CharField(verbose_name=_('Message Role'), max_length=10, choices=RoleChoices.choices, db_column='role')
    content = models.TextField(verbose_name=_('Message Content'), db_column='content')
    
    class Meta:
        db_table = 'ayupilot_chat_message'
        verbose_name = _('Chat Message')
        verbose_name_plural = _('Chat Messages')
        managed = True
    
    def __str__(self):
        return f"{self.role} - {self.content[:50]}..."

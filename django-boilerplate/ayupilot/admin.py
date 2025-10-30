from django.contrib import admin
from .models import (
    Patient, Appointment, ImageAnalysis,
    DocumentAnalysis, ClinicalReport, SNLPrescription,
    KnowledgeReference, ChatMessage,Medicine, Prescription
)


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('name', 'age', 'gender', 'phone', 'status', 'doctorId', 'createdAt')
    list_filter = ('status', 'gender', 'doctorId', 'createdAt')
    search_fields = ('name', 'phone', 'abhaNumber')
    readonly_fields = ('id', 'createdAt', 'updatedAt')
    ordering = ('-createdAt',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'age', 'gender', 'phone', 'abhaNumber', 'doctorId')
        }),
        ('Medical History', {
            'fields': ('chiefComplaints', 'medicalHistory', 'familyHistory', 'surgicalHistory')
        }),
        ('Prakriti Assessment', {
            'fields': ('prakritiVata', 'prakritiPitta', 'prakritiKapha')
        }),
        ('Vikriti Assessment', {
            'fields': ('vikritiVata', 'vikritiPitta', 'vikritiKapha')
        }),
        ('Diagnostic Information', {
            'fields': ('agniStatus', 'amaLevel', 'ojasLevel', 'dhatuStatus')
        }),
        ('Status & Metadata', {
            'fields': ('status', 'lastVisit', 'createdAt', 'updatedAt'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description', 'createdAt', 'updatedAt')
    list_filter = ('createdAt',)
    search_fields = ('name',)
    readonly_fields = ('id', 'createdAt', 'updatedAt')


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patientId', 'doctorId', 'appointmentDate', 'appointmentTime', 'appointmentType', 'status')
    list_filter = ('appointmentType', 'status', 'appointmentDate', 'doctorId')
    search_fields = ('patientId__name', 'reason')
    readonly_fields = ('id', 'createdAt', 'updatedAt')
    ordering = ('appointmentDate', 'appointmentTime')


@admin.register(ImageAnalysis)
class ImageAnalysisAdmin(admin.ModelAdmin):
    list_display = ('patientId', 'imageType', 'fileName', 'status', 'createdAt')
    list_filter = ('imageType', 'status', 'createdAt')
    search_fields = ('patientId__name', 'fileName')
    readonly_fields = ('id', 'createdAt', 'updatedAt', 'analysisResult')
    ordering = ('-createdAt',)


@admin.register(DocumentAnalysis)
class DocumentAnalysisAdmin(admin.ModelAdmin):
    list_display = ('patientId', 'documentType', 'fileName', 'status', 'createdAt')
    list_filter = ('documentType', 'status', 'createdAt')
    search_fields = ('patientId__name', 'fileName')
    readonly_fields = ('id', 'createdAt', 'updatedAt', 'analysisResult')
    ordering = ('-createdAt',)


@admin.register(ClinicalReport)
class ClinicalReportAdmin(admin.ModelAdmin):
    list_display = ('patientId', 'status', 'createdAt')
    list_filter = ('status', 'createdAt')
    search_fields = ('patientId__name',)
    readonly_fields = ('id', 'createdAt', 'updatedAt')
    ordering = ('-createdAt',)


@admin.register(SNLPrescription)
class SNLPrescriptionAdmin(admin.ModelAdmin):
    list_display = ('patientId', 'status', 'createdAt')
    list_filter = ('status', 'createdAt')
    search_fields = ('patientId__name',)
    readonly_fields = ('id', 'createdAt', 'updatedAt')
    ordering = ('-createdAt',)


@admin.register(KnowledgeReference)
class KnowledgeReferenceAdmin(admin.ModelAdmin):
    list_display = ('patientId', 'status', 'createdAt')
    list_filter = ('status', 'createdAt')
    search_fields = ('patientId__name',)
    readonly_fields = ('id', 'createdAt', 'updatedAt')
    ordering = ('-createdAt',)


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('userId', 'patientId', 'role', 'content_preview', 'createdAt')
    list_filter = ('role', 'createdAt')
    search_fields = ('userId__email', 'patientId__name', 'content')
    readonly_fields = ('id', 'createdAt', 'updatedAt')
    ordering = ('-createdAt',)
    
    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content Preview'

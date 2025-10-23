from rest_framework import serializers
from atomicloops.serializers import AtomicSerializer
from .models import (
    Patient, Medication, Appointment, ImageAnalysis, 
    DocumentAnalysis, ClinicalReport, SNLPrescription, 
    KnowledgeReference, ChatMessage
)


class MedicationSerializer(AtomicSerializer):
    """Serializer for Medication model"""
    
    class Meta:
        model = Medication
        fields = (
            'id', 'createdAt', 'updatedAt',
            'name', 'dosage', 'frequency'
        )
        get_fields = fields
        list_fields = fields


class PatientSerializer(AtomicSerializer):
    """Serializer for Patient model"""
    
    # Nested medications
    medications = MedicationSerializer(many=True, read_only=True)
    
    # Computed fields for frontend compatibility
    dosha = serializers.SerializerMethodField()
    
    class Meta:
        model = Patient
        fields = (
            'id', 'createdAt', 'updatedAt',
            'name', 'age', 'gender', 'phone', 'abhaNumber',
            'chiefComplaints', 'medicalHistory', 'familyHistory', 'surgicalHistory',
            'prakritiVata', 'prakritiPitta', 'prakritiKapha',
            'vikritiVata', 'vikritiPitta', 'vikritiKapha',
            'agniStatus', 'amaLevel', 'ojasLevel', 'dhatuStatus',
            'status', 'lastVisit', 'doctorId',
            'medications', 'dosha'
        )
        get_fields = fields
        list_fields = (
            'id', 'createdAt', 'updatedAt',
            'name', 'age', 'gender', 'phone', 'status', 'lastVisit', 'dosha'
        )
    
    def get_dosha(self, obj):
        """Calculate primary dosha based on Prakriti percentages"""
        doshas = {
            'vata': obj.prakritiVata,
            'pitta': obj.prakritiPitta,
            'kapha': obj.prakritiKapha
        }
        primary = max(doshas, key=doshas.get)
        secondary = sorted(doshas.items(), key=lambda x: x[1], reverse=True)[1][0]
        
        if doshas[primary] - doshas[secondary] < 10:
            return f"{primary.title()}-{secondary.title()}"
        return primary.title()
    
    def create(self, validated_data):
        """Set doctor to current user if not provided"""
        if 'doctorId' not in validated_data:
            validated_data['doctorId'] = self.context['request'].user
        return super().create(validated_data)


class AppointmentSerializer(AtomicSerializer):
    """Serializer for Appointment model"""
    
    # Read-only patient info
    patientName = serializers.CharField(source='patientId.name', read_only=True)
    patientAge = serializers.IntegerField(source='patientId.age', read_only=True)
    patientGender = serializers.CharField(source='patientId.gender', read_only=True)
    patientPhone = serializers.CharField(source='patientId.phone', read_only=True)
    
    # Computed fields for frontend
    time = serializers.SerializerMethodField()
    patient = serializers.SerializerMethodField()
    type = serializers.CharField(source='appointmentType', read_only=True)
    
    class Meta:
        model = Appointment
        fields = (
            'id', 'createdAt', 'updatedAt',
            'patientId', 'doctorId', 'appointmentDate', 'appointmentTime',
            'appointmentType', 'reason', 'notes', 'status',
            'patientName', 'patientAge', 'patientGender', 'patientPhone',
            'time', 'patient', 'type'
        )
        read_only_fields = ('id', 'createdAt', 'updatedAt', 'doctorId')
        get_fields = fields
        list_fields = fields
    
    def get_time(self, obj):
        """Format time for frontend display"""
        return obj.appointmentTime.strftime('%I:%M %p')
    
    def get_patient(self, obj):
        """Get patient name for frontend"""
        return obj.patientId.name
    
    def create(self, validated_data):
        """Set doctor to current user if not provided"""
        if 'doctorId' not in validated_data:
            validated_data['doctorId'] = self.context['request'].user
        return super().create(validated_data)


class ImageAnalysisSerializer(AtomicSerializer):
    """Serializer for ImageAnalysis model"""
    
    # Read-only patient info
    patientName = serializers.CharField(source='patientId.name', read_only=True)
    
    class Meta:
        model = ImageAnalysis
        fields = (
            'id', 'createdAt', 'updatedAt',
            'patientId', 'imageType', 'imageUrl', 'imageData',
            'fileName', 'analysisResult', 'status',
            'patientName'
        )
        get_fields = fields
        list_fields = (
            'id', 'createdAt', 'updatedAt',
            'patientId', 'imageType', 'fileName', 'status',
            'patientName'
        )
    
    def validate_imageType(self, value):
        """Validate image type"""
        valid_types = ['TONGUE', 'IRIS', 'NAILS', 'SKIN']
        if value not in valid_types:
            raise serializers.ValidationError(f"Image type must be one of: {', '.join(valid_types)}")
        return value


class DocumentAnalysisSerializer(AtomicSerializer):
    """Serializer for DocumentAnalysis model"""
    
    # Read-only patient info
    patientName = serializers.CharField(source='patientId.name', read_only=True)
    
    class Meta:
        model = DocumentAnalysis
        fields = (
            'id', 'createdAt', 'updatedAt',
            'patientId', 'documentType', 'documentUrl', 'documentData',
            'fileName', 'fileType', 'analysisResult', 'status',
            'patientName'
        )
        get_fields = fields
        list_fields = (
            'id', 'createdAt', 'updatedAt',
            'patientId', 'documentType', 'fileName', 'fileType', 'status',
            'patientName'
        )
    
    def validate_documentType(self, value):
        """Validate document type"""
        valid_types = ['BLOOD_REPORTS', 'LAB_REPORTS', 'OTHER_DOCUMENTS']
        if value not in valid_types:
            raise serializers.ValidationError(f"Document type must be one of: {', '.join(valid_types)}")
        return value


class ClinicalReportSerializer(AtomicSerializer):
    """Serializer for ClinicalReport model"""
    
    # Read-only patient info
    patientName = serializers.CharField(source='patientId.name', read_only=True)
    
    class Meta:
        model = ClinicalReport
        fields = (
            'id', 'createdAt', 'updatedAt',
            'patientId', 'patientOverview', 'keyClinicalFindings',
            'currentHealthStatus', 'followUpRecommendation',
            'primaryDoshaImbalance', 'impactedSrotas', 'suggestedCondition',
            'prakritiAssessment', 'vikritiAssessment', 'diagnosticSummary',
            'recommendedActions', 'status',
            'patientName'
        )
        get_fields = fields
        list_fields = (
            'id', 'createdAt', 'updatedAt',
            'patientId', 'patientOverview', 'status',
            'patientName'
        )


class SNLPrescriptionSerializer(AtomicSerializer):
    """Serializer for SNLPrescription model"""
    
    # Read-only patient info
    patientName = serializers.CharField(source='patientId.name', read_only=True)
    
    class Meta:
        model = SNLPrescription
        fields = (
            'id', 'createdAt', 'updatedAt',
            'patientId', 'prescriptionContent', 'status',
            'patientName'
        )
        get_fields = fields
        list_fields = fields


class KnowledgeReferenceSerializer(AtomicSerializer):
    """Serializer for KnowledgeReference model"""
    
    # Read-only patient info
    patientName = serializers.CharField(source='patientId.name', read_only=True)
    
    class Meta:
        model = KnowledgeReference
        fields = (
            'id', 'createdAt', 'updatedAt',
            'patientId', 'referencesContent', 'status',
            'patientName'
        )
        get_fields = fields
        list_fields = fields


class ChatMessageSerializer(AtomicSerializer):
    """Serializer for ChatMessage model"""
    
    # Read-only user info
    userName = serializers.CharField(source='userId.email', read_only=True)
    patientName = serializers.CharField(source='patientId.name', read_only=True)
    
    class Meta:
        model = ChatMessage
        fields = (
            'id', 'createdAt', 'updatedAt',
            'patientId', 'userId', 'role', 'content',
            'userName', 'patientName'
        )
        get_fields = fields
        list_fields = fields
    
    def create(self, validated_data):
        """Set user to current user if not provided"""
        if 'userId' not in validated_data:
            validated_data['userId'] = self.context['request'].user
        return super().create(validated_data)


# Specialized serializers for API endpoints

class PatientCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating patients with medications"""
    
    medications = MedicationSerializer(many=True, required=False)
    
    class Meta:
        model = Patient
        fields = (
            'name', 'age', 'gender', 'phone', 'abhaNumber',
            'chiefComplaints', 'medicalHistory', 'familyHistory', 'surgicalHistory',
            'prakritiVata', 'prakritiPitta', 'prakritiKapha',
            'vikritiVata', 'vikritiPitta', 'vikritiKapha',
            'agniStatus', 'amaLevel', 'ojasLevel', 'dhatuStatus',
            'medications'
        )
    
    def create(self, validated_data):
        medications_data = validated_data.pop('medications', [])
        validated_data['doctorId'] = self.context['request'].user
        
        patient = Patient.objects.create(**validated_data)
        
        for medication_data in medications_data:
            Medication.objects.create(patientId=patient, **medication_data)
        
        return patient


class ImageUploadSerializer(serializers.Serializer):
    """Serializer for image upload endpoint"""
    
    patientId = serializers.UUIDField()
    imageType = serializers.ChoiceField(choices=['TONGUE', 'IRIS', 'NAILS', 'SKIN'])
    imageData = serializers.CharField()
    fileName = serializers.CharField(max_length=255)
    
    def validate_imageData(self, value):
        """Validate base64 image data"""
        if not value.startswith('data:image/'):
            raise serializers.ValidationError("Invalid image data format")
        return value


class DocumentUploadSerializer(serializers.Serializer):
    """Serializer for document upload endpoint"""
    
    patientId = serializers.UUIDField()
    documentType = serializers.ChoiceField(choices=['BLOOD_REPORTS', 'LAB_REPORTS', 'OTHER_DOCUMENTS'])
    documentData = serializers.CharField()
    fileName = serializers.CharField(max_length=255)
    fileType = serializers.CharField(max_length=100)
    
    def validate_documentData(self, value):
        """Validate base64 document data"""
        if not (value.startswith('data:application/') or value.startswith('data:image/')):
            raise serializers.ValidationError("Invalid document data format")
        return value


class GenerateReportSerializer(serializers.Serializer):
    """Serializer for generating clinical reports"""
    
    patientId = serializers.UUIDField()


class ChatRequestSerializer(serializers.Serializer):
    """Serializer for chat requests"""
    
    message = serializers.CharField()
    patientId = serializers.UUIDField(required=False)


class DashboardStatsSerializer(serializers.Serializer):
    """Serializer for dashboard statistics"""
    
    totalPatients = serializers.IntegerField()
    todayAppointments = serializers.IntegerField()
    pendingAnalyses = serializers.IntegerField()
    completedReports = serializers.IntegerField()

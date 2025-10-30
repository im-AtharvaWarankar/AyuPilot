from rest_framework import serializers
from atomicloops.serializers import AtomicSerializer
from .models import (
    Patient, Medicine, Appointment, ImageAnalysis, 
    DocumentAnalysis, ClinicalReport, SNLPrescription, 
    KnowledgeReference, ChatMessage, Prescription
)
from django.db import transaction
class PrescriptionSerializer(AtomicSerializer):
    patientName = serializers.CharField(source="patientId.name", read_only=True)
    medicineName = serializers.CharField(source="medicineId.name", read_only=True)

    class Meta:
        model = Prescription
        fields = (
            "id", "createdAt", "updatedAt", "patientId", "medicineId", "dosage", "frequency", "duration", "instructions", "patientName", "medicineName"
        )
        get_fields = fields
        list_fields = (
            "id", "createdAt", "updatedAt", "patientId", "medicineId", "dosage", "frequency", "duration", "patientName", "medicineName"
        )

    def validate(self, data):
        required = ["patientId", "medicineId", "dosage", "frequency"]
        for field in required:
            if not data.get(field):
                raise serializers.ValidationError({field: f'{field} is required.'})
        # Unique constraint check
        if Prescription.objects.filter(patientId=data["patientId"], medicineId=data["medicineId"]).exists():
            raise serializers.ValidationError({"prescription": "This medicine is already prescribed to this patient."})
        return data



class MedicineSerializer(AtomicSerializer):
    """Serializer for Medicine model"""

    class Meta:
        model = Medicine
        fields = (
            'id', 'createdAt', 'updatedAt',
            'name', 'description'
        )
        get_fields = fields
        list_fields = fields

    def validate_name(self, value):
        if not value or len(value) < 2:
            raise serializers.ValidationError('Medicine name must be at least 2 characters.')
        return value


class PatientSerializer(AtomicSerializer):
    medications = MedicineSerializer(many=True, read_only=True)
    dosha = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = (
            "id", "createdAt", "updatedAt", "name", "age", "gender", "phone", "abhaNumber",
            "chiefComplaints", "medicalHistory", "familyHistory", "surgicalHistory",
            "prakritiVata", "prakritiPitta", "prakritiKapha",
            "vikritiVata", "vikritiPitta", "vikritiKapha",
            "agniStatus", "amaLevel", "ojasLevel", "dhatuStatus",
            "status", "lastVisit", "doctorId", "medications", "dosha"
        )
        get_fields = fields
        list_fields = (
            "id", "createdAt", "updatedAt", "name", "age", "gender", "phone", "status", "lastVisit", "dosha"
        )

    def validate(self, data):
        if sum([data.get(f, 0) for f in ["prakritiVata", "prakritiPitta", "prakritiKapha"]]) != 100:
            raise serializers.ValidationError({"prakriti": "Prakriti percentages must add up to 100."})
        if sum([data.get(f, 0) for f in ["vikritiVata", "vikritiPitta", "vikritiKapha"]]) != 100:
            raise serializers.ValidationError({"vikriti": "Vikriti percentages must add up to 100."})
        return data

    def get_dosha(self, obj):
        doshas = {"vata": obj.prakritiVata, "pitta": obj.prakritiPitta, "kapha": obj.prakritiKapha}
        sorted_doshas = sorted(doshas.items(), key=lambda x: x[1], reverse=True)
        if sorted_doshas[0][1] - sorted_doshas[1][1] < 10:
            return f"{sorted_doshas[0][0].title()}-{sorted_doshas[1][0].title()}"
        return sorted_doshas[0][0].title()

    def create(self, validated_data):
        validated_data.setdefault("doctorId", self.context["request"].user)
        return super().create(validated_data)


class AppointmentSerializer(AtomicSerializer):
    patientName = serializers.CharField(source="patientId.name", read_only=True)
    patientAge = serializers.IntegerField(source="patientId.age", read_only=True)
    patientGender = serializers.CharField(source="patientId.gender", read_only=True)
    patientPhone = serializers.CharField(source="patientId.phone", read_only=True)
    time = serializers.SerializerMethodField()
    patient = serializers.SerializerMethodField()
    type = serializers.CharField(source="appointmentType", read_only=True)

    class Meta:
        model = Appointment
        fields = (
            "id", "createdAt", "updatedAt", "patientId", "appointmentDate", "appointmentTime",
            "appointmentType", "reason", "notes", "status",
            "patientName", "patientAge", "patientGender", "patientPhone",
            "time", "patient", "type"
        )
        read_only_fields = ("id", "createdAt", "updatedAt", "doctorId")
        get_fields = fields
        list_fields = fields

    def get_time(self, obj):
        return obj.appointmentTime.strftime("%I:%M %p")

    def get_patient(self, obj):
        return obj.patientId.name

    def create(self, validated_data):
        # Set doctorId from request if not provided
        if not validated_data.get("doctorId") and "request" in self.context:
            validated_data["doctorId"] = self.context["request"].user
        with transaction.atomic():
            # Explicit duplicate check for patientId, doctorId,
            # appointmentDate, appointmentTime
            # appointmentTime
            if Appointment.objects.filter(
                patientId=validated_data['patientId'],
                doctorId=validated_data['doctorId'],
                appointmentDate=validated_data['appointmentDate'],
                appointmentTime=validated_data['appointmentTime']
            ).exists():
                raise serializers.ValidationError({
                    'appointment': (
                        'An appointment for this patient, doctor, date, and '
                        'time '
                        'already exists.'
                    )
                })
            return super().create(validated_data)

    def validate_appointmentDate(self, value):
        from datetime import date
        if value < date.today():
            raise serializers.ValidationError(
                'Appointment date cannot be in the past.'
            )
        return value

    def validate(self, data):
        required = [
            'patientId', 'appointmentDate', 'appointmentTime'
        ]
        for field in required:
            if not data.get(field):
                raise serializers.ValidationError({
                    field: f'{field} is required.'
                })
        return data


class ImageAnalysisSerializer(AtomicSerializer):
    patientName = serializers.CharField(
        source="patientId.name", read_only=True
    )

    class Meta:
        model = ImageAnalysis
        fields = (
            "id", "createdAt", "updatedAt", "patientId", "imageType",
            "imageUrl",
            "imageData",
            "fileName", "analysisResult", "status", "patientName"
        )
        get_fields = fields
        list_fields = (
            "id", "createdAt", "updatedAt", "patientId", "imageType",
            "fileName",
            "status", "patientName"
        )

    def validate_imageType(self, value):
        valid_types = ["TONGUE", "IRIS", "NAILS", "SKIN"]
        if value not in valid_types:
            raise serializers.ValidationError(
                f"Image type must be one of: {', '.join(valid_types)}"
            )
        return value


class DocumentAnalysisSerializer(AtomicSerializer):
    patientName = serializers.CharField(
        source="patientId.name", read_only=True
    )

    class Meta:
        model = DocumentAnalysis
        fields = (
            "id", "createdAt", "updatedAt", "patientId", "documentType",
            "documentUrl",
            "documentData",
            "fileName", "fileType", "analysisResult", "status", "patientName"
        )
        get_fields = fields
        list_fields = (
            "id", "createdAt", "updatedAt", "patientId", "documentType",
            "fileName",
            "fileType", "status", "patientName"
        )

    def validate_documentType(self, value):
        valid_types = ["BLOOD_REPORTS", "LAB_REPORTS", "OTHER_DOCUMENTS"]
        if value not in valid_types:
            raise serializers.ValidationError(
                f"Document type must be one of: {', '.join(valid_types)}"
            )
        return value


class ClinicalReportSerializer(AtomicSerializer):
    patientName = serializers.CharField(
        source="patientId.name", read_only=True
    )

    class Meta:
        model = ClinicalReport
        fields = (
            "id", "createdAt", "updatedAt", "patientId", "patientOverview",
            "keyClinicalFindings",
            "currentHealthStatus", "followUpRecommendation",
            "primaryDoshaImbalance", "impactedSrotas",
            "suggestedCondition", "prakritiAssessment", "vikritiAssessment",
            "diagnosticSummary",
            "recommendedActions", "status", "patientName"
        )
        get_fields = fields
        list_fields = (
            "id", "createdAt", "updatedAt", "patientId", "patientOverview",
            "status", "patientName"
        )


class SNLPrescriptionSerializer(AtomicSerializer):
    patientName = serializers.CharField(
        source="patientId.name", read_only=True
    )

    class Meta:
        model = SNLPrescription
        fields = (
            "id", "createdAt", "updatedAt", "patientId", "prescriptionContent",
            "status", "patientName"
        )
        get_fields = fields
        list_fields = fields


class KnowledgeReferenceSerializer(AtomicSerializer):
    patientName = serializers.CharField(
        source="patientId.name", read_only=True
    )

    class Meta:
        model = KnowledgeReference
        fields = (
            "id", "createdAt", "updatedAt", "patientId", "referencesContent",
            "status", "patientName"
        )
        get_fields = fields
        list_fields = fields


class ChatMessageSerializer(AtomicSerializer):
    userName = serializers.CharField(source="userId.email", read_only=True)
    patientName = serializers.CharField(
        source="patientId.name", read_only=True
    )

    class Meta:
        model = ChatMessage
        fields = (
            "id", "createdAt", "updatedAt", "patientId", "userId", "role",
            "content", "userName", "patientName"
        )
        get_fields = fields
        list_fields = fields

    def create(self, validated_data):
        validated_data.setdefault("userId", self.context["request"].user)
        return super().create(validated_data)


# Specialized serializers for API endpoints

class PatientCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating patients with medications"""
    
    medications = MedicineSerializer(many=True, required=False)
    
    class Meta:
        model = Patient
        fields = (
            'name', 'age', 'gender', 'phone', 'abhaNumber',
            'chiefComplaints', 'medicalHistory', 'familyHistory',
            'surgicalHistory',
            'prakritiVata', 'prakritiPitta', 'prakritiKapha',
            'vikritiVata', 'vikritiPitta', 'vikritiKapha',
            'agniStatus', 'amaLevel', 'ojasLevel', 'dhatuStatus',
            'medications'
        )
    
    def validate_phone(self, value):
        import re
        if not re.match(r'^[6-9]\d{9}$', value):
            raise serializers.ValidationError(
                'Enter a valid 10-digit Indian phone number starting with 6-9.'
            )
        return value

    def validate_age(self, value):
        if not (0 < value < 120):
            raise serializers.ValidationError('Enter a realistic age (1-119).')
        return value

    def validate(self, data):
        """Validate dosha percentages add up to 100"""
        # Check Prakriti percentages
        prakriti_vata = data.get('prakritiVata', 33)
        prakriti_pitta = data.get('prakritiPitta', 33)
        prakriti_kapha = data.get('prakritiKapha', 34)
        
        if prakriti_vata + prakriti_pitta + prakriti_kapha != 100:
            raise serializers.ValidationError({
                'prakriti': 'Prakriti percentages must add up to 100.'
            })
        
        # Check Vikriti percentages
        vikriti_vata = data.get('vikritiVata', 33)
        vikriti_pitta = data.get('vikritiPitta', 33)
        vikriti_kapha = data.get('vikritiKapha', 34)
        
        if vikriti_vata + vikriti_pitta + vikriti_kapha != 100:
            raise serializers.ValidationError({
                'vikriti': 'Vikriti percentages must add up to 100.'
            })
        
        # Required fields
        required = ['name', 'age', 'gender', 'phone']
        for field in required:
            if not data.get(field):
                raise serializers.ValidationError({
                    field: f'{field} is required.'
                })
        return data
    
    def create(self, validated_data):
        medications_data = validated_data.pop('medications', [])
        validated_data['doctorId'] = self.context['request'].user
        with transaction.atomic():
            # Explicit duplicate check for doctorId and phone
            if Patient.objects.filter(
                doctorId=validated_data['doctorId'],
                phone=validated_data['phone']
            ).exists():
                raise serializers.ValidationError({
                    'phone': (
                        'A patient with this phone number already exists for '
                        'this doctor.'
                    )
                })
            patient = Patient.objects.create(**validated_data)
            # Medication logic removed; update to use Prescription/Medicine if needed
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

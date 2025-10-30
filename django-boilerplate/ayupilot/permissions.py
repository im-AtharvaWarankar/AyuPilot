from rest_framework import permissions
from django.db.models import Q
from .models import Patient
from users.models import UserLevel


class IsAuthenticated(permissions.BasePermission):
    """
    Custom permission to only allow authenticated users.
    """
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner of the object.
        return obj.owner == request.user


class IsDoctorOrReadOnly(permissions.BasePermission):
    """
    Custom permission for doctor-related operations.
    Only allows doctors to create/modify, others can only read.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Allow read operations for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # For write operations, check if user is a doctor
        return hasattr(request.user, 'level') and request.user.level == UserLevel.DOCTOR


class IsPatientOwnerOrDoctor(permissions.BasePermission):
    """
    Custom permission for patient-related operations.
    Only allows the assigned doctor to access patient data.
    """
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)
    
    def has_object_permission(self, request, view, obj):
        # For Patient objects
        if hasattr(obj, 'doctorId'):
            return obj.doctorId == request.user
        
        # For objects related to patients (like appointments, analyses, etc.)
        if hasattr(obj, 'patientId'):
            return obj.patientId.doctorId == request.user
        
        return False


class IsPatientDoctorOnly(permissions.BasePermission):
    """
    Permission that only allows the patient's assigned doctor to access.
    Used for sensitive patient data like medical records, analyses, etc.
    """
    
    def has_permission(self, request, view):
        # TODO: Re-enable this for production
        return True
        # return bool(request.user and request.user.is_authenticated)
    
    def has_object_permission(self, request, view, obj):
        # TODO: Re-enable this for production
        return True
        # # Check if the current user is the doctor assigned to the patient
        # if hasattr(obj, 'patientId'):
        #     return obj.patientId.doctorId == request.user
        # elif hasattr(obj, 'doctorId'):
        #     return obj.doctorId == request.user
        # 
        # return False


class CanAccessPatientData(permissions.BasePermission):
    """
    Permission to check if user can access specific patient's data.
    Used for ViewSets that need to filter by patient access.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # If patient_id is provided in query params, check access
        patient_id = request.query_params.get('patient_id')
        if patient_id:
            try:
                patient = Patient.objects.get(id=patient_id, doctorId=request.user)
                return True
            except Patient.DoesNotExist:
                return False
        
        return True
    
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'patientId'):
            return obj.patientId.doctorId == request.user
        return True


class IsImageAnalysisOwner(permissions.BasePermission):
    """
    Permission for image analysis operations.
    Only the doctor who owns the patient can access image analyses.
    """
    
    def has_permission(self, request, view):
        # TODO: Re-enable this for production
        return True
        # return bool(request.user and request.user.is_authenticated)
    
    def has_object_permission(self, request, view, obj):
        # TODO: Re-enable this for production
        return True
        # return obj.patientId.doctorId == request.user


class IsDocumentAnalysisOwner(permissions.BasePermission):
    """
    Permission for document analysis operations.
    Only the doctor who owns the patient can access document analyses.
    """
    
    def has_permission(self, request, view):
        # TODO: Re-enable this for production
        return True
        # return bool(request.user and request.user.is_authenticated)
    
    def has_object_permission(self, request, view, obj):
        # TODO: Re-enable this for production
        return True
        # return obj.patientId.doctorId == request.user


class IsClinicalReportOwner(permissions.BasePermission):
    """
    Permission for clinical report operations.
    Only the doctor who owns the patient can access clinical reports.
    """
    
    def has_permission(self, request, view):
        # TODO: Re-enable this for production
        return True
        # return bool(request.user and request.user.is_authenticated)
    
    def has_object_permission(self, request, view, obj):
        # TODO: Re-enable this for production
        return True
        # return obj.patientId.doctorId == request.user


class IsChatMessageOwner(permissions.BasePermission):
    """
    Permission for chat message operations.
    Users can only access their own chat messages.
    """
    
    def has_permission(self, request, view):
        # TODO: Re-enable this for production
        return True
        # return bool(request.user and request.user.is_authenticated)
    
    def has_object_permission(self, request, view, obj):
        # TODO: Re-enable this for production
        return True
        # return obj.userId == request.user


class IsAppointmentParticipant(permissions.BasePermission):
    """
    Permission for appointment operations.
    Only the doctor or patient involved in the appointment can access it.
    """
    
    def has_permission(self, request, view):
        # TEMPORARY: Allow all requests for testing
        return True
        # TODO: Re-enable this for production:
        # return bool(request.user and request.user.is_authenticated)
    
    def has_object_permission(self, request, view, obj):
        # Check if user is the doctor for this appointment
        if obj.doctorId == request.user:
            return True
        
        # Check if user is the patient (if patients have user accounts)
        # This would need to be implemented based on your user model structure
        return False


class CanUploadFiles(permissions.BasePermission):
    """
    Permission for file upload operations.
    Only authenticated users who have access to the patient can upload files.
    """
    
    def has_permission(self, request, view):
        # TEMPORARY: Allow all requests for testing
        return True
        # TODO: Re-enable this for production:
        # if not request.user.is_authenticated:
        #     return False
        # 
        # # Check if patient_id is provided and user has access
        # # Handle both dict and QueryDict
        # try:
        #     if hasattr(request.data, 'get'):
        #         patient_id = request.data.get('patientId')
        #     else:
        #         return False
        #         
        #     if patient_id:
        #         try:
        #             Patient.objects.get(
        #                 id=patient_id, 
        #                 doctorId=request.user
        #             )
        #             return True
        #         except Patient.DoesNotExist:
        #             return False
        # except Exception:
        #     pass
        # 
        # return False


class CanGenerateReports(permissions.BasePermission):
    """
    Permission for AI report generation operations.
    Only the patient's doctor can generate reports.
    """

    def has_permission(self, request, view):
        # TEMPORARY: Allow all requests for testing
        return True
        # TODO: Re-enable this for production:
        # if not request.user.is_authenticated:
        #     return False
        #
        # # Check if patient_id is provided and user has access
        # # Handle both dict and QueryDict
        # try:
        #     if hasattr(request.data, 'get'):
        #         patient_id = request.data.get('patientId')
        #     else:
        #         return False
        #
        #     if patient_id:
        #         try:
        #             Patient.objects.get(
        #                 id=patient_id,
        #                 doctorId=request.user
        #             )
        #             return True
        #         except Patient.DoesNotExist:
        #             return False
        # except Exception:
        #     pass
        #
        # return False


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admins to edit.
    Regular users can only read.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return request.user.is_staff or request.user.is_superuser


class IsSuperUserOnly(permissions.BasePermission):
    """
    Permission that only allows superusers.
    Used for sensitive administrative operations.
    """
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser)


# Utility functions for permission checks

def user_can_access_patient(user, patient_id):
    """
    Utility function to check if a user can access a specific patient.
    """
    try:
        Patient.objects.get(id=patient_id, doctorId=user)
        return True
    except Patient.DoesNotExist:
        return False


def get_user_patients_queryset(user):
    """
    Utility function to get queryset of patients accessible to a user.
    """
    return Patient.objects.filter(doctorId=user)


def filter_by_patient_access(queryset, user, patient_field='patientId'):
    """
    Utility function to filter any queryset by patient access.
    """
    accessible_patients = get_user_patients_queryset(user)
    filter_kwargs = {f"{patient_field}__in": accessible_patients}
    return queryset.filter(**filter_kwargs)


# Permission class combinations for common use cases

class AyuPilotBasePermission(permissions.BasePermission):
    """
    Base permission class for AyuPilot app.
    Combines authentication and basic access control.
    
    TEMPORARY: Auth disabled for frontend testing
    TODO: Re-enable authentication for production
    """
    
    def has_permission(self, request, view):
        # TEMPORARY: Allow all requests for testing
        return True
        # TODO: Re-enable this for production:
        # return bool(request.user and request.user.is_authenticated)


class PatientDataPermission(permissions.BasePermission):
    """
    Combined permission for all patient-related data access.
    """
    
    def has_permission(self, request, view):
        # TEMPORARY: Allow all requests for testing
        return True
        # TODO: Re-enable this for production:
        # return bool(request.user and request.user.is_authenticated)
    
    def has_object_permission(self, request, view, obj):
        # Handle different object types
        if hasattr(obj, 'doctorId'):
            return obj.doctorId == request.user
        elif hasattr(obj, 'patientId'):
            return obj.patientId.doctorId == request.user
        elif hasattr(obj, 'userId'):
            return obj.userId == request.user
        
        return False

from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (
    PatientViewSet, MedicineViewSet, AppointmentViewSet, ImageAnalysisViewSet,
    DocumentAnalysisViewSet, ClinicalReportViewSet, SNLPrescriptionViewSet,
    KnowledgeReferenceViewSet, ChatMessageViewSet,
    ImageUploadView, DocumentUploadView, GenerateClinicalReportView,
    GenerateSNLPrescriptionView, GenerateKnowledgeReferencesView,
    AIChatView, DashboardStatsView,PrescriptionViewSet
)

# Create router for ViewSets
router = DefaultRouter()
router.register(r'patients', PatientViewSet, basename='patient')
router.register(r'medications', MedicineViewSet, basename='medication')
router.register(r'appointments', AppointmentViewSet, basename='appointment')
router.register(r'image-analyses', ImageAnalysisViewSet, basename='imageanalysis')
router.register(r'document-analyses', DocumentAnalysisViewSet, basename='documentanalysis')
router.register(r'clinical-reports', ClinicalReportViewSet, basename='clinicalreport')
router.register(r'snl-prescriptions', SNLPrescriptionViewSet, basename='snlprescription')
router.register(r'knowledge-references', KnowledgeReferenceViewSet, basename='knowledgereference')
router.register(r'chat-messages', ChatMessageViewSet, basename='chatmessage')
router.register(r'prescriptions', PrescriptionViewSet, basename='prescription')
# Custom API endpoints
urlpatterns = [
    # Dashboard
    path('dashboard/stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    
    # File uploads and AI processing
    path('upload/image/', ImageUploadView.as_view(), name='upload-image'),
    path('upload/document/', DocumentUploadView.as_view(), name='upload-document'),
    
    # AI generation endpoints
    path('generate/clinical-report/', GenerateClinicalReportView.as_view(), name='generate-clinical-report'),
    path('generate/snl-prescription/', GenerateSNLPrescriptionView.as_view(), name='generate-snl-prescription'),
    path('generate/knowledge-references/', GenerateKnowledgeReferencesView.as_view(), name='generate-knowledge-references'),
    
    # AI Chat
    path('chat/', AIChatView.as_view(), name='ai-chat'),
    
    # Include router URLs
    path('', include(router.urls)),
]

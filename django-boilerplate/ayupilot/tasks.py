from celery import shared_task
from django.conf import settings
from .models import (
    ImageAnalysis, DocumentAnalysis, ClinicalReport,
    SNLPrescription, KnowledgeReference, ChatMessage, Patient, Appointment
)
import logging
import os
from django.utils import timezone
from datetime import timedelta, datetime

logger = logging.getLogger(__name__)

# Import OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI package not installed. AI features will use mock responses.")


@shared_task(bind=True, queue='celery')
def analyze_image_task(self, image_analysis_id):
    """Async task for AI image analysis"""
    try:
        image_analysis = ImageAnalysis.objects.get(id=image_analysis_id)
        image_analysis.status = ImageAnalysis.StatusChoices.ANALYZING
        image_analysis.save()
        
        # TODO: Integrate with Claude API for actual image analysis
        # For now, return mock analysis
        mock_analysis = f"AI Analysis for {image_analysis.imageType}: Mock analysis result - to be integrated with Claude API"
        
        image_analysis.analysisResult = mock_analysis
        image_analysis.status = ImageAnalysis.StatusChoices.COMPLETED
        image_analysis.save()
        
        return {"status": "success", "image_analysis_id": str(image_analysis_id)}
    
    except ImageAnalysis.DoesNotExist:
        return {"status": "error", "message": "Image analysis not found"}
    except Exception as e:
        logger.error(f"Error in analyze_image_task: {str(e)}")
        if 'image_analysis' in locals():
            image_analysis.status = ImageAnalysis.StatusChoices.FAILED
            image_analysis.save()
        raise self.retry(exc=e, countdown=60, max_retries=3)


@shared_task(bind=True, queue='celery')
def analyze_document_task(self, document_analysis_id):
    """Async task for AI document analysis"""
    try:
        # Delegate to synchronous helper so it can be reused by view fallbacks
        analyze_document_sync(document_analysis_id)
        return {"status": "success", "document_analysis_id": str(document_analysis_id)}
    
    except DocumentAnalysis.DoesNotExist:
        return {"status": "error", "message": "Document analysis not found"}
    except Exception as e:
        logger.error(f"Error in analyze_document_task: {str(e)}")
        if 'document_analysis' in locals():
            document_analysis.status = DocumentAnalysis.StatusChoices.FAILED
            document_analysis.save()
        raise self.retry(exc=e, countdown=60, max_retries=3)


def analyze_document_sync(document_analysis_id):
    """Synchronous document analysis helper used by the Celery task and by view fallbacks.

    This performs the same work as the task but runs in-process so development uploads
    won't remain stuck when the worker/broker is temporarily unavailable.
    """
    try:
        document_analysis = DocumentAnalysis.objects.get(id=document_analysis_id)
        document_analysis.status = DocumentAnalysis.StatusChoices.ANALYZING
        document_analysis.save()

        # TODO: Integrate with Claude API for actual document analysis
        mock_analysis = f"AI Analysis for {document_analysis.fileName}: Mock document analysis - to be integrated with Claude API"

        document_analysis.analysisResult = mock_analysis
        document_analysis.status = DocumentAnalysis.StatusChoices.COMPLETED
        document_analysis.save()

        # Auto-create an SNL prescription for certain document types
        try:
            if document_analysis.documentType in ["BLOOD_REPORTS", "LAB_REPORTS"]:
                snl = SNLPrescription.objects.create(
                    patientId=document_analysis.patientId,
                    prescriptionContent="",
                    status=SNLPrescription.StatusChoices.GENERATING
                )
                # Queue generation task; try to use Celery but fall back to sync if needed
                try:
                    generate_snl_prescription_task.delay(snl.id)
                except Exception:
                    # run synchronously if broker unavailable
                    generate_snl_prescription_task.run(None, snl.id)
        except Exception as e:
            logger.error(f"Failed to auto-create SNLPrescription: {e}")

        return {"status": "success", "document_analysis_id": str(document_analysis_id)}

    except DocumentAnalysis.DoesNotExist:
        return {"status": "error", "message": "Document analysis not found"}
    except Exception as e:
        logger.error(f"Error in analyze_document_sync: {str(e)}")
        if 'document_analysis' in locals():
            document_analysis.status = DocumentAnalysis.StatusChoices.FAILED
            document_analysis.save()
        raise


@shared_task(bind=True, queue='celery')
def generate_clinical_report_task(self, clinical_report_id):
    """Async task for generating clinical intelligence reports"""
    try:
        clinical_report = ClinicalReport.objects.get(id=clinical_report_id)
        clinical_report.status = ClinicalReport.StatusChoices.GENERATING
        clinical_report.save()
        
        # TODO: Integrate with Claude API for actual report generation
        mock_report_data = {
            "patientOverview": "Mock patient overview - to be generated by Claude API",
            "keyClinicalFindings": ["Mock finding 1", "Mock finding 2"],
            "currentHealthStatus": "Mock health status",
            "followUpRecommendation": "2 weeks for reassessment",
            "primaryDoshaImbalance": {"title": "Mock Dosha Imbalance"},
            "diagnosticSummary": {"dosha": "V:30% P:50% K:20%"}
        }
        
        clinical_report.patientOverview = mock_report_data["patientOverview"]
        clinical_report.keyClinicalFindings = mock_report_data["keyClinicalFindings"]
        clinical_report.currentHealthStatus = mock_report_data["currentHealthStatus"]
        clinical_report.followUpRecommendation = mock_report_data["followUpRecommendation"]
        clinical_report.primaryDoshaImbalance = mock_report_data["primaryDoshaImbalance"]
        clinical_report.diagnosticSummary = mock_report_data["diagnosticSummary"]
        clinical_report.status = ClinicalReport.StatusChoices.COMPLETED
        clinical_report.save()
        
        return {"status": "success", "clinical_report_id": str(clinical_report_id)}
    
    except ClinicalReport.DoesNotExist:
        return {"status": "error", "message": "Clinical report not found"}
    except Exception as e:
        logger.error(f"Error in generate_clinical_report_task: {str(e)}")
        if 'clinical_report' in locals():
            clinical_report.status = ClinicalReport.StatusChoices.FAILED
            clinical_report.save()
        raise self.retry(exc=e, countdown=60, max_retries=3)


@shared_task(bind=True, queue='celery')
def generate_snl_prescription_task(self, snl_prescription_id):
    """Async task for generating SNL prescriptions"""
    try:
        snl_prescription = SNLPrescription.objects.get(id=snl_prescription_id)
        snl_prescription.status = SNLPrescription.StatusChoices.GENERATING
        snl_prescription.save()
        
        # TODO: Integrate with Claude API for actual prescription generation
        # Try to include context from the latest completed DocumentAnalysis for this patient
        doc_context = None
        try:
            latest_doc = DocumentAnalysis.objects.filter(
                patientId=snl_prescription.patientId,
                status=DocumentAnalysis.StatusChoices.COMPLETED
            ).order_by('-createdAt').first()
            if latest_doc and latest_doc.analysisResult:
                doc_context = latest_doc.analysisResult
        except Exception:
            doc_context = None

        mock_prescription = """
**SUPPLEMENTS & FORMULATIONS:**
- Mock Supplement 1 - 500mg - Twice daily
- Mock Supplement 2 - 250mg - Once daily

**NUTRITION PLAN:**
- Foods to Include: Mock foods list
- Foods to Avoid: Mock avoid list

**LIFESTYLE RECOMMENDATIONS:**
- Wake time: 6:00 AM
- Exercise: 30 minutes daily
- Sleep: 10:00 PM

"""

        if doc_context:
            mock_prescription += "\n**REPORT SUMMARY (from uploaded document):**\n" + doc_context + "\n"

        snl_prescription.prescriptionContent = mock_prescription
        snl_prescription.status = SNLPrescription.StatusChoices.COMPLETED
        snl_prescription.save()
        
        return {"status": "success", "snl_prescription_id": str(snl_prescription_id)}
    
    except SNLPrescription.DoesNotExist:
        return {"status": "error", "message": "SNL prescription not found"}
    except Exception as e:
        logger.error(f"Error in generate_snl_prescription_task: {str(e)}")
        if 'snl_prescription' in locals():
            snl_prescription.status = SNLPrescription.StatusChoices.FAILED
            snl_prescription.save()
        raise self.retry(exc=e, countdown=60, max_retries=3)


@shared_task(bind=True, queue='celery')
def generate_knowledge_references_task(self, knowledge_reference_id):
    """Async task for generating knowledge base references"""
    try:
        knowledge_reference = KnowledgeReference.objects.get(id=knowledge_reference_id)
        knowledge_reference.status = KnowledgeReference.StatusChoices.GENERATING
        knowledge_reference.save()
        
        # TODO: Integrate with Claude API for actual reference generation
        mock_references = """
**CLASSICAL REFERENCES:**
1. Charaka Samhita - Mock reference
2. Sushruta Samhita - Mock reference

**CLINICAL STUDIES:**
1. Mock Study Title - Journal Name 2023
2. Mock Study 2 - Another Journal 2024

(This is mock data - to be generated by Claude API)
        """
        
        knowledge_reference.referencesContent = mock_references
        knowledge_reference.status = KnowledgeReference.StatusChoices.COMPLETED
        knowledge_reference.save()
        
        return {"status": "success", "knowledge_reference_id": str(knowledge_reference_id)}
    
    except KnowledgeReference.DoesNotExist:
        return {"status": "error", "message": "Knowledge reference not found"}
    except Exception as e:
        logger.error(f"Error in generate_knowledge_references_task: {str(e)}")
        if 'knowledge_reference' in locals():
            knowledge_reference.status = KnowledgeReference.StatusChoices.FAILED
            knowledge_reference.save()
        raise self.retry(exc=e, countdown=60, max_retries=3)


@shared_task(bind=True)
def process_ai_chat_task(self, user_message_id, assistant_message_id):
    """Async task for processing AI chat messages with OpenAI"""
    try:
        user_message = ChatMessage.objects.get(id=user_message_id)
        assistant_message = ChatMessage.objects.get(id=assistant_message_id)
        
        # Get API key from environment or settings
        api_key = os.environ.get('OPENAI_API_KEY') or getattr(
            settings, 'OPENAI_API_KEY', None
        )
        
        if OPENAI_AVAILABLE and api_key:
            try:
                # Initialize OpenAI client
                client = OpenAI(api_key=api_key)
                
                # Build context from patient data if available
                context_parts = []
                if user_message.patientId:
                    patient = user_message.patientId
                    context_parts.append(
                        f"Patient: {patient.name}, "
                        f"Age: {patient.age}, Gender: {patient.gender}"
                    )
                    if patient.chiefComplaints:
                        context_parts.append(
                            f"Chief Complaints: {patient.chiefComplaints}"
                        )
                
                system_prompt = (
                    "You are an expert Ayurvedic healthcare assistant "
                    "named AyuPilot. You provide helpful, accurate "
                    "information about Ayurvedic medicine, treatments, "
                    "and wellness practices. Always be professional, "
                    "compassionate, and evidence-based in your responses."
                )
                
                if context_parts:
                    system_prompt += (
                        "\n\nPatient Context:\n" + "\n".join(context_parts)
                    )
                
                # Call OpenAI API
                response = client.chat.completions.create(
                    model="gpt-4o-mini",  # or "gpt-4" for better quality
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message.content}
                    ],
                    temperature=0.7,
                    max_tokens=500
                )
                
                ai_response = response.choices[0].message.content
                assistant_message.content = ai_response
                assistant_message.save()
                
                return {
                    "status": "success",
                    "user_message_id": str(user_message_id),
                    "assistant_message_id": str(assistant_message_id)
                }
                
            except Exception as e:
                logger.error(f"OpenAI API error: {str(e)}")
                # Fall back to mock response on API error
                assistant_message.content = (
                    "I apologize, but I'm currently unable to process "
                    "your request due to a technical issue. "
                    "Please try again in a moment."
                )
                assistant_message.save()
                return {
                    "status": "error",
                    "message": f"OpenAI API error: {str(e)}"
                }
        else:
            # Enhanced mock response when OpenAI is not available
            user_query = user_message.content.lower()
            
            # Intelligent mock responses based on keywords
            if any(word in user_query for word in ['hello', 'hi', 'hey', 'namaste']):
                mock_response = (
                    "Namaste! 🙏 I'm AyuPilot, your Ayurvedic AI assistant. "
                    "I can help you with:\n\n"
                    "• Ayurvedic health recommendations\n"
                    "• Dosha analysis (Vata, Pitta, Kapha)\n"
                    "• Herbal remedies and treatments\n"
                    "• Dietary advice based on Ayurvedic principles\n"
                    "• Lifestyle modifications for wellness\n\n"
                    "How can I assist you today?"
                )
            elif any(word in user_query for word in ['help', 'what can you', 'do', 'assist']):
                mock_response = (
                    "I can assist you with various aspects of Ayurvedic medicine:\n\n"
                    "🌿 **Health Assessment**: Understanding your dosha type\n"
                    "💊 **Remedies**: Suggesting Ayurvedic treatments and herbs\n"
                    "🍽️ **Diet**: Personalized dietary recommendations\n"
                    "🧘 **Lifestyle**: Yoga, meditation, and daily routines\n"
                    "📚 **Education**: Explaining Ayurvedic concepts\n\n"
                    "What specific topic would you like to explore?"
                )
            elif any(word in user_query for word in ['vata', 'pitta', 'kapha', 'dosha']):
                mock_response = (
                    "The three doshas are fundamental to Ayurveda:\n\n"
                    "**Vata** (Air + Space): Governs movement, creativity, flexibility\n"
                    "**Pitta** (Fire + Water): Controls digestion, metabolism, energy\n"
                    "**Kapha** (Earth + Water): Manages structure, stability, immunity\n\n"
                    "Each person has a unique dosha balance. Would you like to learn more "
                    "about any specific dosha or get a personalized assessment?"
                )
            elif any(word in user_query for word in ['diet', 'food', 'eat', 'nutrition']):
                mock_response = (
                    "Ayurvedic nutrition focuses on eating according to your dosha:\n\n"
                    "• **Warm, cooked foods** are easier to digest\n"
                    "• **Six tastes**: Sweet, sour, salty, pungent, bitter, astringent\n"
                    "• **Seasonal eating**: Align diet with nature's cycles\n"
                    "• **Mindful eating**: Eat in a calm environment\n\n"
                    "Would you like specific dietary recommendations based on your constitution?"
                )
            elif any(word in user_query for word in ['sick', 'pain', 'cold', 'fever', 'headache']):
                mock_response = (
                    "For common ailments, Ayurveda suggests:\n\n"
                    "🌡️ **Cold/Flu**: Ginger tea, turmeric milk, rest\n"
                    "🤕 **Headache**: Peppermint oil, proper hydration, stress relief\n"
                    "💊 **Digestion**: Triphala, fennel seeds, warm water\n\n"
                    "⚠️ Note: For serious symptoms, please consult a qualified healthcare provider. "
                    "What symptoms are you experiencing?"
                )
            else:
                mock_response = (
                    f"Thank you for your question about '{user_message.content[:50]}'. "
                    f"As an Ayurvedic assistant, I'm here to provide guidance on:\n\n"
                    f"• Health and wellness based on Ayurvedic principles\n"
                    f"• Natural remedies and herbal treatments\n"
                    f"• Lifestyle recommendations\n\n"
                    f"💡 **For real AI-powered responses**: Configure the OPENAI_API_KEY "
                    f"in your environment to unlock advanced AI capabilities.\n\n"
                    f"How else can I help you today?"
                )
            
            assistant_message.content = mock_response
            assistant_message.save()
            
            return {
                "status": "success",
                "user_message_id": str(user_message_id),
                "assistant_message_id": str(assistant_message_id),
                "note": "Using mock response - OpenAI not configured"
            }
    
    except ChatMessage.DoesNotExist:
        return {"status": "error", "message": "Chat message not found"}
    except Exception as e:
        logger.error(f"Error in process_ai_chat_task: {str(e)}")
        raise self.retry(exc=e, countdown=60, max_retries=3)


@shared_task(bind=True)
def update_appointment_statuses(self):
    """
    Auto-update appointment statuses with simple business rules:
    - If an appointment is SCHEDULED and the date is before today -> mark as NO_SHOW
    - If an appointment is SCHEDULED for today and the time has passed:
        - If there is any patient activity today (clinical report, SNL, knowledge reference,
          image/document analysis), mark as COMPLETED
        - Else if more than 2 hours have passed since scheduled time, mark as NO_SHOW
    """
    now = timezone.localtime()
    today = now.date()

    # Past-day scheduled appointments -> NO_SHOW
    past_qs = Appointment.objects.filter(
        status=Appointment.StatusChoices.SCHEDULED,
        appointmentDate__lt=today,
    )
    past_count = past_qs.count()
    if past_count:
        for appt in past_qs.iterator():
            appt.status = Appointment.StatusChoices.NO_SHOW
            appt.save(update_fields=["status", "updatedAt"])

    # Today's appointments whose time has passed
    todays_qs = Appointment.objects.filter(
        status=Appointment.StatusChoices.SCHEDULED,
        appointmentDate=today,
        appointmentTime__lte=now.time(),
    ).select_related("patientId")

    todays_checked = 0
    for appt in todays_qs.iterator():
        todays_checked += 1
        patient = appt.patientId
        # Any activity for the patient today?
        has_activity = (
            ClinicalReport.objects.filter(patientId=patient, createdAt__date=today).exists() or
            SNLPrescription.objects.filter(patientId=patient, createdAt__date=today).exists() or
            KnowledgeReference.objects.filter(patientId=patient, createdAt__date=today).exists() or
            ImageAnalysis.objects.filter(patientId=patient, createdAt__date=today).exists() or
            DocumentAnalysis.objects.filter(patientId=patient, createdAt__date=today).exists()
        )

        appt_dt = datetime.combine(today, appt.appointmentTime)
        appt_dt = timezone.make_aware(appt_dt, timezone.get_current_timezone())

        if has_activity:
            appt.status = Appointment.StatusChoices.COMPLETED
            appt.save(update_fields=["status", "updatedAt"])
        elif now >= appt_dt + timedelta(hours=2):
            appt.status = Appointment.StatusChoices.NO_SHOW
            appt.save(update_fields=["status", "updatedAt"])

    return {"past_marked_no_show": past_count, "todays_checked": todays_checked}

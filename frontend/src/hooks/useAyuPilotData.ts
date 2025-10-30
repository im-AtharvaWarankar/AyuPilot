import { useApiData, useApiMutation } from './useApi';
import api, { 
  Patient, 
  Appointment, 
  ImageAnalysis, 
  DocumentAnalysis, 
  ClinicalReport, 
  SNLPrescription, 
  KnowledgeReference
} from '../services/api';

// Dashboard hooks
export function useDashboardStats() {
  return useApiData(() => api.dashboard.getStats());
}

// Patient hooks
export function usePatients(params?: Record<string, any>) {
  return useApiData(() => api.patients.getAll(params), [params]);
}

export function usePatient(id: string) {
  return useApiData(() => api.patients.getById(id), [id]);
}

export function useCreatePatient() {
  return useApiMutation<Patient, Partial<Patient>>();
}

export function useUpdatePatient() {
  return useApiMutation<Patient, { id: string; data: Partial<Patient> }>();
}

export function useDeletePatient() {
  return useApiMutation<void, string>();
}

// Appointment hooks
export function useAppointments(params?: Record<string, any>) {
  return useApiData(() => api.appointments.getAll(params), [params]);
}

export function useTodayAppointments() {
  return useApiData(() => api.appointments.getTodayAppointments());
}

export function useAppointment(id: string) {
  return useApiData(() => api.appointments.getById(id), [id]);
}

export function useCreateAppointment() {
  return useApiMutation<Appointment, Partial<Appointment>>();
}

export function useUpdateAppointment() {
  return useApiMutation<Appointment, { id: string; data: Partial<Appointment> }>();
}

// Image Analysis hooks
export function useImageAnalyses(params?: Record<string, any>) {
  return useApiData(() => api.imageAnalysis.getAll(params), [params]);
}

export function useImageAnalysis(id: string) {
  return useApiData(() => api.imageAnalysis.getById(id), [id]);
}

export function useUploadImage() {
  return useApiMutation<ImageAnalysis, FormData>();
}

// Document Analysis hooks
export function useDocumentAnalyses(params?: Record<string, any>) {
  return useApiData(() => api.documentAnalysis.getAll(params), [params]);
}

export function useDocumentAnalysis(id: string) {
  return useApiData(() => api.documentAnalysis.getById(id), [id]);
}

export function useUploadDocument() {
  return useApiMutation<DocumentAnalysis, FormData>();
}

// Clinical Report hooks
export function useClinicalReports(params?: Record<string, any>) {
  return useApiData(() => api.clinicalReports.getAll(params), [params]);
}

export function useClinicalReport(id: string) {
  return useApiData(() => api.clinicalReports.getById(id), [id]);
}

export function useGenerateClinicalReport() {
  return useApiMutation<ClinicalReport, { patientId: string }>();
}

// SNL Prescription hooks
export function useSNLPrescriptions(params?: Record<string, any>) {
  return useApiData(() => api.snlPrescriptions.getAll(params), [params]);
}

export function useSNLPrescription(id: string) {
  return useApiData(() => api.snlPrescriptions.getById(id), [id]);
}

export function useGenerateSNLPrescription() {
  return useApiMutation<SNLPrescription, { patientId: string }>();
}

// Knowledge Reference hooks
export function useKnowledgeReferences(params?: Record<string, any>) {
  return useApiData(() => api.knowledgeReferences.getAll(params), [params]);
}

export function useKnowledgeReference(id: string) {
  return useApiData(() => api.knowledgeReferences.getById(id), [id]);
}

export function useGenerateKnowledgeReferences() {
  return useApiMutation<KnowledgeReference, { patientId: string }>();
}

// Chat hooks
export function useChatMessages(params?: Record<string, any>) {
  return useApiData(() => api.chat.getAll(params), [params]);
}

export function useSendMessage() {
  return useApiMutation<{ response: string }, { 
    patientId?: string; 
    message: string; 
    context?: any 
  }>();
}

// Combined hooks for complex operations
export function usePatientData(patientId: string) {
  const patient = usePatient(patientId);
  const appointments = useAppointments({ patientId });
  const imageAnalyses = useImageAnalyses({ patientId });
  const documentAnalyses = useDocumentAnalyses({ patientId });
  const clinicalReports = useClinicalReports({ patientId });
  const snlPrescriptions = useSNLPrescriptions({ patientId });
  const knowledgeReferences = useKnowledgeReferences({ patientId });
  const chatMessages = useChatMessages({ patientId });

  const loading = patient.loading || appointments.loading || imageAnalyses.loading || 
                  documentAnalyses.loading || clinicalReports.loading || 
                  snlPrescriptions.loading || knowledgeReferences.loading || 
                  chatMessages.loading;

  const error = patient.error || appointments.error || imageAnalyses.error || 
                documentAnalyses.error || clinicalReports.error || 
                snlPrescriptions.error || knowledgeReferences.error || 
                chatMessages.error;

  const refetchAll = () => {
    patient.refetch();
    appointments.refetch();
    imageAnalyses.refetch();
    documentAnalyses.refetch();
    clinicalReports.refetch();
    snlPrescriptions.refetch();
    knowledgeReferences.refetch();
    chatMessages.refetch();
  };

  return {
    patient: patient.data,
    appointments: appointments.data || [],
    imageAnalyses: imageAnalyses.data || [],
    documentAnalyses: documentAnalyses.data || [],
    clinicalReports: clinicalReports.data || [],
    snlPrescriptions: snlPrescriptions.data || [],
    knowledgeReferences: knowledgeReferences.data || [],
    chatMessages: chatMessages.data || [],
    loading,
    error,
    refetchAll,
  };
}

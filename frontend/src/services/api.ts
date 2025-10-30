// API Service for AyuPilot Backend Integration
// Use relative path to leverage Vite proxy in development
const API_BASE_URL = '/api/ayupilot';

// Types for API responses
export interface Patient {
  id: string;
  name: string;
  age: number;
  gender: string;
  phone: string;
  abhaNumber?: string;
  status: string;
  lastVisit?: string;
  dosha?: string;
  role?: string;
  roleDisplay?: string;
}

export interface Appointment {
  id: string;
  patientId: string;
  patientName: string;
  appointmentDate: string;
  appointmentTime: string;
  appointmentType: string;
  status: string;
  notes?: string;
  time?: string;
  patient?: string;
  type?: string;
}

export interface ImageAnalysis {
  id: string;
  patientId: string;
  imageType: string;
  imageUrl?: string;
  imageData?: string;
  analysisResult?: string;
  status: string;
  fileName?: string;
  patientName?: string;
}

export interface DocumentAnalysis {
  id: string;
  patientId: string;
  documentType: string;
  documentUrl?: string;
  documentData?: string;
  analysisResult?: string;
  status: string;
  fileName?: string;
  fileType?: string;
  patientName?: string;
}

export interface ClinicalReport {
  id: string;
  patientId: string;
  patientOverview?: string;
  keyClinicalFindings?: any;
  currentHealthStatus?: string;
  followUpRecommendation?: string;
  recommendedActions?: any;
  status: string;
  patientName?: string;
}

export interface SNLPrescription {
  id: string;
  patientId: string;
  prescriptionContent: string;
  status: string;
  patientName?: string;
}

export interface KnowledgeReference {
  id: string;
  patientId: string;
  referencesContent: string;
  status: string;
  patientName?: string;
}

export interface ChatMessage {
  id: string;
  patientId?: string;
  userId: string;
  role: string;
  content: string;
  userName?: string;
  patientName?: string;
}

export interface DashboardStats {
  totalPatients: number;
  todayAppointments: number;
  pendingAnalyses: number;
  completedReports: number;
}

// Error types
export interface ApiError {
  message: string;
  status?: number;
  details?: any;
}

// API Response wrapper
export interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
}

// Authentication helpers
export function setAuthToken(token: string): void {
  localStorage.setItem('authToken', token);
}

export function getAuthToken(): string | null {
  // Read token from localStorage (dev). If you prefer a hardcoded token,
  // you can uncomment the hardcoded return below and paste a token.
  return localStorage.getItem('authToken');
}

export function clearAuthToken(): void {
  localStorage.removeItem('authToken');
}

// API Helper function with comprehensive error handling
async function apiCall<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const defaultHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  // Add authentication if token exists
  const token = getAuthToken();
  if (token) {
    defaultHeaders['Authorization'] = `Bearer ${token}`;
  }

  const config: RequestInit = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  };

  try {
    const response = await fetch(url, config);
    
    if (!response.ok) {
      let errorMessage = `API call failed: ${response.status} ${response.statusText}`;
      let errorDetails = null;

      try {
        const errorData = await response.json();
        errorMessage = errorData.message || errorData.detail || errorMessage;
        errorDetails = errorData;
      } catch {
        // If response is not JSON, use status text
      }

      const apiError: ApiError = {
        message: errorMessage,
        status: response.status,
        details: errorDetails,
      };

      throw apiError;
    }

    // Handle empty responses (like DELETE)
    if (response.status === 204) {
      return {} as T;
    }

    const jsonResponse = await response.json();
    
    // Unwrap the AtomicSerializer response structure for non-list endpoints
    // Keep pagination structure for list endpoints
    if (jsonResponse && typeof jsonResponse === 'object' && 'data' in jsonResponse) {
      // If data has results/count/pagination, return the whole data object
      if (jsonResponse.data && typeof jsonResponse.data === 'object' && 
          ('results' in jsonResponse.data || 'count' in jsonResponse.data)) {
        return jsonResponse.data as T;
      }
      // Otherwise unwrap single objects
      return jsonResponse.data as T;
    }
    
    return jsonResponse;
  } catch (error) {
    console.error(`API Error for ${endpoint}:`, error);
    
    // Re-throw ApiError as is, wrap other errors
    if ((error as ApiError).message) {
      throw error;
    }
    
    throw {
      message: error instanceof Error ? error.message : 'Unknown API error',
      details: error,
    } as ApiError;
  }
}

// Dashboard API
export const dashboardApi = {
  getStats: (): Promise<DashboardStats> =>
    apiCall<DashboardStats>('/dashboard/stats/'),
};

// Patient API
export const patientApi = {
  getAll: (params?: Record<string, any>): Promise<Patient[]> => {
    const queryString = params ? '?' + new URLSearchParams(params).toString() : '';
    return apiCall<Patient[]>(`/patients/${queryString}`);
  },
  
  getById: (id: string): Promise<Patient> =>
    apiCall<Patient>(`/patients/${id}/`),
  
  create: (data: Partial<Patient>): Promise<Patient> =>
    apiCall<Patient>('/patients/', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  
  update: (id: string, data: Partial<Patient>): Promise<Patient> =>
    apiCall<Patient>(`/patients/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),
  
  delete: (id: string): Promise<void> =>
    apiCall<void>(`/patients/${id}/`, {
      method: 'DELETE',
    }),
};

// Appointment API
export const appointmentApi = {
  getAll: (params?: Record<string, any>): Promise<Appointment[]> => {
    const queryString = params ? '?' + new URLSearchParams(params).toString() : '';
    return apiCall<Appointment[]>(`/appointments/${queryString}`);
  },
  
  getById: (id: string): Promise<Appointment> =>
    apiCall<Appointment>(`/appointments/${id}/`),
  
  create: (data: Partial<Appointment>): Promise<Appointment> =>
    apiCall<Appointment>('/appointments/', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  
  update: (id: string, data: Partial<Appointment>): Promise<Appointment> =>
    apiCall<Appointment>(`/appointments/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),
  
  getTodayAppointments: (): Promise<Appointment[]> =>
    apiCall<Appointment[]>('/appointments/?today=true'),
};

// Image Analysis API
export const imageAnalysisApi = {
  getAll: (params?: Record<string, any>): Promise<ImageAnalysis[]> => {
    const queryString = params ? '?' + new URLSearchParams(params).toString() : '';
    return apiCall<ImageAnalysis[]>(`/image-analyses/${queryString}`);
  },
  
  upload: (data: { patientId: string; imageType: string; imageData: string; fileName: string }): Promise<ImageAnalysis> =>
    apiCall<ImageAnalysis>('/upload/image/', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  
  getById: (id: string): Promise<ImageAnalysis> =>
    apiCall<ImageAnalysis>(`/image-analyses/${id}/`),
};

// Document Analysis API
export const documentAnalysisApi = {
  getAll: (params?: Record<string, any>): Promise<DocumentAnalysis[]> => {
    const queryString = params ? '?' + new URLSearchParams(params).toString() : '';
    return apiCall<DocumentAnalysis[]>(`/document-analyses/${queryString}`);
  },
  
  upload: (formData: FormData): Promise<DocumentAnalysis> =>
    apiCall<DocumentAnalysis>('/upload/document/', {
      method: 'POST',
      body: formData,
      headers: {}, // Don't set Content-Type for FormData
    }),
  
  getById: (id: string): Promise<DocumentAnalysis> =>
    apiCall<DocumentAnalysis>(`/document-analyses/${id}/`),
};

// Clinical Report API
export const clinicalReportApi = {
  getAll: (params?: Record<string, any>): Promise<ClinicalReport[]> => {
    const queryString = params ? '?' + new URLSearchParams(params).toString() : '';
    return apiCall<ClinicalReport[]>(`/clinical-reports/${queryString}`);
  },
  
  generate: (data: { patientId: string }): Promise<ClinicalReport> =>
    apiCall<ClinicalReport>('/generate/clinical-report/', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  
  getById: (id: string): Promise<ClinicalReport> =>
    apiCall<ClinicalReport>(`/clinical-reports/${id}/`),
};

// SNL Prescription API
export const snlPrescriptionApi = {
  getAll: (params?: Record<string, any>): Promise<SNLPrescription[]> => {
    const queryString = params ? '?' + new URLSearchParams(params).toString() : '';
    return apiCall<SNLPrescription[]>(`/snl-prescriptions/${queryString}`);
  },
  
  generate: (data: { patientId: string }): Promise<SNLPrescription> =>
    apiCall<SNLPrescription>('/generate/snl-prescription/', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  
  getById: (id: string): Promise<SNLPrescription> =>
    apiCall<SNLPrescription>(`/snl-prescriptions/${id}/`),
};

// Knowledge Reference API
export const knowledgeReferenceApi = {
  getAll: (params?: Record<string, any>): Promise<KnowledgeReference[]> => {
    const queryString = params ? '?' + new URLSearchParams(params).toString() : '';
    return apiCall<KnowledgeReference[]>(`/knowledge-references/${queryString}`);
  },
  
  generate: (data: { patientId: string }): Promise<KnowledgeReference> =>
    apiCall<KnowledgeReference>('/generate/knowledge-references/', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  
  getById: (id: string): Promise<KnowledgeReference> =>
    apiCall<KnowledgeReference>(`/knowledge-references/${id}/`),
};

// Chat API
export const chatApi = {
  getAll: (params?: Record<string, any>): Promise<ChatMessage[]> => {
    const queryString = params ? '?' + new URLSearchParams(params).toString() : '';
    return apiCall<ChatMessage[]>(`/chat-messages/${queryString}`);
  },
  
  sendMessage: (data: { 
    patientId?: string; 
    message: string; 
    context?: any 
  }): Promise<{ response: string }> =>
    apiCall<{ response: string }>('/chat/', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
};

// Export all APIs
export const api = {
  dashboard: dashboardApi,
  patients: patientApi,
  appointments: appointmentApi,
  imageAnalysis: imageAnalysisApi,
  documentAnalysis: documentAnalysisApi,
  clinicalReports: clinicalReportApi,
  snlPrescriptions: snlPrescriptionApi,
  knowledgeReferences: knowledgeReferenceApi,
  chat: chatApi,
};

export default api;

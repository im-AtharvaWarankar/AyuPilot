import React, { useState, useRef, useEffect } from 'react';
import { 
  Users, Activity, FileText, Image, Leaf, BookOpen, Calendar, Bell, Search, 
  Menu, X, Plus, Upload, Eye, Heart, Droplet, Flame, Shield, Phone, Pill, 
  ClipboardList, MessageSquare, Send, Loader, AlertTriangle 
} from 'lucide-react';
import api from '../services/api';
import { 
  useDashboardStats, 
  usePatients, 
  useTodayAppointments,
  useGenerateClinicalReport,
  useGenerateSNLPrescription,
  useGenerateKnowledgeReferences,
  useUploadImage,
  useUploadDocument,
  useSendMessage
} from '../hooks/useAyuPilotData';
// import { ApiErrorDisplay, LoadingSpinner } from './ErrorBoundary';

export default function AyuPilotDashboard() {
  // UI State
  const [activeModule, setActiveModule] = useState('overview');
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // Debug logging
  useEffect(() => {
    console.log('Active module changed to:', activeModule);
  }, [activeModule]);
  const [selectedPatient, setSelectedPatient] = useState<any>(null);
  const [selectedAppointment, setSelectedAppointment] = useState<any>(null);
  const [imageUploadTab, setImageUploadTab] = useState('tongue');
  const [prakritiAnswers, setPrakritiAnswers] = useState<any>({});
  const [expandedClinicalSection, setExpandedClinicalSection] = useState<string | null>(null);

  // API Hooks for data fetching
  const dashboardStats = useDashboardStats();
  const patients = usePatients();
  const todayAppointmentsData = useTodayAppointments();

  // API Hooks for mutations
  const generateClinicalReportMutation = useGenerateClinicalReport();
  const generateSNLPrescriptionMutation = useGenerateSNLPrescription();
  const generateKnowledgeReferencesMutation = useGenerateKnowledgeReferences();
  const uploadImageMutation = useUploadImage();
  const uploadDocumentMutation = useUploadDocument();
  const sendMessageMutation = useSendMessage();

  // Image Analysis State
  const [uploadedImages, setUploadedImages] = useState<any>({
    tongue: null,
    iris: null,
    nails: null,
    skin: null
  });
  const [imageAnalysis, setImageAnalysis] = useState<any>({
    tongue: null,
    iris: null,
    nails: null,
    skin: null
  });
  const [analyzingImage, setAnalyzingImage] = useState<string | null>(null);

  // Document Upload State
  const [uploadedDocuments, setUploadedDocuments] = useState<any>({
    bloodReports: [],
    labReports: [],
    otherDocuments: []
  });
  const [documentAnalysis, setDocumentAnalysis] = useState<any>({});
  const [analyzingDocument, setAnalyzingDocument] = useState<string | null>(null);

  // Claude AI Assistant State
  const [showAIAssistant, setShowAIAssistant] = useState(false);
  const [messages, setMessages] = useState<any>([
    { role: 'assistant', content: 'Namaste! I\'m your AyuPilot AI assistant. How can I help you today?' }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Clinical Intelligence Report State
  const [clinicalReport, setClinicalReport] = useState<any>(null);
  const generatingClinicalReport = generateClinicalReportMutation.loading;

  // SNL Prescription State
  const [snlPrescription, setSnlPrescription] = useState<string | null>(null);
  const generatingSNL = generateSNLPrescriptionMutation.loading;

    // Knowledge Base References State
  const [knowledgeReferences, setKnowledgeReferences] = useState<any>(null);
  const generatingKnowledge = generateKnowledgeReferencesMutation.loading;

  // Case Intake Form State
  const [intakeForm, setIntakeForm] = useState({
    chiefComplaints: '',
    medicalHistory: '',
    currentMedications: '',
    sleepPattern: 'Regular (7-8 hours)',
    appetite: 'Normal',
  });
  const [savingIntake, setSavingIntake] = useState(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Real API functions
  const generateClinicalReport = async () => {
    if (!selectedPatient?.id) {
      console.error('No patient selected for clinical report generation');
      return;
    }

    try {
      const result = await generateClinicalReportMutation.mutate(
        api.clinicalReports.generate,
        { patientId: selectedPatient.id }
      );
      setClinicalReport(result);
    } catch (error) {
      console.error('Failed to generate clinical report:', error);
    }
  };

  const generateSNLPrescription = async () => {
    if (!selectedPatient?.id) {
      console.error('No patient selected for SNL prescription generation');
      return;
    }

    try {
      // Start the prescription generation (returns immediately with GENERATING status)
      const result = await generateSNLPrescriptionMutation.mutate(
        api.snlPrescriptions.generate,
        { patientId: selectedPatient.id }
      );
      
      // Poll for completion
      const prescriptionId = result.id;
      const pollInterval = 2000; // 2 seconds
      const maxAttempts = 30; // 60 seconds max
      
      for (let attempt = 0; attempt < maxAttempts; attempt++) {
        await new Promise(resolve => setTimeout(resolve, pollInterval));
        
        const prescription = await api.snlPrescriptions.getById(prescriptionId);
        
        if (prescription.status === 'COMPLETED') {
          setSnlPrescription(prescription.prescriptionContent);
          console.log('SNL Prescription generated successfully!');
          return;
        } else if (prescription.status === 'FAILED') {
          console.error('Prescription generation failed');
          return;
        }
      }
      
      console.error('Prescription generation timed out');
    } catch (error) {
      console.error('Failed to generate SNL prescription:', error);
    }
  };

  const saveCaseIntake = async () => {
    if (!selectedPatient?.id) {
      console.error('No patient selected for case intake');
      return;
    }

    setSavingIntake(true);
    try {
      const appointmentData = {
        patientId: selectedPatient.id,
        appointmentDate: new Date().toISOString().split('T')[0],
        appointmentTime: new Date().toTimeString().split(' ')[0].substring(0, 5),
        appointmentType: 'NEW_CASE',
        status: 'COMPLETED',
        reason: 'Case Intake - Initial Assessment',
        notes: `CHIEF COMPLAINTS:\n${intakeForm.chiefComplaints}\n\nMEDICAL HISTORY:\n${intakeForm.medicalHistory}\n\nCURRENT MEDICATIONS:\n${intakeForm.currentMedications}\n\nLIFESTYLE:\nSleep Pattern: ${intakeForm.sleepPattern}\nAppetite: ${intakeForm.appetite}`,
      };

      console.log('Sending appointment data:', JSON.stringify(appointmentData, null, 2));
      const response = await api.appointments.create(appointmentData);
      console.log('Case intake saved successfully!', response);
      
      // Clear form after successful save
      clearIntakeForm();
      
      // Show success message
      alert('Case intake saved successfully!');
    } catch (error: any) {
      console.error('Failed to save case intake:', error);
      console.error('Error details:', error.response || error.message);
      alert(`Failed to save case intake: ${error.message || 'Please try again.'}`);
    } finally {
      setSavingIntake(false);
    }
  };

  const clearIntakeForm = () => {
    setIntakeForm({
      chiefComplaints: '',
      medicalHistory: '',
      currentMedications: '',
      sleepPattern: 'Regular (7-8 hours)',
      appetite: 'Normal',
    });
  };

  const generateKnowledgeReferences = async () => {
    if (!selectedPatient?.id) {
      console.error('No patient selected for knowledge references generation');
      return;
    }

    try {
      const result = await generateKnowledgeReferencesMutation.mutate(
        api.knowledgeReferences.generate,
        { patientId: selectedPatient.id }
      );
      
      // Poll for completion
      const referenceId = result.id;
      const pollInterval = 2000;
      const maxAttempts = 30;
      
      for (let attempt = 0; attempt < maxAttempts; attempt++) {
        await new Promise(resolve => setTimeout(resolve, pollInterval));
        
        const reference = await api.knowledgeReferences.getById(referenceId);
        
        if (reference.status === 'COMPLETED') {
          setKnowledgeReferences(reference.referencesContent);
          console.log('Knowledge references generated successfully!');
          return;
        } else if (reference.status === 'FAILED') {
          console.error('Knowledge reference generation failed');
          return;
        }
      }
      
      console.error('Knowledge reference generation timed out');
    } catch (error) {
      console.error('Failed to generate knowledge references:', error);
    }
  };

  const handleImageUpload = async (event: any, imageType: string) => {
    const file = event.target.files[0];
    if (!file || !selectedPatient?.id) return;

    try {
      setAnalyzingImage(imageType);
      
      // Convert file to base64
      const reader = new FileReader();
      reader.onloadend = async () => {
        try {
          const base64String = reader.result as string;
          
          const result = await uploadImageMutation.mutate(
            api.imageAnalysis.upload,
            {
              patientId: selectedPatient.id,
              imageType: imageType.toUpperCase(),
              imageData: base64String,
              fileName: file.name
            }
          );
          
          setUploadedImages((prev: any) => ({
            ...prev,
            [imageType]: {
              data: result.imageData,
              preview: URL.createObjectURL(file),
              fileName: file.name,
              id: result.id
            }
          }));

          setImageAnalysis((prev: any) => ({
            ...prev,
            [imageType]: result.analysisResult || 'Analysis in progress...'
          }));
        } catch (error) {
          console.error('Failed to upload image:', error);
        } finally {
          setAnalyzingImage(null);
        }
      };
      
      reader.readAsDataURL(file);
    } catch (error) {
      console.error('Failed to read file:', error);
      setAnalyzingImage(null);
    }
  };

  const handleDocumentUpload = async (event: any, docType: string) => {
    const file = event.target.files[0];
    if (!file || !selectedPatient?.id) return;

    const formData = new FormData();
    formData.append('document', file);
    formData.append('documentType', docType.toUpperCase());
    formData.append('patientId', selectedPatient.id);

    try {
      setAnalyzingDocument(file.name);
      const result = await uploadDocumentMutation.mutate(
        (formData) => api.documentAnalysis.upload(formData),
        formData
      );
      
      setUploadedDocuments((prev: any) => ({
        ...prev,
        [docType]: [...(prev[docType] || []), {
          data: result.documentData,
          fileName: file.name,
          fileType: file.type,
          id: result.id,
          url: result.documentUrl
        }]
      }));

      setDocumentAnalysis((prev: any) => ({
        ...prev,
        [file.name]: result.analysisResult || 'Analysis in progress...'
      }));
    } catch (error) {
      console.error('Failed to upload document:', error);
    } finally {
      setAnalyzingDocument(null);
    }
  };

  const sendMessageToClaude = async (userMessage: string) => {
    setIsLoading(true);
    
    // Add user message immediately
    setMessages((prev: any) => [...prev, { role: 'user', content: userMessage }]);

    try {
      const result = await sendMessageMutation.mutate(
        api.chat.sendMessage,
        {
          patientId: selectedPatient?.id,
          message: userMessage,
          context: selectedPatient ? {
            patientName: selectedPatient.name,
            age: selectedPatient.age,
            gender: selectedPatient.gender,
            chiefComplaints: selectedPatient.chiefComplaints
          } : undefined
        }
      );
      
      // Add AI response
      setMessages((prev: any) => [...prev, { 
        role: 'assistant', 
        content: result.response 
      }]);
    } catch (error) {
      console.error('Failed to send message:', error);
      // Add error message
      setMessages((prev: any) => [...prev, { 
        role: 'assistant', 
        content: 'Sorry, I encountered an error. Please try again.' 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;
    const userMessage = inputMessage;
    setInputMessage('');
    await sendMessageToClaude(userMessage);
  };

  // Use real API data instead of mock data
  // API now returns unwrapped data, so access results directly
  const recentPatientsData = (patients.data as any)?.results || [];
  const todayAppointmentsApiData = (todayAppointmentsData.data as any)?.results || [];
  const dashboardStatsData = dashboardStats.data || {
    totalPatients: 0,
    todayAppointments: 0,
    pendingAnalyses: 0,
    completedReports: 0
  };

  // Loading states
  const isLoadingData = patients.loading || todayAppointmentsData.loading || dashboardStats.loading;
  const apiError = patients.error || todayAppointmentsData.error || dashboardStats.error;



  const modules = [
    { id: 'overview', name: 'Dashboard', icon: Activity },
    { id: 'intake', name: 'Case Intake', icon: FileText },
    { id: 'visual', name: 'Visual Diagnostics', icon: Eye },
    { id: 'clinical', name: 'Clinical Intelligence', icon: Activity },
    { id: 'snl', name: 'SNL Composer', icon: Leaf },
    { id: 'knowledge', name: 'Knowledge Base', icon: BookOpen },
  ];

  const prakritiQuestions = [
    {
      id: 'body_frame',
      question: 'Body Frame',
      options: [
        { label: 'Thin, light frame', dosha: 'vata' },
        { label: 'Medium, muscular frame', dosha: 'pitta' },
        { label: 'Large, heavy frame', dosha: 'kapha' }
      ]
    },
    {
      id: 'skin_type',
      question: 'Skin Type',
      options: [
        { label: 'Dry, rough, cool', dosha: 'vata' },
        { label: 'Warm, oily, prone to rashes', dosha: 'pitta' },
        { label: 'Thick, moist, cool', dosha: 'kapha' }
      ]
    }
  ];

  // Render functions will be added in next part due to size constraints
  const renderContent = () => {
    if (activeModule === 'overview') {
      return (
        <div className="space-y-6">
          {/* Dashboard Stats */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-600 text-sm">Total Patients</p>
                  <p className="text-3xl font-bold text-gray-800">{dashboardStatsData.totalPatients}</p>
                </div>
                <Users className="text-green-600" size={32} />
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-600 text-sm">Today's Appointments</p>
                  <p className="text-3xl font-bold text-gray-800">{dashboardStatsData.todayAppointments}</p>
                </div>
                <Calendar className="text-blue-600" size={32} />
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-600 text-sm">Pending Analyses</p>
                  <p className="text-3xl font-bold text-gray-800">{dashboardStatsData.pendingAnalyses}</p>
                </div>
                <Activity className="text-orange-600" size={32} />
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-600 text-sm">Completed Reports</p>
                  <p className="text-3xl font-bold text-gray-800">{dashboardStatsData.completedReports}</p>
                </div>
                <FileText className="text-purple-600" size={32} />
              </div>
            </div>
          </div>

          {/* Recent Patients */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-xl font-bold text-gray-800 mb-4">Recent Patients</h3>
            <div className="space-y-4">
              {isLoadingData ? (
                <p className="text-gray-600">Loading patients...</p>
              ) : recentPatientsData.length === 0 ? (
                <p className="text-gray-600">No patients found</p>
              ) : (
                recentPatientsData.slice(0, 5).map((patient: any) => (
                  <div key={patient.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer" onClick={() => setSelectedPatient(patient)}>
                    <div>
                      <h4 className="font-semibold text-gray-800">{patient.name}</h4>
                      <p className="text-sm text-gray-600">{patient.age} years  {patient.gender}  {patient.dosha || 'N/A'}</p>
                    </div>
                    <Phone className="text-gray-400" size={20} />
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Today's Appointments */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-xl font-bold text-gray-800 mb-4">Today's Appointments</h3>
            <div className="space-y-4">
              {isLoadingData ? (
                <p className="text-gray-600">Loading appointments...</p>
              ) : todayAppointmentsApiData.length === 0 ? (
                <p className="text-gray-600">No appointments scheduled for today</p>
              ) : (
                todayAppointmentsApiData.map((appointment: any) => (
                  <div key={appointment.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50">
                    <div className="flex items-center gap-4">
                      <div className="bg-green-100 text-green-700 px-3 py-1 rounded">
                        {appointment.appointmentTime || appointment.time}
                      </div>
                      <div>
                        <h4 className="font-semibold text-gray-800">{appointment.patientName || appointment.patient}</h4>
                        <p className="text-sm text-gray-600">{appointment.appointmentType || appointment.type}</p>
                      </div>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${appointment.status === 'SCHEDULED' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-700'}`}>
                      {appointment.status}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      );
    }

    if (activeModule === 'intake') {
      return (
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-2xl font-bold text-gray-800 mb-6">Patient Case Intake Form</h3>
            
            {/* Patient Selection */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">Select Patient</label>
              <select 
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                value={selectedPatient?.id || ''}
                onChange={(e) => {
                  const patient = recentPatientsData.find((p: any) => p.id === e.target.value);
                  setSelectedPatient(patient);
                }}
              >
                <option value="">Select a patient...</option>
                {recentPatientsData.map((patient: any) => (
                  <option key={patient.id} value={patient.id}>
                    {patient.name} - {patient.age}y {patient.gender}
                  </option>
                ))}
              </select>
            </div>

            {selectedPatient ? (
              <div className="space-y-6">
                {/* Patient Info */}
                <div className="bg-green-50 p-4 rounded-lg">
                  <h4 className="font-semibold text-green-800 mb-2">Patient Information</h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <p className="text-gray-600">Name</p>
                      <p className="font-medium">{selectedPatient.name}</p>
                    </div>
                    <div>
                      <p className="text-gray-600">Age</p>
                      <p className="font-medium">{selectedPatient.age} years</p>
                    </div>
                    <div>
                      <p className="text-gray-600">Gender</p>
                      <p className="font-medium">{selectedPatient.gender}</p>
                    </div>
                    <div>
                      <p className="text-gray-600">Phone</p>
                      <p className="font-medium">{selectedPatient.phone}</p>
                    </div>
                  </div>
                </div>

                {/* Chief Complaints */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Chief Complaints</label>
                  <textarea
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    rows={4}
                    placeholder="Enter patient's main symptoms and complaints..."
                    value={intakeForm.chiefComplaints}
                    onChange={(e) => setIntakeForm({ ...intakeForm, chiefComplaints: e.target.value })}
                  />
                </div>

                {/* Medical History */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Medical History</label>
                  <textarea
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    rows={3}
                    placeholder="Past medical conditions, surgeries, etc..."
                    value={intakeForm.medicalHistory}
                    onChange={(e) => setIntakeForm({ ...intakeForm, medicalHistory: e.target.value })}
                  />
                </div>

                {/* Current Medications */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Current Medications</label>
                  <textarea
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    rows={3}
                    placeholder="List current medications..."
                    value={intakeForm.currentMedications}
                    onChange={(e) => setIntakeForm({ ...intakeForm, currentMedications: e.target.value })}
                  />
                </div>

                {/* Lifestyle Factors */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Sleep Pattern</label>
                    <select 
                      className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
                      value={intakeForm.sleepPattern}
                      onChange={(e) => setIntakeForm({ ...intakeForm, sleepPattern: e.target.value })}
                    >
                      <option>Regular (7-8 hours)</option>
                      <option>Irregular</option>
                      <option>Insufficient (&lt;6 hours)</option>
                      <option>Excessive (&gt;9 hours)</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Appetite</label>
                    <select 
                      className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
                      value={intakeForm.appetite}
                      onChange={(e) => setIntakeForm({ ...intakeForm, appetite: e.target.value })}
                    >
                      <option>Normal</option>
                      <option>Increased</option>
                      <option>Decreased</option>
                      <option>Irregular</option>
                    </select>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex gap-4">
                  <button 
                    onClick={saveCaseIntake}
                    disabled={savingIntake}
                    className="flex-1 bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 transition font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    {savingIntake ? (
                      <><Loader className="animate-spin" size={20} /><span>Saving...</span></>
                    ) : (
                      <span>Save Case Intake</span>
                    )}
                  </button>
                  <button 
                    onClick={clearIntakeForm}
                    disabled={savingIntake}
                    className="px-6 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Clear Form
                  </button>
                </div>
              </div>
            ) : (
              <div className="text-center py-12 text-gray-500">
                <FileText size={48} className="mx-auto mb-4 text-gray-400" />
                <p>Please select a patient to begin case intake</p>
              </div>
            )}
          </div>
        </div>
      );
    }

    if (activeModule === 'visual') {
      return (
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-2xl font-bold text-gray-800 mb-6">Visual Diagnostics</h3>
            
            {/* Patient Selection */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">Select Patient</label>
              <select 
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                value={selectedPatient?.id || ''}
                onChange={(e) => {
                  const patient = recentPatientsData.find((p: any) => p.id === e.target.value);
                  setSelectedPatient(patient);
                }}
              >
                <option value="">Select a patient...</option>
                {recentPatientsData.map((patient: any) => (
                  <option key={patient.id} value={patient.id}>
                    {patient.name} - {patient.age}y {patient.gender}
                  </option>
                ))}
              </select>
            </div>

            {selectedPatient ? (
              <div className="space-y-6">
                {/* Patient Info */}
                <div className="bg-blue-50 p-4 rounded-lg">
                  <h4 className="font-semibold text-blue-800 mb-2">Selected Patient</h4>
                  <p className="text-blue-900">{selectedPatient.name} - {selectedPatient.age}y {selectedPatient.gender}</p>
                </div>

                {/* Image Upload Tabs */}
                <div className="border-b border-gray-200">
                  <div className="flex gap-4">
                    {['tongue', 'iris', 'nails', 'skin'].map((type) => (
                      <button
                        key={type}
                        onClick={() => setImageUploadTab(type)}
                        className={`px-4 py-2 font-medium capitalize transition ${
                          imageUploadTab === type
                            ? 'text-green-600 border-b-2 border-green-600'
                            : 'text-gray-600 hover:text-gray-800'
                        }`}
                      >
                        {type} Analysis
                      </button>
                    ))}
                  </div>
                </div>

                {/* Upload Section */}
                <div className="space-y-4">
                  <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-green-500 transition cursor-pointer">
                    <input
                      type="file"
                      accept="image/*"
                      onChange={(e) => handleImageUpload(e, imageUploadTab)}
                      className="hidden"
                      id={`upload-${imageUploadTab}`}
                    />
                    <label htmlFor={`upload-${imageUploadTab}`} className="cursor-pointer">
                      <Upload size={48} className="mx-auto mb-4 text-gray-400" />
                      <p className="text-gray-600 mb-2">
                        Click to upload or drag and drop
                      </p>
                      <p className="text-sm text-gray-500">
                        Upload {imageUploadTab} image for AI analysis
                      </p>
                    </label>
                  </div>

                  {/* Display uploaded image */}
                  {uploadedImages[imageUploadTab] && (
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <div className="flex items-start gap-4">
                        <img
                          src={uploadedImages[imageUploadTab].preview}
                          alt={`${imageUploadTab} analysis`}
                          className="w-48 h-48 object-cover rounded-lg"
                        />
                        <div className="flex-1">
                          <h4 className="font-semibold text-gray-800 mb-2">Analysis Result</h4>
                          {analyzingImage === imageUploadTab ? (
                            <div className="flex items-center gap-2 text-gray-600">
                              <Loader className="animate-spin" size={20} />
                              <span>Analyzing image...</span>
                            </div>
                          ) : (
                            <p className="text-gray-700">
                              {imageAnalysis[imageUploadTab] || 'Analysis completed. Ready for review.'}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Analysis Summary */}
                {Object.keys(uploadedImages).some(key => uploadedImages[key]) && (
                  <div className="bg-green-50 p-6 rounded-lg">
                    <h4 className="font-semibold text-green-800 mb-4">Visual Diagnostics Summary</h4>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      {['tongue', 'iris', 'nails', 'skin'].map((type) => (
                        <div key={type} className="flex items-center gap-2">
                          {uploadedImages[type] ? (
                            <><Eye className="text-green-600" size={16} />
                            <span className="text-green-700 capitalize">{type}: Analyzed</span></>
                          ) : (
                            <span className="text-gray-500 capitalize">{type}: Not uploaded</span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-12 text-gray-500">
                <Eye size={48} className="mx-auto mb-4 text-gray-400" />
                <p>Please select a patient to begin visual diagnostics</p>
              </div>
            )}
          </div>
        </div>
      );
    }

    if (activeModule === 'clinical') {
      return (
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-2xl font-bold text-gray-800 mb-6">Clinical Intelligence Report</h3>
            
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">Select Patient</label>
              <select 
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
                value={selectedPatient?.id || ''}
                onChange={(e) => {
                  const patient = recentPatientsData.find((p: any) => p.id === e.target.value);
                  setSelectedPatient(patient);
                }}
              >
                <option value="">Select a patient...</option>
                {recentPatientsData.map((patient: any) => (
                  <option key={patient.id} value={patient.id}>{patient.name} - {patient.age}y</option>
                ))}
              </select>
            </div>

            {selectedPatient ? (
              <div className="space-y-6">
                <div className="bg-purple-50 p-4 rounded-lg">
                  <h4 className="font-semibold text-purple-800 mb-2">Patient: {selectedPatient.name}</h4>
                  <p className="text-sm text-purple-700">{selectedPatient.age}y  {selectedPatient.gender}  Dosha: {selectedPatient.dosha}</p>
                </div>

                <button 
                  onClick={generateClinicalReport}
                  disabled={generatingClinicalReport}
                  className="w-full bg-purple-600 text-white px-6 py-3 rounded-lg hover:bg-purple-700 transition font-medium disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {generatingClinicalReport ? (
                    <><Loader className="animate-spin" size={20} /><span>Generating Report...</span></>
                  ) : (
                    <><Activity size={20} /><span>Generate Clinical Intelligence Report</span></>
                  )}
                </button>

                {clinicalReport && (
                  <div className="bg-gray-50 p-6 rounded-lg space-y-4">
                    <h4 className="font-bold text-gray-800 text-lg">Clinical Report Generated</h4>
                    <div className="space-y-3">
                      <div>
                        <p className="text-sm font-medium text-gray-600">Patient Overview</p>
                        <p className="text-gray-800">{clinicalReport.patientOverview || 'Comprehensive assessment completed'}</p>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-600">Current Health Status</p>
                        <p className="text-gray-800">{clinicalReport.currentHealthStatus || 'Status evaluated'}</p>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-600">Follow-up Recommendation</p>
                        <p className="text-gray-800">{clinicalReport.followUpRecommendation || 'Schedule follow-up in 2 weeks'}</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-12 text-gray-500">
                <Activity size={48} className="mx-auto mb-4 text-gray-400" />
                <p>Select a patient to generate clinical intelligence report</p>
              </div>
            )}
          </div>
        </div>
      );
    }

    if (activeModule === 'snl') {
      return (
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-2xl font-bold text-gray-800 mb-6">SNL Prescription Composer</h3>
            
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">Select Patient</label>
              <select 
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
                value={selectedPatient?.id || ''}
                onChange={(e) => {
                  const patient = recentPatientsData.find((p: any) => p.id === e.target.value);
                  setSelectedPatient(patient);
                }}
              >
                <option value="">Select a patient...</option>
                {recentPatientsData.map((patient: any) => (
                  <option key={patient.id} value={patient.id}>{patient.name} - {patient.age}y</option>
                ))}
              </select>
            </div>

            {selectedPatient ? (
              <div className="space-y-6">
                <div className="bg-green-50 p-4 rounded-lg">
                  <h4 className="font-semibold text-green-800 mb-2">Patient: {selectedPatient.name}</h4>
                  <p className="text-sm text-green-700">{selectedPatient.age}y  {selectedPatient.gender}  Dosha: {selectedPatient.dosha}</p>
                </div>

                <button 
                  onClick={generateSNLPrescription}
                  disabled={generatingSNL}
                  className="w-full bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 transition font-medium disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {generatingSNL ? (
                    <><Loader className="animate-spin" size={20} /><span>Generating Prescription...</span></>
                  ) : (
                    <><Leaf size={20} /><span>Generate SNL Prescription</span></>
                  )}
                </button>

                {snlPrescription && (
                  <div className="bg-gray-50 p-6 rounded-lg">
                    <h4 className="font-bold text-gray-800 text-lg mb-4">SNL Prescription</h4>
                    <div className="bg-white p-4 rounded border border-gray-200">
                      <pre className="whitespace-pre-wrap text-sm text-gray-800 font-mono">
                        {snlPrescription}
                      </pre>
                    </div>
                    <div className="mt-4 flex gap-3">
                      <button className="flex-1 bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 transition">
                        Download PDF
                      </button>
                      <button className="flex-1 border border-gray-300 px-4 py-2 rounded hover:bg-gray-50 transition">
                        Print
                      </button>
                    </div>
                  </div>
                )}

                <div className="bg-blue-50 p-4 rounded-lg">
                  <h5 className="font-medium text-blue-800 mb-2">SNL Format Components:</h5>
                  <ul className="text-sm text-blue-700 space-y-1">
                    <li> Herbal formulations based on prakriti</li>
                    <li> Dietary recommendations (Pathya-Apathya)</li>
                    <li> Lifestyle modifications (Dinacharya)</li>
                    <li> Yoga and Pranayama guidance</li>
                  </ul>
                </div>
              </div>
            ) : (
              <div className="text-center py-12 text-gray-500">
                <Leaf size={48} className="mx-auto mb-4 text-gray-400" />
                <p>Select a patient to compose SNL prescription</p>
              </div>
            )}
          </div>
        </div>
      );
    }

    if (activeModule === 'knowledge') {
      return (
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-2xl font-bold text-gray-800 mb-6">Ayurvedic Knowledge Base</h3>
            
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">Select Patient (Optional)</label>
              <select 
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
                value={selectedPatient?.id || ''}
                onChange={(e) => {
                  const patient = recentPatientsData.find((p: any) => p.id === e.target.value);
                  setSelectedPatient(patient);
                }}
              >
                <option value="">Browse general knowledge...</option>
                {recentPatientsData.map((patient: any) => (
                  <option key={patient.id} value={patient.id}>{patient.name} - Get patient-specific references</option>
                ))}
              </select>
            </div>

            {selectedPatient && (
              <div className="mb-6">
                <div className="bg-orange-50 p-4 rounded-lg mb-4">
                  <h4 className="font-semibold text-orange-800 mb-2">Patient: {selectedPatient.name}</h4>
                  <p className="text-sm text-orange-700">Generating knowledge references for {selectedPatient.dosha} dosha type</p>
                </div>

                <button 
                  onClick={generateKnowledgeReferences}
                  disabled={generatingKnowledge}
                  className="w-full bg-orange-600 text-white px-6 py-3 rounded-lg hover:bg-orange-700 transition font-medium disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {generatingKnowledge ? (
                    <><Loader className="animate-spin" size={20} /><span>Searching Knowledge Base...</span></>
                  ) : (
                    <><BookOpen size={20} /><span>Generate Knowledge References</span></>
                  )}
                </button>

                {knowledgeReferences && (
                  <div className="mt-6 bg-gray-50 p-6 rounded-lg">
                    <h4 className="font-bold text-gray-800 text-lg mb-4">Relevant Ayurvedic References</h4>
                    <div className="bg-white p-4 rounded border border-gray-200">
                      <div className="prose prose-sm max-w-none">
                        <p className="text-gray-800 whitespace-pre-wrap">{knowledgeReferences}</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 cursor-pointer">
                <BookOpen className="text-orange-600 mb-2" size={32} />
                <h4 className="font-semibold text-gray-800 mb-2">Classical Texts</h4>
                <p className="text-sm text-gray-600">Browse Charaka Samhita, Sushruta Samhita, Ashtanga Hridaya</p>
              </div>

              <div className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 cursor-pointer">
                <Leaf className="text-green-600 mb-2" size={32} />
                <h4 className="font-semibold text-gray-800 mb-2">Herbal Database</h4>
                <p className="text-sm text-gray-600">Search medicinal plants and their properties</p>
              </div>

              <div className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 cursor-pointer">
                <Activity className="text-blue-600 mb-2" size={32} />
                <h4 className="font-semibold text-gray-800 mb-2">Treatment Protocols</h4>
                <p className="text-sm text-gray-600">Evidence-based Ayurvedic treatment guidelines</p>
              </div>

              <div className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 cursor-pointer">
                <FileText className="text-purple-600 mb-2" size={32} />
                <h4 className="font-semibold text-gray-800 mb-2">Research Papers</h4>
                <p className="text-sm text-gray-600">Latest research in Ayurvedic medicine</p>
              </div>
            </div>
          </div>
        </div>
      );
    }

    // Other modules still show placeholder
    return (
      <div className="p-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">
          {modules.find(m => m.id === activeModule)?.name || 'Dashboard'}
        </h2>
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
          <p className="text-yellow-800">
            This module will be implemented soon. Current module: <strong>{activeModule}</strong>
          </p>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-blue-50">
      <nav className="bg-white border-b border-gray-200 px-6 py-4 sticky top-0 z-50 shadow-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button onClick={() => setSidebarOpen(!sidebarOpen)} className="lg:hidden">
              {sidebarOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
            <div className="flex items-center space-x-2">
              <Leaf className="text-green-600" size={32} />
              <div>
                <h1 className="text-xl font-bold text-gray-800">AyuPilot</h1>
                <p className="text-xs text-gray-600">Ayurvedic Co-Pilot</p>
              </div>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <button 
              onClick={() => setShowAIAssistant(!showAIAssistant)}
              className="flex items-center gap-2 bg-gradient-to-r from-green-600 to-green-700 text-white px-4 py-2 rounded-lg hover:from-green-700 hover:to-green-800 transition shadow-lg"
            >
              <MessageSquare size={20} />
              <span className="hidden md:inline">AI Assistant</span>
            </button>
          </div>
        </div>
      </nav>

      <div className="flex">
        <aside className={`${sidebarOpen ? 'translate-x-0' : '-translate-x-full'} lg:translate-x-0 fixed lg:static inset-y-0 left-0 z-40 w-64 bg-white border-r border-gray-200 transition-transform duration-300 mt-16 lg:mt-0`}>
          <div className="p-6 space-y-2">
            {modules.map(module => (
              <button
                key={module.id}
                onClick={() => {
                  setActiveModule(module.id);
                  if (window.innerWidth < 1024) setSidebarOpen(false);
                }}
                className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition ${
                  activeModule === module.id 
                    ? 'bg-green-100 text-green-700 font-medium' 
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                <module.icon size={20} />
                <span>{module.name}</span>
              </button>
            ))}
          </div>
        </aside>

        <main className="flex-1 p-6 lg:p-8">
          {renderContent()}
        </main>
      </div>

      {showAIAssistant && (
        <div className="fixed bottom-6 right-6 w-96 h-[600px] bg-white rounded-lg shadow-2xl border border-gray-200 flex flex-col z-50">
          <div className="bg-gradient-to-r from-green-600 to-green-700 text-white p-4 rounded-t-lg flex items-center justify-between">
            <div className="flex items-center gap-2">
              <MessageSquare size={20} />
              <div>
                <h3 className="font-semibold">AyuPilot AI Assistant</h3>
                <p className="text-xs text-green-100">Ready for Backend Integration</p>
              </div>
            </div>
            <button 
              onClick={() => setShowAIAssistant(false)}
              className="hover:bg-green-800 p-1 rounded"
            >
              <X size={20} />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((msg: any, idx: number) => (
              <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[80%] rounded-lg p-3 ${
                  msg.role === 'user' 
                    ? 'bg-green-600 text-white' 
                    : 'bg-gray-100 text-gray-800'
                }`}>
                  <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          <div className="border-t border-gray-200 p-4">
            <div className="flex gap-2">
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && handleSendMessage()}
                placeholder="Ask about diagnosis, treatments..."
                className="flex-1 p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm"
                disabled={isLoading}
              />
              <button
                onClick={handleSendMessage}
                disabled={isLoading || !inputMessage.trim()}
                className="bg-green-600 text-white p-2 rounded-lg hover:bg-green-700 transition disabled:opacity-50"
              >
                <Send size={20} />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}




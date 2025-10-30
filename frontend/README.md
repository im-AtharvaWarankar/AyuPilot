# AyuPilot Frontend

A modern React-based frontend for the AyuPilot Ayurvedic healthcare management system.

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm
- Backend Django server running on `http://localhost:8000`

### Installation

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Start development server:**
   ```bash
   npm run dev
   ```

3. **Open in browser:**
   Navigate to `http://localhost:3000`

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   └── AyuPilotDashboard.tsx    # Main dashboard component
│   ├── App.tsx                      # Root component
│   ├── main.tsx                     # Entry point
│   └── index.css                    # Global styles
├── public/
├── package.json
├── vite.config.ts                   # Vite configuration
├── tailwind.config.js               # TailwindCSS configuration
└── tsconfig.json                    # TypeScript configuration
```

## 🔧 Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## 🎨 Features

- **Dashboard Overview** - Patient statistics and appointments
- **Case Intake** - New patient registration with Prakriti assessment
- **Visual Diagnostics** - AI-powered image analysis (tongue, iris, nails, skin)
- **Clinical Intelligence** - Comprehensive AI-generated reports
- **SNL Composer** - Supplements, Nutrition & Lifestyle prescriptions
- **Knowledge Base** - Classical references and clinical studies
- **AI Assistant** - Real-time chat support

## 🔗 Backend Integration

The frontend is configured to proxy API requests to the Django backend:

- **API Base URL:** `http://localhost:8000/api/`
- **Proxy Configuration:** See `vite.config.ts`

### API Endpoints (To be implemented in Django)

```
POST /api/patients/           # Create patient
GET  /api/patients/           # List patients
POST /api/images/analyze/     # Analyze medical images
POST /api/documents/analyze/  # Analyze medical documents
POST /api/reports/clinical/   # Generate clinical reports
POST /api/prescriptions/snl/  # Generate SNL prescriptions
POST /api/chat/              # AI assistant chat
```

## 🎯 Next Steps for Backend Integration

1. **Create Django API endpoints** for all frontend features
2. **Replace placeholder functions** in `AyuPilotDashboard.tsx` with actual API calls
3. **Add authentication** and user management
4. **Implement file upload** handling for images and documents
5. **Add error handling** and loading states
6. **Configure CORS** in Django for frontend communication

## 🛠 Technology Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **TailwindCSS** - Styling
- **Lucide React** - Icons
- **Axios** - HTTP client (ready for API integration)

## 📝 Development Notes

- The current component contains placeholder data and mock API calls
- All AI functionality is prepared for backend integration
- Responsive design optimized for desktop and tablet use
- Modern UI/UX following healthcare application best practices

## 🔒 Security Considerations

- API keys should be stored in backend environment variables
- File uploads should be validated and sanitized
- User authentication and authorization required
- HTTPS recommended for production deployment

# AyuPilot - Ayurvedic Healthcare Management System

A comprehensive Ayurvedic healthcare platform combining AI-powered diagnostics with traditional Ayurvedic wisdom.

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.12+
- Node.js 18+
- PostgreSQL 14+
- RabbitMQ
- Redis

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd django-boilerplate
   ```

2. **Create vault.py from example:**
   ```bash
   cp src/vault.example.py src/vault.py
   ```
   Edit `src/vault.py` and fill in your credentials (AWS, database, email, etc.)

3. **Create .env file:**
   ```bash
   cp .env.example .env
   ```
   Add your OpenAI API key and other environment variables

4. **Start with Docker:**
   ```bash
   bash run.sh start-dev
   ```

5. **Run migrations:**
   ```bash
   docker exec -it ayupilot-backend python manage.py makemigrations
   docker exec -it ayupilot-backend python manage.py migrate
   ```

6. **Create superuser:**
   ```bash
   docker exec -it ayupilot-backend python manage.py createsuperuser
   ```

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start development server:**
   ```bash
   npm run dev
   ```

4. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - Admin Panel: http://localhost:8000/admin

## 📋 Features

- **AI-Powered Diagnostics**: Visual analysis of tongue, iris, nails, and skin
- **Prakriti Assessment**: Dosha-based constitutional analysis
- **Clinical Intelligence**: Automated report generation
- **SNL Composer**: Supplements, Nutrition & Lifestyle prescriptions
- **Knowledge Base**: Integration with classical Ayurvedic texts
- **Real-time Chat**: AI assistant for healthcare queries
- **Appointment Management**: Automated status tracking
- **Multi-tenant Support**: Doctor and patient dashboards

## 🛠 Tech Stack

### Backend
- Django 4.x + Django REST Framework
- PostgreSQL 14
- Celery + RabbitMQ (task queue)
- Redis (caching)
- Docker & Docker Compose
- OpenAI API integration

### Frontend
- React 18 + TypeScript
- Vite (build tool)
- TailwindCSS
- Axios (API client)
- Lucide Icons

## 📁 Project Structure

```
AyuPilot/
├── django-boilerplate/          # Backend Django application
│   ├── ayupilot/                # Main app (models, views, tasks)
│   ├── users/                   # User management
│   ├── atomicloops/             # Base utilities
│   ├── src/                     # Settings and configs
│   ├── utils/                   # Helper functions
│   ├── docker-compose-dev.yml   # Dev environment
│   └── requirements.txt         # Python dependencies
│
└── frontend/                    # React frontend
    ├── src/
    │   ├── components/          # React components
    │   ├── services/            # API services
    │   └── hooks/               # Custom hooks
    ├── package.json             # Node dependencies
    └── vite.config.ts           # Vite configuration
```

## 🔧 Configuration

### Environment Variables

**Backend (.env):**
```env
ENV=dev
OPENAI_API_KEY=your-openai-api-key
SECRET_KEY=your-django-secret-key
```

**Vault (src/vault.py):**
- Database credentials
- AWS S3 credentials
- Email configuration
- API endpoints

See `vault.example.py` for template.

## 🧪 Testing

```bash
# Run Django tests
docker exec -it ayupilot-backend python manage.py test

# Run with coverage
docker exec -it ayupilot-backend coverage run manage.py test
docker exec -it ayupilot-backend coverage report
```

## 📝 API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/swagger/
- ReDoc: http://localhost:8000/redoc/

## 🔐 Security Notes

- Never commit `vault.py` or `.env` files
- Use `.env.example` and `vault.example.py` as templates
- Rotate credentials regularly
- Enable proper authentication before production

## 📦 Deployment

The project includes Docker configurations for production deployment. See `docker-compose.yml` for production setup.

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Write/update tests
4. Submit a pull request

## 📄 License

[Add your license here]

## 📧 Support

For issues and questions, please open a GitHub issue or contact the development team.

---

**Note**: This project integrates OpenAI GPT models for AI assistance. Ensure you have valid API credentials and understand associated costs.

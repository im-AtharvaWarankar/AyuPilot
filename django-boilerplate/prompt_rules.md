# Django Best Practices and Patterns Guide

## Project Overview
This guide covers Django development best practices, patterns, and conventions for building scalable, maintainable web applications using Django REST Framework.

## 🚨 CRITICAL CODING RULES - MUST FOLLOW STRICTLY

### ❌ FORBIDDEN: Never Use `blank=True` in Model Fields
- **NEVER** add `blank=True` to any Django model field definition
- Use `null=True` only when the database column should genuinely allow NULL values
- Handle all form and API validation at the serializer/form level, not at the model level
- This ensures consistency between database constraints and application validation logic
- Violating this rule will cause validation inconsistencies and data integrity issues

**Example of CORRECT usage:**
```python
# ✅ CORRECT - Only null=True for database nullability
content = models.TextField(verbose_name=_("Content"), null=True)

# ❌ WRONG - Never use blank=True
content = models.TextField(verbose_name=_("Content"), null=True, blank=True)  # FORBIDDEN
```

## Django Project Structure
```
project_name/
├── src/                       # Django settings and configuration
│   ├── __init__.py           # Package initialization
│   ├── asgi.py               # ASGI configuration for async deployment
│   ├── wsgi.py               # WSGI configuration for production deployment
│   ├── urls.py               # Main URL routing configuration
│   ├── celery.py             # Celery configuration for background tasks
│   ├── vault.py              # Secure configuration management (not in git)
│   └── settings/             # Environment-specific settings
│       ├── __init__.py       # Settings package initialization
│       ├── base.py           # Common/shared settings for all environments
│       ├── dev.py            # Development environment settings
│       ├── prod.py           # Production environment settings
│       └── staging.py        # Staging environment settings (optional)
├── app_name/                  # Individual Django apps
│   ├── models.py             # Database models
│   ├── serializers.py        # API serializers
│   ├── views.py              # API views and viewsets
│   ├── urls.py               # URL routing
│   ├── admin.py              # Django admin configuration
│   ├── tasks.py              # Celery background tasks
│   ├── filters.py            # Query filters
│   ├── permissions.py        # Custom permissions
│   ├── signals.py            # Django signals
│   ├── utils.py              # Utility functions
│   ├── apps.py               # App configuration
│   ├── migrations/           # Database migrations
│   └── tests.py              # Unit tests
├── utils/                     # Shared utilities
├── helpers/                   # Helper scripts
├── templates/                 # HTML templates
├── static/                    # Static files
├── locale/                    # Internationalization files
├── requirements.txt           # Python dependencies
├── manage.py                  # Django management script
└── docker-compose.yml         # Docker configuration
```

## Coding Guidelines

### Django Best Practices
- Use Django's built-in authentication system
- Follow Django's model-view-template (MVT) pattern
- Use Django REST Framework for API endpoints
- Implement proper permission classes for API views
- Use Django's translation framework for internationalization
- Follow the "fat models, thin views" principle
- Use database transactions for data integrity
- **NEVER use `blank=True` in model fields** - Use `null=True` only for database-level nullability
- Always validate data at the serializer/form level, not at the model level with `blank=True`

### Code Style Standards
- Follow PEP 8 standards consistently
- Use meaningful variable and function names
- Add docstrings to classes and complex functions
- Use type hints where appropriate
- Keep line length under 120-127 characters
- Use consistent indentation (4 spaces)

### Database Guidelines
- Use UUID primary keys for better scalability
- Implement proper database indexing for performance
- Use select_related() and prefetch_related() for query optimization
- Handle database migrations carefully
- Use database constraints and validations
- Consider database partitioning for large tables
- **CRITICAL: Never use `blank=True` in model field definitions**
  - Use `null=True` only when the database column should allow NULL values
  - Handle form/API validation at the serializer or form level
  - `blank=True` creates inconsistency between database and application validation
  - Always prefer explicit validation in serializers over implicit model-level blank validation

### API Design Principles
- Use ModelViewSet for standard CRUD operations
- Implement proper serializers with validation
- Use pagination for list endpoints
- Return proper HTTP status codes and error messages
- Implement API versioning when needed
- Use consistent URL patterns

## Model Patterns

### Base Model Pattern
```python
from django.db import models
import uuid

class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
```

### Model Best Practices
```python
class Article(BaseModel):
    title = models.CharField(
        verbose_name=_("Title"),
        max_length=500,
        help_text="Article title"
    )
    content = models.TextField(
        verbose_name=_("Content"),
        null=True
    )
    published_date = models.DateTimeField(
        verbose_name=_("Publication Date"),
        null=True,
        db_index=True  # Add indexes for frequently queried fields
    )
    
    class Meta:
        db_table = "article"
        verbose_name = _("Article")
        verbose_name_plural = _("Articles")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['published_date', 'title']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Custom save logic here
        super().save(*args, **kwargs)
```

## Serializer Patterns

### Base Serializer
```python
from rest_framework import serializers

class BaseSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    class Meta:
        abstract = True
```

### Serializer Best Practices
```python
class ArticleSerializer(BaseSerializer):
    author_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Article
        fields = (
            'id', 'created_at', 'updated_at',
            'title', 'content', 'published_date',
            'author_name'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')
    
    def get_author_name(self, obj):
        return obj.author.get_full_name() if obj.author else None
    
    def validate_title(self, value):
        if len(value) < 5:
            raise serializers.ValidationError("Title must be at least 5 characters long")
        return value
    
    def create(self, validated_data):
        # Custom creation logic
        return super().create(validated_data)
```

## View Patterns

### ModelViewSet Pattern
```python
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

class ArticleViewSet(ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    filterset_class = ArticleFilter
    search_fields = ('title', 'content')
    ordering_fields = ('created_at', 'updated_at', 'published_date')
    ordering = ('-created_at',)
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Filter based on user permissions
        queryset = super().get_queryset()
        if not self.request.user.is_superuser:
            queryset = queryset.filter(author=self.request.user)
        return queryset
    
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        article = self.get_object()
        article.published_date = timezone.now()
        article.save()
        return Response({'status': 'published'})
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        recent_articles = self.get_queryset().filter(
            published_date__gte=timezone.now() - timedelta(days=7)
        )
        serializer = self.get_serializer(recent_articles, many=True)
        return Response(serializer.data)
```

### APIView Pattern
```python
from rest_framework.views import APIView

class CustomArticleView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        try:
            # Custom logic here
            data = {"message": "success"}
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request, *args, **kwargs):
        serializer = ArticleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
```

## Admin Patterns

### ModelAdmin Best Practices
```python
from django.contrib import admin

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'author', 'published_date', 'created_at'
    )
    list_filter = (
        'published_date', 'created_at', 'author'
    )
    search_fields = ('title', 'content', 'author__email')
    readonly_fields = ('id', 'created_at', 'updated_at')
    date_hierarchy = 'published_date'
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {
            'fields': ('title', 'content', 'author')
        }),
        ('Metadata', {
            'fields': ('published_date', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('author')
```

## Task Patterns (Celery)

### Task Best Practices
```python
from celery import shared_task
from django.core.mail import send_mail

@shared_task(bind=True, queue='default')
def process_article(self, article_id):
    try:
        article = Article.objects.get(id=article_id)
        # Process article logic
        return {"status": "success", "article_id": article_id}
    except Article.DoesNotExist:
        return {"status": "error", "message": "Article not found"}
    except Exception as e:
        # Retry logic
        raise self.retry(exc=e, countdown=60, max_retries=3)

@shared_task(queue='email')
def send_notification_email(user_email, subject, message):
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email='noreply@example.com',
            recipient_list=[user_email]
        )
        return {"status": "email_sent"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
```

## Permission Patterns

### Custom Permission Classes
```python
from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only to the owner
        return obj.owner == request.user

class IsAuthorOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user
```

## Filter Patterns

### Django Filter Best Practices
```python
import django_filters
from django_filters import rest_framework as filters

class ArticleFilter(filters.FilterSet):
    title = filters.CharFilter(lookup_expr='icontains')
    published_after = filters.DateTimeFilter(
        field_name='published_date', 
        lookup_expr='gte'
    )
    published_before = filters.DateTimeFilter(
        field_name='published_date', 
        lookup_expr='lte'
    )
    author = filters.ModelChoiceFilter(queryset=User.objects.all())
    
    class Meta:
        model = Article
        fields = ['title', 'published_after', 'published_before', 'author']
```

## URL Patterns

### URL Configuration Best Practices
```python
from rest_framework.routers import DefaultRouter
from django.urls import path, include

router = DefaultRouter()
router.register(r'articles', ArticleViewSet, basename='article')
router.register(r'categories', CategoryViewSet, basename='category')

urlpatterns = [
    path('custom-endpoint/', CustomView.as_view(), name='custom-endpoint'),
    path('health/', HealthCheckView.as_view(), name='health-check'),
]

urlpatterns += router.urls
```

## Naming Conventions

### File and Directory Names
- Use **snake_case** for Python files and variables
- Use **PascalCase** for model and class names  
- Use **kebab-case** for URL patterns
- Use descriptive names for utility scripts

### Database Naming
- Table names: **snake_case** (e.g., `user_profile`)
- Field names: **snake_case** (e.g., `created_at`)
- Index names: descriptive (e.g., `idx_article_published_date`)

### API Naming
- Endpoints: **kebab-case** (e.g., `/api/user-profiles/`)
- Query parameters: **snake_case** (e.g., `?created_after=`)
- JSON fields: **camelCase** or **snake_case** (be consistent)

## Testing Patterns

### Test Best Practices
```python
from django.test import TestCase
from rest_framework.test import APITestCase
from django.urls import reverse

class ArticleModelTest(TestCase):
    def setUp(self):
        self.article = Article.objects.create(
            title="Test Article",
            content="Test content"
        )
    
    def test_string_representation(self):
        self.assertEqual(str(self.article), "Test Article")
    
    def test_model_fields(self):
        self.assertTrue(hasattr(self.article, 'created_at'))
        self.assertTrue(hasattr(self.article, 'updated_at'))

class ArticleAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_create_article(self):
        url = reverse('article-list')
        data = {
            'title': 'New Article',
            'content': 'Article content'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 201)
```

## Performance Optimization

### Query Optimization
```python
# Use select_related for foreign key relationships
articles = Article.objects.select_related('author').all()

# Use prefetch_related for many-to-many relationships
articles = Article.objects.prefetch_related('tags').all()

# Use only() to fetch specific fields
articles = Article.objects.only('title', 'published_date')

# Use values() for simple data retrieval
article_data = Article.objects.values('title', 'author__email')

# Use database functions
from django.db.models import Count
popular_tags = Tag.objects.annotate(article_count=Count('articles'))
```

### Caching Patterns
```python
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

# Function-based caching
def get_popular_articles():
    cache_key = 'popular_articles'
    articles = cache.get(cache_key)
    if articles is None:
        articles = Article.objects.filter(views__gt=1000)
        cache.set(cache_key, articles, 3600)  # Cache for 1 hour
    return articles

# View-level caching
@method_decorator(cache_page(60 * 15), name='list')
class ArticleViewSet(ModelViewSet):
    pass
```

## Security Best Practices

### Authentication and Authorization
```python
# Use proper permission classes
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly

class ArticleViewSet(ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def perform_create(self, serializer):
        # Automatically set the author to the current user
        serializer.save(author=self.request.user)
```

### Input Validation
```python
class ArticleSerializer(serializers.ModelSerializer):
    def validate_title(self, value):
        # Custom validation logic
        if 'spam' in value.lower():
            raise serializers.ValidationError("Title contains inappropriate content")
        return value
    
    def validate(self, data):
        # Cross-field validation
        if data['published_date'] and data['published_date'] > timezone.now():
            raise serializers.ValidationError("Cannot publish in the future")
        return data
```

## Environment Configuration

### Settings Pattern
```python
# settings/base.py - Common settings
# settings/dev.py - Development settings
# settings/prod.py - Production settings

# Use centralized configuration files for sensitive data
from src.config import credentials
from pathlib import Path

# Get environment from system (only for determining config)
ENV = os.getenv('ENV', 'dev')

# Load configuration from centralized config file
config = credentials[ENV]

SECRET_KEY = "django-insecure--3zfk*i#_uvt=z*z!i(cl#$-je(zcfffuc&jj4p+pn@&!i-vgr"
DEBUG = ENV == 'dev'

DATABASES = {
    'default': {
        'ENGINE': config['DB_ENGINE'],
        'NAME': config['DB_NAME'],
        'USER': config['DB_USER'],
        'PASSWORD': config['DB_PASSWORD'],
        'HOST': config['DB_HOST'],
        'PORT': config['DB_PORT'],
    }
}

# Additional configuration from config file
EMAIL = config['EMAIL']
PASSWORD = config['PASSWORD']
AWS_ACCESS_KEY_ID = config['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = config['AWS_SECRET_ACCESS_KEY']
FIREBASE_JSON = config['FIREBASE_JSON']
```

### Configuration File Structure (src/config.py)
```python
credentials = {
    "dev": {
        "DB_ENGINE": "django.db.backends.postgresql",
        "DB_NAME": "defaultdb",
        "DB_USER": "avnadmin", 
        "DB_PASSWORD": "your_password",
        "DB_HOST": "host.docker.internal",
        "DB_PORT": "15432",
        "EMAIL": "atomic.automail@gmail.com",
        "PASSWORD": "app_password",
        "AWS_ACCESS_KEY_ID": "your_key",
        "AWS_SECRET_ACCESS_KEY": "your_secret",
        "FIREBASE_JSON": {
            "type": "service_account",
            "project_id": "your-project",
            # ... firebase config
        }
    },
    "prod": {
        # Production configuration
        "DB_ENGINE": "django.db.backends.postgresql",
        "DB_NAME": "news_monitoring_db",
        "DB_USER": "prod_user",
        # ... production config
    }
}
```

### Alternative: Vault Configuration (src/vault.py)
For even more sensitive data, consider using a vault pattern:
```python
# src/vault.py - For highly sensitive credentials
VAULT = {
    "dev": {
        "database_credentials": {
            "host": "encrypted_or_secured_host",
            "password": "secured_password"
        },
        "api_keys": {
            "stripe_secret": "sk_test_...",
            "openai_key": "sk-..."
        }
    }
}
```

### Benefits of Centralized Configuration:
- **Environment-specific configs**: Easy switching between dev/prod/test
- **Type safety**: Direct Python objects instead of string parsing
- **Validation**: Can add validation logic in config files
- **Documentation**: Self-documenting configuration structure
- **Version control**: Configuration changes are tracked (excluding sensitive files)

### Security Notes:
- Add `src/config.py` to `.gitignore` for sensitive deployments
- Use environment variables only for `ENV` to determine which config to load
- Consider using `src/vault.py` for highly sensitive data with encryption
- Use different config files per environment when needed
## Error Handling

### Exception Handling Patterns
```python
from rest_framework.views import exception_handler
from rest_framework.response import Response

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    
    if response is not None:
        custom_response_data = {
            'error': {
                'status_code': response.status_code,
                'message': response.data.get('detail', 'An error occurred'),
                'timestamp': timezone.now().isoformat()
            }
        }
        response.data = custom_response_data
    
    return response
```

## Logging Configuration

### Logging Best Practices
```python
import logging

logger = logging.getLogger(__name__)

class ArticleViewSet(ModelViewSet):
    def create(self, request, *args, **kwargs):
        logger.info(f"User {request.user.email} creating new article")
        try:
            response = super().create(request, *args, **kwargs)
            logger.info(f"Article created successfully: {response.data['id']}")
            return response
        except Exception as e:
            logger.error(f"Error creating article: {str(e)}")
            raise
```

## Documentation Standards

### Code Documentation
```python
class ArticleManager(models.Manager):
    """
    Custom manager for Article model.
    
    Provides methods for common article queries and operations.
    """
    
    def published(self):
        """
        Returns queryset of published articles.
        
        Returns:
            QuerySet: Articles with published_date not null
        """
        return self.filter(published_date__isnull=False)
    
    def by_author(self, author):
        """
        Returns articles by specific author.
        
        Args:
            author (User): The author to filter by
            
        Returns:
            QuerySet: Articles by the specified author
        """
        return self.filter(author=author)
```

This guide provides comprehensive Django development patterns and best practices that can be applied to any Django project for building scalable, maintainable applications.

## MODELS - Implementation Rules

### ✅ Checklist: Creating a New Model

**Step 1: Inheritance & Imports**

```python
from django.db import models
from atomicloops.models import AtomicBaseModel
from django.utils.translation import gettext_lazy as _
# Import related models

```

- [ ]  Always inherit from `AtomicBaseModel` (provides UUID `id`, `createdAt`, `updatedAt`)
- [ ]  Import `gettext_lazy` as `_` for verbose names

**Step 2: Field Naming**

- [ ]  Use camelCase for all field names (`firstName`, `videoUrl`, `trainingPlanId`)
- [ ]  Foreign keys: name as `<target>Id` (e.g., `userId`, `petId`)
- [ ]  URLs: use `Url` suffix (e.g., `imageUrl`, `videoUrl`)
- [ ]  Booleans: use `is` prefix (e.g., `isCompleted`, `isActive`)

**Step 3: Foreign Key Configuration**

```python
userId = models.ForeignKey(
    CustomUser,
    verbose_name=_('User Id'),
    related_name='model_name_relation',  # REQUIRED
    db_column='user_id',
    on_delete=models.CASCADE
)

```

- [ ]  Always set `related_name` explicitly (avoid default `_set`)
- [ ]  Use descriptive `related_name` that serializers will reference
- [ ]  Set appropriate `on_delete` behavior (`CASCADE`, `SET_NULL`, etc.)
- [ ]  Use `db_column` in snake_case

**Step 4: Choices Implementation**

```python
class StatusChoices(models.TextChoices):
    ACTIVE = 'ACTIVE', _('Active')
    INACTIVE = 'INACTIVE', _('Inactive')

status = models.CharField(
    verbose_name=_('Status'),
    choices=StatusChoices.choices,
    default=StatusChoices.ACTIVE,
    max_length=20,
    db_column='status'
)

```

- [ ]  Use `TextChoices` for enums
- [ ]  Define choices as inner classes
- [ ]  Set appropriate defaults

**Step 5: Meta Configuration**

```python
class Meta:
    db_table = 'table_name'  # snake_case
    verbose_name = 'Model Name'
    verbose_name_plural = 'Model Names'
    managed = True
    # Add constraints only when needed:
    # unique_together = ('field1', 'field2')
    # ordering = ['-createdAt']
    # indexes = [models.Index(fields=['field'])]

```

- [ ]  Set `db_table` in snake_case
- [ ]  Set `managed = True`
- [ ]  Add `verbose_name` and `verbose_name_plural`
- [ ]  Only add `unique_together`, `ordering`, `indexes` when needed

**Step 6: String Representation**

```python
def __str__(self):
    return self.name  # or meaningful identifier

```

- [ ]  Return a concise, meaningful identifier
- [ ]  For relations, use format like `f"{self.petId.name} - {self.levelId.name}"`

---

## 2️⃣ SERIALIZERS - Implementation Rules

### ✅ Checklist: Creating a New Serializer

**Step 1: Inheritance & Imports**

```python
from rest_framework import serializers
from atomicloops.serializers import AtomicSerializer
from .models import YourModel

```

- [ ]  Use `AtomicSerializer` for model serializers (handles timezone conversion, field filtering)
- [ ]  Use `serializers.Serializer` for non-model payloads

**Step 2: Field Definitions**

```python
class YourModelSerializer(AtomicSerializer):
    # Read-only computed fields
    userEmail = serializers.CharField(source='userId.email', read_only=True)

    # SerializerMethodField for complex logic
    isCompleted = serializers.SerializerMethodField()

    def get_isCompleted(self, obj):
        # Custom logic here
        return obj.some_calculation()

```

- [ ]  Use `source='fk.field'` for denormalized read-only fields
- [ ]  Use `SerializerMethodField` for computed values
- [ ]  Keep computed fields read-only

**Step 3: Meta Configuration**

```python
class Meta:
    model = YourModel
    fields = (
        'id', 'createdAt', 'updatedAt',
        'field1', 'field2', 'computed_field'
    )
    get_fields = fields  # Same if no narrowing needed
    list_fields = fields  # Same if no narrowing needed

```

- [ ]  Always include `id`, `createdAt`, `updatedAt` in fields
- [ ]  Set `get_fields` and `list_fields` (same as `fields` if no narrowing)
- [ ]  For different representations, customize `list_fields` vs `get_fields`

**Step 4: Custom Create/Update (when needed)**

```python
def create(self, validated_data):
    # Custom logic before/after creation
    instance = YourModel.objects.create(**validated_data)
    # Additional processing
    return instance

def update(self, instance, validated_data):
    # Custom update logic
    return super().update(instance, validated_data)

```

- [ ]  Override `create`/`update` only when custom logic is needed
- [ ]  Handle password hashing, cascade updates, etc.

**Step 5: Validation (when needed)**

```python
def validate_field_name(self, value):
    if some_condition:
        raise serializers.ValidationError("Error message")
    return value

def validate(self, data):
    # Cross-field validation
    return data

```

- [ ]  Add field-level validation with `validate_<field_name>`
- [ ]  Add cross-field validation with `validate`

---

## 3️⃣ VIEWS - Implementation Rules

### ✅ Checklist: Creating ViewSets (for CRUD resources)

**Step 1: Inheritance & Imports**

```python
from atomicloops.viewsets import AtomicViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import YourModel
from .serializers import YourModelSerializer
from .filters import YourModelFilter

```

- [ ]  Use `AtomicViewSet` for CRUD resources (handles 204/423 delete responses)

**Step 2: Basic Configuration**

```python
class YourModelViewSet(AtomicViewSet):
    queryset = YourModel.objects.all()
    serializer_class = YourModelSerializer
    permission_classes = [IsAuthenticated]  # Override defaults when needed

```

- [ ]  Set `queryset` and `serializer_class`
- [ ]  Override `permission_classes` only when different from defaults
- [ ]  Use `select_related`/`prefetch_related` in queryset for performance

**Step 3: Filtering Configuration**

```python
# Option A: Simple filtering
filterset_fields = ('userId', 'status')

# Option B: Custom filter class (preferred)
filterset_class = YourModelFilter
search_fields = ('name', 'description')
ordering_fields = ('createdAt', 'name')
ordering = ('-createdAt',)

```

- [ ]  Use `filterset_class` for complex filtering
- [ ]  Use `filterset_fields` for simple exact matches
- [ ]  Set `search_fields` for text search
- [ ]  Set `ordering_fields` and default `ordering`

**Step 4: Custom Actions (when needed)**

```python
@action(detail=False, methods=['post'], url_path='bulk-create')
def bulk_create(self, request):
    # Custom logic
    return Response({"created": count})

@action(detail=True, methods=['post'], url_path='mark-complete')
def mark_complete(self, request, pk=None):
    obj = self.get_object()
    # Custom logic
    return Response({"status": "completed"})

```

- [ ]  Use `@action` for additional endpoints on resources
- [ ]  Use `detail=False` for collection actions, `detail=True` for instance actions
- [ ]  Use kebab-case for `url_path`

### ✅ Checklist: Creating APIViews (for non-CRUD actions)

**Step 1: Use Cases for APIView**

- [ ]  Webhooks and external callbacks
- [ ]  Multi-step workflows
- [ ]  Aggregations that don't fit a resource model
- [ ]  Public endpoints (login, register)

**Step 2: Configuration**

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

class YourAPIView(APIView):
    # For public endpoints
    authentication_classes = ()
    permission_classes = (AllowAny,)

    # For admin-only
    # permission_classes = (IsAdminUser, IsAuthenticated,)

    def post(self, request):
        # Logic here
        return Response({"result": "success"}, status=200)

```

- [ ]  For public endpoints: set both `authentication_classes = ()` and `permission_classes = (AllowAny,)`
- [ ]  For admin-only: use `(IsAdminUser, IsAuthenticated,)`
- [ ]  Return `Response` objects only (let renderer handle wrapping)

**Step 3: Pagination in APIViews (when needed)**

```python
from atomicloops.pagination import AtomicPagination

class YourListView(APIView):
    pagination_class = AtomicPagination

    def get(self, request):
        queryset = YourModel.objects.all()
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        if page is not None:
            serializer = YourModelSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        # Handle non-paginated case

```

- [ ]  Use `AtomicPagination` for consistency
- [ ]  Follow DRF paginator pattern

---

## 4️⃣ URLS - Implementation Rules

### ✅ Checklist: App-Level URL Configuration

**Step 1: File Structure**

```python
# app_name/urls.py
from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import YourViewSet, YourAPIView

```

- [ ]  Always create `urls.py` in each app
- [ ]  Import `DefaultRouter` for ViewSets

**Step 2: Router Configuration**

```python
router = DefaultRouter()
router.register('resource-name', YourViewSet, basename='resource-name')
# Use plural nouns, kebab-case

```

- [ ]  Use plural nouns for resources (`users`, `training-plans`)
- [ ]  Use kebab-case for multi-word resources
- [ ]  Provide `basename` when ViewSet has no `queryset`

**Step 3: URL Patterns**

```python
urlpatterns = [
    # APIViews - use verbs for actions
    path('start-session/', StartSessionView.as_view(), name='start-session'),
    path('webhook/', WebhookView.as_view(), name='webhook'),
    path('export-data/', ExportDataView.as_view(), name='export-data'),
]
urlpatterns += router.urls

```

- [ ]  Use verbs for APIView actions (`start-`, `export-`, `webhook/`)
- [ ]  Always end paths with trailing slash
- [ ]  Use kebab-case for multi-word paths
- [ ]  Ensure `name` is unique across entire project

**Step 4: Dynamic Segments**

```python
path('users/<uuid:user_id>/pets/', UserPetsView.as_view(), name='user-pets'),
path('update-pet/<uuid:pk>/', UpdatePetView.as_view(), name='update-pet'),

```

- [ ]  Use explicit converters (`<uuid:pk>`, `<uuid:pet_id>`)
- [ ]  Use `pk` for primary keys, descriptive names for others

### ✅ Checklist: Project-Level URL Inclusion

**In `src/urls.py`:**

```python
urlpatterns = [
    # ... existing patterns ...
    path('', include('your_app.urls')),
]

if settings.DEBUG:
    urlpatterns += [
        path('debug-endpoint/', DebugView.as_view(), name='debug'),
    ]

```

- [ ]  Include app URLs at root level with `path('', include('app.urls'))`
- [ ]  Gate dev-only endpoints with `if settings.DEBUG:`
- [ ]  Maintain stable include order

---

## 5️⃣ FILTERS - Implementation Rules

### ✅ Checklist: Creating Filters

**Step 1: Choose Filter Base Class**

```python
import django_filters
from atomicloops.filters import AtomicDateFilter, AtomicUserFilter, MultiValueCharFilter
from .models import YourModel

# For date filtering
class YourModelFilter(AtomicDateFilter):
    pass

# For user-related filtering
class YourModelFilter(AtomicUserFilter):
    pass

# For basic filtering
class YourModelFilter(django_filters.FilterSet):
    pass

```

- [ ]  Use `AtomicDateFilter` for `fromDate`/`toDate` filtering
- [ ]  Use `AtomicUserFilter` for user fields + dates
- [ ]  Use base `FilterSet` for simple cases

**Step 2: Custom Filter Fields**

```python
class YourModelFilter(AtomicDateFilter):
    status = MultiValueCharFilter(field_name='status', lookup_expr='in')
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')

    class Meta:
        model = YourModel
        fields = ('userId', 'status', 'name', 'fromDate', 'toDate')

```

- [ ]  Use `MultiValueCharFilter` for CSV inclusion (`?status=a,b,c`)
- [ ]  Use appropriate `lookup_expr` (`icontains`, `exact`, `in`, etc.)
- [ ]  Include base filter fields in `Meta.fields`

**Step 3: Wire to ViewSet**

```python
class YourModelViewSet(AtomicViewSet):
    filterset_class = YourModelFilter  # Preferred
    # OR for simple cases:
    # filterset_fields = ('userId', 'status')

```

- [ ]  Use `filterset_class` for custom filters
- [ ]  Use `filterset_fields` only for simple exact matching

---

## 6️⃣ PERMISSIONS - Implementation Rules

### ✅ Checklist: Permission Strategy

**Step 1: Understand Defaults**

- Global defaults from settings:
    - `IsOwnerOrAdminOrReadOnly`
    - `IsAuthenticated`
- [ ]  Only override when you need different behavior

**Step 2: Common Permission Patterns**

```python
# Public endpoints (login, register, webhooks)
authentication_classes = ()
permission_classes = (AllowAny,)

# Admin-only endpoints
permission_classes = (IsAdminUser, IsAuthenticated,)

# Subscription-required endpoints
permission_classes = [UserSubscriptionCheckPermissions, IsAuthenticated]

# Custom ownership check
permission_classes = [IsOwnerOrAdmin]

```

- [ ]  For public: set both auth and permission to empty/AllowAny
- [ ]  For admin: use `IsAdminUser` + `IsAuthenticated`
- [ ]  For subscription: use existing `UserSubscriptionCheckPermissions`

**Step 3: Creating Custom Permissions**

```python
from rest_framework import permissions

class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        try:
            return (request.user.is_superuser or
                   getattr(obj, 'userId', None) == request.user)
        except Exception:
            return False

```

- [ ]  Inherit from `BasePermission`
- [ ]  Allow safe methods (GET, HEAD, OPTIONS) for read access
- [ ]  Handle exceptions gracefully
- [ ]  Check ownership via appropriate field (`userId`, `petId.userId`, etc.)

**Step 4: Permission Declaration**

```python
class YourViewSet(AtomicViewSet):
    permission_classes = [IsAuthenticated, YourCustomPermission]
    # Don't leave commented placeholders in committed code

```

- [ ]  Be explicit about permissions when overriding defaults
- [ ]  Remove commented permission placeholders before commit
- [ ]  Keep declarations minimal and clear

---

## 🚀 Implementation Workflow

### When Adding a New Feature:

1. **Plan the Data Model**
    - [ ]  Identify relationships and constraints
    - [ ]  Choose appropriate field types and names
2. **Create Model**
    - [ ]  Follow Model rules checklist
    - [ ]  Run migrations: `python manage.py makemigrations && python manage.py migrate`
3. **Create Serializer**
    - [ ]  Follow Serializer rules checklist
    - [ ]  Test serialization in Django shell
4. **Create Views**
    - [ ]  Choose ViewSet vs APIView based on use case
    - [ ]  Follow appropriate view checklist
    - [ ]  Test endpoints manually
5. **Create URLs**
    - [ ]  Follow URL rules checklist
    - [ ]  Test URL routing
6. **Add Filtering (if needed)**
    - [ ]  Follow Filter rules checklist
    - [ ]  Test filter parameters
7. **Set Permissions**
    - [ ]  Follow Permission rules checklist
    - [ ]  Test access control
8. **Code Review Checklist**
    - [ ]  All rule checklists followed
    - [ ]  No commented-out code
    - [ ]  Consistent naming conventions
    - [ ]  Proper error handling
    - [ ]  Tests written (if applicable)

---

## ❌ Common Mistakes to Avoid

- **Models**: Forgetting `related_name`, using default `_set` relations
- **Serializers**: Not setting `get_fields`/`list_fields`, missing timezone handling
- **Views**: Overriding defaults unnecessarily, not using `AtomicViewSet` for CRUD
- **URLs**: Missing trailing slashes, inconsistent naming, no `basename` for ViewSets
- **Filters**: Not reusing base filter classes, inefficient queries
- **Permissions**: Leaving commented placeholders, not handling exceptions

---

## 📋 Pre-Commit Checklist

Before submitting PR:

- [ ]  All implementation checklists completed
- [ ]  Code follows naming conventions
- [ ]  No commented-out code blocks
- [ ]  Migrations created and tested
- [ ]  Manual testing completed
- [ ]  Error cases handled gracefully

---

## ADMIN - Implementation Rules

### ✅ Checklist: Creating `admin.py` for an app

**Step 1: File presence**

- [ ]  Always create an `admin.py` when adding any new app that has models
- [ ]  Register all public models used by the app (avoid leaving models unregistered)

**Step 2: Imports & Basics**

```python
from django.contrib import admin
from .models import YourModel, AnotherModel
```

- [ ]  Import only the models you need from the current app
- [ ]  Use `@admin.register(Model)` decorator for clarity

**Step 3: ModelAdmin configuration**

- [ ]  Provide `list_display` for primary identifying fields
- [ ]  Provide `list_filter` for high-cardinality enums and statuses
- [ ]  Provide `search_fields` for text fields frequently searched
- [ ]  Provide `readonly_fields` for `id`, `createdAt`, `updatedAt`
- [ ]  Provide `ordering` default (prefer `-createdAt`)

Example:

```python
@admin.register(YourModel)
class YourModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'status')
    list_filter = ('status',)
    search_fields = ('name', 'description')
    readonly_fields = ('id', 'createdAt', 'updatedAt')
    ordering = ('-createdAt',)
```

**Step 4: Avoid common mistakes**

- [ ]  Do not leave `admin.py` empty or commented out in commits
- [ ]  Do not import admin-related utilities unnecessarily
- [ ]  Avoid overly verbose `list_display` that hurts performance

**Step 5: Review / Pre-commit**

- [ ]  Ensure `admin.py` is included in the app directory before creating migrations
- [ ]  Run quick smoke check by logging into Django admin locally to verify models appear


import os
import django
import sys

# Add the project directory to Python path
sys.path.append('/opt')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.settings.dev')
django.setup()

from users.models import Users

# Create admin user with all required fields
if not Users.objects.filter(email='admin@gmail.com').exists():
    user = Users.objects.create_user(
        username='admin',
        email='admin@gmail.com',
        password='admin',
        firstName='Admin',
        lastName='User',
        isVerified=True,
        is_active=True,
        is_superuser=True,
        is_staff=True,
        level=5  # Admin level
    )
    print('✅ Admin user created successfully!')
else:
    # Update existing user to ensure it's verified
    user = Users.objects.get(email='admin@gmail.com')
    user.isVerified = True
    user.is_active = True
    user.level = 5
    user.save()
    print('✅ Admin user updated and verified!')

print('Email: admin@gmail.com')
print('Password: admin')
print('Ready for login!')

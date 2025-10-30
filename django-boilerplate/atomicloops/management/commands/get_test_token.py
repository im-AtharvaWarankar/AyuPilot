"""
Django management command to generate a fresh JWT token for frontend testing
Usage: python manage.py get_test_token
"""
from django.core.management.base import BaseCommand
from users.models import Users
from rest_framework_simplejwt.tokens import RefreshToken


class Command(BaseCommand):
    help = 'Generate a fresh JWT token for frontend testing'

    def handle(self, *args, **options):
        # Get or create test user
        email = 'admin@gmail.com'
        
        try:
            user = Users.objects.get(email=email)
            self.stdout.write(f'✅ Found user: {email}')
        except Users.DoesNotExist:
            self.stdout.write(f'⚠️  User {email} not found. Creating...')
            user = Users.objects.create_user(
                username='admin',
                email=email,
                password='admin',
                firstName='Admin',
                lastName='User',
                isVerified=True,
                is_active=True,
                level=3  # Doctor level
            )
            self.stdout.write(f'✅ Created user: {email}')
        
        # Make sure user is verified and active
        if not user.isVerified or not user.is_active:
            user.isVerified = True
            user.is_active = True
            user.save()
            self.stdout.write('✅ User verified and activated')
        
        # Generate token
        token = RefreshToken.for_user(user)
        access_token = str(token.access_token)
        refresh_token = str(token)
        
        # Print results
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS('JWT TOKEN GENERATED!'))
        self.stdout.write('=' * 70)
        self.stdout.write(f'\nUser: {email}')
        self.stdout.write(f'Password: admin')
        self.stdout.write(f'\nACCESS TOKEN (copy to frontend):')
        self.stdout.write('=' * 70)
        self.stdout.write(access_token)
        self.stdout.write('=' * 70)
        self.stdout.write(f'\nREFRESH TOKEN:')
        self.stdout.write(refresh_token)
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write('\n📝 TO UPDATE FRONTEND:')
        self.stdout.write('1. Open: frontend/src/services/api.ts')
        self.stdout.write('2. Find getAuthToken() function (line ~125)')
        self.stdout.write('3. Replace with:')
        self.stdout.write(f"   return '{access_token}';")
        self.stdout.write('\n' + '=' * 70 + '\n')

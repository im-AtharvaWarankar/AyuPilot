from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from ayupilot.models import Patient, Medicine, Prescription

class Command(BaseCommand):
    help = 'Insert demo doctors, patients, and prescriptions'

    def handle(self, *args, **options):
        User = get_user_model()
        # Create doctors
        doctor1 = User.objects.create_user(username='doctor1', email='doctor1@example.com', password='test123')
        doctor2 = User.objects.create_user(username='doctor2', email='doctor2@example.com', password='test123')
        self.stdout.write(self.style.SUCCESS(f'Doctors created: {doctor1.id}, {doctor2.id}'))

        # Create medicines (shared)
        paracetamol = Medicine.objects.create(name='Paracetamol', description='Pain reliever')
        sinarest = Medicine.objects.create(name='Sinarest', description='Cold relief')
        self.stdout.write(self.style.SUCCESS(f'Medicines created: {paracetamol.id}, {sinarest.id}'))

        # Create patients for each doctor
        patient1 = Patient.objects.create(
            doctorId=doctor1, name='Alice', age=30, gender='F', phone='9123456789', status=Patient.StatusChoices.ACTIVE
        )
        patient2 = Patient.objects.create(
            doctorId=doctor2, name='Bob', age=40, gender='M', phone='9876543210', status=Patient.StatusChoices.ACTIVE
        )
        self.stdout.write(self.style.SUCCESS(f'Patients created: {patient1.id}, {patient2.id}'))

        # Prescribe medicines to both patients (same medicine ids, diff patient ids)
        Prescription.objects.create(patientId=patient1, medicineId=paracetamol, dosage='500mg', frequency='2x/day')
        Prescription.objects.create(patientId=patient1, medicineId=sinarest, dosage='1 tab', frequency='1x/day')
        Prescription.objects.create(patientId=patient2, medicineId=paracetamol, dosage='500mg', frequency='2x/day')
        Prescription.objects.create(patientId=patient2, medicineId=sinarest, dosage='1 tab', frequency='1x/day')
        self.stdout.write(self.style.SUCCESS('Prescriptions added for both patients.'))
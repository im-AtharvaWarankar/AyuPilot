from ayupilot.models import Patient, SNLPrescription, KnowledgeReference
from users.models import Users, UserLevel

# Get patients
patients = list(Patient.objects.all()[:3])
print(f"Found {len(patients)} patients")

# Create SNL prescriptions for first 2 patients
for i, patient in enumerate(patients[:2]):
    snl = SNLPrescription.objects.create(
        patientId=patient,
        shaman='Tulsi (Holy Basil)' if i == 0 else 'Ashwagandha',
        nidan='Stress and anxiety' if i == 0 else 'Low energy and fatigue',
        line='Vata imbalance' if i == 0 else 'Kapha imbalance',
        aiGenerated=True,
        status='COMPLETED'
    )
    print(f"Created SNL prescription {snl.id} for {patient.fullName}")

# Create knowledge references for all 3 patients
references_data = [
    ('Charaka Samhita - Chapter on Vata Disorders', 'Ancient Ayurvedic text discussing Vata imbalances and treatments'),
    ('Ashtanga Hridayam - Digestive Health', 'Classical text on digestive system and Agni (digestive fire)'),
    ('Sushruta Samhita - Cardiovascular System', 'Traditional wisdom on heart health and blood pressure management')
]

for i, patient in enumerate(patients):
    title, desc = references_data[i]
    ref = KnowledgeReference.objects.create(
        patientId=patient,
        title=title,
        description=desc,
        source='Classical Ayurvedic Texts',
        aiGenerated=True,
        status='COMPLETED'
    )
    print(f"Created knowledge reference {ref.id} for {patient.fullName}")

print("\nDone! Created test data successfully.")

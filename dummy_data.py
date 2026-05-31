import os
import django
import random
from datetime import datetime, timedelta

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'docx_project.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import SymptomEntry
from django.utils import timezone

def seed_data():
    print("Starting Seeding Process...")

    # 1. Create/Update Admin User
    admin_username = 'admin'
    admin_password = '1234'
    admin_user, created = User.objects.get_or_create(username=admin_username)
    admin_user.set_password(admin_password)
    admin_user.is_superuser = True
    admin_user.is_staff = True
    admin_user.first_name = "System"
    admin_user.last_name = "Administrator"
    admin_user.save()
    print(f"Admin user {'created' if created else 'updated'} (Login: {admin_username}, Pass: {admin_password})")

    # 2. Create Dummy Patients
    patients_data = [
        ('rahul_v', 'Rahul Verma', 'rahul@example.com'),
        ('anita_s', 'Anita Sharma', 'anita@example.com'),
        ('vikram_k', 'Vikram Kumar', 'vikram@example.com'),
        ('sneha_r', 'Sneha Reddy', 'sneha@example.com'),
        ('david_w', 'David Wilson', 'david@example.com'),
    ]

    patients = []
    for username, full_name, email in patients_data:
        user, created = User.objects.get_or_create(username=username, email=email)
        if created:
            user.set_password('1234')
            names = full_name.split(' ')
            user.first_name = names[0]
            user.last_name = names[1]
            user.save()
        patients.append(user)
    print(f"{len(patients)} dummy patients ready.")

    # 3. Create Dummy Symptoms
    symptoms_list = [
        ("Persistent dry cough and mild fever", "Low", "Monitor temperature and stay hydrated. Rest well."),
        ("Severe headache with blurred vision", "High", "Immediate medical consultation required. Check blood pressure."),
        ("Occasional chest pain during exercise", "High", "Consult a cardiologist immediately. Avoid strenuous activity."),
        ("Mild joint pain in the mornings", "Low", "Maintain light stretching and check vitamin D levels."),
        ("Moderate abdominal pain and bloating", "Medium", "Adjust diet, avoid spicy food, and consult a GP if it persists."),
        ("Shortness of breath after climbing stairs", "Medium", "Schedule a lung function test and monitor oxygen levels."),
        ("Sudden skin rash and itching", "Medium", "Identify allergens and apply soothing lotion. Consult a dermatologist."),
        ("Extreme fatigue and loss of appetite", "High", "Full blood count recommended. Consult a physician."),
        ("Sore throat and nasal congestion", "Low", "Saltwater gargle and over-the-counter decongestants."),
        ("Frequent dizziness and lightheadedness", "Medium", "Check hydration and iron levels. Avoid sudden movements.")
    ]

    # Clear existing entries to start fresh for a clean demo
    SymptomEntry.objects.all().delete()
    print("Cleared old symptom entries.")

    count = 0
    now = timezone.now()

    # Distribute symptoms across patients and admin
    all_users = patients + [admin_user]

    for i in range(25): # Create 25 total records
        user = random.choice(all_users)
        symptom_text, severity, suggestion = random.choice(symptoms_list)
        
        # Randomize date within last 30 days
        days_ago = random.randint(0, 30)
        hours_ago = random.randint(0, 23)
        created_at = now - timedelta(days=days_ago, hours=hours_ago)

        SymptomEntry.objects.create(
            user=user,
            symptom_text=symptom_text,
            severity=severity,
            suggestion=suggestion,
            created_at=created_at
        )
        count += 1

    print(f"Created {count} realistic health records.")
    print("Seeding completed successfully!")

if __name__ == '__main__':
    seed_data()

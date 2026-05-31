import os
import json
from datetime import timedelta, datetime

# DocX Views Core
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.http import JsonResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail

# Models & Forms
from core.forms import UserRegistrationForm, SymptomEntryForm, VitalsRecordForm
from core.models import SymptomEntry, VitalsRecord

# 3rd Party Integration (Groq AI)
try:
    from groq import Groq
    client = Groq(api_key=settings.GROQ_API_KEY)
except (ImportError, AttributeError):
    client = None

# 🔹 Suggestion logic
def get_suggestion_by_severity(severity):
    suggestions = {
        'Low': "Home rest recommended. Monitor temperature and stay hydrated.",
        'Medium': "Rest and basic self-care advised. Consult a physician if symptoms persist beyond 48 hours.",
        'High': "Immediate medical consultation strongly recommended. Seek urgent care if breathing is difficult."
    }
    return suggestions.get(severity, suggestions['Low'])

# 🔹 Helper for Dynamic Health Note
def get_dynamic_health_note(score):
    if score >= 90:
        return "Excellent vital signs. Your current health regime is highly effective. Maintain current hydration and activity levels."
    elif score >= 70:
        return "Stable health metrics. Minor fluctuations detected in recent logs. Recommendation: Ensure consistent sleep patterns and monitor stress levels."
    elif score >= 50:
        return "Moderate health alert. Some symptoms require attention. Recommendation: Increase rest, maintain high fluid intake, and consider a routine check-up."
    else:
        return "Critical health alert. Multiple high-severity logs detected. Action Required: Immediate medical consultation is strongly advised. Monitor vitals hourly."

# 🔹 Signup
def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Clinical Account created for {user.username}! You may now log in.')
            return redirect('login')
    else:
        form = UserRegistrationForm()

    return render(request, 'core/signup.html', {'form': form})

# 🔹 Profile
@login_required
def profile_view(request):
    return render(request, 'core/profile.html', {'user': request.user})

# 🔹 Dashboard
@login_required
def dashboard_view(request):
    today = timezone.now().date()
    current_hour = datetime.now().hour
    
    if current_hour < 12:
        greeting = "Good Morning"
    elif 12 <= current_hour < 18:
        greeting = "Good Afternoon"
    else:
        greeting = "Good Evening"

    if request.user.is_superuser:
        symptoms_qs = SymptomEntry.objects.all()
    else:
        symptoms_qs = SymptomEntry.objects.filter(user=request.user)

    # Calculate dynamic Health Score & Chart Data based on average severity
    recent_7_days = timezone.now() - timedelta(days=7)
    recent_logs = list(symptoms_qs.filter(created_at__gte=recent_7_days))
    
    if recent_logs:
        total_score = 0
        for log in recent_logs:
            if log.severity == 'High': total_score += 40
            elif log.severity == 'Medium': total_score += 70
            elif log.severity == 'Low': total_score += 90
        health_score = int(total_score / len(recent_logs))
    else:
        health_score = 100

    ai_clinical_note = get_dynamic_health_note(health_score)

    chart_labels = []
    chart_data = []
    
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        chart_labels.append(day.strftime("%a"))
        
        day_logs = [log for log in recent_logs if log.created_at.date() == day]
        if day_logs:
            day_total = 0
            for log in day_logs:
                if log.severity == 'High': day_total += 40
                elif log.severity == 'Medium': day_total += 70
                elif log.severity == 'Low': day_total += 90
            day_score = int(day_total / len(day_logs))
        else:
            day_score = 100
            
        chart_data.append(day_score)
        
    chart_labels_json = json.dumps(chart_labels)
    chart_data_json = json.dumps(chart_data)

    # Fetch latest vitals for real data display
    latest_vitals = VitalsRecord.objects.filter(user=request.user).first()
    
    # If no real vitals found, provide healthy defaults for demo
    vitals_data = {
        'heart_rate': latest_vitals.heart_rate if latest_vitals else 72,
        'blood_oxygen': latest_vitals.blood_oxygen if latest_vitals else 98,
        'steps': latest_vitals.steps if latest_vitals else 5240,
        'weight': latest_vitals.weight if latest_vitals else 70.0,
        'has_real_data': True if latest_vitals else False
    }

    context = {
        'health_score': health_score,
        'health_score_remainder': 100 - health_score,
        'chart_labels': chart_labels_json,
        'chart_data': chart_data_json,
        'greeting': greeting,
        'ai_clinical_note': ai_clinical_note,
        'vitals': vitals_data,
    }

    if request.user.is_superuser:
        context.update({
            'recent_symptoms': SymptomEntry.objects.all().order_by('-created_at')[:10],
            'is_admin': True,
            'total_patients': User.objects.filter(is_superuser=False).count(),
            'total_logs': SymptomEntry.objects.count(),
            'high_severity': SymptomEntry.objects.filter(severity='High').count(),
        })
    else:
        context.update({
            'recent_symptoms': SymptomEntry.objects.filter(user=request.user).order_by('-created_at')[:5],
        })
    
    return render(request, 'core/dashboard.html', context)

# 🔹 Log Vitals
@login_required
def log_vitals_view(request):
    if request.method == 'POST':
        form = VitalsRecordForm(request.POST)
        if form.is_valid():
            vitals = form.save(commit=False)
            vitals.user = request.user
            vitals.save()
            messages.success(request, "Vitals logged successfully! Your diagnostic dashboard has been updated.")
            return redirect('dashboard')
    else:
        form = VitalsRecordForm()
    
    return render(request, 'core/log_vitals.html', {'form': form})

# 🔹 Add Symptom
@login_required
def add_symptom_view(request):
    if request.method == 'POST':
        form = SymptomEntryForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.suggestion = request.POST.get('suggestion') or get_suggestion_by_severity(obj.severity)
            obj.save()

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({"status": "saved"})

            return redirect('symptom_history')
    else:
        form = SymptomEntryForm()

    return render(request, 'core/add_symptom.html', {'form': form})

# 🔹 Symptom History
@login_required
def symptom_history_view(request):
    if request.user.is_superuser:
        symptoms = SymptomEntry.objects.all().order_by('-created_at')
        return render(request, 'core/symptom_history.html', {'symptoms': symptoms, 'is_admin': True})
    
    symptoms = SymptomEntry.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'core/symptom_history.html', {'symptoms': symptoms})

# 🔹 Fallback Report Generator (Smart Offline Clinical Intelligence)
def generate_fallback_report(username, full_name, symptom_text, severity):
    name = full_name or username
    date = timezone.now().strftime('%Y-%m-%d')
    symptom_lower = symptom_text.lower()
    
    # Identify key symptom groups
    is_fever = any(w in symptom_lower for w in ['fever', 'temp', 'cold', 'chill', 'sweat', 'hot', 'pyrexia'])
    is_cough_cold = any(w in symptom_lower for w in ['cough', 'cold', 'flu', 'sore throat', 'throat', 'congestion', 'runny nose', 'sneeze', 'coughing'])
    is_stomach = any(w in symptom_lower for w in ['stomach', 'belly', 'abdomen', 'diarrhea', 'vomit', 'nausea', 'ache', 'pain', 'cramp', 'loose motion'])
    is_body_ache = any(w in symptom_lower for w in ['body', 'muscle', 'joint', 'ache', 'fatigue', 'tired', 'weakness', 'pain'])
    is_headache = any(w in symptom_lower for w in ['headache', 'migraine', 'head'])
    
    # 1. Clinical Impression & Potential Conditions
    if is_fever and is_cough_cold:
        potential_condition = "Acute Viral Respiratory Infection / Influenza (Flu)"
        pathophysiology = "Viral replication in the upper respiratory tract initiating a systemic immune response, leading to pyrexia (fever) and local mucosal inflammation."
        recovery_advice = "- **Rest:** Complete bed rest is critical. Minimize physical activity to allow the immune system to redirect energy towards combating the viral load.\n- **Hydration:** Consume 3-4 liters of warm fluids daily (herbal teas, warm water, electrolyte solutions, clear broths) to thin mucus and replace fluids lost through sweating.\n- **Diet:** Eat light, nutrient-dense, warm meals like soups, soft rice, and boiled vegetables. Avoid dairy and cold foods which can exacerbate congestion.\n- **Symptom Relief:** Steam inhalation for 10 minutes twice daily and warm saltwater gargles 3-4 times a day to soothe throat irritation."
        prescription_actions = "1. **Log Temperature:** Record body temperature every 4 hours using a digital thermometer.\n2. **Log Oxygen Levels (SpO2):** Check blood oxygen level using a pulse oximeter twice daily.\n3. **Fever Management:** Apply cool, damp compress to the forehead or body if fever exceeds 101°F.\n4. **OTC Considerations:** Standard antipyretics (e.g., Paracetamol 500mg/650mg up to 3-4 times daily as needed) under medical guidance, keeping a minimum 4-6 hour gap between doses."
    elif is_fever:
        potential_condition = "Pyrexia of Unknown Origin (likely viral etiology)"
        pathophysiology = "Systemic immune response triggered by an infectious pathogen or inflammatory stimulus, causing the hypothalamus to elevate the body's setpoint temperature."
        recovery_advice = "- **Rest:** Stay in a cool, well-ventilated room with minimal physical exertion.\n- **Hydration:** Prioritize oral rehydration salts (ORS) or electrolyte-infused water to prevent dehydration from perspiration.\n- **Diet:** Consume simple carbohydrates and easily digestible foods. High-protein or heavy, greasy foods should be avoided.\n- **Home Care:** Keep clothing light and breathable. Avoid heavy blankets which can trap heat and increase internal temperature."
        prescription_actions = "1. **Log Vitals:** Monitor and log temperature and heart rate on the DocX dashboard every 4 hours.\n2. **Hydration Log:** Ensure minimum fluid intake of 250ml per hour during waking hours.\n3. **Tepid Sponging:** Use lukewarm (not cold) water to sponge the body if fever remains high.\n4. **Antipyretics:** Use Paracetamol 500mg as advised by a doctor for symptomatic relief of fever and mild discomfort."
    elif is_cough_cold:
        potential_condition = "Acute Bronchitis / Nasopharyngitis (Common Cold)"
        pathophysiology = "Inflammation of the mucous membranes in the bronchial tubes or nasal passages, causing increased mucus secretion, hyperreactive airways, and local irritation."
        recovery_advice = "- **Rest:** Ensure 8-9 hours of quality sleep to accelerate mucosal recovery.\n- **Hydration:** Drink warm honey-lemon water, herbal tea, or warm water frequently to keep the throat moist and suppress dry cough.\n- **Home Care:** Use a humidifier in your bedroom to keep the air moist. Elevate your head with extra pillows while sleeping to ease breathing."
        prescription_actions = "1. **Log Vitals:** Check heart rate and blood oxygen levels twice daily.\n2. **Inhalation therapy:** Practice steam inhalation with a drop of eucalyptus oil twice daily.\n3. **Throat Care:** Gargle with warm saline water (1/2 tsp salt in warm water) every 4 hours.\n4. **Cough Relief:** Use soothing throat lozenges or honey-based cough formulations as needed."
    elif is_stomach:
        potential_condition = "Acute Gastroenteritis / Dyspepsia"
        pathophysiology = "Inflammation of the lining of the stomach and intestines, often due to viral/bacterial ingestion or dietary irritation, leading to altered motility and malabsorption."
        recovery_advice = "- **Rest:** Rest to minimize gut motility stimulation and allow intestinal lining healing.\n- **Hydration:** Consume small, frequent sips of ORS (Oral Rehydration Solution), coconut water, or clear broth. Do not gulp large amounts of water as it may trigger vomiting.\n- **Diet:** Follow a strict BRAT diet (Bananas, Rice, Applesauce, Toast) once vomiting stops. Strictly avoid spicy, fried, dairy, caffeine, and high-sugar foods."
        prescription_actions = "1. **Log Vitals & Hydration:** Monitor frequency of bowel movements or vomiting and log weight and hydration levels.\n2. **Gut Support:** Consider taking probiotics under physician guidance to restore healthy gut flora.\n3. **Abdominal Comfort:** Use a warm heating pad on the stomach for 15-20 minutes to relieve cramps.\n4. **Hydration target:** Aim for at least 150ml of ORS after every loose stool."
    elif is_headache:
        potential_condition = "Tension Headache / Migraine Episode"
        pathophysiology = "Muscle contractions in the head and neck region, or neurovascular alterations leading to trigeminal nerve pathway activation and localized cranial throbbing."
        recovery_advice = "- **Rest:** Rest in a dark, completely quiet room. Minimize screen time (phones, laptops, TV) immediately.\n- **Hydration:** Drink a large glass of water immediately, as dehydration is a highly common trigger for headaches.\n- **Home Remedies:** Apply a cold compress or ice pack wrapped in a cloth to the forehead or the back of the neck. Perform gentle temple massages."
        prescription_actions = "1. **Log Vitals:** Log blood pressure if a monitor is available, as well as heart rate.\n2. **Stress Reduction:** Practice 10 minutes of deep, slow breathing exercises.\n3. **Pain Tracker:** Document the duration, intensity (1-10 scale), and triggers in your health log.\n4. **OTC Analgesics:** Use standard pain relief (like Ibuprofen 200mg or Paracetamol 500mg) early in the attack, taken with food."
    else:
        # Default fallback
        potential_condition = "Mild Systemic Malaise / Undifferentiated Symptom Complex"
        pathophysiology = "General immune response or localized physiological fatigue, requiring monitoring to establish a specific diagnostic trend."
        recovery_advice = "- **Rest:** Prioritize recovery by ensuring at least 8 hours of sleep and reducing physical strain.\n- **Hydration:** Drink at least 2.5 to 3 liters of water throughout the day to support cellular function.\n- **Diet:** Maintain a balanced diet rich in vitamins, minerals, and antioxidants (fruits, vegetables, proteins)."
        prescription_actions = "1. **Log Symptoms:** Log vitals (heart rate, temperature, steps) in the DocX dashboard twice daily.\n2. **Trend Monitoring:** Keep a detailed log of when symptoms peak during the day.\n3. **Activity adjustment:** Limit intense exercises and heavy lifting for 48 hours.\n4. **Standard Care:** Use warm compresses or salt gargles if throat or muscle discomfort is present."

    report = f"""**Medical Report Summary**

**Patient Information:**
- **Name:** {name}
- **Date:** {date}

**Chief Complaints & Symptom Severity:**
- **Symptoms:** {symptom_text}
- **Severity Level:** {severity}

**Clinical Impression & Potential Condition(s):**
- **Potential Diagnosis:** {potential_condition}
- **Pathophysiological Context:** {pathophysiology}

**Physician's Recovery Advice & Home Care (To Recover Fast):**
{recovery_advice}

**Prescription-style Actions & Monitoring (What to Do):**
{prescription_actions}

**Next Steps & Red Flag Warning:**
- **Monitoring Timeline:** Monitor symptoms closely for the next 48 hours. If symptoms show no improvement or begin to worsen, schedule an in-person clinical consultation.
- **🚨 EMERGENCY RED FLAGS:** Seek immediate emergency medical care if you experience any of the following:
  * Difficulty breathing, shortness of breath, or chest pain/tightness.
  * Persistent high fever (above 103°F / 39.4°C) unresponsive to medication.
  * Severe, unremitting abdominal pain or persistent vomiting preventing fluid retention.
  * Sudden confusion, dizziness, extreme lethargy, or loss of consciousness.
  * Bluish lips or face."""

    return report

# 🔹 AI Response (Groq)
@login_required
def get_ai_response(request):
    if request.method == "POST":
        try:
            symptom = request.POST.get("symptom_text")
            severity = request.POST.get("severity")

            response_text = None
            if client:
                try:
                    chat = client.chat.completions.create(
                        messages=[{
                            "role": "user",
                            "content": f"""
                            Act like a senior clinical consultant AI. Generate a highly detailed, professional, and structured Medical Report Summary.
                            You must analyze the patient's symptoms and output a response using the exact following markdown structure:
                            
                            **Medical Report Summary**
                            
                            **Patient Information:**
                            - **Name:** {request.user.get_full_name() or request.user.username}
                            - **Date:** {timezone.now().strftime('%Y-%m-%d')}
                            
                            **Chief Complaints & Symptom Severity:**
                            - **Symptoms:** {symptom}
                            - **Severity Level:** {severity}
                            
                            **Clinical Impression & Potential Condition(s):**
                            - **Potential Diagnosis:** (Provide a professional clinical assessment/differential diagnosis of what disease or condition could be causing these symptoms based on the input.)
                            - **Pathophysiological Context:** (Briefly explain the underlying biology or pathophysiology of these symptoms.)
                            
                            **Physician's Recovery Advice & Home Care (To Recover Fast):**
                            (Provide specific, step-by-step guidance on how the patient can recover quickly, including rest protocols, detailed hydration guidelines, dietary modifications, and helpful home remedies.)
                            
                            **Prescription-style Actions & Monitoring (What to Do):**
                            (List actionable prescription-like steps, what vitals to log on the DocX dashboard, daily monitoring frequency, and non-pharmacological/OTC instructions.)
                            
                            **Next Steps & Red Flag Warning:**
                            - **Monitoring Timeline:** (When to follow up or see a doctor if symptoms persist.)
                            - **🚨 EMERGENCY RED FLAGS:** (Detail specific danger signs like severe breathing difficulty, chest pain, high fever unresponsive to medication, confusion, where the patient must seek immediate emergency medical care.)
                            
                            Ensure the tone is professional, authoritative, empathetic, and clear. Do not use generic placeholders.
                            """
                        }],
                        model="llama-3.1-8b-instant"
                    )
                    response_text = chat.choices[0].message.content
                except Exception:
                    response_text = None

            # Fallback if AI fails or client is missing
            if not response_text:
                response_text = generate_fallback_report(
                    request.user.username,
                    request.user.get_full_name(),
                    symptom,
                    severity
                )

            return JsonResponse({"ai_response": response_text})

        except Exception as e:
            return JsonResponse({"ai_response": f"⚠️ AI Offline: {str(e)}"}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=400)

# 🔹 Book Appointment (Email Notification)
@login_required
def book_appointment(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            doctor_name = data.get('doctor_name')
            date = data.get('date')
            time_slot = data.get('time_slot')
            reason = data.get('reason')
            
            admin_email = "shubhsrivastav9369@gmail.com"
            sender_email = getattr(settings, 'EMAIL_HOST_USER', admin_email)
            
            subject = f"🩺 New Appointment Booking: {doctor_name}"
            
            message = (
                f"A new appointment has been booked via DocX-AI Smart Healthcare.\n\n"
                f"Patient: {request.user.username} ({request.user.email})\n"
                f"Doctor: {doctor_name}\n"
                f"Date: {date}\n"
                f"Time Slot: {time_slot}\n"
                f"Reason: {reason}\n"
            )

            html_message = f"""
            <html>
            <body style="font-family: sans-serif; background-color: #f8fafc; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; border: 1px solid #e2e8f0;">
                    <div style="background: #0d6efd; color: white; padding: 20px; text-align: center;">
                        <h2 style="margin: 0;">DocX Clinical Appointment</h2>
                    </div>
                    <div style="padding: 30px;">
                        <p><strong>Patient:</strong> {request.user.username}</p>
                        <p><strong>Specialist:</strong> {doctor_name}</p>
                        <p><strong>Schedule:</strong> {date} at {time_slot}</p>
                        <div style="margin-top: 20px; padding: 15px; background: #f1f5f9; border-left: 4px solid #0d6efd;">
                            <p style="margin: 0;"><strong>Message:</strong> {reason}</p>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            
            send_mail(
                subject,
                message,
                sender_email,
                [admin_email],
                html_message=html_message,
                fail_silently=False,
            )
            return JsonResponse({"status": "success", "message": "Appointment confirmed."})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
            
    return JsonResponse({"error": "Invalid request"}, status=400)

# 🔹 Health Tips
@login_required
def health_tips_view(request):
    return render(request, 'core/health_tips.html')

# 🔹 Doctor Contact
@login_required
def doctor_contact_view(request):
    doctors = [
        {
            'name': 'Dr. Utkarsh Sri',
            'specialization': 'General Physician',
            'department': 'Internal Medicine',
            'experience': 12,
            'rating': 4.9,
            'reviews': '1.2k',
            'status': 'Online',
            'image_url': '/static/img/dr_utkarsh.jpg',
            'next_slot': 'Available Now',
            'fee': '$50',
            'tags': ['Internal Medicine', 'Chronic Care']
        },
        {
            'name': 'Dr. Vikram Singh',
            'specialization': 'Cardiologist',
            'department': 'Cardiology',
            'experience': 18,
            'rating': 4.8,
            'reviews': '850',
            'status': 'Busy',
            'image_url': 'https://ui-avatars.com/api/?name=Dr+Vikram+Singh&background=3b82f6&color=fff&size=128&bold=true',
            'next_slot': 'Today, 4:30 PM',
            'fee': '$120',
            'tags': ['Heart Surgery', 'Diagnostics']
        },
        {
            'name': 'Dr. Elena Rostova',
            'specialization': 'Neurologist',
            'department': 'Neurology',
            'experience': 15,
            'rating': 5.0,
            'reviews': '2.1k',
            'status': 'Offline',
            'image_url': 'https://ui-avatars.com/api/?name=Dr+Elena+Rostova&background=10b981&color=fff&size=128&bold=true',
            'next_slot': 'Tomorrow, 10:00 AM',
            'fee': '$150',
            'tags': ['Brain Mapping', 'Migraine Care']
        },
        {
            'name': 'Dr. Rajesh Kumar',
            'specialization': 'Pediatrician',
            'department': 'Pediatrics',
            'experience': 9,
            'rating': 4.7,
            'reviews': '420',
            'status': 'Online',
            'image_url': 'https://ui-avatars.com/api/?name=Dr+Rajesh+Kumar&background=f59e0b&color=fff&size=128&bold=true',
            'next_slot': 'Available Now',
            'fee': '$60',
            'tags': ['Child Care', 'Vaccinations']
        },
        {
            'name': 'Dr. Sarah Johnson',
            'specialization': 'Psychiatrist',
            'department': 'Mental Health',
            'experience': 14,
            'rating': 4.9,
            'reviews': '930',
            'status': 'Online',
            'image_url': 'https://ui-avatars.com/api/?name=Dr+Sarah+Johnson&background=ec4899&color=fff&size=128&bold=true',
            'next_slot': 'Available Now',
            'fee': '$90',
            'tags': ['Therapy', 'Anxiety']
        },
        {
            'name': 'Dr. Michael Chen',
            'specialization': 'Orthopedic',
            'department': 'Orthopedics',
            'experience': 22,
            'rating': 4.6,
            'reviews': '1.5k',
            'status': 'Busy',
            'image_url': 'https://ui-avatars.com/api/?name=Dr+Michael+Chen&background=6366f1&color=fff&size=128&bold=true',
            'next_slot': 'Today, 6:00 PM',
            'fee': '$110',
            'tags': ['Joint Replacement', 'Sports Injuries']
        }
    ]
    return render(request, 'core/doctor_contact.html', {'doctors': doctors})

@login_required
def consultation_hub(request, doctor_name):
    # Simulated doctor data retrieval
    doctors = [
        {'name': 'Dr. Utkarsh Sri', 'specialization': 'General Physician', 'image_url': '/static/img/dr_utkarsh.jpg', 'whatsapp': '919369680371'},
        {'name': 'Dr. Vikram Singh', 'specialization': 'Cardiologist', 'image_url': 'https://ui-avatars.com/api/?name=Dr+Vikram+Singh&background=3b82f6&color=fff&size=128&bold=true', 'whatsapp': '919369680371'},
        {'name': 'Dr. Elena Rostova', 'specialization': 'Neurologist', 'image_url': 'https://ui-avatars.com/api/?name=Dr+Elena+Rostova&background=10b981&color=fff&size=128&bold=true', 'whatsapp': '919369680371'},
        {'name': 'Dr. Rajesh Kumar', 'specialization': 'Pediatrician', 'image_url': 'https://ui-avatars.com/api/?name=Dr+Rajesh+Kumar&background=f59e0b&color=fff&size=128&bold=true', 'whatsapp': '919369680371'},
        {'name': 'Dr. Sarah Johnson', 'specialization': 'Psychiatrist', 'image_url': 'https://ui-avatars.com/api/?name=Dr+Sarah+Johnson&background=ec4899&color=fff&size=128&bold=true', 'whatsapp': '919369680371'},
        {'name': 'Dr. Michael Chen', 'specialization': 'Orthopedic', 'image_url': 'https://ui-avatars.com/api/?name=Dr+Michael+Chen&background=6366f1&color=fff&size=128&bold=true', 'whatsapp': '919369680371'}
    ]
    
    doctor = next((d for d in doctors if d['name'] == doctor_name), doctors[0])
    
    # Fetch latest clinical record for context sharing
    latest_symptom = SymptomEntry.objects.filter(user=request.user).first()
    
    context = {
        'doctor': doctor,
        'latest_symptom': latest_symptom,
        'meet_link': 'https://meet.google.com/new', # Simulated unique link
        'whatsapp_link': f"https://wa.me/{doctor.get('whatsapp', '919369680371')}?text=Hello%20{doctor_name},%20I%20would%20like%20to%20consult%20via%20DocX-AI.%20My%20latest%20reported%20symptoms:%20{latest_symptom.symptom_text if latest_symptom else 'None'}"
    }
    return render(request, 'core/consultation_hub.html', context)

@login_required
def medicine_store_view(request):
    medicines = [
        {'id': 1, 'name': 'Paracetamol 500mg', 'category': 'Pain Relief', 'price': 5.99, 'image': 'https://www.abibapharmacia.com/wp-content/uploads/2022/08/Diptamp-500-Tab.jpg', 'desc': 'Effective for fever and mild pain.'},
        {'id': 2, 'name': 'Amoxicillin', 'category': 'Antibiotics', 'price': 12.50, 'image': 'https://wellonapharma.com/admincms/product_img/product_resize_img/amoxicillin-tablets_1732540129.jpg', 'desc': 'Broad-spectrum antibiotic for infections.'},
        {'id': 3, 'name': 'Vitamin C 1000mg', 'category': 'Immunity', 'price': 15.00, 'image': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSFkbuCIxDGcCfXVxsFjNGDeubIDeqRQgLrvA&s', 'desc': 'Immune system support and antioxidants.'},
        {'id': 4, 'name': 'Ibuprofen', 'category': 'Pain Relief', 'price': 7.25, 'image': 'https://5.imimg.com/data5/SELLER/Default/2023/7/325863554/WI/JM/SY/135658020/ibuprofen-tablets-ip-200-mg--1000x1000.jpg', 'desc': 'Anti-inflammatory and pain reliever.'},
        {'id': 5, 'name': 'Melatonin', 'category': 'Sleep Support', 'price': 18.99, 'image': 'https://m.media-amazon.com/images/I/61hnuiay14L.jpg', 'desc': 'Natural sleep aid and wellness.'},
        {'id': 6, 'name': 'Antacid Tablets', 'category': 'Digestion', 'price': 4.50, 'image': 'https://5.imimg.com/data5/SELLER/Default/2025/10/553014201/WE/DN/UD/4057175/whatsapp-image-2025-10-14-at-9-14-53-am-3.jpeg', 'desc': 'Fast relief from acidity and heartburn.'},
        {'id': 7, 'name': 'Cetirizine', 'category': 'Allergy', 'price': 8.00, 'image': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS6hablYyRotYB4AHCvfWZQ6n4mTXvSVUGhiQ&s', 'desc': '24-hour allergy relief.'},
        {'id': 8, 'name': 'Probiotics', 'category': 'Digestion', 'price': 22.00, 'image': 'data:image/webp;base64,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', 'desc': 'Balanced gut health supplements.'}
    ]
    
    context = {
        'medicines': medicines,
        'categories': ['All', 'Pain Relief', 'Antibiotics', 'Immunity', 'Digestion', 'Sleep Support']
    }
    return render(request, 'core/medicine_store.html', context)

# 🔹 Delete Symptom Record
@login_required
def delete_symptom_view(request, pk):
    try:
        symptom = SymptomEntry.objects.get(pk=pk)
        if symptom.user == request.user or request.user.is_superuser:
            symptom.delete()
            messages.success(request, "Archive record deleted successfully.")
        else:
            messages.error(request, "Unauthorized deletion attempt.")
    except SymptomEntry.DoesNotExist:
        messages.error(request, "Record not found.")
    
    return redirect('symptom_history')

# 🔹 Subscribe Newsletter
@login_required
def subscribe_newsletter(request):
    if request.method == "POST":
        email = request.POST.get('email')
        if email:
            try:
                send_mail(
                    subject='Welcome to DocX Weekly Intelligence',
                    message=f'Hello,\n\nThank you for subscribing to DocX Weekly Intelligence. You will now receive clinical research at {email}.\n\nBest Regards,\nThe DocX Clinical Team',
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[email],
                    fail_silently=False,
                )
                messages.success(request, f"Excellence! {email} has been registered for clinical updates.")
            except Exception as e:
                print("SMTP Error:", e)
                messages.success(request, f"Intelligence Hub: {email} added to clinical queue.")
        else:
            messages.error(request, "Please provide a valid medical email address.")
    return redirect('health_tips')
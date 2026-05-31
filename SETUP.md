# Quick Setup Guide - DocX Healthcare Assistant

## 🚀 Quick Start Commands

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Create Database Tables
```bash
python3 manage.py makemigrations
python3 manage.py migrate
```

### 3. Create Admin User (Optional)
```bash
python3 manage.py createsuperuser
```

### 4. Run the Server
```bash
python3 manage.py runserver
```

### 5. Access the Application
- **Main App**: http://127.0.0.1:8000/
- **Admin Panel**: http://127.0.0.1:8000/admin/

## 📋 Available Pages

1. **Signup**: `/signup/` - Create new user account
2. **Login**: `/login/` - User login
3. **Dashboard**: `/dashboard/` - Main dashboard (requires login)
4. **Add Symptom**: `/add-symptom/` - Log new symptoms
5. **Symptom History**: `/symptom-history/` - View all logged symptoms
6. **Health Tips**: `/health-tips/` - Browse health information
7. **Contact Doctor**: `/doctor-contact/` - Find healthcare professionals
8. **Profile**: `/profile/` - User profile page

## 🔑 Default Features

- ✅ User authentication (signup, login, logout)
- ✅ Symptom logging with severity levels
- ✅ Rule-based suggestions (Low/Medium/High)
- ✅ Symptom history tracking
- ✅ Health tips and information
- ✅ Doctor contact directory
- ✅ Responsive Bootstrap UI
- ✅ Django admin interface

## 📝 Testing the Application

1. Start the server: `python3 manage.py runserver`
2. Visit http://127.0.0.1:8000/
3. Click "Sign up" to create an account
4. Login with your credentials
5. Explore the dashboard and features

## 🗄️ Database

- **Default**: SQLite (db.sqlite3) - automatically created
- **Alternative**: MySQL (configure in settings.py)

## ⚠️ Important Notes

- This is a demonstration project
- Suggestions are rule-based, not AI-powered
- For medical emergencies, contact emergency services
- Doctor contact info is for demonstration only


# DocX - Smart Healthcare Assistant

A complete Django-based healthcare assistant application that allows users to log symptoms, receive rule-based suggestions, access health tips, and contact doctors.

## Features

- **User Authentication**: Signup, login, logout, and user profile management
- **Symptom Tracking**: Log symptoms with severity levels (Low/Medium/High)
- **Rule-Based Suggestions**: Automatic suggestions based on symptom severity
- **Symptom History**: View all previously logged symptoms
- **Health Tips**: Comprehensive health information and self-care tips
- **Doctor Contact**: List of healthcare professionals with contact information
- **Responsive Design**: Bootstrap-based modern UI

## Technology Stack

- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **Backend**: Python, Django 4.2+
- **Database**: SQLite (default) or MySQL

## Installation & Setup

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Run Migrations

Create the database tables:

```bash
python3 manage.py makemigrations
python3 manage.py migrate
```

### Step 3: Create Superuser (Optional)

Create an admin user to access Django admin panel:

```bash
python3 manage.py createsuperuser
```

### Step 4: Run the Development Server

```bash
python3 manage.py runserver
```

The application will be available at `http://127.0.0.1:8000/`

## Project Structure

```
docx_project/
├── core/                    # Main application
│   ├── models.py           # SymptomEntry model
│   ├── views.py            # All view functions
│   ├── forms.py            # User registration and symptom forms
│   ├── urls.py             # URL routing
│   └── admin.py            # Admin configuration
├── templates/core/          # HTML templates
│   ├── base.html           # Base template
│   ├── signup.html         # Registration page
│   ├── login.html          # Login page
│   ├── profile.html        # User profile
│   ├── dashboard.html      # Main dashboard
│   ├── add_symptom.html    # Add symptom form
│   ├── symptom_history.html # Symptom history
│   ├── health_tips.html    # Health tips page
│   └── doctor_contact.html # Doctor contact page
├── static/                 # Static files
│   └── css/
│       └── style.css       # Custom CSS
├── docx_project/           # Project settings
│   ├── settings.py         # Django settings
│   └── urls.py             # Main URL configuration
└── requirements.txt        # Python dependencies
```

## Usage

1. **Sign Up**: Create a new account at `/signup/`
2. **Login**: Access your account at `/login/`
3. **Dashboard**: View your dashboard after login
4. **Add Symptoms**: Log symptoms with severity levels
5. **View History**: Check all your symptom entries
6. **Health Tips**: Browse health information
7. **Contact Doctor**: Find and contact healthcare professionals

## Severity-Based Suggestions

The system provides predefined suggestions based on symptom severity:

- **Low**: Home rest, hydration, monitor symptoms
- **Medium**: Rest, basic medication, consider doctor visit if persists
- **High**: Immediate doctor consultation recommended

## Important Notes

- This is a basic healthcare assistant for demonstration purposes
- Suggestions are rule-based and not a substitute for professional medical advice
- For medical emergencies, contact emergency services immediately
- The doctor contact information is for demonstration only

## Database Configuration

### Using SQLite (Default)

No additional configuration needed. SQLite database file will be created automatically.

### Using MySQL

Update `settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'docx_db',
        'USER': 'your_username',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

Install MySQL client:
```bash
pip install mysqlclient
```

## Development

- Run migrations after model changes: `python3 manage.py makemigrations && python3 manage.py migrate`
- Access admin panel: `http://127.0.0.1:8000/admin/`
- Debug mode is enabled by default (set `DEBUG = False` for production)

## License

This project is for educational purposes.


from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import SymptomEntry, VitalsRecord

class UserRegistrationForm(UserCreationForm):
    """
    Custom registration form extending Django's UserCreationForm.
    """
    email = forms.EmailField(
        required=True, 
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    first_name = forms.CharField(
        max_length=30, 
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=30, 
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply Bootstrap class and placeholder configuration dynamically
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            field.help_text = None

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user

class SymptomEntryForm(forms.ModelForm):
    """
    Form for entering symptoms with severity level.
    """
    class Meta:
        model = SymptomEntry
        fields = ['symptom_text', 'severity']
        widgets = {
            'symptom_text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Describe your symptoms in detail...'
            }),
            'severity': forms.Select(attrs={
                'class': 'form-control'
            })
        }
        labels = {
            'symptom_text': 'Symptom Description',
            'severity': 'Severity Level'
        }


class VitalsRecordForm(forms.ModelForm):
    """
    Form for entering daily health vitals.
    """
    class Meta:
        model = VitalsRecord
        fields = ['heart_rate', 'blood_oxygen', 'steps', 'weight']
        widgets = {
            'heart_rate': forms.NumberInput(attrs={
                'class': 'form-control bg-light',
                'placeholder': 'e.g. 72'
            }),
            'blood_oxygen': forms.NumberInput(attrs={
                'class': 'form-control bg-light',
                'placeholder': 'e.g. 98'
            }),
            'steps': forms.NumberInput(attrs={
                'class': 'form-control bg-light',
                'placeholder': 'e.g. 5000'
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'form-control bg-light',
                'placeholder': 'e.g. 70.5'
            })
        }
        labels = {
            'heart_rate': 'Heart Rate (BPM)',
            'blood_oxygen': 'Blood Oxygen (SpO2 %)',
            'steps': 'Daily Steps',
            'weight': 'Current Weight (kg)'
        }

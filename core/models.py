from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.

class SymptomEntry(models.Model):
    """
    Model to store user symptom entries with severity levels and suggestions.
    """
    # Severity choices
    SEVERITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
    ]
    
    # Foreign key to User model
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='symptom_entries')
    
    # Symptom description
    symptom_text = models.TextField(help_text="Describe your symptoms")
    
    # Severity level
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='Low')
    
    # Predefined suggestion based on severity
    suggestion = models.TextField(help_text="Suggestion based on severity")
    
    # Timestamp
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-created_at']  # Most recent first
        verbose_name_plural = "Symptom Entries"
    
    def __str__(self):
        return f"{self.user.username} - {self.symptom_text[:50]} ({self.severity})"

class VitalsRecord(models.Model):
    """
    Model to store user-reported vitals for dashboard tracking.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vitals_records')
    heart_rate = models.IntegerField(help_text="Heart Rate in BPM")
    blood_oxygen = models.IntegerField(help_text="Blood Oxygen SpO2 %")
    steps = models.IntegerField(default=0, help_text="Daily steps count")
    weight = models.FloatField(null=True, blank=True, help_text="Weight in kg")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Vitals Records"

    def __str__(self):
        return f"{self.user.username} Vitals - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

from django.contrib import admin
from .models import SymptomEntry

# Register your models here.

@admin.register(SymptomEntry)
class SymptomEntryAdmin(admin.ModelAdmin):
    """
    Admin interface for SymptomEntry model.
    """
    list_display = ('user', 'symptom_text', 'severity', 'created_at')
    list_filter = ('severity', 'created_at')
    search_fields = ('user__username', 'symptom_text')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Symptom Details', {
            'fields': ('symptom_text', 'severity')
        }),
        ('Suggestion', {
            'fields': ('suggestion',)
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )

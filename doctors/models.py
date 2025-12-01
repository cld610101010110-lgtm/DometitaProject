from django.db import models
from django.conf import settings
from django.utils.text import slugify


class DoctorSpecialization(models.Model):
    """Reusable list of doctor specialties that admins can manage"""
    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=160, unique=True, blank=True)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['display_order', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class DoctorProfile(models.Model):
    """Extended profile for doctors with medical information"""
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='doctor_profile',
        limit_choices_to={'role': 'doctor'}
    )
    
    specialization = models.CharField(max_length=200, help_text='Medical specialization')
    license_number = models.CharField(max_length=50, unique=True, help_text='Medical license number')
    years_of_experience = models.PositiveIntegerField(default=0)
    education = models.TextField(help_text='Educational background')
    
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    bio = models.TextField(blank=True, null=True, help_text='Professional biography')
    
    is_available = models.BooleanField(default=True, help_text='Currently accepting patients')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Doctor Profile'
        verbose_name_plural = 'Doctor Profiles'
        ordering = ['user__last_name', 'user__first_name']
    
    def __str__(self):
        return f"Dr. {self.user.get_full_name()} - {self.specialization}"


class DoctorSchedule(models.Model):
    """Model for doctor's weekly schedule"""
    
    DAYS_OF_WEEK = (
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    )
    
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='schedules',
        limit_choices_to={'role': 'doctor'}
    )
    
    day_of_week = models.CharField(max_length=10, choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Doctor Schedule'
        verbose_name_plural = 'Doctor Schedules'
        ordering = ['day_of_week', 'start_time']
        unique_together = ['doctor', 'day_of_week', 'start_time']
    
    def __str__(self):
        return f"Dr. {self.doctor.get_full_name()} - {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"
from django.db import models
from django.conf import settings
from django.utils import timezone

class Doctor(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    specialization = models.CharField(max_length=100)
    bio = models.TextField()
    license_number = models.CharField(max_length=50)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"Dr. {self.user.get_full_name()}"
    
    def get_average_rating(self):
        """Calculate average rating for this doctor"""
        ratings = self.ratings.all()
        if ratings.exists():
            return round(sum(r.rating for r in ratings) / ratings.count(), 1)
        return 0.0
    
    def get_rating_count(self):
        """Get total number of ratings"""
        return self.ratings.count()

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    date = models.DateField()
    time = models.TimeField()
    reason = models.TextField()
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    patient_confirmed_completion = models.BooleanField(default=False, help_text="Patient confirmed the appointment was completed")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date', '-time']
    
    def __str__(self):
        return f"{self.patient.get_full_name()} - {self.doctor} on {self.date}"

class DoctorRating(models.Model):
    """Rating given by patient to doctor after appointment completion"""
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='rating')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='ratings')
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='given_ratings')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)], help_text="Rating from 1 to 5")
    comment = models.TextField(blank=True, help_text="Optional feedback")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['appointment', 'patient']
    
    def __str__(self):
        return f"{self.patient.get_full_name()} rated {self.doctor} {self.rating}/5"

class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title


class AppointmentMessage(models.Model):
    """Simple messaging thread tied to an appointment"""
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_appointment_messages')
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_appointment_messages')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Message from {self.sender.get_full_name()} about appointment {self.appointment.id}"

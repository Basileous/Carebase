from django.db import models
from .chatbot_logic import get_medical_advice
from django.conf import settings


class Doctor(models.Model):
    name      = models.CharField(max_length=200)
    specialty = models.CharField(max_length=100)

    def __str__(self):
        return f"Dr. {self.name} ({self.specialty})"


class DoctorTimeSlot(models.Model):
    """Admin-defined available time slots per doctor."""
    DAYS = [
        ('Monday', 'Monday'), ('Tuesday', 'Tuesday'), ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'), ('Friday', 'Friday'), ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    ]
    doctor     = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='time_slots')
    day        = models.CharField(max_length=10, choices=DAYS)
    time_slot  = models.TimeField()

    class Meta:
        unique_together = ('doctor', 'day', 'time_slot')
        ordering = ['day', 'time_slot']

    def __str__(self):
        return f"Dr. {self.doctor.name} — {self.day} {self.time_slot.strftime('%I:%M %p')}"

    def display_time(self):
        return self.time_slot.strftime('%I:%M %p')


class Patient(models.Model):
    user    = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name    = models.CharField(max_length=200)
    address = models.CharField(max_length=200)
    age     = models.IntegerField()
    profile_complete = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class ChatMessage(models.Model):
    patient      = models.ForeignKey('Patient', on_delete=models.CASCADE, related_name='chats')
    user_message = models.TextField()
    ai_response  = models.TextField()
    timestamp    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']


class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending',  'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]

    patient    = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor     = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True)
    date       = models.DateField()
    time_slot  = models.TimeField()
    symptoms   = models.TextField()
    status     = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    ai_predicted_disease = models.CharField(max_length=200, blank=True)
    ai_precaution        = models.TextField(blank=True)
    ai_assigned_doctor   = models.BooleanField(default=False)

    class Meta:
        unique_together = ('doctor', 'date', 'time_slot')

    def save(self, *args, **kwargs):
        suggested_spec, prediction, precaution = get_medical_advice(self.symptoms)
        self.ai_predicted_disease = prediction
        self.ai_precaution        = precaution

        if not self.doctor_id:
            suggested_doctor = Doctor.objects.filter(specialty__icontains=suggested_spec).first()
            if not suggested_doctor:
                suggested_doctor = Doctor.objects.first()
            if suggested_doctor:
                self.doctor             = suggested_doctor
                self.ai_assigned_doctor = True

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.patient} → {self.doctor} on {self.date}"


class Notification(models.Model):
    NOTIF_TYPES = [
        ('rescheduled', 'Appointment Rescheduled'),
        ('cancelled', 'Appointment Cancelled'),
        ('accepted', 'Appointment Accepted'),
        ('rejected', 'Appointment Rejected'),
    ]
    patient     = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='notifications')
    notif_type  = models.CharField(max_length=20, choices=NOTIF_TYPES)
    message     = models.TextField()
    is_read     = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.notif_type}] {self.patient} — {self.created_at:%Y-%m-%d}"

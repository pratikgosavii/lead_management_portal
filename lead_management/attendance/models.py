from django.db import models
from django.urls import reverse
from django.utils import timezone
from accounts.models import CustomUser
from datetime import date, time, datetime, timedelta
import pytz

# Set Indian Standard Time timezone
IST = pytz.timezone('Asia/Kolkata')

class Attendance(models.Model):
    """Model to track employee attendance"""
    STATUS_CHOICES = (
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('half_day', 'Half Day'),
        ('leave', 'Leave'),
        ('holiday', 'Holiday'),
    )
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField(default=date.today)
    time_in = models.TimeField(null=True, blank=True)
    time_out = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='present')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', '-time_in']
        unique_together = ('user', 'date')
    
    def __str__(self):
        return f"{self.user.username} - {self.date} ({self.status})"
    
    def get_absolute_url(self):
        return reverse('attendance_detail', args=[str(self.id)])
    
    @property
    def total_hours(self):
        """Calculate total working hours using IST timezone"""
        if self.time_in and self.time_out:
            # Combine date and time for calculation and make timezone aware in IST
            naive_datetime_in = datetime.combine(self.date, self.time_in)
            naive_datetime_out = datetime.combine(self.date, self.time_out)
            
            # Convert to IST timezone-aware datetimes
            datetime_in = IST.localize(naive_datetime_in)
            datetime_out = IST.localize(naive_datetime_out)
            
            # If out time is earlier than in time, assume it's for the next day
            if datetime_out < datetime_in:
                naive_datetime_out = datetime.combine(self.date + timedelta(days=1), self.time_out)
                datetime_out = IST.localize(naive_datetime_out)
            
            # Calculate difference
            difference = datetime_out - datetime_in
            hours = difference.total_seconds() / 3600
            return round(hours, 2)
        return 0
    
    @property
    def is_ongoing(self):
        """Check if attendance is ongoing (clocked in but not out)"""
        return self.time_in is not None and self.time_out is None

    @classmethod
    def get_current_attendance(cls, user):
        """Get the current attendance for a user using Indian Standard Time"""
        # Use IST date rather than server date
        ist_now = timezone.now().astimezone(IST)
        ist_date = ist_now.date()
        
        try:
            return cls.objects.get(user=user, date=ist_date)
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def punch_in(cls, user, notes=None):
        """Record attendance punch in using Indian Standard Time"""
        # Get the current date and time in IST
        ist_now = timezone.now().astimezone(IST)
        ist_date = ist_now.date()
        ist_time = ist_now.time()
        
        attendance, created = cls.objects.get_or_create(
            user=user,
            date=ist_date,
            defaults={
                'time_in': ist_time,
                'status': 'present',
                'notes': notes if notes else f"Punched in at {ist_time.strftime('%H:%M:%S')} IST",
            }
        )
        
        if not created and attendance.time_in is None:
            attendance.time_in = ist_time
            attendance.status = 'present'
            if notes:
                attendance.notes = notes
            else:
                attendance.notes = f"Punched in at {ist_time.strftime('%H:%M:%S')} IST"
            attendance.save()
            
        return attendance
    
    @classmethod
    def punch_out(cls, user, notes=None):
        """Record attendance punch out using Indian Standard Time"""
        # Get the current date and time in IST
        ist_now = timezone.now().astimezone(IST)
        ist_date = ist_now.date()
        ist_time = ist_now.time()
        
        try:
            attendance = cls.objects.get(user=user, date=ist_date)
            attendance.time_out = ist_time
            
            # Update notes if provided
            if notes:
                current_notes = attendance.notes or ""
                attendance.notes = f"{current_notes}\nOut: {notes}".strip()
            else:
                current_notes = attendance.notes or ""
                attendance.notes = f"{current_notes}\nPunched out at {ist_time.strftime('%H:%M:%S')} IST".strip()
                
            attendance.save()
            return attendance
        except cls.DoesNotExist:
            return None

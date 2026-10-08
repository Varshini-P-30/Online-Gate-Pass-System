from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

# ------------------- CHOICES -------------------
DEPARTMENTS = [
    ('CSE', 'Computer Science and Engineering'),
    ('ISE', 'Information Science and Engineering'),
    ('ECE', 'Electronics and Communication Engineering'),
    ('EEE', 'Electrical and Electronics Engineering'),
    ('AIML', 'Artificial Intelligence and Machine Learning'),
    ('AIDS', 'Artificial Intelligence and Data Science'),
]

COURSE_YEARS = [
    ('1st Year', '1st Year'),
    ('2nd Year', '2nd Year'),
    ('3rd Year', '3rd Year'),
    ('4th Year', '4th Year'),
]

COURSE_SEMESTERS = [
    ('1st Sem', '1st Sem'),
    ('2nd Sem', '2nd Sem'),
    ('3rd Sem', '3rd Sem'),
    ('4th Sem', '4th Sem'),
    ('5th Sem', '5th Sem'),
    ('6th Sem', '6th Sem'),
    ('7th Sem', '7th Sem'),
    ('8th Sem', '8th Sem'),
]


# ------------------- COUNSELLOR -------------------
class Counsellor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    eid = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=50, choices=DEPARTMENTS)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.department})"


# ------------------- HOD -------------------
class HOD(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    eid = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=50, choices=DEPARTMENTS)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.department})"


# ------------------- STUDENT -------------------
class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    usn = models.CharField(max_length=15, unique=True)
    department = models.CharField(max_length=50, choices=DEPARTMENTS)
    course_year = models.CharField(max_length=20, choices=COURSE_YEARS)
    course_semester = models.CharField(max_length=20, choices=COURSE_SEMESTERS)
    phone = models.CharField(max_length=15)
    parent_phone = models.CharField(max_length=15)
    counsellor = models.ForeignKey(Counsellor, on_delete=models.SET_NULL, null=True, blank=True)
    hod = models.ForeignKey(HOD, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.usn})"


# ------------------- GATE PASS -------------------
class GatePass(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    reason = models.TextField()
    from_date = models.DateField()
    to_date = models.DateField()

    # Auto-filled from Student model
    department = models.CharField(max_length=50)
    course_year = models.CharField(max_length=20, choices=COURSE_YEARS)
    course_semester = models.CharField(max_length=20, choices=COURSE_SEMESTERS)
    counsellor = models.ForeignKey(Counsellor, on_delete=models.SET_NULL, null=True, blank=True)
    hod = models.ForeignKey(HOD, on_delete=models.SET_NULL, null=True, blank=True)

    # Approval Fields
    counsellor_approved = models.BooleanField(default=False)
    counsellor_rejected = models.BooleanField(default=False)
    hod_approved = models.BooleanField(default=False)
    hod_rejected = models.BooleanField(default=False)
    counsellor_comment = models.TextField(blank=True, null=True)

    # Timestamps
    applied_date = models.DateTimeField(auto_now_add=True)
    approved_date = models.DateTimeField(blank=True, null=True)

    def is_active(self):
        """Gate pass valid for 1 hour after HOD approval"""
        if self.approved_date:
            return timezone.now() <= self.approved_date + timedelta(hours=1)
        return False

    def status(self):
        """Readable status for UI display"""
        if self.hod_rejected:
            return "Rejected by HOD"
        elif self.hod_approved:
            return "Approved by HOD"
        elif self.counsellor_rejected:
            return "Rejected by Counsellor"
        elif self.counsellor_approved:
            return "Approved by Counsellor (Waiting for HOD)"
        else:
            return "Waiting for Counsellor Approval"

    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.status()}"

    class Meta:
        verbose_name_plural = "Gate Passes"

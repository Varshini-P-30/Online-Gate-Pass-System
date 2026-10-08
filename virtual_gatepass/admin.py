from django.contrib import admin
from .models import Student, GatePass

# ✅ Student admin configuration
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('user', 'usn', 'department', 'course_year', 'counsellor', 'hod', 'phone', 'parent_phone')
    search_fields = ('user__username', 'usn', 'department', 'counsellor', 'hod')

# ✅ GatePass admin configuration (only once)
@admin.register(GatePass)
class GatePassAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'reason')  # Simple and safe fields
  # Use only existing safe fields



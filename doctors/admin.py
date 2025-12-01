from django.contrib import admin
from .models import DoctorProfile, DoctorSchedule, DoctorSpecialization


@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'specialization', 'license_number', 'is_available']
    search_fields = ['user__first_name', 'user__last_name', 'license_number', 'specialization']
    list_filter = ['is_available']


@admin.register(DoctorSchedule)
class DoctorScheduleAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'day_of_week', 'start_time', 'end_time', 'is_active']
    list_filter = ['day_of_week', 'is_active']
    search_fields = ['doctor__first_name', 'doctor__last_name']


@admin.register(DoctorSpecialization)
class DoctorSpecializationAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'display_order']
    list_editable = ['is_active', 'display_order']
    search_fields = ['name']

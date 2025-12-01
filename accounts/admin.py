from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User Admin with approval actions"""
    model = User
    list_display = ['email', 'first_name', 'last_name', 'role', 'is_approved', 
                    'is_active', 'date_joined']
    list_filter = ['role', 'is_approved', 'is_active', 'is_staff', 'date_joined']
    search_fields = ['email', 'first_name', 'last_name', 'phone_number']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {
            'fields': ('first_name', 'last_name', 'phone_number', 
                      'address', 'date_of_birth', 'height', 'weight')
        }),
        ('Permissions', {
            'fields': ('role', 'is_approved', 'is_active', 'is_staff', 
                      'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'phone_number', 
                      'role', 'password1', 'password2', 'is_approved', 
                      'is_active', 'is_staff')
        }),
    )
    
    readonly_fields = ['date_joined', 'last_login']
    
    actions = ['approve_doctors', 'reject_doctors', 'deactivate_users', 'activate_users']
    
    def approve_doctors(self, request, queryset):
        """Approve selected doctor accounts"""
        doctors = queryset.filter(role='doctor', is_approved=False)
        count = 0
        
        for user in doctors:
            user.is_approved = True
            user.is_active = True
            user.save()
            
            # Update doctor profile if exists
            try:
                if hasattr(user, 'doctor'):
                    user.doctor.is_available = True
                    user.doctor.save()
            except Exception as e:
                print(f"Error updating doctor profile: {e}")
            
            count += 1
        
        self.message_user(request, f'{count} doctor(s) approved successfully.')
    approve_doctors.short_description = "✅ Approve selected doctors"
    
    def reject_doctors(self, request, queryset):
        """Reject and delete selected doctor accounts"""
        doctors = queryset.filter(role='doctor', is_approved=False)
        count = doctors.count()
        doctors.delete()
        self.message_user(request, f'{count} doctor registration(s) rejected and deleted.')
    reject_doctors.short_description = "❌ Reject selected doctors"
    
    def deactivate_users(self, request, queryset):
        """Deactivate selected user accounts"""
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} user(s) deactivated.')
    deactivate_users.short_description = "🔒 Deactivate selected users"
    
    def activate_users(self, request, queryset):
        """Activate selected user accounts"""
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} user(s) activated.')
    activate_users.short_description = "🔓 Activate selected users"
    
    def get_queryset(self, request):
        """Customize queryset to show pending doctors first"""
        qs = super().get_queryset(request)
        # Show unapproved doctors first
        return qs.order_by('is_approved', '-date_joined')
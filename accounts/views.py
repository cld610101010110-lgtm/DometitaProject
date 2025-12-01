from django.shortcuts import render, redirect, get_object_or_404
from accounts.models import User
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .forms import UserRegistrationForm, UserLoginForm, ProfileUpdateForm
from .models import User
from appointments.models import Appointment
from notifications.models import Notification

# Home View
def home_view(request):
    """Landing page - redirects based on user type or shows public home"""
    if request.user.is_authenticated:
        if request.user.role == 'doctor':
            return redirect('doctors:dashboard')
        elif request.user.role == 'patient':
            return redirect('patient_dashboard')
        else:
            return redirect('admin_dashboard')
    
    context = {
        'title': 'MedLynk - Home'
    }
    return render(request, 'pages/home.html', context)

# Registration View
def register_view(request):
    """Handle user registration with approval system"""
    if request.user.is_authenticated:
        return redirect('patient_dashboard')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            
            # Prevent doctor self-registration
            if user.role == 'doctor':
                messages.error(request, 'Doctor registration is currently handled by administrators. Please contact support.')
                return redirect('register')
            
            user.set_password(form.cleaned_data['password1'])
            user.save()
            messages.success(request, 'Registration successful! You can now login.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'pages/registration/register.html', {'form': form, 'title': 'Register'})

# Login View
def login_view(request):
    """Handle user login"""
    if request.user.is_authenticated:
        return redirect('patient_dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if email and password:
            user = authenticate(request, email=email, password=password)
            if user:
                if not user.is_active:
                    messages.error(request, 'Your account is inactive. Please contact support.')
                elif user.role == 'doctor' and not user.is_approved:
                    messages.warning(request, 'Your account is pending approval. Please wait for admin approval.')
                else:
                    login(request, user)
                    messages.success(request, f'Welcome back, {user.get_full_name()}!')
                    if user.role == 'doctor':
                        return redirect('doctors:dashboard')
                    elif user.role == 'patient':
                        return redirect('patient_dashboard')
                    else:
                        return redirect('admin_dashboard')
            else:
                messages.error(request, 'Invalid email or password.')
        else:
            messages.error(request, 'Please provide both email and password.')
    
    return render(request, 'pages/registration/login.html', {'title': 'Login'})

# Logout View
def logout_view(request):
    """Handle user logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')

# Patient Dashboard
@login_required
def patient_dashboard(request):
    """Dashboard for patient users"""
    from datetime import date
    
    # Get upcoming appointments (confirmed or pending, future dates)
    upcoming_appointments = Appointment.objects.filter(
        patient=request.user,
        date__gte=date.today(),
        status__in=['confirmed', 'pending']
    ).select_related('doctor', 'doctor__user').order_by('date', 'time')[:5]
    
    # Get recent completed appointments
    completed_appointments = Appointment.objects.filter(
        patient=request.user,
        status='completed'
    ).select_related('doctor', 'doctor__user').order_by('-date', '-time')[:5]
    
    # Calculate BMI if metrics are available
    bmi = request.user.calculate_bmi()
    bmi_category = request.user.get_bmi_category()
    
    # Calculate age if date_of_birth is available
    age = None
    if request.user.date_of_birth:
        from datetime import date
        today = date.today()
        age = today.year - request.user.date_of_birth.year - ((today.month, today.day) < (request.user.date_of_birth.month, request.user.date_of_birth.day))
    
    context = {
        'upcoming_appointments': upcoming_appointments,
        'completed_appointments': completed_appointments,
        'bmi': bmi,
        'bmi_category': bmi_category,
        'age': age,
        'title': 'Patient Dashboard'
    }
    
    return render(request, 'pages/patient/patient_dashboard.html', context)

# Profile View
@login_required
def profile_view(request):
    """View and edit user profile"""
    edit_mode = request.GET.get('edit') == 'true' or request.method == 'POST'
    
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
    
    # Calculate BMI if metrics are available
    bmi = request.user.calculate_bmi()
    bmi_category = request.user.get_bmi_category()
    
    context = {
        'form': form,
        'bmi': bmi,
        'bmi_category': bmi_category,
        'edit_mode': edit_mode,
        'title': 'My Profile'
    }
    return render(request, 'pages/profile.html', context)

# Admin Dashboard (for superusers/staff)
@login_required
def admin_dashboard(request):
    """Admin dashboard with real statistics"""
    if request.user.role != 'admin' and not request.user.is_staff:
        messages.error(request, 'Access denied. Admin only.')
        return redirect('home')
    
    # Import models
    from appointments.models import Appointment, Doctor
    from doctors.models import DoctorProfile
    from django.db.models import Count
    from datetime import date, timedelta
    
    # Real Statistics from Database
    total_appointments = Appointment.objects.count()
    active_doctors = Doctor.objects.count()
    total_patients = User.objects.filter(role='patient').count()
    pending_appointments = Appointment.objects.filter(status='pending').count()
    
    # Get all doctors with their profiles
    all_doctors = User.objects.filter(role='doctor', is_approved=True).select_related('doctor', 'doctor_profile')
    
    # Recent Appointments (Real data)
    recent_appointments = Appointment.objects.select_related(
        'patient', 'doctor', 'doctor__user'
    ).order_by('-created_at')[:10]
    
    # Today's Schedule (Real data)
    today = date.today()
    today_schedule = Appointment.objects.filter(
        date=today
    ).select_related('patient', 'doctor', 'doctor__user').order_by('time')
    
    # Appointments by Status (Real data)
    appointments_by_status = Appointment.objects.values('status').annotate(
        count=Count('id')
    )
    
    context = {
        'total_appointments': total_appointments,
        'active_doctors': active_doctors,
        'total_patients': total_patients,
        'pending_appointments': pending_appointments,
        'recent_appointments': recent_appointments,
        'today_schedule': today_schedule,
        'appointments_by_status': appointments_by_status,
        'all_doctors': all_doctors,
        'title': 'Admin Dashboard'
    }
    return render(request, 'pages/admin/admin_dashboard.html', context)

# Admin: Create Doctor
@login_required
def admin_create_doctor(request):
    """Admin creates a new doctor account"""
    if request.user.role != 'admin' and not request.user.is_staff:
        messages.error(request, 'Access denied. Admin only.')
        return redirect('home')
    
    from appointments.models import Doctor
    from doctors.models import DoctorProfile, DoctorSpecialization
    
    specializations = DoctorSpecialization.objects.filter(is_active=True)
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number', '')
        password = request.POST.get('password')
        specialization_slug = request.POST.get('specialization')
        specialization_obj = None
        if specialization_slug:
            specialization_obj = specializations.filter(slug=specialization_slug).first()
        specialization = specialization_obj.name if specialization_obj else 'General Practice'
        license_number = request.POST.get('license_number', '')
        consultation_fee = request.POST.get('consultation_fee', '500.00')
        
        # Validate email uniqueness
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
            return render(request, 'pages/admin/create_doctor.html', {'title': 'Create Doctor'})
        
        # Create user
        doctor_user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            role='doctor',
            is_approved=True,
            is_active=True
        )
        
        # Create Doctor instance
        Doctor.objects.create(
            user=doctor_user,
            specialization=specialization,
            license_number=license_number,
            consultation_fee=consultation_fee,
            bio='Professional healthcare provider'
        )
        
        # Create DoctorProfile
        DoctorProfile.objects.create(
            user=doctor_user,
            specialization=specialization,
            license_number=license_number or f'LIC-{doctor_user.id}',
            years_of_experience=0,
            education='To be updated',
            consultation_fee=consultation_fee,
            is_available=True
        )
        
        messages.success(request, f'Doctor account created successfully for {doctor_user.get_full_name()}.')
        return redirect('admin_dashboard')
    
    return render(request, 'pages/admin/create_doctor.html', {
        'title': 'Create Doctor',
        'specializations': specializations
    })

# Admin: Edit Doctor
@login_required
def admin_edit_doctor(request, doctor_id):
    """Admin edits doctor details"""
    if request.user.role != 'admin' and not request.user.is_staff:
        messages.error(request, 'Access denied. Admin only.')
        return redirect('home')
    
    from appointments.models import Doctor
    from doctors.models import DoctorProfile, DoctorSpecialization
    
    specializations = DoctorSpecialization.objects.filter(is_active=True)
    
    doctor_user = get_object_or_404(User, id=doctor_id, role='doctor')
    doctor, _ = Doctor.objects.get_or_create(user=doctor_user, defaults={
        'specialization': 'General Practice',
        'bio': 'Professional healthcare provider',
        'license_number': f'LIC-{doctor_user.id}',
        'consultation_fee': 500.00
    })
    doctor_profile, _ = DoctorProfile.objects.get_or_create(user=doctor_user, defaults={
        'specialization': doctor.specialization,
        'license_number': doctor.license_number,
        'years_of_experience': 0,
        'education': 'To be updated',
        'consultation_fee': doctor.consultation_fee,
        'is_available': True
    })
    current_specialization = specializations.filter(name=doctor.specialization).first()
    
    if request.method == 'POST':
        doctor_user.first_name = request.POST.get('first_name')
        doctor_user.last_name = request.POST.get('last_name')
        doctor_user.phone_number = request.POST.get('phone_number', '')
        doctor_user.email = request.POST.get('email')
        doctor_user.save()
        
        consultation_fee = request.POST.get('consultation_fee', '500.00')
        specialization_slug = request.POST.get('specialization')
        specialization_obj = None
        if specialization_slug:
            specialization_obj = specializations.filter(slug=specialization_slug).first()
        doctor.specialization = specialization_obj.name if specialization_obj else doctor.specialization
        doctor.consultation_fee = consultation_fee
        doctor.license_number = request.POST.get('license_number', '')
        doctor.bio = request.POST.get('bio', '')
        doctor.save()
        
        # Sync with DoctorProfile
        doctor_profile.specialization = doctor.specialization
        doctor_profile.consultation_fee = doctor.consultation_fee
        doctor_profile.license_number = doctor.license_number
        doctor_profile.is_available = request.POST.get('is_available') == 'on'
        doctor_profile.save()
        
        messages.success(request, 'Doctor details updated successfully.')
        return redirect('admin_dashboard')
    
    context = {
        'doctor_user': doctor_user,
        'doctor': doctor,
        'doctor_profile': doctor_profile,
        'title': 'Edit Doctor',
        'specializations': specializations,
        'current_specialization_slug': current_specialization.slug if current_specialization else ''
    }
    return render(request, 'pages/admin/edit_doctor.html', context)

@login_required
def admin_update_account(request):
    """Admin updates their own email and password"""
    if request.user.role != 'admin' and not request.user.is_staff:
        messages.error(request, 'Access denied. Admin only.')
        return redirect('home')
    
    if request.method == 'POST':
        new_email = request.POST.get('email')
        new_password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if new_email and new_email != request.user.email:
            # Check if email is already taken
            if User.objects.filter(email=new_email).exclude(id=request.user.id).exists():
                messages.error(request, 'This email is already in use.')
            else:
                request.user.email = new_email
                messages.success(request, 'Email updated successfully.')
        
        if new_password:
            if new_password != confirm_password:
                messages.error(request, 'Passwords do not match.')
            elif len(new_password) < 8:
                messages.error(request, 'Password must be at least 8 characters long.')
            else:
                request.user.set_password(new_password)
                messages.success(request, 'Password updated successfully.')
                # Re-login after password change
                from django.contrib.auth import update_session_auth_hash
                update_session_auth_hash(request, request.user)
        
        request.user.save()
        return redirect('admin_dashboard')
    
    return render(request, 'pages/admin/update_account.html', {'title': 'Update Account'})

@login_required
def notification_list(request):
    """View all notifications for the logged-in user"""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Mark as read when viewing
    notifications.filter(is_read=False).update(is_read=True)
    
    context = {
        'notifications': notifications,
        'title': 'Notifications'
    }
    return render(request, 'pages/notifications/notification_list.html', context)

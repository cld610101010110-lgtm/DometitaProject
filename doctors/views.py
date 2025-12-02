from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from accounts.models import User
from appointments.models import Appointment, Doctor  # Import Doctor from appointments
from .models import DoctorProfile, DoctorSpecialization

@login_required
def doctor_dashboard(request):
    """Dashboard for doctor users"""
    # Check if user is a doctor
    if request.user.role != 'doctor':
        messages.error(request, 'Access denied. This page is only for doctors.')
        return redirect('profile')
    
    # Get or create Doctor instance (for appointments)
    doctor, created = Doctor.objects.get_or_create(
        user=request.user,
        defaults={
            'specialization': 'General Practice',
            'bio': 'Professional healthcare provider',
            'license_number': f'LIC-{request.user.id}',
            'consultation_fee': 500.00
        }
    )
    
    # Also get or create DoctorProfile (for extended info)
    doctor_profile, _ = DoctorProfile.objects.get_or_create(
        user=request.user,
        defaults={
            'specialization': 'General Practice',
            'license_number': f'LIC-{request.user.id}',
            'years_of_experience': 0,
            'education': 'To be updated',
            'consultation_fee': 500.00
        }
    )
    
    # Get all appointments for this doctor
    today = timezone.now().date()
    
    # Today's appointments
    todays_appointments = Appointment.objects.filter(
        doctor=doctor,  # Use Doctor instance
        date=today
    ).select_related('patient').order_by('time')
    
    # Pending appointments
    pending_appointments = Appointment.objects.filter(
        doctor=doctor,
        status='pending'
    ).select_related('patient').order_by('date', 'time')
    
    # Upcoming appointments (next 7 days, excluding today)
    upcoming_appointments = Appointment.objects.filter(
        doctor=doctor,
        date__gt=today,
        date__lte=today + timedelta(days=7),
        status__in=['pending', 'confirmed']
    ).select_related('patient').order_by('date', 'time')[:6]
    
    # Statistics
    total_appointments = Appointment.objects.filter(doctor=doctor).count()
    total_patients = Appointment.objects.filter(
        doctor=doctor
    ).values('patient').distinct().count()
    
    # Handle availability toggle
    if request.method == 'POST' and 'toggle_availability' in request.POST:
        doctor_profile.is_available = not doctor_profile.is_available
        doctor_profile.save()
        status = 'available' if doctor_profile.is_available else 'unavailable'
        messages.success(request, f'You are now {status}.')
        return redirect('doctors:dashboard')
    
    context = {
        'doctor': doctor,
        'doctor_profile': doctor_profile,
        'todays_appointments': todays_appointments,
        'todays_count': todays_appointments.count(),
        'pending_appointments': pending_appointments,
        'pending_count': pending_appointments.count(),
        'upcoming_appointments': upcoming_appointments,
        'total_appointments': total_appointments,
        'total_patients': total_patients,
    }
    
    return render(request, 'pages/doctors/doctor_dashboard.html', context)


@login_required
def doctor_appointments(request):
    """List all appointments for the doctor"""
    if request.user.role != 'doctor':
        messages.error(request, 'Access denied.')
        return redirect('profile')
    
    # Get or create Doctor instance
    doctor, _ = Doctor.objects.get_or_create(
        user=request.user,
        defaults={
            'specialization': 'General Practice',
            'bio': 'Professional healthcare provider',
            'license_number': f'LIC-{request.user.id}',
            'consultation_fee': 500.00
        }
    )
    
    appointments = Appointment.objects.filter(
        doctor=doctor
    ).select_related('patient').order_by('-date', '-time')
    
    # Filter by status if provided
    status = request.GET.get('status')
    if status:
        appointments = appointments.filter(status=status)
    
    # Filter by date
    date_filter = request.GET.get('date')
    if date_filter == 'today':
        appointments = appointments.filter(date=timezone.now().date())
    elif date_filter == 'upcoming':
        appointments = appointments.filter(
            date__gte=timezone.now().date(),
            status__in=['pending', 'confirmed']
        )
    
    return render(request, 'pages/doctors/doctor_appointments.html', {
        'appointments': appointments
    })


@login_required
def doctor_patients(request):
    """List all patients who have appointments with this doctor"""
    if request.user.role != 'doctor':
        messages.error(request, 'Access denied.')
        return redirect('profile')
    
    # Get or create Doctor instance
    doctor, _ = Doctor.objects.get_or_create(
        user=request.user,
        defaults={
            'specialization': 'General Practice',
            'bio': 'Professional healthcare provider',
            'license_number': f'LIC-{request.user.id}',
            'consultation_fee': 500.00
        }
    )
    
    # Get unique patients from appointments
    patient_ids = Appointment.objects.filter(
        doctor=doctor
    ).values_list('patient_id', flat=True).distinct()
    
    patients = User.objects.filter(id__in=patient_ids, role='patient')
    
    return render(request, 'pages/doctors/doctor_patients.html', {
        'patients': patients
    })


@login_required
def appointment_action(request, appointment_id, action):
    """Handle appointment actions (confirm, cancel, complete)"""
    if request.user.role != 'doctor':
        messages.error(request, 'Access denied.')
        return redirect('profile')
    
    # Get or create Doctor instance
    doctor, _ = Doctor.objects.get_or_create(
        user=request.user,
        defaults={
            'specialization': 'General Practice',
            'bio': 'Professional healthcare provider',
            'license_number': f'LIC-{request.user.id}',
            'consultation_fee': 500.00
        }
    )
    
    appointment = get_object_or_404(
        Appointment, 
        id=appointment_id, 
        doctor=doctor
    )
    
    if action == 'confirm':
        appointment.status = 'confirmed'
        appointment.save()
        messages.success(request, f'Appointment with {appointment.patient.get_full_name()} confirmed.')

        # Create notification for patient
        from notifications.models import Notification
        Notification.objects.create(
            user=appointment.patient,
            notification_type='appointment_confirmed',
            title='Appointment Confirmed',
            message=f'Your appointment with Dr. {doctor.user.get_full_name()} on {appointment.date.strftime("%B %d, %Y")} at {appointment.time.strftime("%I:%M %p")} has been confirmed.'
        )
    elif action == 'cancel':
        appointment.status = 'cancelled'
        appointment.save()
        messages.warning(request, f'Appointment with {appointment.patient.get_full_name()} cancelled.')

        # Create notification for patient
        from notifications.models import Notification
        Notification.objects.create(
            user=appointment.patient,
            notification_type='appointment_cancelled',
            title='Appointment Cancelled',
            message=f'Your appointment with Dr. {doctor.user.get_full_name()} on {appointment.date.strftime("%B %d, %Y")} at {appointment.time.strftime("%I:%M %p")} has been cancelled.'
        )
    elif action == 'complete':
        appointment.status = 'completed'
        appointment.save()
        messages.success(request, f'Appointment with {appointment.patient.get_full_name()} marked as completed.')

    return redirect('doctors:dashboard')


def doctor_list(request):
    """List all approved and available doctors"""
    # Get Doctor objects (from appointments app) for approved doctor users
    doctor_users = User.objects.filter(
        role='doctor', 
        is_approved=True, 
        is_active=True
    )
    
    # Get Doctor instances for these users
    doctors = Doctor.objects.filter(user__in=doctor_users).select_related('user')
    
    # Filter by availability - only show available doctors
    from .models import DoctorProfile
    available_doctor_ids = DoctorProfile.objects.filter(
        is_available=True,
        user__in=doctor_users
    ).values_list('user_id', flat=True)
    doctors = doctors.filter(user_id__in=available_doctor_ids)
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        doctors = doctors.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(specialization__icontains=search_query)
        )
    
    # Filter by specialization
    specialization_slug = request.GET.get('specialization')
    current_specialization = None
    if specialization_slug:
        try:
            specialization_obj = DoctorSpecialization.objects.get(slug=specialization_slug, is_active=True)
            current_specialization = specialization_obj
            doctors = doctors.filter(specialization__iexact=specialization_obj.name)
        except DoctorSpecialization.DoesNotExist:
            pass
    
    # Filter by high rating (4.0 and above)
    rating_filter = request.GET.get('rating')
    if rating_filter == 'high':
        # Get doctors with average rating >= 4.0
        high_rated_doctors = []
        for doctor in doctors:
            if doctor.get_average_rating() >= 4.0:
                high_rated_doctors.append(doctor.id)
        doctors = doctors.filter(id__in=high_rated_doctors)
    
    # Get specializations for dropdown
    specializations = DoctorSpecialization.objects.filter(is_active=True)
    
    return render(request, 'pages/doctors/doctor_list.html', {
        'doctors': doctors,
        'specializations': specializations,
        'current_specialization': current_specialization
    })


def doctor_detail(request, pk):
    """Public-facing profile for a doctor"""
    doctor = get_object_or_404(
        Doctor.objects.select_related('user'),
        pk=pk,
        user__is_active=True,
        user__is_approved=True
    )
    profile = DoctorProfile.objects.filter(user=doctor.user).first()
    ratings = doctor.ratings.select_related('patient').all()
    total_appointments = doctor.appointments.count()
    total_patients = doctor.appointments.values('patient_id').distinct().count()

    context = {
        'doctor': doctor,
        'profile': profile,
        'average_rating': doctor.get_average_rating(),
        'rating_count': doctor.get_rating_count(),
        'ratings': ratings,
        'total_appointments': total_appointments,
        'total_patients': total_patients,
        'title': f"Dr. {doctor.user.get_full_name()}"
    }
    return render(request, 'pages/doctors/doctor_detail.html', context)


@login_required
def doctor_ratings_feedback(request):
    """View for doctors to see their ratings and patient feedback"""
    # Check if user is a doctor
    if request.user.role != 'doctor':
        messages.error(request, 'Access denied. This page is only for doctors.')
        return redirect('profile')

    # Get Doctor instance
    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        messages.error(request, 'Doctor profile not found.')
        return redirect('doctors:dashboard')

    # Get all ratings with related patient and appointment info
    from appointments.models import DoctorRating
    ratings = DoctorRating.objects.filter(doctor=doctor).select_related(
        'patient', 'appointment'
    ).order_by('-created_at')

    # Calculate statistics
    total_ratings = ratings.count()
    average_rating = doctor.get_average_rating()

    # Count ratings by star level
    ratings_breakdown = {
        5: ratings.filter(rating=5).count(),
        4: ratings.filter(rating=4).count(),
        3: ratings.filter(rating=3).count(),
        2: ratings.filter(rating=2).count(),
        1: ratings.filter(rating=1).count(),
    }

    context = {
        'doctor': doctor,
        'ratings': ratings,
        'total_ratings': total_ratings,
        'average_rating': average_rating,
        'ratings_breakdown': ratings_breakdown,
        'title': 'My Ratings & Feedback'
    }
    return render(request, 'pages/doctors/doctor_ratings.html', context)
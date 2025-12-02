from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import FileResponse, Http404
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from .models import Appointment, Doctor, DoctorRating, AppointmentMessage
from .forms import AppointmentForm, RatingForm


def _get_appointment_for_user(pk, user):
    """Helper to fetch appointment ensuring user is participant"""
    appointment = get_object_or_404(Appointment, pk=pk)
    if user.role == 'patient' and appointment.patient != user:
        raise Http404("Appointment not found")
    if user.role == 'doctor' and appointment.doctor.user != user:
        raise Http404("Appointment not found")
    if user.role not in ['patient', 'doctor']:
        raise Http404("Appointment not available")
    return appointment

# List all appointments
@login_required
def appointment_list(request):
    """View all appointments for the logged-in patient"""
    appointments = Appointment.objects.filter(patient=request.user).order_by('-date', '-time')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        appointments = appointments.filter(status=status_filter)
    
    context = {
        'appointments': appointments,
        'current_status': status_filter,
        'title': 'My Appointments'
    }
    return render(request, 'pages/appointments/appointment_list.html', context)

# Create new appointment
@login_required
def appointment_create(request):
    """Create a new appointment"""
    # Ensure only patients can book appointments
    if request.user.role != 'patient':
        messages.error(request, 'Only patients can book appointments.')
        return redirect('home')
    
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.patient = request.user
            appointment.status = 'pending'
            appointment.save()
            
            messages.success(request, 'Appointment booked successfully! We will confirm shortly.')
            return redirect('appointments:appointment_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AppointmentForm()
        # Pre-select doctor if provided in URL
        doctor_id = request.GET.get('doctor')
        if doctor_id:
            try:
                form.initial['doctor'] = doctor_id
            except:
                pass
    
    doctors = Doctor.objects.filter(user__is_approved=True, user__is_active=True).select_related('user')
    context = {
        'form': form,
        'doctors': doctors,
        'title': 'Book Appointment'
    }
    return render(request, 'pages/appointments/appointment_form.html', context)

# View appointment detail
@login_required
def appointment_detail(request, pk):
    """View single appointment details"""
    # Allow admin, patient, and doctor to view
    appointment = get_object_or_404(Appointment, pk=pk)

    # Check permissions
    if request.user.role == 'patient':
        if appointment.patient != request.user:
            raise Http404("Appointment not found")
    elif request.user.role == 'doctor':
        if appointment.doctor.user != request.user:
            raise Http404("Appointment not found")
    elif request.user.role != 'admin' and not request.user.is_staff:
        raise Http404("Appointment not found")

    # Check if rating exists
    has_rating = hasattr(appointment, 'rating')

    context = {
        'appointment': appointment,
        'has_rating': has_rating,
        'is_admin': request.user.role == 'admin' or request.user.is_staff,
        'title': 'Appointment Details'
    }
    return render(request, 'pages/appointments/appointment_detail.html', context)

# Confirm appointment completion
@login_required
def confirm_completion(request, pk):
    """Patient confirms appointment completion"""
    appointment = get_object_or_404(Appointment, pk=pk, patient=request.user)
    
    if appointment.status != 'completed':
        messages.error(request, 'This appointment is not marked as completed by the doctor yet.')
        return redirect('appointments:appointment_detail', pk=pk)
    
    if request.method == 'POST':
        appointment.patient_confirmed_completion = True
        appointment.save()
        return redirect('appointments:rate_appointment', pk=pk)
    
    return redirect('appointments:appointment_detail', pk=pk)

# Rate appointment
@login_required
def rate_appointment(request, pk):
    """Rate doctor after appointment completion"""
    appointment = get_object_or_404(Appointment, pk=pk, patient=request.user)
    
    if appointment.status != 'completed' or not appointment.patient_confirmed_completion:
        messages.error(request, 'You can only rate completed appointments that you have confirmed.')
        return redirect('appointments:appointment_detail', pk=pk)
    
    # Check if already rated
    if hasattr(appointment, 'rating'):
        messages.info(request, 'You have already rated this appointment.')
        return redirect('appointments:appointment_detail', pk=pk)
    
    if request.method == 'POST':
        form = RatingForm(request.POST)
        if form.is_valid():
            rating = form.save(commit=False)
            rating.appointment = appointment
            rating.doctor = appointment.doctor
            rating.patient = request.user
            rating.save()
            messages.success(request, 'Thank you for your rating!')
            return redirect('appointments:appointment_detail', pk=pk)
    else:
        form = RatingForm()
    
    context = {
        'form': form,
        'appointment': appointment,
        'title': 'Rate Appointment'
    }
    return render(request, 'pages/appointments/rate_appointment.html', context)

# Edit appointment
@login_required
def appointment_edit(request, pk):
    """Edit an existing appointment (reschedule)"""
    appointment = get_object_or_404(Appointment, pk=pk, patient=request.user)
    
    # Only allow editing if status is pending or confirmed
    if appointment.status not in ['pending', 'confirmed']:
        messages.error(request, 'You can only reschedule pending or confirmed appointments.')
        return redirect('appointments:appointment_detail', pk=pk)
    
    if request.method == 'POST':
        form = AppointmentForm(request.POST, instance=appointment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Appointment updated successfully!')
            return redirect('appointments:appointment_detail', pk=pk)
    else:
        form = AppointmentForm(instance=appointment)
    
    context = {
        'form': form,
        'appointment': appointment,
        'title': 'Edit Appointment'
    }
    return render(request, 'pages/appointments/appointment_form.html', context)

# Delete appointment
@login_required
def appointment_delete(request, pk):
    """Cancel/delete an appointment"""
    appointment = get_object_or_404(Appointment, pk=pk, patient=request.user)
    
    if request.method == 'POST':
        appointment.status = 'cancelled'
        appointment.save()
        messages.success(request, 'Appointment cancelled successfully.')
        return redirect('appointments:appointment_list')
    
    context = {
        'appointment': appointment,
        'title': 'Cancel Appointment'
    }
    return render(request, 'pages/appointments/appointment_confirm_delete.html', context)


@login_required
def appointment_messages(request, pk):
    """Simple messaging thread between patient and doctor"""
    appointment = _get_appointment_for_user(pk, request.user)
    
    if request.method == 'POST':
        content = request.POST.get('message', '').strip()
        if content:
            recipient = appointment.doctor.user if request.user.role == 'patient' else appointment.patient
            AppointmentMessage.objects.create(
                appointment=appointment,
                sender=request.user,
                recipient=recipient,
                message=content
            )
            messages.success(request, 'Message sent.')
            return redirect('appointments:appointment_messages', pk=pk)
        messages.error(request, 'Please enter a message before sending.')
    
    messages_thread = appointment.messages.select_related('sender').all()

    # Mark all messages in this conversation as read for the current user
    appointment.messages.filter(
        recipient=request.user,
        is_read=False
    ).update(is_read=True)

    context = {
        'appointment': appointment,
        'messages_thread': messages_thread,
        'title': 'Appointment Messages'
    }
    return render(request, 'pages/appointments/appointment_messages.html', context)


@login_required
def completed_history(request):
    """Display all completed appointments for the patient"""
    if request.user.role != 'patient':
        messages.error(request, 'Only patients can view completed appointment history.')
        return redirect('home')
    
    history = Appointment.objects.filter(
        patient=request.user,
        status='completed'
    ).select_related('doctor', 'doctor__user').order_by('-date', '-time')
    
    return render(request, 'pages/appointments/completed_history.html', {
        'appointments': history,
        'title': 'Completed Consultations'
    })


@login_required
def download_receipt(request, pk):
    """Generate a simple PDF receipt for an appointment"""
    appointment = _get_appointment_for_user(pk, request.user)
    
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, "MedLynk Consultation Receipt")
    
    p.setFont("Helvetica", 12)
    y = height - 100
    p.drawString(50, y, f"Appointment ID: {appointment.id}")
    y -= 20
    p.drawString(50, y, f"Patient: {appointment.patient.get_full_name()} ({appointment.patient.email})")
    y -= 20
    p.drawString(50, y, f"Doctor: Dr. {appointment.doctor.user.get_full_name()} - {appointment.doctor.specialization}")
    y -= 20
    p.drawString(50, y, f"Date & Time: {appointment.date.strftime('%B %d, %Y')} at {appointment.time.strftime('%I:%M %p')}")
    y -= 20
    p.drawString(50, y, f"Status: {appointment.get_status_display()}")
    y -= 20
    p.drawString(50, y, f"Consultation Fee: ₱{appointment.doctor.consultation_fee}")
    y -= 20
    notes = appointment.notes or 'N/A'
    p.drawString(50, y, f"Notes: {notes}")
    y -= 40
    p.drawString(50, y, "Thank you for choosing MedLynk.")
    
    p.showPage()
    p.save()
    buffer.seek(0)
    filename = f"appointment_{appointment.id}_receipt.pdf"
    return FileResponse(buffer, as_attachment=True, filename=filename)


@login_required
def messages_inbox(request):
    """View all message conversations for the logged-in user"""
    from django.db.models import Q, Max

    # Get all appointments where user is involved and has messages
    if request.user.role == 'patient':
        appointments_with_messages = Appointment.objects.filter(
            patient=request.user,
            messages__isnull=False
        ).distinct().select_related('doctor', 'doctor__user').prefetch_related('messages')
    elif request.user.role == 'doctor':
        appointments_with_messages = Appointment.objects.filter(
            doctor__user=request.user,
            messages__isnull=False
        ).distinct().select_related('patient', 'doctor__user').prefetch_related('messages')
    else:
        appointments_with_messages = Appointment.objects.none()

    # Add last message info to each appointment
    conversations = []
    for appointment in appointments_with_messages:
        last_message = appointment.messages.order_by('-created_at').first()
        if last_message:
            conversations.append({
                'appointment': appointment,
                'last_message': last_message,
                'unread_count': appointment.messages.filter(
                    recipient=request.user,
                    sender=last_message.sender
                ).count()
            })

    # Sort by most recent message
    conversations.sort(key=lambda x: x['last_message'].created_at, reverse=True)

    context = {
        'conversations': conversations,
        'title': 'Messages'
    }
    return render(request, 'pages/messages/inbox.html', context)


@login_required
def delete_message(request, message_id):
    """Delete a single message"""
    message = get_object_or_404(AppointmentMessage, id=message_id)

    # Verify user is sender or recipient
    if request.user != message.sender and request.user != message.recipient:
        messages.error(request, 'You do not have permission to delete this message.')
        return redirect('appointments:messages_inbox')

    appointment_id = message.appointment.id
    message.delete()
    messages.success(request, 'Message deleted successfully.')
    return redirect('appointments:appointment_messages', pk=appointment_id)


@login_required
def delete_conversation(request, appointment_id):
    """Delete entire conversation (all messages for an appointment)"""
    appointment = _get_appointment_for_user(appointment_id, request.user)

    # Delete all messages for this appointment
    message_count = appointment.messages.count()
    appointment.messages.all().delete()

    messages.success(request, f'{message_count} message(s) deleted successfully.')
    return redirect('appointments:messages_inbox')


@login_required
def acknowledge_appointment(request, pk):
    """Mark a completed appointment as acknowledged (Done button)"""
    appointment = _get_appointment_for_user(pk, request.user)

    # Only allow acknowledging completed appointments
    if appointment.status != 'completed':
        messages.error(request, 'Only completed appointments can be marked as done.')
        return redirect(request.META.get('HTTP_REFERER', 'home'))

    # Mark as acknowledged based on user role
    if request.user.role == 'patient':
        appointment.patient_acknowledged = True
    elif request.user.role == 'doctor':
        appointment.doctor_acknowledged = True

    appointment.save()
    messages.success(request, 'Appointment marked as done.')

    # Redirect back to referring page
    return redirect(request.META.get('HTTP_REFERER', 'home'))
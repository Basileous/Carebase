from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.http import require_POST

from .models import Appointment, Doctor, Patient, DoctorTimeSlot, Notification
from .chatbot_logic import get_medical_advice

User = get_user_model()


def is_admin(user):
    return user.is_authenticated and user.is_staff


# ── PUBLIC PAGES ─────────────────────────────────────────────────────────────

def home(request):
    doctors = Doctor.objects.all()[:3]
    return render(request, 'appointments/home.html', {'doctors': doctors})

def about(request):
    return render(request, 'appointments/about.html', {'doctors': Doctor.objects.all()})

def patients(request):
    return render(request, 'appointments/patients.html')

def rates(request):
    return render(request, 'appointments/rates.html')

def contact(request):
    return render(request, 'appointments/contacts.html')

def ratings(request):
    return render(request, 'appointments/ratings.html')


# ── PROFILE ──────────────────────────────────────────────────────────────────

@login_required
def profile_view(request):
    patient = getattr(request.user, 'patient', None)
    appointments = Appointment.objects.filter(
        patient=patient
    ).select_related('doctor').order_by('-date') if patient else []

    if request.method == 'POST':
        name    = request.POST.get('name', '').strip()
        age_raw = request.POST.get('age', '').strip()
        address = request.POST.get('address', '').strip()
        try:
            age = int(age_raw)
            if patient:
                patient.name = name; patient.age = age; patient.address = address
                patient.save()
            else:
                patient = Patient.objects.create(
                    user=request.user, name=name, age=age, address=address)
            messages.success(request, 'Profile updated successfully.')
        except ValueError:
            messages.error(request, 'Please enter a valid age.')

    total    = len(appointments)
    accepted = sum(1 for a in appointments if a.status == 'accepted')
    pending  = sum(1 for a in appointments if a.status == 'pending')

    notifications = list(patient.notifications.filter(is_read=False)) if patient else []
    # Don't auto-mark as read here — bell dropdown AJAX handles that explicitly

    return render(request, 'appointments/profile.html', {
        'patient': patient, 'appointments': appointments,
        'stats': {'total': total, 'accepted': accepted, 'pending': pending},
        'notifications': notifications,
    })


# ── BOOKING ──────────────────────────────────────────────────────────────────

@login_required
def book_appointment(request):
    existing_patient = getattr(request.user, 'patient', None)
    form_data = {
        'name':    existing_patient.name    if existing_patient else '',
        'age':     existing_patient.age     if existing_patient else '',
        'address': existing_patient.address if existing_patient else '',
    }

    if request.method == "POST":
        doctor_id = request.POST.get('doctor')
        date      = request.POST.get('date')
        time_slot = request.POST.get('time_slot')
        symptoms  = request.POST.get('symptoms')

        if doctor_id:
            if Appointment.objects.filter(doctor_id=doctor_id, date=date, time_slot=time_slot).exists():
                messages.error(request, "This doctor is already booked for this time slot.")
                return render(request, 'appointments/book_appointment.html', {
                    'doctors': Doctor.objects.all(), 'form_data': request.POST, 'patient': existing_patient})

        try:
            if existing_patient:
                p = existing_patient
                p.name = request.POST.get('name'); p.age = int(request.POST.get('age'))
                p.address = request.POST.get('address'); p.save()
            else:
                p = Patient.objects.create(
                    user=request.user, name=request.POST.get('name'),
                    age=int(request.POST.get('age')), address=request.POST.get('address'))
            appt = Appointment.objects.create(
                patient=p, doctor_id=doctor_id or None,
                date=date, time_slot=time_slot, symptoms=symptoms)
            request.session['last_appointment_id'] = appt.id
            return redirect('appointment_success')
        except ValueError:
            messages.error(request, "Please enter a valid age.")
        except Exception as e:
            messages.error(request, f"An error occurred: {e}")

    return render(request, 'appointments/book_appointment.html', {
        'doctors': Doctor.objects.all(), 'form_data': form_data, 'patient': existing_patient})


@login_required
def appointment_success(request):
    appt_id = request.session.get('last_appointment_id')
    if not appt_id:
        return redirect('book_appointment')
    return render(request, 'appointments/appointment_success.html', {
        'appointment': get_object_or_404(Appointment, pk=appt_id)})


# ── CHATBOT ───────────────────────────────────────────────────────────────────

@login_required
def chatbot_view(request):
    from .models import ChatMessage
    patient = getattr(request.user, 'patient', None)
    if not patient:
        messages.warning(request, "Please complete your profile first.")
        return redirect('profile')

    chat_history = ChatMessage.objects.filter(patient=patient)
    analysis = None
    if request.method == "POST":
        syms = request.POST.get('symptoms', '')
        _, diagnosis, precautions = get_medical_advice(syms)
        analysis = {'diagnosis': diagnosis, 'precautions': precautions}
        ChatMessage.objects.create(patient=patient, user_message=syms,
            ai_response=f"Diagnosis: {diagnosis}\nPrecautions: {precautions}")

    return render(request, 'appointments/chatbot.html', {
        'analysis': analysis, 'chat_history': chat_history})


# ── AJAX ──────────────────────────────────────────────────────────────────────

def get_doctor_slots(request):
    doctor_id = request.GET.get('doctor_id')
    if not doctor_id:
        return JsonResponse({'slots': []})
    slots = DoctorTimeSlot.objects.filter(doctor_id=doctor_id).order_by('day', 'time_slot')
    return JsonResponse({'slots': [
        {'id': s.id, 'day': s.day, 'time': s.time_slot.strftime('%H:%M'),
         'label': f"{s.day} — {s.time_slot.strftime('%I:%M %p')}"}
        for s in slots]})


def ai_recommend_doctor(request):
    """AJAX: run AI on symptoms, return best matching doctor + their slots."""
    symptoms = request.GET.get('symptoms', '').strip()
    if not symptoms:
        return JsonResponse({'error': 'No symptoms provided'}, status=400)

    specialty, diagnosis, precautions = get_medical_advice(symptoms)

    # Match doctor by specialty (case-insensitive partial)
    doctors = Doctor.objects.prefetch_related('time_slots').all()
    matched = None
    spec_lower = specialty.lower()
    for doc in doctors:
        if doc.specialty and spec_lower in doc.specialty.lower():
            matched = doc
            break
    if not matched and doctors.exists():
        # Try reverse match
        for doc in doctors:
            if doc.specialty and doc.specialty.lower() in spec_lower:
                matched = doc
                break
    if not matched and doctors.exists():
        matched = doctors.first()

    slots = []
    if matched:
        slots = [
            {'id': s.id, 'day': s.day,
             'time': s.time_slot.strftime('%H:%M'),
             'label': f"{s.day} — {s.time_slot.strftime('%I:%M %p')}"}
            for s in matched.time_slots.order_by('day', 'time_slot')
        ]

    return JsonResponse({
        'specialty':   specialty,
        'diagnosis':   diagnosis,
        'precautions': precautions,
        'doctor': {
            'id':        matched.id        if matched else None,
            'name':      matched.name      if matched else None,
            'specialty': matched.specialty if matched else None,
        } if matched else None,
        'slots': slots,
    })


# ── ADMIN DASHBOARD ───────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin, login_url='home')
def admin_dashboard(request):
    appointments = Appointment.objects.select_related('patient', 'doctor').order_by('-date', '-time_slot')
    return render(request, 'appointments/admin_dashboard.html', {
        'appointments': appointments,
        'users':        User.objects.all().order_by('-date_joined'),
        'doctors':      Doctor.objects.prefetch_related('time_slots').all(),
        'total_appts':  appointments.count(),
        'pending':      appointments.filter(status='pending').count(),
        'accepted':     appointments.filter(status='accepted').count(),
        'rejected':     appointments.filter(status='rejected').count(),
    })


@login_required
@user_passes_test(is_admin)
@require_POST
def appointment_action(request, pk):
    appt = get_object_or_404(Appointment, pk=pk)
    action = request.POST.get('action')
    
    # ── NEW: Handle Deletion ──
    if action == 'deleted':
        appt.delete()
        messages.success(request, f"Rejected appointment #{pk} has been permanently deleted.")
        return redirect('admin_dashboard')
        
    # ── EXISTING: Handle Accept/Reject ──
    if action in ('accepted', 'rejected'):
        appt.status = action; appt.save()
        messages.success(request, f"Appointment #{pk} marked as {action}.")
        if appt.patient:
            doc_name = f"Dr. {appt.doctor.name}" if appt.doctor else "your doctor"
            if action == 'accepted':
                notif_msg = (f"Your appointment with {doc_name} on {appt.date} at "
                       f"{appt.time_slot.strftime('%I:%M %p')} has been confirmed.")
            else:
                notif_msg = (f"Your appointment with {doc_name} on {appt.date} at "
                       f"{appt.time_slot.strftime('%I:%M %p')} was not accepted. Please book a new slot.")
            Notification.objects.create(patient=appt.patient, notif_type=action, message=notif_msg)
            
    return redirect('admin_dashboard')

@login_required
@user_passes_test(is_admin)
@require_POST
def allot_time_slot(request):
    doctor_id = request.POST.get('doctor_id')
    day       = request.POST.get('day')
    time_slot = request.POST.get('time_slot')
    if not all([doctor_id, day, time_slot]):
        messages.error(request, "All fields are required.")
        return redirect('admin_dashboard')
    doctor = get_object_or_404(Doctor, pk=doctor_id)
    _, created = DoctorTimeSlot.objects.get_or_create(doctor=doctor, day=day, time_slot=time_slot)
    messages.success(request, f"Slot added for Dr. {doctor.name}.") if created else \
        messages.warning(request, "That slot already exists.")
    return redirect('admin_dashboard')


@login_required
@user_passes_test(is_admin)
@require_POST
def delete_time_slot(request, pk):
    get_object_or_404(DoctorTimeSlot, pk=pk).delete()
    messages.success(request, "Time slot removed.")
    return redirect('admin_dashboard')


@login_required
@user_passes_test(is_admin)
@require_POST
def reschedule_appointment(request, pk):
    appt     = get_object_or_404(Appointment, pk=pk)
    new_date = request.POST.get('new_date')
    slot_id  = request.POST.get('slot_id')
    if not new_date or not slot_id:
        messages.error(request, "Date and time slot are required.")
        return redirect('admin_dashboard')
    slot = get_object_or_404(DoctorTimeSlot, pk=slot_id)
    if Appointment.objects.filter(doctor=appt.doctor, date=new_date, time_slot=slot.time_slot).exclude(pk=pk).exists():
        messages.error(request, "That slot is already taken.")
        return redirect('admin_dashboard')
    old_date, old_time = appt.date, appt.time_slot
    appt.date = new_date; appt.time_slot = slot.time_slot; appt.status = 'accepted'; appt.save()
    doc_name = f"Dr. {appt.doctor.name}" if appt.doctor else 'your doctor'
    notif_msg = (
        f"Your appointment with {doc_name} has been rescheduled."
        f"Previous: {old_date} at {old_time.strftime('%I:%M %p')}"
        f"New: {new_date} ({slot.day}) at {slot.time_slot.strftime('%I:%M %p')}"
    )
    Notification.objects.create(patient=appt.patient, notif_type='rescheduled', message=notif_msg)
    messages.success(request, f"Appointment rescheduled. Notification sent to {appt.patient.name}.")
    return redirect('admin_dashboard')


@login_required
def get_notifications(request):
    """AJAX: return latest 15 notifications for the bell dropdown."""
    try:
        patient = request.user.patient
    except Exception:
        return JsonResponse({'notifications': []})
    notifs = patient.notifications.order_by('-created_at')[:15]
    return JsonResponse({'notifications': [
        {
            'id':         n.id,
            'notif_type': n.notif_type,
            'message':    n.message,
            'is_read':    n.is_read,
            'created_at': n.created_at.isoformat(),
        }
        for n in notifs
    ]})


@login_required
@require_POST
def mark_notifications_read(request):
    """AJAX: mark all notifications as read."""
    try:
        patient = request.user.patient
        patient.notifications.filter(is_read=False).update(is_read=True)
    except Exception:
        pass
    return JsonResponse({'ok': True})

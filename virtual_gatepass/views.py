from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from .sms_utils import send_sms_via_twilio

from .forms import (
    StudentRegisterForm,
    CounsellorRegisterForm,
    HODRegisterForm,
    LoginForm,
    GatePassForm,
)
from .models import Student, Counsellor, HOD, GatePass


# ------------------ HOME ------------------
def home(request):
    return render(request, 'home.html')


# ------------------ REGISTRATION ------------------
def student_register(request):
    if request.method == 'POST':
        form = StudentRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Student registered successfully!")
            return redirect('login')
    else:
        form = StudentRegisterForm()
    return render(request, 'student_register.html', {'form': form})


def counsellor_register(request):
    if request.method == 'POST':
        form = CounsellorRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Counsellor registered successfully!")
            return redirect('login')
    else:
        form = CounsellorRegisterForm()
    return render(request, 'counsellor_register.html', {'form': form})


def hod_register(request):
    if request.method == 'POST':
        form = HODRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ HOD registered successfully!")
            return redirect('login')
    else:
        form = HODRegisterForm()
    return render(request, 'hod_register.html', {'form': form})


# ------------------ LOGIN & LOGOUT ------------------
def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # Redirect based on user role
            if hasattr(user, 'student'):
                return redirect('student_dashboard')
            elif hasattr(user, 'counsellor'):
                return redirect('counsellor_dashboard')
            elif hasattr(user, 'hod'):
                return redirect('hod_dashboard')
            else:
                messages.error(request, "❌ Your account has no role assigned.")
                logout(request)
                return redirect('login')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "👋 Logged out successfully.")
    return redirect('home')


# ------------------ STUDENT DASHBOARD ------------------
@login_required
def student_dashboard(request):
    student = get_object_or_404(Student, user=request.user)
    gatepasses = GatePass.objects.filter(student=student).order_by('-applied_date')
    return render(request, 'student_dashboard.html', {'student': student, 'gatepasses': gatepasses})


# ------------------ APPLY GATEPASS ------------------
@login_required
def apply_gatepass(request):
    student = get_object_or_404(Student, user=request.user)

    if request.method == 'POST':
        form = GatePassForm(request.POST, student=student)
        if form.is_valid():
            gatepass = form.save(commit=False)
            gatepass.student = student
            gatepass.department = student.department
            gatepass.course_year = student.course_year
            gatepass.course_semester = student.course_semester
            gatepass.counsellor = form.cleaned_data['counsellor']
            gatepass.hod = HOD.objects.filter(department=student.department).first()
            gatepass.applied_date = timezone.now()
            gatepass.save()

            messages.success(request, "📝 Gate pass request submitted successfully!")
            return redirect('student_dashboard')
    else:
        form = GatePassForm(student=student, initial={
            'course_year': student.course_year,
            'course_semester': student.course_semester,
        })

    return render(request, 'apply_gatepass.html', {'form': form, 'student': student, 'now': timezone.now()})


# ------------------ GET HOD (AJAX) ------------------
@login_required
def get_hod(request, counsellor_id):
    try:
        counsellor = Counsellor.objects.get(id=counsellor_id)
        hod = HOD.objects.filter(department=counsellor.department).first()
        return JsonResponse({"hod_name": hod.user.get_full_name() if hod else None})
    except Counsellor.DoesNotExist:
        return JsonResponse({"hod_name": None})


# ------------------ COUNSELLOR DASHBOARD ------------------
@login_required
def counsellor_dashboard(request):
    counsellor = get_object_or_404(Counsellor, user=request.user)
    gatepasses = GatePass.objects.filter(
        counsellor=counsellor,
        counsellor_approved=False,
        counsellor_rejected=False,
    ).order_by('-applied_date')

    if request.method == 'POST':
        gatepass_id = request.POST.get('gatepass_id')
        comment = request.POST.get('comment', '')
        decision = request.POST.get('decision')
        gatepass = get_object_or_404(GatePass, id=gatepass_id)

        gatepass.counsellor_comment = comment
        if decision == 'approve':
            gatepass.counsellor_approved = True
        elif decision == 'reject':
            gatepass.counsellor_rejected = True
        gatepass.save()

        messages.success(request, "✅ Counsellor decision recorded successfully!")
        return redirect('counsellor_dashboard')

    return render(request, 'counsellor_dashboard.html', {'gatepasses': gatepasses})


# ------------------ HOD DASHBOARD ------------------
@login_required
def hod_dashboard(request):
    hod = get_object_or_404(HOD, user=request.user)
    gatepasses = GatePass.objects.filter(
        hod=hod,
        counsellor_approved=True,
        hod_approved=False,
        hod_rejected=False
    ).order_by('-applied_date')

    if request.method == 'POST':
        gatepass_id = request.POST.get('gatepass_id')
        decision = request.POST.get('decision')
        gatepass = get_object_or_404(GatePass, id=gatepass_id)

        if decision == 'approve':
            gatepass.hod_approved = True
            gatepass.approved_date = timezone.now()
        elif decision == 'reject':
            gatepass.hod_rejected = True

        gatepass.save()
        messages.success(request, "✅ HOD decision recorded successfully.")
        return redirect('hod_dashboard')

    return render(request, 'hod_dashboard.html', {'gatepasses': gatepasses})


# ------------------ SECURITY DASHBOARD ------------------
@login_required
def security_dashboard(request):
    gatepasses = GatePass.objects.filter(
        hod_approved=True,
        hod_rejected=False
    ).order_by('-approved_date')

    student = None
    selected_gatepass = None
    message = ""

    if request.method == "POST":
        usn = request.POST.get("usn", "").strip().upper()
        try:
            student = Student.objects.get(usn=usn)
            selected_gatepass = GatePass.objects.filter(
                student=student,
                hod_approved=True
            ).last()
            if selected_gatepass:
                message = "✅ Gate Pass Approved Successfully!"
            else:
                message = "⚠️ No approved gate pass found for this USN."
        except Student.DoesNotExist:
            message = "❌ Invalid USN entered."

    return render(request, 'security_dashboard.html', {
        'gatepasses': gatepasses,
        'student': student,
        'gatepass': selected_gatepass,
        'message': message,
    })


# ------------------ SECURITY ACTION (Twilio SMS Trigger) ------------------
@login_required
def security_action(request, gp_id):
    """
    Security confirms or rejects student exit/entry. If confirmed, SMS is sent to parent.
    """
    gatepass = get_object_or_404(GatePass, id=gp_id)
    action = request.GET.get('action')

    if action == 'confirm':
        confirm_time = timezone.now().strftime('%Y-%m-%d %H:%M')
        student = gatepass.student

        # Prepare SMS message
        sms_message = (
            f"Dear Parent, your child {student.user.get_full_name()} (USN: {student.usn}) "
            f"has exited the campus at {confirm_time}. Reason: '{gatepass.reason}'."
        )

        # Send SMS via Twilio
        if student.parent_phone:
            send_sms_via_twilio(student.parent_phone, sms_message)
            messages.success(
                request,
                f"✅ Gate pass confirmed. SMS sent to parent ({student.parent_phone})."
            )
        else:
            messages.warning(request, "⚠️ Parent phone number not found.")

    elif action == 'reject':
        messages.warning(request, f"🚫 Gate pass for {gatepass.student.user.get_full_name()} rejected by security.")

    return redirect('security_dashboard')


# ------------------ SECURITY QR SCAN (Alternate Method) ------------------
@login_required
def security_scan(request):
    gatepass = None
    student = None
    message = ""

    if request.method == "POST":
        qr_data = request.POST.get('qr_code_data', '').strip().upper()

        try:
            student = Student.objects.get(usn=qr_data)
            gatepass = GatePass.objects.filter(
                student=student,
                hod_approved=True,
                hod_rejected=False
            ).last()

            if gatepass and gatepass.is_active():
                confirm_time = timezone.now().strftime('%Y-%m-%d %H:%M')

                sms_message = (
                    f"Dear Parent, your child {student.user.get_full_name()} (USN: {student.usn}) "
                    f"has exited the college at {confirm_time}. Reason: '{gatepass.reason}'."
                )

                if student.parent_phone:
                    send_sms_via_twilio(student.parent_phone, sms_message)
                    messages.success(request, f"📩 SMS sent to parent ({student.parent_phone}).")
                else:
                    messages.warning(request, "⚠️ Parent phone number missing.")
                message = "✅ Gate Pass Verified Successfully!"
            else:
                message = "⚠️ No active approved gate pass found."

        except Student.DoesNotExist:
            message = "❌ Invalid QR code!"

    return render(request, 'security_scan.html', {
        'gatepass': gatepass,
        'student': student,
        'message': message,
    })

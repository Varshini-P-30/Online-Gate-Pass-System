from django.urls import path
from . import views

urlpatterns = [
    # ------------------ HOME & AUTH ------------------
    path('', views.home, name='home'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # ------------------ REGISTRATION ------------------
    path('register/student/', views.student_register, name='student_register'),
    path('register/counsellor/', views.counsellor_register, name='counsellor_register'),
    path('register/hod/', views.hod_register, name='hod_register'),

    # ------------------ STUDENT ------------------
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/apply/', views.apply_gatepass, name='apply_gatepass'),

    # ------------------ AJAX (Fetch HOD based on Counsellor) ------------------
    path('get_hod/<int:counsellor_id>/', views.get_hod, name='get_hod'),

    # ------------------ COUNSELLOR ------------------
    path('counsellor/dashboard/', views.counsellor_dashboard, name='counsellor_dashboard'),

    # ------------------ HOD ------------------
    path('hod/dashboard/', views.hod_dashboard, name='hod_dashboard'),

    # ------------------ SECURITY ------------------
    path('security/dashboard/', views.security_dashboard, name='security_dashboard'),
    path('security/scan/', views.security_scan, name='security_scan'),
    path('security/action/<int:gp_id>/', views.security_action, name='security_action'),
]

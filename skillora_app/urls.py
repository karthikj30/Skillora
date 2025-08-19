from django.urls import path
from . import views

urlpatterns = [
    # Main pages
    path('', views.home, name='home'),
    path('student/', views.student_home, name='student_home'),
    # Student actions
    path('student/toggle-save/<int:course_id>/', views.student_toggle_save, name='student_toggle_save'),
    path('student/certificate/<int:course_id>/', views.student_certificate, name='student_certificate'),
    path('teacher/', views.teacher_home, name='teacher_home'),
    path('company/', views.company_home, name='company_home'),
    path('about/', views.about, name='about'),
    path('courses/', views.courses, name='courses'),
    path('course/<int:course_id>/', views.course_detail, name='course_detail'),
    path('instructors/', views.instructors, name='instructors'),
    path('jobs/', views.jobs, name='jobs'),
    path('career-paths/', views.career_paths, name='career_paths'),
    path('team/', views.team, name='team'),
    path('testimonials/', views.testimonials, name='testimonials'),
    path('contact/', views.contact, name='contact'),
    
    # Authentication
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('signup/', views.user_signup, name='signup'),
    path('profile/', views.profile, name='profile'),
    
    # Teacher specific routes
    path('teacher/courses/', views.teacher_courses, name='teacher_courses'),
    path('teacher/students/', views.teacher_students, name='teacher_students'),
    path('teacher/payments/', views.teacher_payments, name='teacher_payments'),
    path('teacher/create-course/', views.create_course, name='create_course'),
]

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
    
    # Teacher Classroom Routes
    path('teacher/course/<int:course_id>/', views.teacher_course_detail, name='teacher_course_detail'),
    path('teacher/course/<int:course_id>/add-material/', views.add_course_material, name='add_course_material'),
    path('teacher/course/<int:course_id>/add-assignment/', views.add_assignment, name='add_assignment'),
    path('teacher/course/<int:course_id>/add-announcement/', views.add_announcement, name='add_announcement'),
    path('teacher/course/<int:course_id>/student-progress/', views.teacher_student_progress, name='teacher_student_progress'),
    path('teacher/assignment/<int:assignment_id>/submissions/', views.view_assignment_submissions, name='view_assignment_submissions'),
    path('teacher/submission/<int:submission_id>/grade/', views.grade_submission, name='grade_submission'),
    
    # Internship/Placement System Routes
    path('internships/', views.internships_list, name='internships_list'),
    path('internships/<int:internship_id>/', views.internship_detail, name='internship_detail'),
    path('internships/<int:internship_id>/apply/', views.apply_internship, name='apply_internship'),
    path('student/applications/', views.student_applications, name='student_applications'),
    path('student/placement-profile/', views.student_placement_profile, name='student_placement_profile'),
    
    # Placement Cell Routes
    path('placement-cell/', views.placement_cell_home, name='placement_cell_home'),
    path('placement-cell/internships/', views.placement_cell_internships, name='placement_cell_internships'),
    path('placement-cell/create-internship/', views.create_internship, name='create_internship'),
    
    # Mentor Routes
    path('mentor/', views.mentor_home, name='mentor_home'),
    path('mentor/approve/<int:application_id>/', views.mentor_approve_application, name='mentor_approve_application'),
]

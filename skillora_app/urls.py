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
    path('company/post-job/', views.post_job, name='post_job'),
    path('about/', views.about, name='about'),
    path('courses/', views.courses, name='courses'),
    path('course/<int:course_id>/', views.course_detail, name='course_detail'),
    path('instructors/', views.instructors, name='instructors'),
    path('jobs/', views.jobs, name='jobs'),
    path('jobs/<int:job_id>/apply/', views.apply_job, name='apply_job'),
    path('job-application/<int:application_id>/view/', views.view_job_application, name='view_job_application'),
    path('company/update-application-status/', views.update_application_status, name='update_application_status'),
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
    path('teacher/student-progress-analytics/', views.student_progress_analytics, name='student_progress_analytics'),
    path('teacher/assignments/', views.teacher_assignments, name='teacher_assignments'),
    path('teacher/announcements/', views.teacher_announcements, name='teacher_announcements'),
    path('teacher/payments/', views.teacher_payments, name='teacher_payments'),
    path('teacher/payments/approve/<str:payment_id>/', views.approve_payment, name='approve_payment'),
    path('teacher/payments/export/', views.export_payments_pdf, name='export_payments_pdf'),
    path('teacher/payments/analytics/', views.payment_analytics, name='payment_analytics'),
    path('teacher/create-course/', views.create_course, name='create_course'),
    path('teacher/edit-course/<int:course_id>/', views.edit_course, name='edit_course'),
    
    # Teacher Classroom Routes
    path('teacher/course/<int:course_id>/', views.teacher_course_detail, name='teacher_course_detail'),
    path('teacher/course/<int:course_id>/add-material/', views.add_course_material, name='add_course_material'),
    path('teacher/course/<int:course_id>/add-assignment/', views.add_assignment, name='add_assignment'),
    path('teacher/course/<int:course_id>/add-announcement/', views.add_announcement, name='add_announcement'),
    path('teacher/course/<int:course_id>/student-progress/<int:student_id>/', views.teacher_student_progress, name='teacher_student_progress'),
    path('teacher/course/<int:course_id>/student-progress/', views.teacher_student_progress, name='teacher_student_progress_all'),
    path('teacher/assignment/<int:assignment_id>/submissions/', views.view_assignment_submissions, name='view_assignment_submissions'),
    path('teacher/submission/<int:submission_id>/grade/', views.grade_submission, name='grade_submission'),
    path('teacher/create-schedule/', views.create_scheduled_class, name='create_scheduled_class'),
    path('teacher/scheduled-classes/', views.scheduled_classes, name='scheduled_classes'),
    path('teacher/quick-upload-material/', views.quick_upload_material, name='quick_upload_material'),
    path('teacher/material/<int:material_id>/view/', views.view_material, name='view_material'),
    path('teacher/material/<int:material_id>/delete/', views.delete_material, name='delete_material'),
    path('teacher/assignment/<int:assignment_id>/delete/', views.delete_assignment, name='delete_assignment'),
    
    # Student Course Content Routes
    path('student/course/<int:course_id>/content/', views.student_course_content, name='student_course_content'),
    path('student/assignment/<int:assignment_id>/submit/', views.submit_assignment, name='submit_assignment'),
    path('student/material/<int:material_id>/mark-done/', views.mark_material_done, name='mark_material_done'),
    path('student/course/<int:course_id>/remove/', views.remove_course, name='remove_course'),
    
    # Internship/Placement System Routes
    path('internships/', views.internships_list, name='internships_list'),
    path('internships/<int:internship_id>/', views.internship_detail, name='internship_detail'),
    path('internships/<int:internship_id>/apply/', views.apply_internship, name='apply_internship'),
    path('student/applications/', views.student_applications, name='student_applications'),
    path('student/placement-profile/', views.student_placement_profile, name='student_placement_profile'),
    
    
    # Company Dashboard Features
    path('company/excel-upload/', views.excel_upload, name='excel_upload'),
    path('company/ai-verification/', views.ai_verification, name='ai_verification'),
    path('company/generate-report/', views.generate_report, name='generate_report'),
    path('company/dashboard-data/', views.company_dashboard_data, name='company_dashboard_data'),
    
    # Dashboard API Endpoints
    path('api/dashboard/students/', views.dashboard_students_api, name='dashboard_students_api'),
    path('api/dashboard/placements/', views.dashboard_placements_api, name='dashboard_placements_api'),
    path('api/dashboard/reports/', views.dashboard_reports_api, name='dashboard_reports_api'),
    path('api/dashboard/users/', views.dashboard_users_api, name='dashboard_users_api'),
    path('api/dashboard/add-student/', views.add_student, name='add_student'),
    path('api/dashboard/add-placement/', views.add_placement, name='add_placement'),
    path('api/dashboard/delete-student/', views.delete_student, name='delete_student'),
    path('api/dashboard/delete-placement/', views.delete_placement, name='delete_placement'),
    path('api/dashboard/delete-user/', views.delete_user, name='delete_user'),
    path('api/dashboard/edit-student/', views.edit_student, name='edit_student'),
    path('api/dashboard/edit-placement/', views.edit_placement, name='edit_placement'),
    
    # Cart and Payment Routes
    path('add-to-cart/<int:course_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<int:course_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/', views.cart_view, name='cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('payment/<str:payment_id>/', views.payment_view, name='payment'),
    path('payment-otp/<str:payment_id>/', views.payment_otp, name='payment_otp'),
    path('payment-success/<str:payment_id>/', views.payment_success, name='payment_success'),
    path('my-certificates/', views.my_certificates, name='my_certificates'),
    path('certificate/<str:certificate_id>/', views.view_certificate, name='view_certificate'),
    path('api/chatbot/', views.chatbot_api, name='chatbot_api'),
    path('download-receipt/<str:payment_id>/', views.download_receipt, name='download_receipt'),
    
    # Skill Category Detail Route
    path('skill/<str:category_name>/', views.skill_category_detail, name='skill_category_detail'),
]

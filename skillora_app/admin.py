from django.contrib import admin
from .models import (Course, Instructor, Job, Testimonial, TeamMember, Contact, UserProfile, 
                     Student, Teacher, Company, Internship, InternshipApplication, StudentProfile, 
                     PlacementCell, Mentor, InternshipFeedback, Notification, CourseMaterial, 
                     Assignment, AssignmentSubmission, CourseAnnouncement, StudentProgress)

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'instructor', 'category', 'price', 'level', 'created_at')
    list_filter = ('category', 'level', 'created_at')
    search_fields = ('title', 'instructor', 'description')
    ordering = ('-created_at',)

@admin.register(Instructor)
class InstructorAdmin(admin.ModelAdmin):
    list_display = ('name', 'specialization', 'experience_years', 'rating')
    list_filter = ('specialization', 'experience_years')
    search_fields = ('name', 'bio', 'specialization')

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'location', 'job_type', 'salary_range', 'posted_date')
    list_filter = ('job_type', 'posted_date')
    search_fields = ('title', 'company', 'description')
    ordering = ('-posted_date',)

@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('name', 'position', 'company', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('name', 'position', 'company', 'content')

@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'position', 'email')
    search_fields = ('name', 'position', 'bio')

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email', 'skills')

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('user', 'enrollment_date')
    search_fields = ('user__username', 'user__email')
    filter_horizontal = ('courses_enrolled', 'saved_courses')

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialization', 'experience_years', 'rating', 'is_verified')
    list_filter = ('specialization', 'is_verified', 'experience_years')
    search_fields = ('user__username', 'user__email', 'specialization')

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('user', 'company_name', 'industry', 'company_size')
    list_filter = ('industry', 'company_size')
    search_fields = ('user__username', 'company_name', 'industry')

@admin.register(PlacementCell)
class PlacementCellAdmin(admin.ModelAdmin):
    list_display = ('user', 'department', 'organization', 'contact_email')
    search_fields = ('user__username', 'department', 'organization')

@admin.register(Mentor)
class MentorAdmin(admin.ModelAdmin):
    list_display = ('user', 'department', 'designation', 'specialization', 'experience_years')
    list_filter = ('department', 'designation', 'experience_years')
    search_fields = ('user__username', 'department', 'specialization')

@admin.register(Internship)
class InternshipAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'internship_type', 'location', 'status', 'seats_available', 'application_deadline')
    list_filter = ('internship_type', 'status', 'has_placement_potential', 'created_at')
    search_fields = ('title', 'company__company_name', 'location', 'required_skills')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(InternshipApplication)
class InternshipApplicationAdmin(admin.ModelAdmin):
    list_display = ('student', 'internship', 'status', 'applied_at', 'mentor')
    list_filter = ('status', 'applied_at', 'mentor_approval_date')
    search_fields = ('student__user__username', 'internship__title', 'internship__company__company_name')
    ordering = ('-applied_at',)
    readonly_fields = ('applied_at', 'updated_at')

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('student', 'department', 'year_of_study', 'cgpa', 'is_placement_ready')
    list_filter = ('department', 'year_of_study', 'graduation_year', 'is_placement_ready')
    search_fields = ('student__user__username', 'department', 'skills')

@admin.register(InternshipFeedback)
class InternshipFeedbackAdmin(admin.ModelAdmin):
    list_display = ('application', 'supervisor_name', 'overall_rating', 'completion_date', 'certificate_issued')
    list_filter = ('overall_rating', 'certificate_issued', 'recommend_for_placement', 'created_at')
    search_fields = ('application__student__user__username', 'supervisor_name', 'supervisor_email')
    ordering = ('-created_at',)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'notification_type', 'title', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('recipient__username', 'title', 'message')
    ordering = ('-created_at',)

# Teacher Classroom Admin

@admin.register(CourseMaterial)
class CourseMaterialAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'teacher', 'material_type', 'is_published', 'created_at')
    list_filter = ('material_type', 'is_published', 'created_at')
    search_fields = ('title', 'course__title', 'teacher__user__username')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'teacher', 'assignment_type', 'due_date', 'max_points', 'is_published')
    list_filter = ('assignment_type', 'is_published', 'due_date', 'created_at')
    search_fields = ('title', 'course__title', 'teacher__user__username')
    readonly_fields = ('assigned_date', 'created_at', 'updated_at')

@admin.register(AssignmentSubmission)
class AssignmentSubmissionAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'student', 'status', 'points_earned', 'submitted_at', 'graded_at')
    list_filter = ('status', 'submitted_at', 'graded_at')
    search_fields = ('assignment__title', 'student__user__username')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(CourseAnnouncement)
class CourseAnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'teacher', 'is_important', 'created_at')
    list_filter = ('is_important', 'created_at')
    search_fields = ('title', 'course__title', 'teacher__user__username')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(StudentProgress)
class StudentProgressAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'progress_percentage', 'last_accessed')
    list_filter = ('course', 'last_accessed', 'created_at')
    search_fields = ('student__user__username', 'course__title')
    readonly_fields = ('created_at', 'updated_at')

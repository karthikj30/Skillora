from django.contrib import admin
from .models import Course, Instructor, Job, Testimonial, TeamMember, Contact, UserProfile

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
    list_display = ('user', 'phone', 'skills')
    search_fields = ('user__username', 'user__email', 'skills')

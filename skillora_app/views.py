from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from django.utils.crypto import get_random_string
import json
from .models import (Course, Instructor, Job, JobApplication, Testimonial, TeamMember, Contact, UserProfile, 
                     Student, Teacher, Company, Internship, InternshipApplication, StudentProfile, 
                     InternshipFeedback, Notification, CourseMaterial, 
                     Assignment, AssignmentSubmission, CourseAnnouncement, StudentProgress, ScheduledClass,
                     ExcelUpload, AIVerification, Report, PlacementRecord, DashboardStats, DepartmentStats,
                     Cart, Payment, Enrollment)
from .forms import (ContactForm, UserRegistrationForm, StudentProfileForm, TeacherProfileForm, 
                    CompanyProfileForm, UserProfileForm, CourseMaterialForm, AssignmentForm, 
                    CourseAnnouncementForm, AssignmentSubmissionForm, GradeSubmissionForm, JobForm)
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Q, Count, Avg, Max
from django.db import models
import re

def home(request):
    """Home page view - redirects based on user role"""
    if request.user.is_authenticated:
            try:
                profile = UserProfile.objects.get(user=request.user)
                if profile.role == 'teacher':
                    return redirect('teacher_home')
                elif profile.role == 'company':
                    return redirect('company_home')
                else:
                    # Student - go to student dashboard
                    return redirect('student_home')
            except UserProfile.DoesNotExist:
                # No profile - show public landing
                courses = Course.objects.all()[:6]
                testimonials = Testimonial.objects.all()[:4]
                context = {
                    'courses': courses,
                    'testimonials': testimonials,
                    'user_role': None,
                }
                return render(request, 'index.html', context)
    else:
        # Not logged in - show public landing
        courses = Course.objects.all()[:6]
        testimonials = Testimonial.objects.all()[:4]
        context = {
            'courses': courses,
            'testimonials': testimonials,
            'user_role': None,
        }
        return render(request, 'index.html', context)

def student_home(request):
    """Student dashboard view. Falls back to landing when not authenticated."""
    if not request.user.is_authenticated:
        courses = Course.objects.all()[:6]
        testimonials = Testimonial.objects.all()[:4]
        context = {
            'courses': courses,
            'testimonials': testimonials,
            'user_role': None,
        }
        return render(request, 'index.html', context)

    # Ensure the user has a student profile
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user, role='student')

    if profile.role != 'student':
        return redirect('home')

    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        student = Student.objects.create(user=request.user)

    enrolled_courses = student.courses_enrolled.all()
    # Also get courses from new Enrollment model
    enrollment_courses = Course.objects.filter(enrollments__user=request.user, enrollments__is_active=True)
    # Combine both sources
    all_enrolled_courses = enrolled_courses.union(enrollment_courses)
    
    # Get progress for each course using StudentProgress model
    progress_map = {}
    progress_values = []
    course_progress_data = []
    
    for course in all_enrolled_courses:
        try:
            progress = StudentProgress.objects.get(student=student, course=course)
            progress.update_progress()  # Recalculate progress
            progress_percentage = float(progress.progress_percentage)
        except StudentProgress.DoesNotExist:
            progress = StudentProgress.objects.create(student=student, course=course)
            progress.update_progress()
            progress_percentage = 0.0
        
        progress_map[str(course.id)] = progress_percentage
        progress_values.append(progress_percentage)
        course_progress_data.append({
            'course': course,
            'progress': progress,
            'progress_percentage': progress_percentage,
        })
    
    # Calculate average progress
    avg_progress = round(sum(progress_values) / len(progress_values), 2) if progress_values else 0.0
    completed_courses = sum(1 for pct in progress_values if pct >= 100)
    completed_courses_qs = Course.objects.filter(
        id__in=[c['course'].id for c in course_progress_data if c['progress_percentage'] >= 100]
    )

    recommended_courses = Course.objects.exclude(id__in=all_enrolled_courses.values_list('id', flat=True))[:6]

    # Fetch student's job applications
    job_applications = []
    try:
        job_applications = JobApplication.objects.filter(user=request.user).select_related('job').order_by('-applied_date')
    except Exception:
        job_applications = []

    context = {
        'user_role': 'student',
        'student': student,
        'enrolled_courses': all_enrolled_courses,
        'course_progress_data': course_progress_data,
        'recommended_courses': recommended_courses,
        'total_enrolled': all_enrolled_courses.count(),
        'completed_courses': completed_courses,
        'avg_progress': avg_progress,
        'progress_map': progress_map,
        'progress_map_json': json.dumps(progress_map or {}),
        'completed_courses_list': completed_courses_qs,
        'job_applications': job_applications,
    }
    return render(request, 'student_home.html', context)

@login_required
def student_toggle_save(request, course_id):
    try:
        course = Course.objects.get(id=course_id)
        student = Student.objects.get(user=request.user)
        if course in student.saved_courses.all():
            student.saved_courses.remove(course)
            messages.success(request, 'Removed from saved courses.')
        else:
            student.saved_courses.add(course)
            messages.success(request, 'Saved course!')
    except (Course.DoesNotExist, Student.DoesNotExist):
        messages.error(request, 'Unable to update saved courses.')
    return redirect('student_home')

@login_required
def student_certificate(request, course_id):
    try:
        course = Course.objects.get(id=course_id)
        student = Student.objects.get(user=request.user)
    except (Course.DoesNotExist, Student.DoesNotExist):
        messages.error(request, 'Certificate not available.')
        return redirect('student_home')

    # Use the canonical StudentProgress model to determine completion
    try:
        progress_obj = StudentProgress.objects.get(student=student, course=course)
        # Ensure progress is up to date
        progress_obj.update_progress()
        pct = float(progress_obj.progress_percentage)
    except StudentProgress.DoesNotExist:
        # If no progress record exists, treat as not completed
        pct = 0.0
    if pct < 100:
        messages.error(request, 'Complete the course to view certificate.')
        return redirect('student_home')

    context = {
        'student': student,
        'course': course,
        'issued_on': student.enrollment_date.date(),
    }
    # Ensure a persistent Certificate object exists so it appears in the list page
    try:
        from .models import Certificate
        cert, _ = Certificate.objects.get_or_create(
            user=request.user,
            course=course,
            defaults={'certificate_id': get_random_string(16)}
        )
        context['certificate_id'] = cert.certificate_id
    except Exception:
        # Non-fatal: render on-screen certificate even if persistence fails
        pass
    return render(request, 'student_certificate.html', context)

@login_required
def teacher_home(request):
    """Teacher home page view"""
    try:
        teacher = Teacher.objects.get(user=request.user)
        courses_created = Course.objects.filter(instructor=teacher).order_by('-created_at')
        teacher.update_stats() # Call to update teacher stats
        
        # Get recent activities
        recent_materials = CourseMaterial.objects.filter(teacher=teacher).order_by('-created_at')[:5]
        recent_assignments = Assignment.objects.filter(teacher=teacher).order_by('-created_at')[:5]
        recent_submissions = AssignmentSubmission.objects.filter(
            assignment__teacher=teacher,
            status='submitted'
        ).order_by('-submitted_at')[:5]
        
        # Get pending grading count
        pending_grading = AssignmentSubmission.objects.filter(
            assignment__teacher=teacher,
            status='submitted'
        ).count()
        
        # Get total materials and assignments count
        total_materials = CourseMaterial.objects.filter(teacher=teacher).count()
        total_assignments = Assignment.objects.filter(teacher=teacher).count()
        
        # Get all materials and assignments for view/delete
        all_materials = CourseMaterial.objects.filter(teacher=teacher).order_by('-created_at')
        all_assignments = Assignment.objects.filter(teacher=teacher).order_by('-created_at')
        
        # Calculate actual total students enrolled across all courses and per-course counts
        all_students_set = set()
        courses_with_student_counts = []
        for course in courses_created:
            # Get students from both enrollment methods
            enrolled_students_m2m = course.students_enrolled.all()
            enrollments = Enrollment.objects.filter(course=course, is_active=True)
            enrolled_users = [e.user for e in enrollments]
            enrolled_students_from_enrollment = Student.objects.filter(user__in=enrolled_users)
            enrolled_students = enrolled_students_m2m.union(enrolled_students_from_enrollment)
            all_students_set.update(enrolled_students)
            
            # Store course with its student count
            courses_with_student_counts.append({
                'course': course,
                'student_count': enrolled_students.count(),
            })
        
        actual_total_students = len(all_students_set)
        
        # Get user profile for profile picture
        try:
            user_profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            user_profile = None
        
        context = {
            'teacher': teacher,
            'user_profile': user_profile,
            'courses_created': courses_created,
            'courses_with_student_counts': courses_with_student_counts,
            'recent_materials': recent_materials,
            'recent_assignments': recent_assignments,
            'recent_submissions': recent_submissions,
            'pending_grading': pending_grading,
            'total_materials': total_materials,
            'total_assignments': total_assignments,
            'all_materials': all_materials,
            'all_assignments': all_assignments,
            'actual_total_students': actual_total_students,
            'user_role': 'teacher',
        }
        return render(request, 'teacher_home.html', context)
    except Teacher.DoesNotExist:
        messages.error(request, 'Teacher profile not found.')
        return redirect('home')

@login_required
def teacher_courses(request):
    """Teacher courses management view"""
    try:
        teacher = Teacher.objects.get(user=request.user)
        courses = Course.objects.filter(instructor=teacher).order_by('-created_at')
        teacher.update_stats()
        context = {
            'teacher': teacher,
            'courses': courses,
            'user_role': 'teacher',
        }
        return render(request, 'teacher_courses.html', context)
    except Teacher.DoesNotExist:
        messages.error(request, 'Teacher profile not found.')
        return redirect('home')

@login_required
def teacher_assignments(request):
    """Teacher assignments management view"""
    try:
        teacher = Teacher.objects.get(user=request.user)
        teacher.update_stats()
        
        # Get all assignments from teacher's courses
        teacher_courses = Course.objects.filter(instructor=teacher)
        assignments = Assignment.objects.filter(course__in=teacher_courses).order_by('-created_at')
        
        # Calculate statistics
        total_assignments = assignments.count()
        active_assignments = assignments.filter(is_published=True).count()
        pending_submissions = AssignmentSubmission.objects.filter(
            assignment__course__in=teacher_courses,
            status='submitted'
        ).count()
        graded_submissions = AssignmentSubmission.objects.filter(
            assignment__course__in=teacher_courses,
            status='graded'
        ).count()
        
        # Get assignments with submission details
        assignments_with_submissions = []
        for assignment in assignments:
            submissions = AssignmentSubmission.objects.filter(assignment=assignment)
            pending_count = submissions.filter(status='submitted').count()
            graded_count = submissions.filter(status='graded').count()
            total_submissions = submissions.count()
            
            assignments_with_submissions.append({
                'assignment': assignment,
                'submissions': submissions.order_by('-submitted_at')[:5],  # Recent 5 submissions
                'total_submissions': total_submissions,
                'pending_count': pending_count,
                'graded_count': graded_count,
            })
        
        context = {
            'teacher': teacher,
            'assignments': assignments,
            'assignments_with_submissions': assignments_with_submissions,
            'teacher_courses': teacher_courses,
            'total_assignments': total_assignments,
            'active_assignments': active_assignments,
            'pending_submissions': pending_submissions,
            'graded_submissions': graded_submissions,
            'user_role': 'teacher',
        }
        return render(request, 'teacher_assignments.html', context)
    except Teacher.DoesNotExist:
        messages.error(request, 'Teacher profile not found.')
        return redirect('home')

@login_required
def teacher_announcements(request):
    """Teacher announcements management view"""
    try:
        teacher = Teacher.objects.get(user=request.user)
        teacher.update_stats()
        
        # Get all announcements from teacher's courses
        teacher_courses = Course.objects.filter(instructor=teacher).order_by('-created_at')
        announcements = CourseAnnouncement.objects.filter(course__in=teacher_courses).order_by('-created_at')
        
        # Calculate statistics
        total_announcements = announcements.count()
        active_announcements = announcements.count()  # All announcements are considered active
        important_announcements = announcements.filter(is_important=True).count()
        recent_announcements = announcements.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        ).count()
        
        context = {
            'teacher': teacher,
            'announcements': announcements,
            'teacher_courses': teacher_courses,
            'total_announcements': total_announcements,
            'active_announcements': active_announcements,
            'important_announcements': important_announcements,
            'recent_announcements': recent_announcements,
            'user_role': 'teacher',
        }
        return render(request, 'teacher_announcements.html', context)
    except Teacher.DoesNotExist:
        messages.error(request, 'Teacher profile not found.')
        return redirect('home')

@login_required
def edit_course(request, course_id):
    """Edit course view"""
    try:
        teacher = Teacher.objects.get(user=request.user)
        course = Course.objects.get(id=course_id, instructor=teacher)
        
        if request.method == 'POST':
            # Update course with new data
            course.title = request.POST.get('title', course.title)
            course.description = request.POST.get('description', course.description)
            
            # Convert price to Decimal (handle text input)
            from decimal import Decimal, InvalidOperation
            price_text = request.POST.get('price', str(course.price))
            try:
                course.price = Decimal(str(price_text))
            except (InvalidOperation, ValueError):
                messages.error(request, 'Invalid price format. Please enter a valid number.')
                context = {
                    'teacher': teacher,
                    'course': course,
                    'user_role': 'teacher',
                }
                return render(request, 'edit_course.html', context)
            
            course.duration = request.POST.get('duration', course.duration)
            course.level = request.POST.get('level', request.POST.get('difficulty_level', course.level))
            course.category = request.POST.get('category', course.category)
            
            # Update new fields
            course.skills = request.POST.get('skills', course.skills)
            course.syllabus = request.POST.get('syllabus', course.syllabus)
            lectures = request.POST.get('lectures', '0')
            course.lectures = int(lectures) if lectures.isdigit() else course.lectures
            course.language = request.POST.get('language', course.language)
            course.deadline = request.POST.get('deadline', course.deadline)
            certificate = request.POST.get('certificate', 'true')
            course.certificate = certificate == 'true'
            course.additional_info = request.POST.get('additional_info', course.additional_info)
            
            # Handle image upload
            if 'image' in request.FILES:
                course.image = request.FILES['image']
            
            course.save()
            messages.success(request, 'Course updated successfully!')
            return redirect('teacher_courses')
        
        context = {
            'teacher': teacher,
            'course': course,
            'user_role': 'teacher',
        }
        return render(request, 'edit_course.html', context)
    except Teacher.DoesNotExist:
        messages.error(request, 'Teacher profile not found.')
        return redirect('home')
    except Course.DoesNotExist:
        messages.error(request, 'Course not found.')
        return redirect('teacher_courses')

@login_required
def teacher_students(request):
    try:
        teacher = Teacher.objects.get(user=request.user)
        teacher.update_stats()
        
        # Get all courses taught by the teacher
        teacher_courses = Course.objects.filter(instructor=teacher).order_by('-created_at')
        
        # Get course filter from request (optional)
        selected_course_id = request.GET.get('course', None)
        
        # Group students by course
        courses_with_students = []
        all_students = set()
        
        for course in teacher_courses:
            # Get students from both enrollment methods
            # Method 1: Direct ManyToMany relationship
            enrolled_students_m2m = course.students_enrolled.all()
            
            # Method 2: From Enrollment model
            enrollments = Enrollment.objects.filter(course=course, is_active=True)
            enrolled_users = [e.user for e in enrollments]
            enrolled_students_from_enrollment = Student.objects.filter(user__in=enrolled_users)
            
            # Combine both sources
            enrolled_students = enrolled_students_m2m.union(enrolled_students_from_enrollment)
            all_students.update(enrolled_students)
            
            # Get progress for each student in this course
            students_with_progress = []
            for student in enrolled_students:
                try:
                    progress = StudentProgress.objects.get(student=student, course=course)
                    progress_percentage = progress.progress_percentage
                except StudentProgress.DoesNotExist:
                    progress_percentage = 0.0
                
                students_with_progress.append({
                    'student': student,
                    'progress_percentage': progress_percentage,
                })
            
            courses_with_students.append({
                'course': course,
                'students': enrolled_students,
                'students_with_progress': students_with_progress,
                'student_count': enrolled_students.count(),
            })
        
        # If a specific course is selected, filter to show only that course
        if selected_course_id:
            courses_with_students = [
                item for item in courses_with_students 
                if item['course'].id == int(selected_course_id)
            ]
        
        context = {
            'teacher': teacher,
            'courses_with_students': courses_with_students,
            'teacher_courses': teacher_courses,
            'selected_course_id': selected_course_id,
            'total_students_count': len(all_students),
            'user_role': 'teacher',
        }
        return render(request, 'teacher_students.html', context)
    except Teacher.DoesNotExist:
        messages.error(request, 'Teacher profile not found.')
        return redirect('home')

@login_required
def student_progress_analytics(request):
    """Detailed student progress analytics view with per-student and per-course breakdown"""
    try:
        teacher = Teacher.objects.get(user=request.user)
        teacher_courses = Course.objects.filter(instructor=teacher).order_by('-created_at')
        
        # Get course filter from request
        selected_course_id = request.GET.get('course', None)
        
        # Build comprehensive analytics data
        courses_analytics = []
        all_students_data = {}
        
        for course in teacher_courses:
            if selected_course_id and course.id != int(selected_course_id):
                continue
                
            # Get enrolled students
            enrolled_students_m2m = course.students_enrolled.all()
            enrollments = Enrollment.objects.filter(course=course, is_active=True)
            enrolled_users = [e.user for e in enrollments]
            enrolled_students_from_enrollment = Student.objects.filter(user__in=enrolled_users)
            enrolled_students = enrolled_students_m2m.union(enrolled_students_from_enrollment)
            
            # Get course materials and assignments
            course_materials = course.materials.filter(is_published=True)
            course_assignments = course.assignments.filter(is_published=True)
            
            # Student analytics for this course
            students_analytics = []
            for student in enrolled_students:
                # Get progress
                try:
                    progress = StudentProgress.objects.get(student=student, course=course)
                    progress.update_progress()  # Ensure it's up to date
                    progress_percentage = progress.progress_percentage
                    materials_viewed = progress.materials_viewed.count()
                    assignments_completed = progress.assignments_completed.count()
                except StudentProgress.DoesNotExist:
                    progress = None
                    progress_percentage = 0.0
                    materials_viewed = 0
                    assignments_completed = 0
                
                # Get assignment submissions with grades
                submissions = AssignmentSubmission.objects.filter(
                    assignment__course=course,
                    student=student
                ).select_related('assignment')
                
                assignment_data = []
                total_points_earned = 0
                total_points_possible = 0
                
                for submission in submissions:
                    assignment = submission.assignment
                    points_earned = submission.points_earned if submission.points_earned is not None else 0
                    max_points = assignment.max_points
                    grade_percentage = (points_earned / max_points * 100) if max_points > 0 else 0
                    
                    assignment_data.append({
                        'assignment': assignment,
                        'submission': submission,
                        'points_earned': points_earned,
                        'max_points': max_points,
                        'grade_percentage': grade_percentage,
                        'status': submission.get_status_display(),
                    })
                    
                    total_points_earned += points_earned
                    total_points_possible += max_points
                
                overall_grade = (total_points_earned / total_points_possible * 100) if total_points_possible > 0 else 0
                
                student_data = {
                    'student': student,
                    'progress': progress,
                    'progress_percentage': progress_percentage,
                    'materials_viewed': materials_viewed,
                    'total_materials': course_materials.count(),
                    'assignments_completed': assignments_completed,
                    'total_assignments': course_assignments.count(),
                    'assignments': assignment_data,
                    'total_points_earned': total_points_earned,
                    'total_points_possible': total_points_possible,
                    'overall_grade': overall_grade,
                }
                
                students_analytics.append(student_data)
                
                # Aggregate data for all students view
                student_key = student.id
                if student_key not in all_students_data:
                    all_students_data[student_key] = {
                        'student': student,
                        'courses': [],
                        'total_progress': 0,
                        'course_count': 0,
                    }
                
                all_students_data[student_key]['courses'].append({
                    'course': course,
                    'progress_percentage': progress_percentage,
                    'overall_grade': overall_grade,
                })
                all_students_data[student_key]['total_progress'] += progress_percentage
                all_students_data[student_key]['course_count'] += 1
            
            # Calculate average progress for this course
            avg_progress = sum(s['progress_percentage'] for s in students_analytics) / len(students_analytics) if students_analytics else 0
            
            courses_analytics.append({
                'course': course,
                'students_count': enrolled_students.count(),
                'students_analytics': students_analytics,
                'avg_progress': avg_progress,
                'total_materials': course_materials.count(),
                'total_assignments': course_assignments.count(),
            })
        
        # Calculate overall averages for all students
        for student_key, student_info in all_students_data.items():
            if student_info['course_count'] > 0:
                student_info['avg_progress'] = student_info['total_progress'] / student_info['course_count']
            else:
                student_info['avg_progress'] = 0
        
        # Calculate overall average progress across all courses
        overall_avg_progress = 0
        total_assignments_count = 0
        if courses_analytics:
            total_avg = sum(course_data['avg_progress'] for course_data in courses_analytics)
            overall_avg_progress = total_avg / len(courses_analytics) if courses_analytics else 0
            total_assignments_count = sum(course_data['total_assignments'] for course_data in courses_analytics)
        
        context = {
            'teacher': teacher,
            'courses_analytics': courses_analytics,
            'all_students_data': list(all_students_data.values()),
            'teacher_courses': teacher_courses,
            'selected_course_id': selected_course_id,
            'overall_avg_progress': overall_avg_progress,
            'total_assignments_count': total_assignments_count,
            'user_role': 'teacher',
        }
        return render(request, 'teacher/student_progress_analytics.html', context)
    except Teacher.DoesNotExist:
        messages.error(request, 'Teacher profile not found.')
        return redirect('home')

@login_required
def teacher_payments(request):
    """Teacher payments view"""
    try:
        teacher = Teacher.objects.get(user=request.user)
        # Get payments for courses created by this teacher
        teacher_courses = Course.objects.filter(instructor=teacher)
        
        # Get all payments for these courses
        payments_list = []
        for course in teacher_courses:
            enrollments = Enrollment.objects.filter(course=course, payment__isnull=False).select_related('payment', 'user')
            for enrollment in enrollments:
                payment = enrollment.payment
                payments_list.append({
                    'id': payment.id,
                    'payment_id': payment.payment_id,
                    'course': course.title,
                    'student': enrollment.user.get_full_name() or enrollment.user.username,
                    'amount': float(payment.amount),
                    'date': payment.created_at.strftime('%Y-%m-%d'),
                    'status': payment.get_status_display(),
                    'status_code': payment.status,
                })
        
        # If no payments, use sample data for demo
        if not payments_list:
            payments_list = [
                {'id': 1, 'payment_id': 'PAY001', 'course': 'React for Beginners', 'student': 'John Doe', 'amount': 99.99, 'date': '2024-01-15', 'status': 'Completed', 'status_code': 'completed'},
                {'id': 2, 'payment_id': 'PAY002', 'course': 'JavaScript Essentials', 'student': 'Jane Smith', 'amount': 79.99, 'date': '2024-01-14', 'status': 'Completed', 'status_code': 'completed'},
                {'id': 3, 'payment_id': 'PAY003', 'course': 'CSS for Styling', 'student': 'Mike Johnson', 'amount': 59.99, 'date': '2024-01-13', 'status': 'Pending', 'status_code': 'pending'},
            ]
        
        # Calculate summary statistics from payments
        total_earnings = sum(float(p['amount']) for p in payments_list if p['status_code'] == 'completed')
        completed_payments = sum(1 for p in payments_list if p['status_code'] == 'completed')
        pending_payments = sum(1 for p in payments_list if p['status_code'] == 'pending')
        
        # Calculate this month's payments and earnings
        from datetime import datetime
        current_month = datetime.now().month
        current_year = datetime.now().year
        this_month_payments = [p for p in payments_list 
                              if datetime.strptime(p['date'], '%Y-%m-%d').month == current_month 
                              and datetime.strptime(p['date'], '%Y-%m-%d').year == current_year]
        this_month_count = len(this_month_payments)
        this_month_earnings = sum(float(p['amount']) for p in this_month_payments if p['status_code'] == 'completed')
        
        # Calculate monthly breakdown
        monthly_breakdown = {}
        month_names = ['January', 'February', 'March', 'April', 'May', 'June', 
                       'July', 'August', 'September', 'October', 'November', 'December']
        
        for payment in payments_list:
            try:
                payment_date = datetime.strptime(payment['date'], '%Y-%m-%d')
                month_name = month_names[payment_date.month - 1]
                if month_name not in monthly_breakdown:
                    monthly_breakdown[month_name] = 0.0
                if payment['status_code'] == 'completed':
                    monthly_breakdown[month_name] += float(payment['amount'])
            except Exception:
                continue
        
        # Ensure all months show at least $0.00
        for month in month_names[:3]:  # Show first 3 months as in template
            if month not in monthly_breakdown:
                monthly_breakdown[month] = 0.0
        
        context = {
            'teacher': teacher,
            'payments': payments_list,
            'user_role': 'teacher',
            'total_earnings': round(total_earnings, 2),
            'completed_payments': completed_payments,
            'pending_payments': pending_payments,
            'this_month': this_month_count,
            'this_month_earnings': round(this_month_earnings, 2),
            'monthly_breakdown': monthly_breakdown,
        }
        return render(request, 'teacher_payments.html', context)
    except Teacher.DoesNotExist:
        messages.error(request, 'Teacher profile not found.')
        return redirect('home')

@login_required
def approve_payment(request, payment_id):
    """Approve a pending payment"""
    try:
        teacher = Teacher.objects.get(user=request.user)
        payment = Payment.objects.get(payment_id=payment_id)
        
        # Verify this payment is for a course created by this teacher
        teacher_courses = Course.objects.filter(instructor=teacher)
        payment_courses = payment.courses.all()
        
        if not any(course in teacher_courses for course in payment_courses):
            messages.error(request, 'You do not have permission to approve this payment.')
            return redirect('teacher_payments')
        
        if payment.status == 'pending':
            payment.status = 'completed'
            payment.completed_at = timezone.now()
            payment.save()
            messages.success(request, f'Payment {payment_id} approved successfully!')
        else:
            messages.warning(request, f'Payment {payment_id} is already {payment.get_status_display()}.')
        
        return redirect('teacher_payments')
    except (Teacher.DoesNotExist, Payment.DoesNotExist):
        messages.error(request, 'Payment not found.')
        return redirect('teacher_payments')

@login_required
def export_payments_pdf(request):
    """Export payment history to PDF"""
    try:
        from io import BytesIO
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from django.http import HttpResponse
        
        teacher = Teacher.objects.get(user=request.user)
        teacher_courses = Course.objects.filter(instructor=teacher)
        
        # Get all payments
        payments_list = []
        for course in teacher_courses:
            enrollments = Enrollment.objects.filter(course=course, payment__isnull=False).select_related('payment', 'user')
            for enrollment in enrollments:
                payment = enrollment.payment
                payments_list.append({
                    'course': course.title,
                    'student': enrollment.user.get_full_name() or enrollment.user.username,
                    'amount': float(payment.amount),
                    'date': payment.created_at.strftime('%Y-%m-%d'),
                    'status': payment.get_status_display(),
                })
        
        # If no payments, use sample data
        if not payments_list:
            payments_list = [
                {'course': 'React for Beginners', 'student': 'John Doe', 'amount': 99.99, 'date': '2024-01-15', 'status': 'Completed'},
                {'course': 'JavaScript Essentials', 'student': 'Jane Smith', 'amount': 79.99, 'date': '2024-01-14', 'status': 'Completed'},
                {'course': 'CSS for Styling', 'student': 'Mike Johnson', 'amount': 59.99, 'date': '2024-01-13', 'status': 'Pending'},
            ]
        
        # Create PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#fb873f'),
            spaceAfter=30,
        )
        
        # Title
        title = Paragraph("Payment History Report", title_style)
        elements.append(title)
        
        # Teacher info
        teacher_info = Paragraph(f"<b>Teacher:</b> {teacher.user.get_full_name() or teacher.user.username}<br/>"
                                 f"<b>Generated:</b> {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}", 
                                 styles['Normal'])
        elements.append(teacher_info)
        elements.append(Spacer(1, 0.3*inch))
        
        # Summary
        total_earnings = sum(float(p['amount']) for p in payments_list if p['status'] == 'Completed')
        completed = sum(1 for p in payments_list if p['status'] == 'Completed')
        pending = sum(1 for p in payments_list if p['status'] == 'Pending')
        
        summary_data = [
            ['Total Earnings', f"${total_earnings:.2f}"],
            ['Completed Payments', str(completed)],
            ['Pending Payments', str(pending)],
        ]
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Payments table
        table_data = [['Course', 'Student', 'Amount', 'Date', 'Status']]
        for payment in payments_list:
            table_data.append([
                payment['course'],
                payment['student'],
                f"${payment['amount']:.2f}",
                payment['date'],
                payment['status'],
            ])
        
        payments_table = Table(table_data, colWidths=[2*inch, 1.5*inch, 1*inch, 1*inch, 1*inch])
        payments_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        elements.append(payments_table)
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        
        # Create response
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="payment_history_{timezone.now().strftime("%Y%m%d")}.pdf"'
        return response
        
    except Teacher.DoesNotExist:
        messages.error(request, 'Teacher profile not found.')
        return redirect('teacher_payments')
    except ImportError:
        messages.error(request, 'PDF library not installed. Please install reportlab: pip install reportlab')
        return redirect('teacher_payments')

@login_required
def payment_analytics(request):
    """Payment analytics view"""
    try:
        teacher = Teacher.objects.get(user=request.user)
        teacher_courses = Course.objects.filter(instructor=teacher)
        
        # Get all payments
        payments_list = []
        for course in teacher_courses:
            enrollments = Enrollment.objects.filter(course=course, payment__isnull=False).select_related('payment', 'user')
            for enrollment in enrollments:
                payment = enrollment.payment
                payments_list.append({
                    'course': course.title,
                    'student': enrollment.user.get_full_name() or enrollment.user.username,
                    'amount': float(payment.amount),
                    'date': payment.created_at,
                    'status': payment.get_status_display(),
                    'status_code': payment.status,
                })
        
        # If no payments, use sample data
        if not payments_list:
            from datetime import datetime
            payments_list = [
                {'course': 'React for Beginners', 'student': 'John Doe', 'amount': 99.99, 'date': datetime(2024, 1, 15), 'status': 'Completed', 'status_code': 'completed'},
                {'course': 'JavaScript Essentials', 'student': 'Jane Smith', 'amount': 79.99, 'date': datetime(2024, 1, 14), 'status': 'Completed', 'status_code': 'completed'},
                {'course': 'CSS for Styling', 'student': 'Mike Johnson', 'amount': 59.99, 'date': datetime(2024, 1, 13), 'status': 'Pending', 'status_code': 'pending'},
            ]
        
        # Calculate analytics
        from datetime import datetime, timedelta
        from collections import defaultdict
        
        total_earnings = sum(float(p['amount']) for p in payments_list if p['status_code'] == 'completed')
        completed_count = sum(1 for p in payments_list if p['status_code'] == 'completed')
        pending_count = sum(1 for p in payments_list if p['status_code'] == 'pending')
        
        # Monthly earnings
        monthly_earnings = defaultdict(float)
        month_names = ['January', 'February', 'March', 'April', 'May', 'June', 
                       'July', 'August', 'September', 'October', 'November', 'December']
        
        for payment in payments_list:
            if payment['status_code'] == 'completed':
                if isinstance(payment['date'], str):
                    payment_date = datetime.strptime(payment['date'], '%Y-%m-%d')
                else:
                    payment_date = payment['date']
                month_name = month_names[payment_date.month - 1]
                monthly_earnings[month_name] += payment['amount']
        
        # Course-wise earnings
        course_earnings = defaultdict(float)
        for payment in payments_list:
            if payment['status_code'] == 'completed':
                course_earnings[payment['course']] += payment['amount']
        
        # Last 30 days earnings
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_earnings = sum(float(p['amount']) for p in payments_list 
                             if p['status_code'] == 'completed' 
                             and (p['date'] if isinstance(p['date'], datetime) else datetime.strptime(p['date'], '%Y-%m-%d')) >= thirty_days_ago)
        
        context = {
            'teacher': teacher,
            'total_earnings': round(total_earnings, 2),
            'completed_count': completed_count,
            'pending_count': pending_count,
            'recent_earnings': round(recent_earnings, 2),
            'monthly_earnings': dict(monthly_earnings),
            'course_earnings': dict(course_earnings),
            'month_names': month_names,
        }
        return render(request, 'payment_analytics.html', context)
    except Teacher.DoesNotExist:
        messages.error(request, 'Teacher profile not found.')
        return redirect('teacher_payments')

@login_required
def create_course(request):
    """Create new course view"""
    if request.method == 'POST':
        # Handle course creation
        title = request.POST.get('title')
        description = request.POST.get('description')
        category = request.POST.get('category')
        price = request.POST.get('price')
        duration = request.POST.get('duration')
        level = request.POST.get('level')
        
        # New fields
        skills = request.POST.get('skills', '')
        syllabus = request.POST.get('syllabus', '')
        lectures = request.POST.get('lectures', '0')
        language = request.POST.get('language', 'English')
        deadline = request.POST.get('deadline', 'Life Time')
        certificate = request.POST.get('certificate', 'true') == 'true'
        additional_info = request.POST.get('additional_info', '')
        
        # Handle image upload
        image = None
        if 'image' in request.FILES:
            image = request.FILES['image']
        
        if title and description and category and price:
            try:
                teacher = Teacher.objects.get(user=request.user)
                
                # Convert price to Decimal (handle text input like "0.02", "10.00", etc.)
                from decimal import Decimal, InvalidOperation
                try:
                    price_decimal = Decimal(str(price))
                except (InvalidOperation, ValueError):
                    messages.error(request, 'Invalid price format. Please enter a valid number.')
                    context = {'user_role': 'teacher'}
                    return render(request, 'create_course.html', context)
                
                # Create course data dictionary
                course_data = {
                    'title': title,
                    'description': description,
                    'category': category,
                    'price': price_decimal,
                    'duration': duration,
                    'level': level,
                    'instructor': teacher,
                    'skills': skills,
                    'syllabus': syllabus,
                    'lectures': int(lectures) if lectures.isdigit() else 0,
                    'language': language,
                    'deadline': deadline,
                    'certificate': certificate,
                    'additional_info': additional_info,
                }
                
                # Include image if provided
                if image:
                    course_data['image'] = image
                
                course = Course.objects.create(**course_data)
                
                # Update teacher stats after course creation
                teacher.update_stats()
                messages.success(request, 'Course created successfully!')
                return redirect('teacher_courses')
            except Exception as e:
                messages.error(request, f'Error creating course: {str(e)}')
        else:
            messages.error(request, 'Please fill in all required fields.')
    
    context = {
        'user_role': 'teacher',
    }
    return render(request, 'create_course.html', context)

@login_required
def company_home(request):
    """Company home page view"""
    try:
        company = Company.objects.get(user=request.user)
        jobs_posted = Job.objects.filter(company=company.company_name).order_by('-posted_date')
        
        # Fetch all job applications for jobs posted by this company
        job_applications = JobApplication.objects.filter(
            job__company=company.company_name
        ).select_related('job', 'user').order_by('-applied_date')
        
        # Group applications by company name
        applications_by_company = {}
        for app in job_applications:
            company_name = app.job.company
            if company_name not in applications_by_company:
                applications_by_company[company_name] = []
            applications_by_company[company_name].append(app)
        
        # Calculate application status counts
        total_applications = job_applications.count()
        accepted_applications = job_applications.filter(status='accepted').count()
        rejected_applications = job_applications.filter(status='rejected').count()
        pending_applications = job_applications.filter(status='pending').count()
        
        context = {
            'company': company,
            'jobs_posted': jobs_posted,
            'job_applications': job_applications,
            'applications_by_company': applications_by_company,
            'total_applications': total_applications,
            'accepted_applications': accepted_applications,
            'rejected_applications': rejected_applications,
            'pending_applications': pending_applications,
            'user_role': 'company',
        }
        return render(request, 'company_home.html', context)
    except Company.DoesNotExist:
        messages.error(request, 'Company profile not found.')
        return redirect('home')

@login_required
def post_job(request):
    """Company posts a new job"""
    try:
        company = Company.objects.get(user=request.user)
    except Company.DoesNotExist:
        messages.error(request, 'Company profile not found.')
        return redirect('home')

    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            # Ensure company field matches the current company name
            job.company = company.company_name
            job.save()
            messages.success(request, 'Job posted successfully!')
            return redirect('company_home')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        # Pre-fill company name
        form = JobForm(initial={'company': company.company_name})

    return render(request, 'company/post_job.html', { 'form': form, 'company': company, 'user_role': 'company' })

def about(request):
    """About page view"""
    team_members = TeamMember.objects.all()
    context = {
        'team_members': team_members,
    }
    return render(request, 'about.html', context)

def courses(request):
    """Courses page view"""
    courses = Course.objects.all()
    categories = Course.objects.values_list('category', flat=True).distinct()
    
    # Filter by category if provided
    category_filter = request.GET.get('category')
    if category_filter:
        courses = courses.filter(category=category_filter)
    
    context = {
        'courses': courses,
        'categories': categories,
        'selected_category': category_filter,
    }
    return render(request, 'courses.html', context)

def course_detail(request, course_id):
    """Single course detail page view"""
    try:
        course = Course.objects.get(id=course_id)
        related_courses = Course.objects.filter(category=course.category).exclude(id=course_id)[:3]
        
        # Populate default skills and syllabus if empty (and not teacher-created)
        if not course.instructor:
            from .course_utils import get_course_skills, get_course_syllabus
            
            if not course.skills:
                course.skills = get_course_skills(course.title)
                course.save(update_fields=['skills'])
            
            if not course.syllabus:
                course.syllabus = get_course_syllabus(course.title)
                course.save(update_fields=['syllabus'])
    except Course.DoesNotExist:
        messages.error(request, 'Course not found.')
        return redirect('courses')
    
    context = {
        'course': course,
        'related_courses': related_courses,
    }
    return render(request, 'single.html', context)

def instructors(request):
    """Instructors page view"""
    instructors = Instructor.objects.all()
    context = {
        'instructors': instructors,
    }
    return render(request, 'instructor.html', context)

def jobs(request):
    """Jobs page view"""
    jobs = Job.objects.all().order_by('-posted_date')
    
    # Get filter parameters
    keyword = request.GET.get('keyword', '').strip()
    location_filter = request.GET.get('location', '')
    job_type_filter = request.GET.get('job_type', '')
    
    # Apply filters
    if keyword:
        jobs = jobs.filter(
            Q(title__icontains=keyword) |
            Q(description__icontains=keyword) |
            Q(company__icontains=keyword)
        )
    
    if location_filter and location_filter != 'Location':
        jobs = jobs.filter(location__icontains=location_filter)
    
    if job_type_filter and job_type_filter != 'Experience Level':
        jobs = jobs.filter(job_type__icontains=job_type_filter)
    
    # Get unique locations and job types for filters
    locations = Job.objects.values_list('location', flat=True).distinct()
    job_types = Job.objects.values_list('job_type', flat=True).distinct()
    
    context = {
        'jobs': jobs,
        'keyword': keyword,
        'location_filter': location_filter,
        'job_type_filter': job_type_filter,
        'locations': locations,
        'job_types': job_types,
    }
    return render(request, 'jobs.html', context)

def career_paths(request):
    """Career paths page view"""
    return render(request, 'career-paths.html')

def team(request):
    """Team page view"""
    team_members = TeamMember.objects.all()
    context = {
        'team_members': team_members,
    }
    return render(request, 'team.html', context)

def testimonials(request):
    """Testimonials page view"""
    testimonials = Testimonial.objects.all().order_by('-created_at')
    context = {
        'testimonials': testimonials,
    }
    return render(request, 'testimonial.html', context)

def contact(request):
    """Contact page view"""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your message has been sent successfully!')
            return redirect('contact')
    else:
        form = ContactForm()
    
    context = {
        'form': form,
    }
    return render(request, 'contact.html', context)

def user_login(request):
    """User login view"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            
            # Redirect based on user role
            try:
                profile = UserProfile.objects.get(user=user)
                if profile.role == 'teacher':
                    return redirect('teacher_home')
                elif profile.role == 'company':
                    return redirect('company_home')
                else:
                    return redirect('home')
            except UserProfile.DoesNotExist:
                return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'login.html')

def user_logout(request):
    """User logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')

def user_signup(request):
    """User registration view"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                role = form.cleaned_data['role']
                
                # Create user profile with role
                user_profile = UserProfile.objects.create(user=user, role=role)
                
                # Create role-specific profile with initial data
                if role == 'student':
                    Student.objects.create(user=user)
                elif role == 'teacher':
                    # Create teacher with initial data
                    teacher = Teacher.objects.create(
                        user=user,
                        specialization="Web Development",  # Default specialization
                        experience_years=0,
                        bio="Welcome to Skillora! I'm a new teacher ready to share knowledge.",
                        rating=0.00,
                        is_verified=False,
                        total_students=0,
                        total_courses=0,
                        upcoming_classes=0,
                        student_progress_avg=0.00
                    )
                    # Update the user's first name and last name to the teacher profile
                    if user.first_name and user.last_name:
                        teacher.bio = f"Welcome to Skillora! I'm {user.first_name} {user.last_name}, a new teacher ready to share knowledge."
                        teacher.save()
                elif role == 'company':
                    Company.objects.create(
                        user=user,
                        company_name=user.username,
                        industry="Technology",
                        company_size="1-10"
                    )
                
                messages.success(request, f'Account created successfully as {role.title()}! Please log in.')
                return redirect('login')
            except Exception as e:
                messages.error(request, f'Error creating account: {str(e)}')
                # Delete the user if there was an error
                if 'user' in locals():
                    user.delete()
        else:
            # Form is not valid, show errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = UserRegistrationForm()
    
    context = {
        'form': form,
    }
    return render(request, 'signup.html', context)

@login_required
def profile(request):
    """User profile view"""
    try:
        profile = UserProfile.objects.get(user=request.user)
        
        # Get role-specific profile and form
        if profile.role == 'student':
            role_profile = Student.objects.get(user=request.user)
            profile_form = UserProfileForm(instance=profile)  # Use UserProfileForm for students
            # Compute completed courses for certificate section using StudentProgress
            try:
                completed_progress = StudentProgress.objects.filter(
                    student=role_profile,
                    progress_percentage__gte=100
                ).select_related('course')
                student_completed_courses = [p.course for p in completed_progress]
            except Exception:
                student_completed_courses = []
            
            # Get enrolled courses count (from both sources)
            enrolled_courses = role_profile.courses_enrolled.all()
            enrollment_courses = Course.objects.filter(enrollments__user=request.user, enrollments__is_active=True)
            all_enrolled_courses = enrolled_courses.union(enrollment_courses)
            enrolled_count = all_enrolled_courses.count()
        elif profile.role == 'teacher':
            role_profile = Teacher.objects.get(user=request.user)
            # Create a combined form approach - we'll handle both forms in POST
            profile_form = TeacherProfileForm(instance=role_profile)
            enrolled_count = 0
            student_completed_courses = None
        elif profile.role == 'company':
            role_profile = Company.objects.get(user=request.user)
            profile_form = CompanyProfileForm(instance=role_profile)
            enrolled_count = 0
            student_completed_courses = None
        else:
            role_profile = None
            profile_form = None
            student_completed_courses = None
            enrolled_count = 0
            
    except (UserProfile.DoesNotExist, Student.DoesNotExist, Teacher.DoesNotExist, Company.DoesNotExist):
        profile = UserProfile.objects.create(user=request.user, role='student')
        role_profile = Student.objects.create(user=request.user)
        profile_form = UserProfileForm(instance=profile)
        enrolled_count = 0
        student_completed_courses = []
    
    if request.method == 'POST':
        if profile.role == 'student':
            # Handle student profile update
            profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Profile updated successfully!')
                return redirect('profile')
        elif profile.role == 'teacher':
            # Handle teacher profile update - both Teacher and UserProfile
            teacher_form = TeacherProfileForm(request.POST, instance=role_profile)
            profile_picture_form = UserProfileForm(request.POST, request.FILES, instance=profile)
            
            # Update teacher-specific fields if form is valid
            if teacher_form.is_valid():
                teacher_form.save()
            
            # Update profile picture if provided
            if 'profile_picture' in request.FILES:
                if profile_picture_form.is_valid():
                    profile_picture_form.save()
            
            # Show success message
            if 'profile_picture' in request.FILES and not teacher_form.has_changed():
                messages.success(request, 'Profile picture updated successfully!')
            else:
                messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
        elif profile.role == 'company':
            profile_form = CompanyProfileForm(request.POST, instance=role_profile)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Profile updated successfully!')
                return redirect('profile')
    
    # Refresh profile and role_profile after potential updates
    profile.refresh_from_db()
    if profile.role == 'student':
        role_profile.refresh_from_db()
        # Recalculate enrolled count
        enrolled_courses = role_profile.courses_enrolled.all()
        enrollment_courses = Course.objects.filter(enrollments__user=request.user, enrollments__is_active=True)
        all_enrolled_courses = enrolled_courses.union(enrollment_courses)
        enrolled_count = all_enrolled_courses.count()
        # Recalculate completed courses
        try:
            completed_progress = StudentProgress.objects.filter(
                student=role_profile,
                progress_percentage__gte=100
            ).select_related('course')
            student_completed_courses = [p.course for p in completed_progress]
        except Exception:
            student_completed_courses = []
    elif profile.role == 'teacher':
        role_profile.refresh_from_db()
    
    context = {
        'profile': profile,
        'role_profile': role_profile,
        'profile_form': profile_form,
        'student_completed_courses': student_completed_courses if profile.role == 'student' else None,
        'enrolled_count': enrolled_count if profile.role == 'student' else 0,
    }
    return render(request, 'profile.html', context)

# Internship/Placement System Views

def calculate_match_score(student_profile, internship):
    """Calculate match score between student and internship (0-100)"""
    score = 0
    max_score = 100
    
    if not student_profile:
        return 0
    
    # Skills matching (40% weight)
    student_skills = set(skill.lower().strip() for skill in student_profile.get_skills_list())
    required_skills = set(skill.lower().strip() for skill in internship.get_required_skills_list())
    
    if required_skills:
        skills_match = len(student_skills.intersection(required_skills)) / len(required_skills)
        score += skills_match * 40
    else:
        score += 20  # No specific skills required
    
    # Location preference (20% weight)
    preferred_locations = set(loc.lower().strip() for loc in student_profile.get_preferred_locations_list())
    if preferred_locations:
        if internship.location.lower() in preferred_locations:
            score += 20
        elif any(loc in internship.location.lower() for loc in preferred_locations):
            score += 15
    else:
        score += 10  # No location preference
    
    # Industry preference (20% weight)
    preferred_industries = set(ind.lower().strip() for ind in student_profile.get_preferred_industries_list())
    if preferred_industries:
        if internship.company.industry.lower() in preferred_industries:
            score += 20
        elif any(ind in internship.company.industry.lower() for ind in preferred_industries):
            score += 15
    else:
        score += 10  # No industry preference
    
    # Internship type preference (10% weight)
    if student_profile.internship_preferences == internship.internship_type:
        score += 10
    elif student_profile.internship_preferences == 'internship' and internship.internship_type in ['internship', 'industrial_training']:
        score += 8
    
    # Placement potential (10% weight)
    if student_profile.is_placement_ready and internship.has_placement_potential:
        score += 10
    elif internship.has_placement_potential:
        score += 5
    
    return min(score, max_score)

def get_recommended_internships(student):
    """Get recommended internships for a student"""
    try:
        student_profile = student.placement_profile
    except StudentProfile.DoesNotExist:
        return Internship.objects.filter(status='published')[:5]
    
    # Get all published internships
    from django.db import models
    internships = Internship.objects.filter(
        status='published',
        application_deadline__gt=timezone.now(),
        seats_filled__lt=models.F('seats_available')
    ).exclude(
        applications__student=student  # Exclude already applied
    )
    
    # Calculate match scores
    internship_scores = []
    for internship in internships:
        score = calculate_match_score(student_profile, internship)
        internship_scores.append((internship, score))
    
    # Sort by score and return top matches
    internship_scores.sort(key=lambda x: x[1], reverse=True)
    return [internship for internship, score in internship_scores[:10]]

@login_required
def internships_list(request):
    """List all available internships with filtering and search"""
    internships = Internship.objects.filter(status='published').order_by('-created_at')
    
    # Filtering
    internship_type = request.GET.get('type')
    location = request.GET.get('location')
    company_industry = request.GET.get('industry')
    search = request.GET.get('search')
    
    if internship_type:
        internships = internships.filter(internship_type=internship_type)
    if location:
        internships = internships.filter(location__icontains=location)
    if company_industry:
        internships = internships.filter(company__industry__icontains=company_industry)
    if search:
        internships = internships.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(company__company_name__icontains=search) |
            Q(required_skills__icontains=search)
        )
    
    # Get filter options
    locations = Internship.objects.filter(status='published').values_list('location', flat=True).distinct()
    industries = Company.objects.values_list('industry', flat=True).distinct()
    
    # Get recommended internships for students
    recommended_internships = []
    if hasattr(request.user, 'student'):
        try:
            student = Student.objects.get(user=request.user)
            recommended_internships = get_recommended_internships(student)
        except Student.DoesNotExist:
            pass
    
    context = {
        'internships': internships,
        'recommended_internships': recommended_internships,
        'locations': locations,
        'industries': industries,
        'selected_type': internship_type,
        'selected_location': location,
        'selected_industry': company_industry,
        'search_query': search,
    }
    return render(request, 'internships/internships_list.html', context)

@login_required
def internship_detail(request, internship_id):
    """Internship detail view"""
    try:
        internship = Internship.objects.get(id=internship_id, status='published')
    except Internship.DoesNotExist:
        messages.error(request, 'Internship not found.')
        return redirect('internships_list')
    
    # Check if user already applied
    has_applied = False
    application = None
    if hasattr(request.user, 'student'):
        try:
            student = Student.objects.get(user=request.user)
            application = InternshipApplication.objects.filter(
                student=student, internship=internship
            ).first()
            has_applied = application is not None
        except Student.DoesNotExist:
            pass
    
    # Calculate match score for students
    match_score = 0
    if hasattr(request.user, 'student'):
        try:
            student = Student.objects.get(user=request.user)
            student_profile = student.placement_profile
            match_score = calculate_match_score(student_profile, internship)
        except (Student.DoesNotExist, StudentProfile.DoesNotExist):
            pass
    
    context = {
        'internship': internship,
        'has_applied': has_applied,
        'application': application,
        'match_score': match_score,
    }
    return render(request, 'internships/internship_detail.html', context)

@login_required
def apply_internship(request, internship_id):
    """Apply for an internship"""
    try:
        internship = Internship.objects.get(id=internship_id, status='published')
        student = Student.objects.get(user=request.user)
    except (Internship.DoesNotExist, Student.DoesNotExist):
        messages.error(request, 'Unable to process application.')
        return redirect('internships_list')
    
    # Check if already applied
    if InternshipApplication.objects.filter(student=student, internship=internship).exists():
        messages.warning(request, 'You have already applied for this internship.')
        return redirect('internship_detail', internship_id=internship_id)
    
    # Check if seats available
    if internship.seats_remaining() <= 0:
        messages.error(request, 'No seats available for this internship.')
        return redirect('internship_detail', internship_id=internship_id)
    
    # Check deadline
    if internship.application_deadline < timezone.now():
        messages.error(request, 'Application deadline has passed.')
        return redirect('internship_detail', internship_id=internship_id)
    
    if request.method == 'POST':
        cover_letter = request.POST.get('cover_letter', '')
        additional_documents = request.FILES.get('additional_documents')
        
        if not cover_letter.strip():
            messages.error(request, 'Cover letter is required.')
            return render(request, 'internships/apply_internship.html', {
                'internship': internship,
            })
        
        # Create application
        application = InternshipApplication.objects.create(
            student=student,
            internship=internship,
            cover_letter=cover_letter,
            additional_documents=additional_documents,
            status='submitted'
        )
        
        # Create notification for placement cell
        if internship.posted_by:
            Notification.objects.create(
                recipient=internship.posted_by.user,
                notification_type='application_status',
                title=f'New Application: {internship.title}',
                message=f'{student.user.get_full_name() or student.user.username} has applied for {internship.title}',
                related_application=application,
                related_internship=internship
            )
        
        messages.success(request, 'Application submitted successfully!')
        return redirect('student_applications')
    
    context = {
        'internship': internship,
    }
    return render(request, 'internships/apply_internship.html', context)

@login_required
def student_applications(request):
    """Student's internship applications"""
    try:
        student = Student.objects.get(user=request.user)
        applications = InternshipApplication.objects.filter(student=student).order_by('-applied_at')
    except Student.DoesNotExist:
        applications = []
    
    context = {
        'applications': applications,
    }
    return render(request, 'internships/student_applications.html', context)


# Enhanced Student Views

@login_required
def student_placement_profile(request):
    """Student placement profile management"""
    try:
        student = Student.objects.get(user=request.user)
        try:
            profile = student.placement_profile
        except StudentProfile.DoesNotExist:
            profile = StudentProfile.objects.create(
                student=student,
                skills='',
                department='Computer Science',
                year_of_study=3,
                graduation_year=2025,
                preferred_locations='',
                preferred_industries=''
            )
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('home')
    
    if request.method == 'POST':
        # Update profile
        profile.skills = request.POST.get('skills', '')
        profile.cgpa = float(request.POST.get('cgpa')) if request.POST.get('cgpa') else None
        profile.department = request.POST.get('department', '')
        profile.year_of_study = int(request.POST.get('year_of_study', 1))
        profile.graduation_year = int(request.POST.get('graduation_year', 2025))
        profile.preferred_locations = request.POST.get('preferred_locations', '')
        profile.preferred_industries = request.POST.get('preferred_industries', '')
        profile.internship_preferences = request.POST.get('internship_preferences', 'internship')
        profile.is_placement_ready = request.POST.get('is_placement_ready') == 'on'
        
        salary_min = request.POST.get('placement_preference_salary_min')
        profile.placement_preference_salary_min = float(salary_min) if salary_min else None
        
        if request.FILES.get('resume'):
            profile.resume = request.FILES['resume']
        
        profile.save()
        messages.success(request, 'Placement profile updated successfully!')
        return redirect('student_placement_profile')
    
    context = {
        'student': student,
        'profile': profile,
        'user_role': 'student',
    }
    return render(request, 'students/placement_profile.html', context)

# Teacher Classroom Views

@login_required
def teacher_course_detail(request, course_id):
    """Teacher course detail with classroom functionality"""
    try:
        teacher = Teacher.objects.get(user=request.user)
        course = Course.objects.get(id=course_id, instructor=teacher)
    except (Teacher.DoesNotExist, Course.DoesNotExist):
        messages.error(request, 'Course not found.')
        return redirect('teacher_courses')
    
    # Get course materials, assignments, and announcements
    materials = CourseMaterial.objects.filter(course=course).order_by('-created_at')
    assignments = Assignment.objects.filter(course=course).order_by('-created_at')
    announcements = CourseAnnouncement.objects.filter(course=course).order_by('-created_at')
    
    # Get enrolled students
    enrolled_students = course.students_enrolled.all()
    
    # Get recent submissions
    recent_submissions = AssignmentSubmission.objects.filter(
        assignment__course=course,
        status='submitted'
    ).order_by('-submitted_at')[:10]
    
    context = {
        'teacher': teacher,
        'course': course,
        'materials': materials,
        'assignments': assignments,
        'announcements': announcements,
        'enrolled_students': enrolled_students,
        'recent_submissions': recent_submissions,
        'user_role': 'teacher',
    }
    return render(request, 'teacher/course_detail.html', context)

@login_required
def add_course_material(request, course_id):
    """Add new course material"""
    try:
        teacher = Teacher.objects.get(user=request.user)
        course = Course.objects.get(id=course_id, instructor=teacher)
    except (Teacher.DoesNotExist, Course.DoesNotExist):
        messages.error(request, 'Course not found.')
        return redirect('teacher_courses')
    
    if request.method == 'POST':
        form = CourseMaterialForm(request.POST, request.FILES)
        if form.is_valid():
            material = form.save(commit=False)
            material.course = course
            material.teacher = teacher
            material.save()
            
            # Notify students
            for student in course.students_enrolled.all():
                Notification.objects.create(
                    recipient=student.user,
                    notification_type='new_material',
                    title=f'New Material: {material.title}',
                    message=f'New {material.get_material_type_display().lower()} added to {course.title}',
                )
            
            messages.success(request, 'Course material added successfully!')
            return redirect('teacher_course_detail', course_id=course.id)
    else:
        form = CourseMaterialForm()
    
    context = {
        'teacher': teacher,
        'course': course,
        'form': form,
        'user_role': 'teacher',
    }
    return render(request, 'teacher/add_material.html', context)

@login_required
def add_assignment(request, course_id):
    """Add new assignment"""
    try:
        teacher = Teacher.objects.get(user=request.user)
        course = Course.objects.get(id=course_id, instructor=teacher)
    except (Teacher.DoesNotExist, Course.DoesNotExist):
        messages.error(request, 'Course not found.')
        return redirect('teacher_courses')
    
    if request.method == 'POST':
        form = AssignmentForm(request.POST, request.FILES)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.course = course
            assignment.teacher = teacher
            assignment.save()
            
            # Notify students
            for student in course.students_enrolled.all():
                Notification.objects.create(
                    recipient=student.user,
                    notification_type='new_assignment',
                    title=f'New Assignment: {assignment.title}',
                    message=f'New {assignment.get_assignment_type_display().lower()} assigned in {course.title}. Due: {assignment.due_date.strftime("%B %d, %Y at %I:%M %p")}',
                )
            
            messages.success(request, 'Assignment created successfully!')
            return redirect('teacher_course_detail', course_id=course.id)
    else:
        form = AssignmentForm()
    
    context = {
        'teacher': teacher,
        'course': course,
        'form': form,
        'user_role': 'teacher',
    }
    return render(request, 'teacher/add_assignment.html', context)

@login_required
def add_announcement(request, course_id):
    """Add course announcement"""
    try:
        teacher = Teacher.objects.get(user=request.user)
        course = Course.objects.get(id=course_id, instructor=teacher)
    except (Teacher.DoesNotExist, Course.DoesNotExist):
        messages.error(request, 'Course not found.')
        return redirect('teacher_courses')
    
    if request.method == 'POST':
        form = CourseAnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.course = course
            announcement.teacher = teacher
            announcement.save()
            
            messages.success(request, 'Announcement posted successfully!')
            return redirect('teacher_course_detail', course_id=course.id)
    else:
        form = CourseAnnouncementForm()
    
    context = {
        'teacher': teacher,
        'course': course,
        'form': form,
        'user_role': 'teacher',
    }
    return render(request, 'teacher/add_announcement.html', context)

@login_required
def view_assignment_submissions(request, assignment_id):
    """View all submissions for an assignment"""
    try:
        teacher = Teacher.objects.get(user=request.user)
        assignment = Assignment.objects.get(id=assignment_id, teacher=teacher)
    except (Teacher.DoesNotExist, Assignment.DoesNotExist):
        messages.error(request, 'Assignment not found.')
        return redirect('teacher_courses')
    
    submissions = AssignmentSubmission.objects.filter(assignment=assignment).order_by(
        '-submitted_at', '-created_at'
    )
    
    context = {
        'teacher': teacher,
        'assignment': assignment,
        'submissions': submissions,
        'user_role': 'teacher',
    }
    return render(request, 'teacher/assignment_submissions.html', context)

@login_required
def grade_submission(request, submission_id):
    """Grade a student submission"""
    try:
        teacher = Teacher.objects.get(user=request.user)
        submission = AssignmentSubmission.objects.get(
            id=submission_id,
            assignment__teacher=teacher
        )
    except (Teacher.DoesNotExist, AssignmentSubmission.DoesNotExist):
        messages.error(request, 'Submission not found.')
        return redirect('teacher_courses')
    
    if request.method == 'POST':
        form = GradeSubmissionForm(request.POST, instance=submission, assignment=submission.assignment)
        if form.is_valid():
            graded_submission = form.save(commit=False)
            graded_submission.status = 'graded'
            graded_submission.graded_at = timezone.now()
            graded_submission.graded_by = teacher
            graded_submission.save()
            
            messages.success(request, 'Submission graded successfully!')
            return redirect('view_assignment_submissions', assignment_id=submission.assignment.id)
    else:
        form = GradeSubmissionForm(instance=submission, assignment=submission.assignment)
    
    context = {
        'teacher': teacher,
        'submission': submission,
        'form': form,
        'user_role': 'teacher',
    }
    return render(request, 'teacher/grade_submission.html', context)

@login_required
def teacher_student_progress(request, course_id, student_id=None):
    """View student progress in a course - individual student or all students"""
    try:
        teacher = Teacher.objects.get(user=request.user)
        course = Course.objects.get(id=course_id, instructor=teacher)
    except (Teacher.DoesNotExist, Course.DoesNotExist):
        messages.error(request, 'Course not found.')
        return redirect('teacher_courses')
    
    # If student_id is provided, show individual student progress
    if student_id:
        try:
            student = Student.objects.get(id=student_id)
            # Verify student is enrolled in this course
            if not (course.students_enrolled.filter(id=student.id).exists() or 
                    Enrollment.objects.filter(course=course, user=student.user, is_active=True).exists()):
                messages.error(request, 'Student is not enrolled in this course.')
                return redirect('teacher_students')
            
            # Get or create progress record
            progress, created = StudentProgress.objects.get_or_create(
                student=student,
                course=course
            )
            if created:
                progress.update_progress()
            else:
                progress.update_progress()  # Update to ensure latest progress
            
            # Get all course materials
            all_materials = course.materials.filter(is_published=True)
            viewed_materials = progress.materials_viewed.all()
            
            # Get all assignments
            all_assignments = course.assignments.filter(is_published=True)
            completed_assignments = progress.assignments_completed.all()
            
            # Get assignment submissions
            submissions = AssignmentSubmission.objects.filter(
                student=student,
                assignment__course=course
            ).select_related('assignment').order_by('-submitted_at')
            
            # Calculate detailed stats
            total_materials = all_materials.count()
            viewed_materials_count = viewed_materials.count()
            total_assignments = all_assignments.count()
            completed_assignments_count = completed_assignments.count()
            
            context = {
                'teacher': teacher,
                'course': course,
                'student': student,
                'progress': progress,
                'all_materials': all_materials,
                'viewed_materials': viewed_materials,
                'all_assignments': all_assignments,
                'completed_assignments': completed_assignments,
                'submissions': submissions,
                'total_materials': total_materials,
                'viewed_materials_count': viewed_materials_count,
                'total_assignments': total_assignments,
                'completed_assignments_count': completed_assignments_count,
                'user_role': 'teacher',
            }
            return render(request, 'teacher/individual_student_progress.html', context)
        except Student.DoesNotExist:
            messages.error(request, 'Student not found.')
            return redirect('teacher_students')
    
    # Otherwise, show progress for all students (existing functionality)
    enrolled_students = course.students_enrolled.all()
    progress_data = []
    
    for student in enrolled_students:
        progress, created = StudentProgress.objects.get_or_create(
            student=student,
            course=course
        )
        if created:
            progress.update_progress()
        
        # Get assignment submissions
        submissions = AssignmentSubmission.objects.filter(
            student=student,
            assignment__course=course
        )
        
        progress_data.append({
            'student': student,
            'progress': progress,
            'submissions': submissions,
            'total_assignments': course.assignments.filter(is_published=True).count(),
            'completed_assignments': submissions.filter(status__in=['submitted', 'graded']).count(),
        })
    
    context = {
        'teacher': teacher,
        'course': course,
        'progress_data': progress_data,
        'user_role': 'teacher',
    }
    return render(request, 'teacher/student_progress.html', context)

@login_required
def view_material(request, material_id):
    """View a specific material"""
    try:
        teacher = Teacher.objects.get(user=request.user)
        material = CourseMaterial.objects.get(id=material_id, teacher=teacher)
    except (Teacher.DoesNotExist, CourseMaterial.DoesNotExist):
        messages.error(request, 'Material not found.')
        return redirect('teacher_home')
    
    context = {
        'material': material,
        'teacher': teacher,
        'user_role': 'teacher',
    }
    return render(request, 'teacher/view_material.html', context)

@login_required
def delete_material(request, material_id):
    """Delete a material"""
    try:
        teacher = Teacher.objects.get(user=request.user)
        material = CourseMaterial.objects.get(id=material_id, teacher=teacher)
        course = material.course
        material_title = material.title
        material.delete()
        messages.success(request, f'Material "{material_title}" deleted successfully!')
        # Redirect based on referrer or default to course detail
        referrer = request.META.get('HTTP_REFERER', '')
        if 'teacher_home' in referrer or 'dashboard' in referrer:
            return redirect('teacher_home')
        return redirect('teacher_course_detail', course_id=course.id)
    except (Teacher.DoesNotExist, CourseMaterial.DoesNotExist):
        messages.error(request, 'Material not found.')
        return redirect('teacher_home')

@login_required
def delete_assignment(request, assignment_id):
    """Delete an assignment"""
    try:
        teacher = Teacher.objects.get(user=request.user)
        assignment = Assignment.objects.get(id=assignment_id, teacher=teacher)
        course = assignment.course
        assignment_title = assignment.title
        assignment.delete()
        messages.success(request, f'Assignment "{assignment_title}" deleted successfully!')
        # Redirect based on referrer or default to course detail
        referrer = request.META.get('HTTP_REFERER', '')
        if 'teacher_home' in referrer or 'dashboard' in referrer:
            return redirect('teacher_home')
        return redirect('teacher_course_detail', course_id=course.id)
    except (Teacher.DoesNotExist, Assignment.DoesNotExist):
        messages.error(request, 'Assignment not found.')
        return redirect('teacher_home')

@login_required
def quick_upload_material(request):
    """Quick upload material from teacher dashboard"""
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        messages.error(request, 'Teacher profile not found.')
        return redirect('teacher_home')
    
    if request.method == 'POST':
        course_id = request.POST.get('course_id')
        material_type = request.POST.get('material_type')
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        content = request.POST.get('content', '')
        youtube_url = request.POST.get('youtube_url', '')
        file = request.FILES.get('file')
        
        try:
            course = Course.objects.get(id=course_id, instructor=teacher)
        except Course.DoesNotExist:
            messages.error(request, 'Course not found.')
            return redirect('teacher_home')
        
        # Create material
        material = CourseMaterial(
            course=course,
            teacher=teacher,
            title=title,
            description=description,
            material_type=material_type
        )
        
        if material_type == 'note':
            if not content:
                messages.error(request, 'Note content is required.')
                return redirect('teacher_home')
            material.content = content
        elif material_type == 'video':
            if youtube_url:
                # Extract YouTube video ID with improved regex to handle more URL formats
                # Handles: youtube.com/watch?v=, youtu.be/, youtube.com/embed/, youtube.com/v/, etc.
                youtube_patterns = [
                    r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/)([a-zA-Z0-9_-]{11})',
                    r'youtube\.com\/.*[?&]v=([a-zA-Z0-9_-]{11})',
                    r'youtu\.be\/([a-zA-Z0-9_-]{11})',
                ]
                video_id = None
                for pattern in youtube_patterns:
                    match = re.search(pattern, youtube_url)
                    if match:
                        video_id = match.group(1)
                        break
                
                if video_id:
                    material.youtube_video_id = video_id
                    # Ensure we store the proper watch URL
                    if 'youtu.be' in youtube_url or 'youtube.com' not in youtube_url:
                        material.url = f"https://www.youtube.com/watch?v={video_id}"
                    else:
                        material.url = youtube_url
                else:
                    messages.error(request, 'Invalid YouTube URL. Please provide a valid YouTube video URL.')
                    return redirect('teacher_home')
            elif file:
                material.file = file
            else:
                messages.error(request, 'Please provide either a YouTube URL or upload a video file.')
                return redirect('teacher_home')
        elif material_type == 'file':
            if not file:
                messages.error(request, 'Please upload a file.')
                return redirect('teacher_home')
            material.file = file
        
        material.save()
        
        # Notify students
        for student in course.students_enrolled.all():
            Notification.objects.create(
                recipient=student.user,
                notification_type='new_material',
                title=f'New Material: {material.title}',
                message=f'New {material.get_material_type_display().lower()} added to {course.title}',
            )
        
        messages.success(request, f'{material.get_material_type_display()} "{title}" uploaded successfully!')
    
    return redirect('teacher_home')

# Student Course Content Views

@login_required
def student_course_content(request, course_id):
    """Student view of course content with materials and videos"""
    try:
        student = Student.objects.get(user=request.user)
        course = Course.objects.get(id=course_id)
    except (Student.DoesNotExist, Course.DoesNotExist):
        messages.error(request, 'Course not found.')
        return redirect('student_home')
    
    # Check if student is enrolled
    is_enrolled = (
        course.students_enrolled.filter(id=student.id).exists() or
        Enrollment.objects.filter(user=request.user, course=course, is_active=True).exists()
    )
    
    if not is_enrolled:
        messages.error(request, 'You are not enrolled in this course.')
        return redirect('student_home')
    
    # Get or create student progress
    progress, created = StudentProgress.objects.get_or_create(
        student=student,
        course=course
    )
    
    # Update last accessed
    progress.last_accessed = timezone.now()
    progress.save()
    
    # Auto-issue certificate if completed
    try:
        if progress.progress_percentage >= 100 and getattr(course, 'certificate', True):
            from .models import Certificate
            Certificate.objects.get_or_create(
                user=request.user,
                course=course,
                defaults={'certificate_id': get_random_string(16)}
            )
    except Exception:
        pass

    # Auto-populate default materials for catalog courses (not teacher-created)
    # Exclude teacher-created demo courses explicitly listed below
    try:
        excluded_titles = {'graphic design', 'hotel management', 'dsa'}
        title_lower = course.title.lower().strip()
        if not course.instructor and title_lower not in excluded_titles:
            existing_materials_count = CourseMaterial.objects.filter(course=course).count()
            if existing_materials_count == 0:
                # Default YouTube videos per course (stable public courses)
                default_videos = {
                    'python': ('Python Full Course', 'rfscVS0vtbw'),
                    'java': ('Java Full Course', 'eIrMbAQSU34'),
                    'mysql': ('MySQL Full Course', 'HXV3zeQKqGY'),
                    'web design': ('HTML & CSS Course', 'mU6anWqZJcc'),
                    'web development': ('Web Development Bootcamp', 'zJSY8tbf_ys'),
                    'ui/ux design': ('UI/UX Design Course', 'c9Wg6Cb_YlU'),
                    'cloud computing': ('Cloud Computing Course', 'mxT233EdY5c'),
                    'cybersecurity': ('Cybersecurity Course', 'bPVaOlJ6ln0'),
                    'digital marketing': ('Digital Marketing Course', 'nJxLGc8v3Zg'),
                    'project management': ('Project Management Basics', 'ZcG9Z4GmYVQ'),
                    'microsoft excel': ('Excel Tutorial for Beginners', 'Vl0H-qTclOg'),
                    'aws': ('AWS Cloud Practitioner Course', '3hLmDS179YE'),
                    'ai and machine learning': ('Machine Learning Course', 'GwIo3gDZCVQ'),
                    'ds': ('Data Science Course', 'ua-CiDNNj30'),
                }
                # Default PDF resources per course (external, public resources)
                default_pdfs = {
                    'python': ('Python Notes (PDF)', 'https://files.realpython.com/media/Python-Cheat-Sheet-RealPython.pdf'),
                    'java': ('Java Cheat Sheet (PDF)', 'https://www.cheatography.com/davechild/cheat-sheets/java/pdf/'),
                    'mysql': ('MySQL Cheat Sheet (PDF)', 'https://files.phpmyadmin.net/cheatsheets/phpMyAdmin-MySQL-cheatsheet.pdf'),
                    'web design': ('HTML & CSS Notes (PDF)', 'https://web.stanford.edu/class/cs142/handouts/HTMLCSS.pdf'),
                    'web development': ('Web Programming Notes (PDF)', 'https://www.eecs.umich.edu/courses/eecs485/static/notes/web.pdf'),
                    'ui/ux design': ('UX Design Guide (PDF)', 'https://pages.interaction-design.org/ebook/interaction-design-foundation-beginners-guide.pdf'),
                    'cloud computing': ('AWS Cloud Practitioner Exam Guide (PDF)', 'https://d1.awsstatic.com/training-and-certification/docs-cloud-practitioner/AWS-Certified-Cloud-Practitioner_Exam-Guide.pdf'),
                    'cybersecurity': ('Cybersecurity Basics (PDF)', 'https://us-cert.cisa.gov/sites/default/files/publications/BestPracticesforSecuringYourHomeNetwork.pdf'),
                    'digital marketing': ('Digital Marketing Basics (PDF)', 'https://www.iimskills.com/wp-content/uploads/2021/08/Digital-Marketing-Course-Content-IIM-SKILLS.pdf'),
                    'project management': ('PMBOK Guide Overview (PDF)', 'https://www.pmi.org/-/media/pmi/documents/public/pdf/standards/pmbok-guide-7th-excerpt.pdf'),
                    'microsoft excel': ('Excel Shortcuts (PDF)', 'https://www.customguide.com/cheat-sheet/excel-shortcuts.pdf'),
                    'aws': ('AWS Well-Architected (PDF)', 'https://d1.awsstatic.com/whitepapers/architecture/AWS_Well-Architected_Framework.pdf'),
                    'ai and machine learning': ('Machine Learning Notes (PDF)', 'https://www.cs.cmu.edu/~aarti/Class/10701_Spring14/recitations/IntroMachineLearning.pdf'),
                    'ds': ('Data Science Handbook (PDF)', 'https://jakevdp.github.io/PythonDataScienceHandbook/figures/PDSH-Cheat-Sheet.pdf'),
                }

                # Create one embedded video material if available
                if title_lower in default_videos:
                    v_title, v_id = default_videos[title_lower]
                    CourseMaterial.objects.create(
                        course=course,
                        teacher=course.instructor if course.instructor else Teacher.objects.first(),
                        title=v_title,
                        description=f"Auto-added learning video for {course.title}",
                        material_type='video',
                        youtube_video_id=v_id,
                        is_published=True,
                    )

                # Create a PDF link resource if available
                if title_lower in default_pdfs:
                    p_title, p_url = default_pdfs[title_lower]
                    CourseMaterial.objects.create(
                        course=course,
                        teacher=course.instructor if course.instructor else Teacher.objects.first(),
                        title=p_title,
                        description=f"Reference notes for {course.title}",
                        material_type='link',
                        url=p_url,
                        is_published=True,
                    )
    except Exception:
        # Do not block rendering if auto-population fails
        pass

    # Get published materials with viewed status
    materials = CourseMaterial.objects.filter(
        course=course,
        is_published=True
    ).order_by('created_at')
    
    materials_with_status = []
    for material in materials:
        is_viewed = material in progress.materials_viewed.all()
        materials_with_status.append({
            'material': material,
            'is_viewed': is_viewed,
        })
    
    # Get assignments with submission status
    assignments = Assignment.objects.filter(
        course=course,
        is_published=True
    ).order_by('created_at')
    
    # Get submission status for each assignment
    assignments_with_submissions = []
    for assignment in assignments:
        try:
            submission = AssignmentSubmission.objects.get(
                assignment=assignment,
                student=student
            )
            submission_status = submission.status
            submission_exists = True
        except AssignmentSubmission.DoesNotExist:
            submission = None
            submission_status = None
            submission_exists = False
        
        assignments_with_submissions.append({
            'assignment': assignment,
            'submission': submission,
            'submission_status': submission_status,
            'submission_exists': submission_exists,
        })
    
    # Get announcements
    announcements = CourseAnnouncement.objects.filter(
        course=course
    ).order_by('-created_at')
    
    context = {
        'course': course,
        'materials': materials,
        'materials_with_status': materials_with_status,
        'assignments': assignments,
        'assignments_with_submissions': assignments_with_submissions,
        'announcements': announcements,
        'progress': progress,
        'student': student,
        'user_role': 'student',
    }
    return render(request, 'student_course_content.html', context)

@login_required
def submit_assignment(request, assignment_id):
    """Student submit assignment view"""
    try:
        student = Student.objects.get(user=request.user)
        assignment = Assignment.objects.get(id=assignment_id, is_published=True)
    except (Student.DoesNotExist, Assignment.DoesNotExist):
        messages.error(request, 'Assignment not found.')
        return redirect('student_home')
    
    # Check if student is enrolled in the course
    is_enrolled = (
        assignment.course.students_enrolled.filter(id=student.id).exists() or
        Enrollment.objects.filter(user=request.user, course=assignment.course, is_active=True).exists()
    )
    
    if not is_enrolled:
        messages.error(request, 'You are not enrolled in this course.')
        return redirect('student_home')
    
    # Get or create submission
    try:
        submission = AssignmentSubmission.objects.get(
            assignment=assignment,
            student=student
        )
    except AssignmentSubmission.DoesNotExist:
        submission = None
    
    if request.method == 'POST':
        form = AssignmentSubmissionForm(request.POST, request.FILES, instance=submission)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.assignment = assignment
            submission.student = student
            submission.status = 'submitted'
            submission.submitted_at = timezone.now()
            submission.save()
            
            # Update progress - mark assignment as completed
            try:
                progress = StudentProgress.objects.get(student=student, course=assignment.course)
                if assignment not in progress.assignments_completed.all():
                    progress.assignments_completed.add(assignment)
                progress.update_progress()
            except StudentProgress.DoesNotExist:
                progress = StudentProgress.objects.create(student=student, course=assignment.course)
                progress.assignments_completed.add(assignment)
                progress.update_progress()
            
            messages.success(request, 'Assignment submitted successfully!')
            return redirect('student_course_content', course_id=assignment.course.id)
    else:
        form = AssignmentSubmissionForm(instance=submission)
    
    context = {
        'assignment': assignment,
        'form': form,
        'submission': submission,
        'course': assignment.course,
        'user_role': 'student',
    }
    return render(request, 'student/submit_assignment.html', context)

@login_required
def mark_material_done(request, material_id):
    """Mark a material as viewed/done and update progress"""
    try:
        student = Student.objects.get(user=request.user)
        material = CourseMaterial.objects.get(id=material_id, is_published=True)
        course = material.course
    except (Student.DoesNotExist, CourseMaterial.DoesNotExist):
        messages.error(request, 'Material not found.')
        return redirect('student_home')
    
    # Check if student is enrolled
    is_enrolled = (
        course.students_enrolled.filter(id=student.id).exists() or
        Enrollment.objects.filter(user=request.user, course=course, is_active=True).exists()
    )
    
    if not is_enrolled:
        messages.error(request, 'You are not enrolled in this course.')
        return redirect('student_home')
    
    # Get or create progress
    try:
        progress = StudentProgress.objects.get(student=student, course=course)
    except StudentProgress.DoesNotExist:
        progress = StudentProgress.objects.create(student=student, course=course)
    
    # Mark material as viewed
    if material not in progress.materials_viewed.all():
        progress.materials_viewed.add(material)
        progress.update_progress()
        messages.success(request, f'"{material.title}" marked as done!')
    else:
        messages.info(request, 'This material is already marked as done.')
    
    return redirect('student_course_content', course_id=course.id)

@login_required
def remove_course(request, course_id):
    """Remove/unenroll from a course"""
    try:
        student = Student.objects.get(user=request.user)
        course = Course.objects.get(id=course_id)
    except (Student.DoesNotExist, Course.DoesNotExist):
        messages.error(request, 'Course not found.')
        return redirect('student_home')
    
    # Remove from ManyToMany relationship
    if course in student.courses_enrolled.all():
        student.courses_enrolled.remove(course)
    
    # Remove from Enrollment model
    Enrollment.objects.filter(user=request.user, course=course, is_active=True).update(is_active=False)
    
    # Delete progress record
    StudentProgress.objects.filter(student=student, course=course).delete()
    
    messages.success(request, f'Successfully removed from "{course.title}".')
    return redirect('student_home')

# Excel Upload and AI Verification Views

@login_required
def excel_upload(request):
    """Handle Excel file upload and processing"""
    try:
        company = Company.objects.get(user=request.user)
    except Company.DoesNotExist:
        messages.error(request, 'Company profile not found.')
        return redirect('home')
    
    if request.method == 'POST':
        excel_file = request.FILES.get('excel_file')
        upload_type = request.POST.get('data_type')
        
        if excel_file and upload_type:
            # Create ExcelUpload record
            upload = ExcelUpload.objects.create(
                company=company,
                file=excel_file,
                upload_type=upload_type,
                status='uploaded'
            )
            
            # Simulate processing (in real implementation, use Celery or similar)
            upload.status = 'processing'
            upload.save()
            
            # Simulate processing delay and results
            import random
            upload.total_records = random.randint(50, 500)
            upload.processed_records = upload.total_records
            upload.status = 'completed'
            upload.processed_at = timezone.now()
            upload.save()
            
            messages.success(request, f'Excel file processed successfully! {upload.processed_records} records processed.')
            return redirect('company_home')
        else:
            messages.error(request, 'Please select a file and data type.')
    
    return redirect('company_home')

@login_required
def ai_verification(request):
    """Handle AI-powered document verification"""
    try:
        company = Company.objects.get(user=request.user)
    except Company.DoesNotExist:
        messages.error(request, 'Company profile not found.')
        return redirect('home')
    
    if request.method == 'POST':
        document_file = request.FILES.get('offer_letter')
        verification_type = request.POST.get('verification_type', 'offer_letter')
        
        if document_file:
            # Create AIVerification record
            verification = AIVerification.objects.create(
                company=company,
                document_file=document_file,
                verification_type=verification_type,
                status='pending'
            )
            
            # Simulate AI processing
            verification.status = 'processing'
            verification.save()
            
            # Simulate AI analysis results
            import random
            verification.confidence_score = round(random.uniform(85.0, 98.5), 2)
            verification.status = 'verified' if verification.confidence_score > 90 else 'rejected'
            verification.verification_result = f"Document verified with {verification.confidence_score}% confidence. All checks passed successfully."
            verification.ai_analysis = {
                'authenticity_score': verification.confidence_score,
                'format_valid': True,
                'signature_detected': True,
                'company_letterhead': True,
                'date_valid': True,
                'recommendations': ['Document appears authentic', 'All security checks passed']
            }
            verification.processed_at = timezone.now()
            verification.save()
            
            if verification.status == 'verified':
                messages.success(request, f'Document verified successfully! Confidence score: {verification.confidence_score}%')
            else:
                messages.warning(request, f'Document verification failed. Confidence score: {verification.confidence_score}%')
            
            return redirect('company_home')
        else:
            messages.error(request, 'Please select a document to verify.')
    
    return redirect('company_home')

@login_required
def generate_report(request):
    """Generate various types of reports"""
    try:
        company = Company.objects.get(user=request.user)
    except Company.DoesNotExist:
        messages.error(request, 'Company profile not found.')
        return redirect('home')
    
    if request.method == 'POST':
        report_type = request.POST.get('report_type')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        
        if report_type and start_date and end_date:
            # Create report record
            report = Report.objects.create(
                company=company,
                report_type=report_type,
                title=f"{report_type.replace('_', ' ').title()} Report",
                description=f"Report generated for {company.company_name} from {start_date} to {end_date}",
                parameters={
                    'start_date': start_date,
                    'end_date': end_date,
                    'report_type': report_type
                }
            )
            
            # Simulate report generation (in real implementation, generate actual reports)
            import os
            from django.core.files.base import ContentFile
            
            # Create a dummy report file
            report_content = f"""
            {report.title}
            Generated for: {company.company_name}
            Date Range: {start_date} to {end_date}
            Generated on: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            Report Summary:
            - Total Records: 150
            - Success Rate: 95%
            - Average Processing Time: 2.3 seconds
            - Recommendations: Continue current practices
            """
            
            report.file.save(f"{report_type}_report_{company.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.txt", 
                           ContentFile(report_content.encode()))
            report.save()
            
            messages.success(request, f'Report generated successfully! {report.title}')
            return redirect('company_home')
        else:
            messages.error(request, 'Please fill in all required fields.')
    
    return redirect('company_home')

@login_required
def company_dashboard_data(request):
    """API endpoint for dashboard data with real statistics"""
    try:
        company = Company.objects.get(user=request.user)
        
        # Get all students
        total_students = Student.objects.count()
        students_with_profiles = Student.objects.filter(placement_profile__isnull=False).count()
        
        # Get all placements
        total_placements = PlacementRecord.objects.filter(company=company).count()
        placed_students = PlacementRecord.objects.filter(company=company).values('student').distinct().count()
        
        # Calculate placement rate
        placement_rate = (placed_students / total_students * 100) if total_students > 0 else 0
        
        # Get package statistics
        placements_with_package = PlacementRecord.objects.filter(company=company, package_amount__isnull=False)
        highest_package = placements_with_package.aggregate(max_package=models.Max('package_amount'))['max_package'] or 0
        average_package = placements_with_package.aggregate(avg_package=models.Avg('package_amount'))['avg_package'] or 0
        
        # Get stipend statistics
        placements_with_stipend = PlacementRecord.objects.filter(company=company, stipend_amount__isnull=False)
        max_stipend = placements_with_stipend.aggregate(max_stipend=models.Max('stipend_amount'))['max_stipend'] or 0
        
        # Get IQAC statistics
        iqac_approved = PlacementRecord.objects.filter(company=company, iqac_status='approved').count()
        iqac_pending = PlacementRecord.objects.filter(company=company, iqac_status='pending').count()
        iqac_rejected = PlacementRecord.objects.filter(company=company, iqac_status='rejected').count()
        
        # Get department statistics
        departments = Student.objects.values('placement_profile__department').distinct().exclude(placement_profile__department__isnull=True).exclude(placement_profile__department='')
        department_count = departments.count()
        
        # Get batch statistics
        batches = Student.objects.values('placement_profile__graduation_year').distinct().exclude(placement_profile__graduation_year__isnull=True)
        batch_count = batches.count()
        
        # Get user statistics
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        pending_users = User.objects.filter(is_active=False).count()
        suspended_users = 0  # We don't have a suspended field, so this is 0
        
        # Get company statistics
        partner_companies = Company.objects.count()
        
        # Get recent activity
        recent_uploads = ExcelUpload.objects.filter(company=company).order_by('-created_at')[:5]
        recent_verifications = AIVerification.objects.filter(company=company).order_by('-created_at')[:5]
        recent_reports = Report.objects.filter(company=company).order_by('-generated_at')[:5]
        
        data = {
            # Dashboard statistics
            'total_students': total_students,
            'total_offers': total_placements,
            'placement_rate': round(placement_rate, 2),
            'placed_students': placed_students,
            'highest_package': float(highest_package),
            'average_package': float(average_package),
            'max_stipend': float(max_stipend),
            'iqac_approved': iqac_approved,
            'iqac_pending': iqac_pending,
            'iqac_rejected': iqac_rejected,
            'partner_companies': partner_companies,
            
            # Students statistics
            'students_total': total_students,
            'students_departments': department_count,
            'students_batches': batch_count,
            'students_active': students_with_profiles,
            
            # Placements statistics
            'placements_total_students': total_students,
            'placements_highest_package': float(highest_package),
            'placements_average_package': float(average_package),
            'placements_max_stipend': float(max_stipend),
            'placements_total_offers': total_placements,
            'placements_iqac_approved': iqac_approved,
            'placements_iqac_pending': iqac_pending,
            'placements_iqac_rejected': iqac_rejected,
            'placements_partner_companies': partner_companies,
            
            # Users statistics
            'users_total': total_users,
            'users_active': active_users,
            'users_pending': pending_users,
            'users_suspended': suspended_users,
            
            # Recent activity
            'recent_uploads': [
                {
                    'id': upload.id,
                    'type': upload.get_upload_type_display(),
                    'status': upload.get_status_display(),
                    'created_at': upload.created_at.strftime('%Y-%m-%d %H:%M'),
                    'processed_records': upload.processed_records
                } for upload in recent_uploads
            ],
            'recent_verifications': [
                {
                    'id': verification.id,
                    'type': verification.get_verification_type_display(),
                    'status': verification.get_status_display(),
                    'confidence_score': verification.confidence_score,
                    'created_at': verification.created_at.strftime('%Y-%m-%d %H:%M')
                } for verification in recent_verifications
            ],
            'recent_reports': [
                {
                    'id': report.id,
                    'title': report.title,
                    'type': report.get_report_type_display(),
                    'generated_at': report.generated_at.strftime('%Y-%m-%d %H:%M')
                } for report in recent_reports
            ]
        }
        
        return JsonResponse(data)
        
    except Company.DoesNotExist:
        return JsonResponse({'error': 'Company profile not found'}, status=404)

# Dashboard API Endpoints

@login_required
def dashboard_students_api(request):
    """API endpoint for students data"""
    try:
        company = Company.objects.get(user=request.user)
        
        # Get all students with their profiles
        students = Student.objects.select_related('user').prefetch_related('placement_profile')
        
        # Search functionality
        search_query = request.GET.get('search', '')
        if search_query:
            students = students.filter(
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query) |
                Q(user__email__icontains=search_query)
            )
        
        # Filter by department
        department = request.GET.get('department', '')
        if department:
            students = students.filter(placement_profile__department=department)
        
        # Filter by batch
        batch = request.GET.get('batch', '')
        if batch:
            students = students.filter(placement_profile__graduation_year=batch)
        
        students_data = []
        for student in students:
            try:
                profile = student.placement_profile
                students_data.append({
                    'id': student.id,
                    'name': student.user.get_full_name(),
                    'email': student.user.email,
                    'phone': getattr(profile, 'phone', ''),
                    'department': getattr(profile, 'department', ''),
                    'batch': getattr(profile, 'graduation_year', ''),
                    'cgpa': float(getattr(profile, 'cgpa', 0)),
                    'is_placement_ready': getattr(profile, 'is_placement_ready', False),
                })
            except StudentProfile.DoesNotExist:
                # If no profile exists, create basic data
                students_data.append({
                    'id': student.id,
                    'name': student.user.get_full_name(),
                    'email': student.user.email,
                    'phone': '',
                    'department': '',
                    'batch': '',
                    'cgpa': 0.0,
                    'is_placement_ready': False,
                })
        
        return JsonResponse({
            'students': students_data,
            'total_count': len(students_data)
        })
        
    except Company.DoesNotExist:
        return JsonResponse({'error': 'Company profile not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def dashboard_placements_api(request):
    """API endpoint for placements data"""
    try:
        company = Company.objects.get(user=request.user)
        
        # Get placement records
        placements = PlacementRecord.objects.filter(company=company).select_related('student__user')
        
        # Search functionality
        search_query = request.GET.get('search', '')
        if search_query:
            placements = placements.filter(
                Q(student__user__first_name__icontains=search_query) |
                Q(student__user__last_name__icontains=search_query) |
                Q(job_title__icontains=search_query)
            )
        
        # Filter by IQAC status
        iqac_status = request.GET.get('iqac_status', '')
        if iqac_status:
            placements = placements.filter(iqac_status=iqac_status)
        
        placements_data = []
        for placement in placements:
            placements_data.append({
                'id': placement.id,
                'student_name': placement.student.user.get_full_name(),
                'student_email': placement.student.user.email,
                'job_title': placement.job_title,
                'package_amount': float(placement.package_amount) if placement.package_amount else None,
                'stipend_amount': float(placement.stipend_amount) if placement.stipend_amount else None,
                'placement_date': placement.placement_date.strftime('%Y-%m-%d'),
                'iqac_status': placement.get_iqac_status_display(),
                'offer_letter': placement.offer_letter.url if placement.offer_letter else None,
                'created_at': placement.created_at.strftime('%Y-%m-%d %H:%M'),
            })
        
        return JsonResponse({
            'placements': placements_data,
            'total_count': len(placements_data)
        })
        
    except Company.DoesNotExist:
        return JsonResponse({'error': 'Company profile not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def dashboard_reports_api(request):
    """API endpoint for reports data"""
    try:
        company = Company.objects.get(user=request.user)
        
        # Get reports
        reports = Report.objects.filter(company=company)
        
        # Filter by report type
        report_type = request.GET.get('report_type', '')
        if report_type:
            reports = reports.filter(report_type=report_type)
        
        reports_data = []
        for report in reports:
            reports_data.append({
                'id': report.id,
                'title': report.title,
                'report_type': report.get_report_type_display(),
                'description': report.description,
                'file_url': report.file.url if report.file else None,
                'generated_at': report.generated_at.strftime('%Y-%m-%d %H:%M'),
            })
        
        # Get dashboard statistics for reports
        total_students = Student.objects.count()
        total_placements = PlacementRecord.objects.filter(company=company).count()
        placed_students = PlacementRecord.objects.filter(company=company).values('student').distinct().count()
        placement_rate = (placed_students / total_students * 100) if total_students > 0 else 0
        
        # Department-wise statistics
        departments = ['CSE', 'IOTIS', 'ECE', 'ME']
        department_stats = []
        for dept in departments:
            dept_students = Student.objects.filter(placement_profile__department=dept).count()
            dept_placed = PlacementRecord.objects.filter(company=company, student__placement_profile__department=dept).values('student').distinct().count()
            dept_rate = (dept_placed / dept_students * 100) if dept_students > 0 else 0
            department_stats.append({
                'department': dept,
                'total_students': dept_students,
                'placed_students': dept_placed,
                'placement_rate': round(dept_rate, 2)
            })
        
        # Company performance data
        company_performance = {
            'total_students': total_students,
            'total_placements': total_placements,
            'placed_students': placed_students,
            'placement_rate': round(placement_rate, 2),
            'department_stats': department_stats
        }
        
        return JsonResponse({
            'reports': reports_data,
            'total_count': len(reports_data),
            'company_performance': company_performance
        })
        
    except Company.DoesNotExist:
        return JsonResponse({'error': 'Company profile not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def dashboard_users_api(request):
    """API endpoint for users data"""
    try:
        company = Company.objects.get(user=request.user)
        
        # Get all users with their profiles
        users = User.objects.select_related('userprofile').all()
        
        # Search functionality
        search_query = request.GET.get('search', '')
        if search_query:
            users = users.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(username__icontains=search_query)
            )
        
        # Filter by role
        role = request.GET.get('role', '')
        if role:
            users = users.filter(userprofile__role=role)
        
        users_data = []
        for user in users:
            try:
                profile = user.userprofile
                users_data.append({
                    'id': user.id,
                    'name': user.get_full_name(),
                    'email': user.email,
                    'username': user.username,
                    'role': profile.get_role_display(),
                    'is_active': user.is_active,
                    'last_login': user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else 'Never',
                    'date_joined': user.date_joined.strftime('%Y-%m-%d %H:%M'),
                })
            except:
                # If no profile exists
                users_data.append({
                    'id': user.id,
                    'name': user.get_full_name(),
                    'email': user.email,
                    'username': user.username,
                    'role': 'No Role',
                    'is_active': user.is_active,
                    'last_login': user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else 'Never',
                    'date_joined': user.date_joined.strftime('%Y-%m-%d %H:%M'),
                })
        
        return JsonResponse({
            'users': users_data,
            'total_count': len(users_data)
        })
        
    except Company.DoesNotExist:
        return JsonResponse({'error': 'Company profile not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def add_student(request):
    """Add new student"""
    if request.method == 'POST':
        try:
            company = Company.objects.get(user=request.user)
            
            # Get form data
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            phone = request.POST.get('phone', '')
            department = request.POST.get('department', '')
            batch_year = request.POST.get('batch_year', '')
            cgpa = request.POST.get('cgpa', '0.0')
            
            # Create user
            user = User.objects.create_user(
                username=email,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password='temp_password_123'  # Temporary password
            )
            
            # Create user profile
            UserProfile.objects.create(
                user=user,
                role='student',
                phone=phone
            )
            
            # Create student
            student = Student.objects.create(user=user)
            
            # Create student profile
            StudentProfile.objects.create(
                student=student,
                phone=phone,
                department=department,
                graduation_year=int(batch_year) if batch_year else None,
                cgpa=float(cgpa) if cgpa else 0.0
            )
            
            return JsonResponse({'success': True, 'message': 'Student added successfully'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def add_placement(request):
    """Add new placement record"""
    if request.method == 'POST':
        try:
            company = Company.objects.get(user=request.user)
            
            # Get form data
            student_id = request.POST.get('student_id')
            job_title = request.POST.get('job_title')
            package_amount = request.POST.get('package_amount', '0')
            stipend_amount = request.POST.get('stipend_amount', '0')
            placement_date = request.POST.get('placement_date')
            offer_letter = request.FILES.get('offer_letter')
            
            # Get student
            student = Student.objects.get(id=student_id)
            
            # Create placement record
            placement = PlacementRecord.objects.create(
                company=company,
                student=student,
                job_title=job_title,
                package_amount=float(package_amount) if package_amount else None,
                stipend_amount=float(stipend_amount) if stipend_amount else None,
                placement_date=datetime.strptime(placement_date, '%Y-%m-%d').date(),
                offer_letter=offer_letter
            )
            
            return JsonResponse({'success': True, 'message': 'Placement record added successfully'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def delete_student(request):
    """Delete student record"""
    if request.method == 'POST':
        try:
            company = Company.objects.get(user=request.user)
            student_id = request.POST.get('student_id')
            
            print(f"Attempting to delete student with ID: {student_id}")
            
            # Get student
            student = Student.objects.get(id=student_id)
            print(f"Found student: {student.user.get_full_name()}")
            
            # Delete student profile first
            try:
                student.placement_profile.delete()
                print("Student profile deleted")
            except StudentProfile.DoesNotExist:
                print("No student profile found")
                pass
            
            # Delete student
            student.delete()
            print("Student deleted successfully")
            
            return JsonResponse({'success': True, 'message': 'Student deleted successfully'})
            
        except Student.DoesNotExist:
            print(f"Student with ID {student_id} not found")
            return JsonResponse({'success': False, 'error': 'Student not found'})
        except Exception as e:
            print(f"Error deleting student: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def delete_placement(request):
    """Delete placement record"""
    if request.method == 'POST':
        try:
            company = Company.objects.get(user=request.user)
            placement_id = request.POST.get('placement_id')
            
            # Get placement record
            placement = PlacementRecord.objects.get(id=placement_id, company=company)
            placement.delete()
            
            return JsonResponse({'success': True, 'message': 'Placement record deleted successfully'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def delete_user(request):
    """Delete user record"""
    try:
        if request.method != 'POST':
            return JsonResponse({'success': False, 'error': 'Invalid request method'})
        
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'error': 'User not authenticated'})
        
        company = Company.objects.get(user=request.user)
        user_id = request.POST.get('user_id')
        
        if not user_id:
            return JsonResponse({'success': False, 'error': 'User ID not provided'})
        
        print(f"Attempting to delete user with ID: {user_id}")
        
        # Get user
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            print(f"User with ID {user_id} not found")
            return JsonResponse({'success': False, 'error': 'User not found'})
        
        print(f"Found user: {user.get_full_name()} ({user.email})")
        
        # Don't allow deleting the current company user
        if user == request.user:
            print("Cannot delete own account")
            return JsonResponse({'success': False, 'error': 'Cannot delete your own account'})
        
        # Delete user (this will cascade to related objects)
        user.delete()
        print("User deleted successfully")
        
        return JsonResponse({'success': True, 'message': 'User deleted successfully'})
        
    except Company.DoesNotExist:
        print("Company profile not found")
        return JsonResponse({'success': False, 'error': 'Company profile not found'})
    except Exception as e:
        print(f"Error deleting user: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def edit_student(request):
    """Edit student record"""
    if request.method == 'POST':
        try:
            company = Company.objects.get(user=request.user)
            student_id = request.POST.get('student_id')
            
            # Get student
            student = Student.objects.get(id=student_id)
            
            # Update user data
            student.user.first_name = request.POST.get('first_name', student.user.first_name)
            student.user.last_name = request.POST.get('last_name', student.user.last_name)
            student.user.email = request.POST.get('email', student.user.email)
            student.user.save()
            
            # Update student profile
            try:
                profile = student.placement_profile
                profile.phone = request.POST.get('phone', profile.phone)
                profile.department = request.POST.get('department', profile.department)
                profile.graduation_year = int(request.POST.get('batch_year', profile.graduation_year or 0)) if request.POST.get('batch_year') else profile.graduation_year
                profile.cgpa = float(request.POST.get('cgpa', profile.cgpa or 0)) if request.POST.get('cgpa') else profile.cgpa
                profile.save()
            except StudentProfile.DoesNotExist:
                # Create profile if it doesn't exist
                StudentProfile.objects.create(
                    student=student,
                    phone=request.POST.get('phone', ''),
                    department=request.POST.get('department', ''),
                    graduation_year=int(request.POST.get('batch_year', 0)) if request.POST.get('batch_year') else None,
                    cgpa=float(request.POST.get('cgpa', 0)) if request.POST.get('cgpa') else 0.0
                )
            
            return JsonResponse({'success': True, 'message': 'Student updated successfully'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def edit_placement(request):
    """Edit placement record"""
    if request.method == 'POST':
        try:
            company = Company.objects.get(user=request.user)
            placement_id = request.POST.get('placement_id')
            
            # Get placement record
            placement = PlacementRecord.objects.get(id=placement_id, company=company)
            
            # Update placement data
            placement.job_title = request.POST.get('job_title', placement.job_title)
            placement.package_amount = float(request.POST.get('package_amount', placement.package_amount or 0)) if request.POST.get('package_amount') else placement.package_amount
            placement.stipend_amount = float(request.POST.get('stipend_amount', placement.stipend_amount or 0)) if request.POST.get('stipend_amount') else placement.stipend_amount
            placement.placement_date = datetime.strptime(request.POST.get('placement_date', placement.placement_date.strftime('%Y-%m-%d')), '%Y-%m-%d').date()
            placement.iqac_status = request.POST.get('iqac_status', placement.iqac_status)
            
            # Handle file upload
            if 'offer_letter' in request.FILES:
                placement.offer_letter = request.FILES['offer_letter']
            
            placement.save()
            
            return JsonResponse({'success': True, 'message': 'Placement record updated successfully'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def create_scheduled_class(request):
    """Create a scheduled class"""
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        messages.error(request, 'Teacher profile not found.')
        return redirect('teacher_home')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        scheduled_date_str = request.POST.get('scheduled_date')
        duration = request.POST.get('duration', 60)
        meeting_link = request.POST.get('meeting_link', '')
        meeting_password = request.POST.get('meeting_password', '')
        course_id = request.POST.get('course_id')
        
        if title and scheduled_date_str:
            try:
                # Parse scheduled date
                from datetime import datetime
                scheduled_date = datetime.strptime(scheduled_date_str, '%Y-%m-%dT%H:%M')
                
                # Get course if provided
                course = None
                if course_id:
                    course = Course.objects.get(id=course_id, instructor=teacher)
                
                # Create scheduled class
                scheduled_class = ScheduledClass.objects.create(
                    teacher=teacher,
                    course=course,
                    title=title,
                    description=description,
                    scheduled_date=scheduled_date,
                    duration_minutes=int(duration),
                    meeting_link=meeting_link,
                    meeting_password=meeting_password,
                    is_recurring=False,
                    is_completed=False
                )
                
                messages.success(request, 'Class scheduled successfully!')
                return redirect('teacher_home')
            except Exception as e:
                messages.error(request, f'Error creating scheduled class: {str(e)}')
        else:
            messages.error(request, 'Please fill in all required fields.')
    
    # Get teacher's courses
    courses = Course.objects.filter(instructor=teacher)
    
    context = {
        'teacher': teacher,
        'courses': courses,
        'user_role': 'teacher',
    }
    return render(request, 'teacher/create_schedule.html', context)

@login_required
def scheduled_classes(request):
    """View all scheduled classes"""
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        messages.error(request, 'Teacher profile not found.')
        return redirect('teacher_home')
    
    scheduled_classes = ScheduledClass.objects.filter(teacher=teacher).order_by('scheduled_date')
    
    # Separate upcoming and past classes
    upcoming_classes = [sc for sc in scheduled_classes if sc.is_upcoming()]
    past_classes = [sc for sc in scheduled_classes if not sc.is_upcoming()]
    
    context = {
        'teacher': teacher,
        'upcoming_classes': upcoming_classes,
        'past_classes': past_classes,
        'user_role': 'teacher',
    }
    return render(request, 'teacher/scheduled_classes.html', context)

def apply_job(request, job_id):
    """Job application form view"""
    try:
        job = Job.objects.get(id=job_id)
    except Job.DoesNotExist:
        messages.error(request, 'Job not found.')
        return redirect('jobs')
    
    if request.method == 'POST':
        # Get form data
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        education_details = request.POST.get('education_details')
        cover_letter = request.POST.get('cover_letter', '')
        resume = request.FILES.get('resume')
        
        # Validation
        if not all([full_name, email, phone, address, education_details]):
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'apply_job.html', {
                'job': job,
                'full_name': full_name,
                'email': email,
                'phone': phone,
                'address': address,
                'education_details': education_details,
                'cover_letter': cover_letter,
            })
        
        if not resume:
            messages.error(request, 'Please upload your resume.')
            return render(request, 'apply_job.html', {
                'job': job,
                'full_name': full_name,
                'email': email,
                'phone': phone,
                'address': address,
                'education_details': education_details,
                'cover_letter': cover_letter,
            })
        
        # Check if already applied
        if JobApplication.objects.filter(job=job, email=email).exists():
            messages.warning(request, 'You have already applied for this job.')
            return redirect('jobs')
        
        # Create application
        try:
            application = JobApplication.objects.create(
                job=job,
                user=request.user if request.user.is_authenticated else None,
                full_name=full_name,
                email=email,
                phone=phone,
                address=address,
                education_details=education_details,
                cover_letter=cover_letter,
                resume=resume,
                status='pending'
            )
            messages.success(request, 'Your application has been submitted successfully!')
            # If logged in as student, redirect to student dashboard to view applied jobs
            try:
                profile = UserProfile.objects.get(user=request.user)
                if profile.role == 'student':
                    return redirect('student_home')
            except UserProfile.DoesNotExist:
                pass
            return redirect('jobs')
        except Exception as e:
            messages.error(request, f'Error submitting application: {str(e)}')
    
    context = {
        'job': job,
    }
    return render(request, 'apply_job.html', context)

@login_required
def view_job_application(request, application_id):
    """View filled job application form"""
    try:
        # Get user profile to determine role
        profile = UserProfile.objects.get(user=request.user)
        
        if profile.role == 'student':
            # Students can only view their own applications
            application = JobApplication.objects.get(id=application_id, user=request.user)
        elif profile.role == 'company':
            # Companies can view applications for their jobs
            company = Company.objects.get(user=request.user)
            application = JobApplication.objects.get(
                id=application_id, 
                job__company=company.company_name
            )
        else:
            messages.error(request, 'Access denied.')
            return redirect('home')
            
    except JobApplication.DoesNotExist:
        messages.error(request, 'Application not found.')
        if profile.role == 'student':
            return redirect('student_home')
        else:
            return redirect('company_home')
    except Company.DoesNotExist:
        messages.error(request, 'Company profile not found.')
        return redirect('home')
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found.')
        return redirect('home')
    
    context = {
        'application': application,
        'job': application.job,
        'user_role': profile.role,
    }
    return render(request, 'view_job_application.html', context)

@login_required
def update_application_status(request):
    """Update job application status (Accept/Reject)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    try:
        application_id = request.POST.get('application_id')
        new_status = request.POST.get('status')
        
        if not application_id or not new_status:
            return JsonResponse({'success': False, 'error': 'Missing required parameters'})
        
        # Get the company
        company = Company.objects.get(user=request.user)
        
        # Get the application and verify it belongs to this company
        application = JobApplication.objects.get(
            id=application_id,
            job__company=company.company_name
        )
        
        # Update status
        application.status = new_status
        application.save()
        
        return JsonResponse({'success': True})
        
    except Company.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Company profile not found'})
    except JobApplication.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Application not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# Cart and Payment Views

@login_required
def add_to_cart(request, course_id):
    """Add course to cart"""
    try:
        course = Course.objects.get(id=course_id)
        cart_item, created = Cart.objects.get_or_create(
            user=request.user,
            course=course
        )
        if created:
            messages.success(request, f'{course.title} added to cart!')
        else:
            messages.info(request, f'{course.title} is already in your cart!')
    except Course.DoesNotExist:
        messages.error(request, 'Course not found!')
    
    return redirect('cart')

@login_required
def remove_from_cart(request, course_id):
    """Remove course from cart"""
    try:
        cart_item = Cart.objects.get(user=request.user, course_id=course_id)
        cart_item.delete()
        messages.success(request, 'Course removed from cart!')
    except Cart.DoesNotExist:
        messages.error(request, 'Course not found in cart!')
    
    return redirect('cart')

@login_required
def cart_view(request):
    """Display cart contents"""
    cart_items = Cart.objects.filter(user=request.user)
    total_amount = sum(item.course.price for item in cart_items)
    
    context = {
        'cart_items': cart_items,
        'total_amount': total_amount,
    }
    return render(request, 'cart.html', context)

@login_required
def checkout(request):
    """Checkout process"""
    cart_items = Cart.objects.filter(user=request.user)
    if not cart_items.exists():
        messages.error(request, 'Your cart is empty!')
        return redirect('cart')
    
    total_amount = sum(item.course.price for item in cart_items)
    
    if request.method == 'POST':
        # Create payment record
        import uuid
        payment_id = str(uuid.uuid4())
        
        payment = Payment.objects.create(
            user=request.user,
            amount=total_amount,
            payment_id=payment_id,
            status='pending'
        )
        
        # Add courses to payment
        for item in cart_items:
            payment.courses.add(item.course)
        
        # Redirect to payment page
        return redirect('payment', payment_id=payment_id)
    
    context = {
        'cart_items': cart_items,
        'total_amount': total_amount,
    }
    return render(request, 'checkout.html', context)

@login_required
def payment_view(request, payment_id):
    """Payment page"""
    try:
        payment = Payment.objects.get(payment_id=payment_id, user=request.user)
        courses = payment.courses.all()
        
        # If payment amount is ₹0, automatically process as successful
        if payment.amount == 0:
            payment.status = 'completed'
            payment.completed_at = timezone.now()
            payment.save()
            
            # Create or update enrollments (avoid unique constraint conflicts on user+course)
            for course in courses:
                Enrollment.objects.update_or_create(
                    user=request.user,
                    course=course,
                    defaults={'payment': payment, 'is_active': True}
                )
            
            # Clear cart
            Cart.objects.filter(user=request.user).delete()
            
            messages.success(request, 'Free course enrolled successfully! You are now enrolled in the courses.')
            return redirect('payment_success', payment_id=payment_id)
        
        if request.method == 'POST':
            payment_mode = request.POST.get('payment_mode', 'card')
            
            # Begin OTP flow instead of immediate success
            request.session['otp_payment_id'] = payment.payment_id
            request.session['otp_payment_mode'] = payment_mode
            # clear any previous code
            request.session.pop('otp_code', None)
            return redirect('payment_otp', payment_id=payment.payment_id)
        
        context = {
            'payment': payment,
            'courses': courses,
        }
        return render(request, 'payment.html', context)
    
    except Payment.DoesNotExist:
        messages.error(request, 'Payment not found!')
        return redirect('cart')

@login_required
def payment_success(request, payment_id):
    """Payment success page with PDF download"""
    try:
        payment = Payment.objects.get(payment_id=payment_id, user=request.user)
        courses = payment.courses.all()
        
        context = {
            'payment': payment,
            'courses': courses,
        }
        return render(request, 'payment_success.html', context)
    
    except Payment.DoesNotExist:
        messages.error(request, 'Payment not found!')
        return redirect('cart')

@login_required
def my_certificates(request):
    from .models import Certificate
    # Get all certificates for the user
    certs = Certificate.objects.filter(user=request.user).select_related('course')
    
    # Auto-create certificates for completed courses that don't have one yet
    try:
        student = Student.objects.get(user=request.user)
        # Get all completed courses (100% progress)
        completed_progress = StudentProgress.objects.filter(
            student=student,
            progress_percentage__gte=100
        ).select_related('course')
        
        for progress in completed_progress:
            # Check if certificate exists and course allows certificates
            if getattr(progress.course, 'certificate', True):
                Certificate.objects.get_or_create(
                    user=request.user,
                    course=progress.course,
                    defaults={'certificate_id': get_random_string(16)}
                )
        
        # Refresh the certificates list after auto-creation
        certs = Certificate.objects.filter(user=request.user).select_related('course').order_by('-issued_at')
    except Student.DoesNotExist:
        pass
    
    return render(request, 'certificates_list.html', { 'certificates': certs })

@login_required
def view_certificate(request, certificate_id):
    from .models import Certificate
    try:
        cert = Certificate.objects.get(certificate_id=certificate_id, user=request.user)
    except Certificate.DoesNotExist:
        messages.error(request, 'Certificate not found')
        return redirect('my_certificates')
    auto_print = request.GET.get('download') in ('1', 'true', 'yes')
    return render(request, 'certificate.html', { 'certificate': cert, 'auto_print': auto_print })

@login_required
def payment_otp(request, payment_id):
    """Two-step OTP verification for payment (demo)."""
    try:
        payment = Payment.objects.get(payment_id=payment_id, user=request.user)
        courses = payment.courses.all()
    except Payment.DoesNotExist:
        messages.error(request, 'Payment not found!')
        return redirect('cart')

    otp_sent_to = None
    otp_stage = 'choose'  # choose -> verify

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'send':
            # Generate a 6-digit OTP and store in session
            import random
            otp_code = f"{random.randint(100000, 999999)}"
            request.session['otp_code'] = otp_code
            # Destination selection
            method = request.POST.get('otp_method', 'email_same')
            other_email = request.POST.get('other_email')
            phone = request.POST.get('phone')
            if method == 'email_same':
                otp_sent_to = request.user.email
            elif method == 'other_email':
                otp_sent_to = other_email
            else:
                otp_sent_to = phone
            request.session['otp_sent_to'] = otp_sent_to
            otp_stage = 'verify'
            # Dev/demo hint to unblock testers
            messages.info(request, f"OTP has been sent to {otp_sent_to}. Demo OTP: {otp_code}")
        elif action == 'verify':
            entered = request.POST.get('otp')
            code = request.session.get('otp_code')
            if entered and code and entered == code:
                # Success: finalize payment and enroll
                payment.status = 'completed'
                payment.completed_at = timezone.now()
                payment.save()
                for course in courses:
                    Enrollment.objects.update_or_create(
                        user=request.user,
                        course=course,
                        defaults={'payment': payment, 'is_active': True}
                    )
                Cart.objects.filter(user=request.user).delete()
                # cleanup session
                for key in ('otp_code', 'otp_payment_id', 'otp_payment_mode', 'otp_sent_to'):
                    request.session.pop(key, None)
                messages.success(request, 'Payment successful! You are now enrolled in the courses.')
                return redirect('payment_success', payment_id=payment.payment_id)
            else:
                otp_stage = 'verify'
                messages.error(request, 'Invalid OTP. Please try again.')
                otp_sent_to = request.session.get('otp_sent_to')

    context = {
        'payment': payment,
        'courses': courses,
        'otp_stage': otp_stage,
        'otp_sent_to': otp_sent_to or request.session.get('otp_sent_to'),
        'demo_otp': request.session.get('otp_code'),
        'user_email': request.user.email,
    }
    return render(request, 'payment_otp.html', context)

@login_required
def download_receipt(request, payment_id):
    """Generate and download PDF receipt"""
    try:
        payment = Payment.objects.get(payment_id=payment_id, user=request.user)
        courses = payment.courses.all()
        
        # Generate PDF
        from django.http import HttpResponse
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        import io
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        
        # Create custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1,  # Center alignment
        )
        
        # Build PDF content
        story = []
        
        # Title
        story.append(Paragraph("Skillora - Payment Receipt", title_style))
        story.append(Spacer(1, 20))
        
        # Payment details
        story.append(Paragraph(f"<b>Payment ID:</b> {payment.payment_id}", styles['Normal']))
        story.append(Paragraph(f"<b>Date:</b> {payment.completed_at.strftime('%B %d, %Y')}", styles['Normal']))
        story.append(Paragraph(f"<b>Student:</b> {payment.user.get_full_name() or payment.user.username}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Courses table
        story.append(Paragraph("<b>Enrolled Courses:</b>", styles['Heading2']))
        story.append(Spacer(1, 10))
        
        table_data = [['Course Title', 'Category', 'Price']]
        for course in courses:
            table_data.append([course.title, course.category, f"₹{course.price}"])
        
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        story.append(Spacer(1, 20))
        
        # Total
        story.append(Paragraph(f"<b>Total Amount:</b> ₹{payment.amount}", styles['Heading2']))
        story.append(Spacer(1, 20))
        
        # Footer
        story.append(Paragraph("Thank you for choosing Skillora!", styles['Normal']))
        story.append(Paragraph("Visit our website: www.skillora.com", styles['Normal']))
        
        # Build PDF
        doc.build(story)
        
        # Get PDF content
        pdf_content = buffer.getvalue()
        buffer.close()
        
        # Create response
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="receipt_{payment_id}.pdf"'
        
        return response
    
    except Payment.DoesNotExist:
        messages.error(request, 'Payment not found!')
        return redirect('cart')

def skill_category_detail(request, category_name):
    """Show course detail page for a specific skill category"""
    # Map skill categories to course titles
    category_mapping = {
        'microsoft-excel': 'Microsoft Excel',
        'aws': 'AWS',
        'python': 'Python',
        'java': 'Java',
        'web-design': 'Web Design',
        'web-development': 'Web Development',
        'mysql': 'MySQL',
        'ui-ux-design': 'UI/UX Design',
        'cybersecurity': 'Cybersecurity',
        'digital-marketing': 'Digital Marketing',
        'ai-machine-learning': 'AI and Machine Learning',
        'cloud-computing': 'Cloud Computing',
        'project-management': 'Project Management',
        'ds': 'DS',
        'dsa': 'dsa'
    }
    
    course_title = category_mapping.get(category_name.lower())
    if not course_title:
        messages.error(request, 'Skill category not found!')
        return redirect('courses')
    
    try:
        course = Course.objects.get(title=course_title)
        related_courses = Course.objects.filter(category=course.category).exclude(id=course.id)[:3]
    except Course.DoesNotExist:
        messages.error(request, 'Course not found!')
        return redirect('courses')
    
    context = {
        'course': course,
        'related_courses': related_courses,
    }
    return render(request, 'single.html', context)

@login_required
def chatbot_api(request):
    """Career guidance chatbot API endpoint"""
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        message = data.get('message', '').lower()
        
        # Career database
        careers_db = {
            # Technology careers
            'software developer': {
                'title': 'Software Developer',
                'description': 'Design, develop, and maintain software applications and systems.',
                'skills': 'Programming Languages (Python, Java, JavaScript), Problem Solving, Software Architecture, Database Management',
                'salary': '$70,000 - $150,000+',
                'growth': 'High (22% growth expected)',
                'roadmap': [
                    {'step': 'Learn programming fundamentals', 'duration': '3 months'},
                    {'step': 'Master a programming language (Python/Java)', 'duration': '4 months'},
                    {'step': 'Learn data structures and algorithms', 'duration': '3 months'},
                    {'step': 'Build projects and portfolio', 'duration': '4 months'},
                    {'step': 'Learn version control (Git)', 'duration': '1 month'},
                    {'step': 'Practice coding interviews', 'duration': '2 months'},
                ]
            },
            'data scientist': {
                'title': 'Data Scientist',
                'description': 'Analyze complex data to help organizations make informed decisions.',
                'skills': 'Python/R Programming, Statistics, Machine Learning, Data Visualization',
                'salary': '$80,000 - $160,000+',
                'growth': 'Very High (35% growth expected)',
                'roadmap': [
                    {'step': 'Learn Python and statistics', 'duration': '3 months'},
                    {'step': 'Master data analysis libraries (Pandas, NumPy)', 'duration': '2 months'},
                    {'step': 'Learn machine learning fundamentals', 'duration': '4 months'},
                    {'step': 'Practice with real datasets', 'duration': '3 months'},
                    {'step': 'Learn data visualization tools', 'duration': '2 months'},
                    {'step': 'Build data science portfolio', 'duration': '3 months'},
                ]
            },
            'cybersecurity': {
                'title': 'Cybersecurity Specialist',
                'description': 'Protect organizations from digital threats and cyber attacks.',
                'skills': 'Network Security, Ethical Hacking, Risk Assessment, Security Frameworks',
                'salary': '$75,000 - $140,000+',
                'growth': 'Very High (33% growth expected)',
                'roadmap': [
                    {'step': 'Learn networking fundamentals', 'duration': '2 months'},
                    {'step': 'Study cybersecurity principles', 'duration': '3 months'},
                    {'step': 'Get CompTIA Security+ certification', 'duration': '2 months'},
                    {'step': 'Practice ethical hacking', 'duration': '4 months'},
                    {'step': 'Learn security tools and frameworks', 'duration': '3 months'},
                    {'step': 'Gain hands-on experience through labs', 'duration': '3 months'},
                ]
            },
            'web developer': {
                'title': 'Web Developer',
                'description': 'Build and maintain websites and web applications using various programming languages.',
                'skills': 'HTML, CSS, JavaScript, React, Node.js, Database Management, API Integration',
                'salary': '$60,000 - $130,000+',
                'growth': 'High (13% growth expected)',
                'roadmap': [
                    {'step': 'Learn HTML, CSS, and JavaScript basics', 'duration': '3 months'},
                    {'step': 'Master frontend frameworks (React, Vue)', 'duration': '4 months'},
                    {'step': 'Learn backend development (Node.js, Python)', 'duration': '4 months'},
                    {'step': 'Understand databases and APIs', 'duration': '3 months'},
                    {'step': 'Build full-stack projects', 'duration': '4 months'},
                    {'step': 'Deploy and maintain web applications', 'duration': '2 months'},
                ]
            },
            'cloud engineer': {
                'title': 'Cloud Engineer',
                'description': 'Design, implement, and manage cloud infrastructure and services.',
                'skills': 'AWS, Azure, GCP, Docker, Kubernetes, Infrastructure as Code, DevOps',
                'salary': '$90,000 - $160,000+',
                'growth': 'Very High (27% growth expected)',
                'roadmap': [
                    {'step': 'Learn cloud fundamentals (AWS/Azure)', 'duration': '3 months'},
                    {'step': 'Master cloud services and architecture', 'duration': '4 months'},
                    {'step': 'Learn containerization (Docker, Kubernetes)', 'duration': '3 months'},
                    {'step': 'Study Infrastructure as Code (Terraform)', 'duration': '2 months'},
                    {'step': 'Get cloud certifications', 'duration': '3 months'},
                    {'step': 'Build and deploy cloud projects', 'duration': '4 months'},
                ]
            },
            'devops engineer': {
                'title': 'DevOps Engineer',
                'description': 'Bridge development and operations to improve software delivery and infrastructure.',
                'skills': 'CI/CD, Docker, Kubernetes, Jenkins, Git, Linux, Monitoring Tools',
                'salary': '$85,000 - $150,000+',
                'growth': 'Very High (21% growth expected)',
                'roadmap': [
                    {'step': 'Learn Linux and command line', 'duration': '2 months'},
                    {'step': 'Master version control (Git)', 'duration': '1 month'},
                    {'step': 'Learn CI/CD pipelines (Jenkins, GitHub Actions)', 'duration': '3 months'},
                    {'step': 'Study containerization and orchestration', 'duration': '4 months'},
                    {'step': 'Learn monitoring and logging tools', 'duration': '2 months'},
                    {'step': 'Gain hands-on DevOps experience', 'duration': '4 months'},
                ]
            },
            'mobile developer': {
                'title': 'Mobile App Developer',
                'description': 'Create applications for iOS and Android mobile devices.',
                'skills': 'Swift, Kotlin, React Native, Flutter, Mobile UI/UX, App Store Deployment',
                'salary': '$70,000 - $140,000+',
                'growth': 'High (22% growth expected)',
                'roadmap': [
                    {'step': 'Learn mobile development fundamentals', 'duration': '2 months'},
                    {'step': 'Choose platform (iOS/Android) or cross-platform', 'duration': '1 month'},
                    {'step': 'Master mobile programming language', 'duration': '4 months'},
                    {'step': 'Learn mobile UI/UX design principles', 'duration': '2 months'},
                    {'step': 'Build mobile app projects', 'duration': '4 months'},
                    {'step': 'Publish apps to app stores', 'duration': '2 months'},
                ]
            },
            # Healthcare careers
            'nurse': {
                'title': 'Registered Nurse',
                'description': 'Provide patient care, educate patients and the public about health conditions.',
                'skills': 'Patient Care, Medical Knowledge, Communication, Critical Thinking, Empathy',
                'salary': '$60,000 - $120,000+',
                'growth': 'High (15% growth expected)',
                'roadmap': [
                    {'step': 'Complete nursing prerequisites', 'duration': '1 year'},
                    {'step': 'Earn nursing degree (ADN or BSN)', 'duration': '2-4 years'},
                    {'step': 'Pass NCLEX-RN exam', 'duration': '2 months'},
                    {'step': 'Obtain state nursing license', 'duration': '1 month'},
                    {'step': 'Gain clinical experience', 'duration': '6 months'},
                    {'step': 'Consider specialization certifications', 'duration': '3 months'},
                ]
            },
            'physician assistant': {
                'title': 'Physician Assistant',
                'description': 'Practice medicine under the supervision of physicians and surgeons.',
                'skills': 'Medical Diagnosis, Treatment Planning, Patient Care, Medical Procedures',
                'salary': '$100,000 - $150,000+',
                'growth': 'Very High (31% growth expected)',
                'roadmap': [
                    {'step': 'Complete prerequisite courses', 'duration': '2 years'},
                    {'step': 'Gain healthcare experience', 'duration': '6 months'},
                    {'step': 'Complete PA program (Master\'s degree)', 'duration': '2-3 years'},
                    {'step': 'Pass PANCE exam', 'duration': '1 month'},
                    {'step': 'Obtain state license', 'duration': '1 month'},
                    {'step': 'Maintain certification with CME', 'duration': 'Ongoing'},
                ]
            },
            'physical therapist': {
                'title': 'Physical Therapist',
                'description': 'Help patients recover from injuries and improve movement and function.',
                'skills': 'Patient Assessment, Exercise Therapy, Manual Therapy, Rehabilitation Planning',
                'salary': '$70,000 - $100,000+',
                'growth': 'High (17% growth expected)',
                'roadmap': [
                    {'step': 'Complete prerequisite courses', 'duration': '2 years'},
                    {'step': 'Earn Doctor of Physical Therapy (DPT) degree', 'duration': '3 years'},
                    {'step': 'Complete clinical rotations', 'duration': '1 year'},
                    {'step': 'Pass NPTE licensing exam', 'duration': '2 months'},
                    {'step': 'Obtain state license', 'duration': '1 month'},
                    {'step': 'Consider specialization (optional)', 'duration': '1 year'},
                ]
            },
            'pharmacist': {
                'title': 'Pharmacist',
                'description': 'Dispense medications and provide pharmaceutical care to patients.',
                'skills': 'Medication Management, Drug Interactions, Patient Counseling, Pharmacy Law',
                'salary': '$120,000 - $150,000+',
                'growth': 'Moderate (2% growth expected)',
                'roadmap': [
                    {'step': 'Complete prerequisite courses', 'duration': '2-3 years'},
                    {'step': 'Earn Doctor of Pharmacy (PharmD) degree', 'duration': '4 years'},
                    {'step': 'Complete pharmacy internships', 'duration': '1 year'},
                    {'step': 'Pass NAPLEX and MPJE exams', 'duration': '2 months'},
                    {'step': 'Obtain state pharmacy license', 'duration': '1 month'},
                    {'step': 'Consider residency or specialization', 'duration': '1-2 years'},
                ]
            },
            'medical technologist': {
                'title': 'Medical Technologist',
                'description': 'Perform laboratory tests to help diagnose and treat diseases.',
                'skills': 'Laboratory Testing, Medical Equipment, Data Analysis, Quality Control',
                'salary': '$55,000 - $80,000+',
                'growth': 'Moderate (7% growth expected)',
                'roadmap': [
                    {'step': 'Earn bachelor\'s degree in medical technology', 'duration': '4 years'},
                    {'step': 'Complete clinical laboratory training', 'duration': '1 year'},
                    {'step': 'Pass ASCP certification exam', 'duration': '2 months'},
                    {'step': 'Obtain state license (if required)', 'duration': '1 month'},
                    {'step': 'Gain laboratory experience', 'duration': '6 months'},
                    {'step': 'Pursue specialization (optional)', 'duration': '1 year'},
                ]
            },
            'healthcare administrator': {
                'title': 'Healthcare Administrator',
                'description': 'Manage healthcare facilities and ensure efficient operations.',
                'skills': 'Healthcare Management, Budgeting, Regulatory Compliance, Staff Management',
                'salary': '$70,000 - $120,000+',
                'growth': 'High (32% growth expected)',
                'roadmap': [
                    {'step': 'Earn bachelor\'s degree in healthcare administration', 'duration': '4 years'},
                    {'step': 'Gain entry-level healthcare experience', 'duration': '1-2 years'},
                    {'step': 'Pursue Master\'s in Healthcare Administration (MHA)', 'duration': '2 years'},
                    {'step': 'Complete administrative residency', 'duration': '1 year'},
                    {'step': 'Get healthcare management certification', 'duration': '3 months'},
                    {'step': 'Advance to management positions', 'duration': '2-3 years'},
                ]
            },
            # Creative Arts careers
            'graphic designer': {
                'title': 'Graphic Designer',
                'description': 'Create visual concepts to communicate ideas that inspire and inform consumers.',
                'skills': 'Adobe Creative Suite, Typography, Color Theory, Layout Design, Branding',
                'salary': '$45,000 - $85,000+',
                'growth': 'Moderate (3% growth expected)',
                'roadmap': [
                    {'step': 'Learn design fundamentals', 'duration': '3 months'},
                    {'step': 'Master Adobe Creative Suite', 'duration': '6 months'},
                    {'step': 'Build design portfolio', 'duration': '6 months'},
                    {'step': 'Study typography and color theory', 'duration': '3 months'},
                    {'step': 'Gain freelance or internship experience', 'duration': '6 months'},
                    {'step': 'Specialize in a design niche', 'duration': '6 months'},
                ]
            },
            'ui/ux designer': {
                'title': 'UI/UX Designer',
                'description': 'Design user interfaces and experiences for digital products.',
                'skills': 'User Research, Wireframing, Prototyping, Figma/Sketch, Usability Testing',
                'salary': '$70,000 - $130,000+',
                'growth': 'High (13% growth expected)',
                'roadmap': [
                    {'step': 'Learn design principles', 'duration': '3 months'},
                    {'step': 'Master design tools (Figma, Sketch)', 'duration': '2 months'},
                    {'step': 'Study user research methods', 'duration': '3 months'},
                    {'step': 'Learn prototyping and wireframing', 'duration': '2 months'},
                    {'step': 'Build UX portfolio', 'duration': '4 months'},
                    {'step': 'Gain real-world project experience', 'duration': '6 months'},
                ]
            },
            'video editor': {
                'title': 'Video Editor',
                'description': 'Edit and produce video content for various media platforms.',
                'skills': 'Video Editing Software, Color Grading, Audio Mixing, Storytelling, Motion Graphics',
                'salary': '$45,000 - $85,000+',
                'growth': 'High (12% growth expected)',
                'roadmap': [
                    {'step': 'Learn video editing fundamentals', 'duration': '3 months'},
                    {'step': 'Master editing software (Premiere Pro, Final Cut)', 'duration': '4 months'},
                    {'step': 'Study color grading and audio mixing', 'duration': '3 months'},
                    {'step': 'Learn motion graphics and effects', 'duration': '4 months'},
                    {'step': 'Build video editing portfolio', 'duration': '6 months'},
                    {'step': 'Gain freelance or production experience', 'duration': '6 months'},
                ]
            },
            'animator': {
                'title': 'Animator',
                'description': 'Create animated content for films, games, and digital media.',
                'skills': '2D/3D Animation, Character Design, Storyboarding, Animation Software, Motion Principles',
                'salary': '$50,000 - $100,000+',
                'growth': 'Moderate (5% growth expected)',
                'roadmap': [
                    {'step': 'Learn animation fundamentals and principles', 'duration': '4 months'},
                    {'step': 'Master animation software (After Effects, Maya, Blender)', 'duration': '6 months'},
                    {'step': 'Study character design and storyboarding', 'duration': '3 months'},
                    {'step': 'Practice 2D and 3D animation techniques', 'duration': '6 months'},
                    {'step': 'Build animation portfolio and demo reel', 'duration': '6 months'},
                    {'step': 'Gain industry experience through internships', 'duration': '6 months'},
                ]
            },
            'photographer': {
                'title': 'Photographer',
                'description': 'Capture images for commercial, artistic, or editorial purposes.',
                'skills': 'Camera Operation, Lighting, Composition, Photo Editing, Client Communication',
                'salary': '$35,000 - $75,000+',
                'growth': 'Moderate (4% growth expected)',
                'roadmap': [
                    {'step': 'Learn photography fundamentals', 'duration': '3 months'},
                    {'step': 'Master camera settings and equipment', 'duration': '2 months'},
                    {'step': 'Study lighting and composition techniques', 'duration': '3 months'},
                    {'step': 'Learn photo editing (Lightroom, Photoshop)', 'duration': '3 months'},
                    {'step': 'Build photography portfolio', 'duration': '6 months'},
                    {'step': 'Gain experience through freelance work', 'duration': '6 months'},
                ]
            },
            'content creator': {
                'title': 'Content Creator',
                'description': 'Create engaging content for social media, blogs, and digital platforms.',
                'skills': 'Content Strategy, Social Media, Video Production, Writing, SEO, Analytics',
                'salary': '$40,000 - $90,000+',
                'growth': 'High (10% growth expected)',
                'roadmap': [
                    {'step': 'Learn content creation fundamentals', 'duration': '2 months'},
                    {'step': 'Master social media platforms', 'duration': '3 months'},
                    {'step': 'Study content strategy and SEO', 'duration': '2 months'},
                    {'step': 'Learn basic video and photo editing', 'duration': '3 months'},
                    {'step': 'Build personal brand and audience', 'duration': '6 months'},
                    {'step': 'Monetize content and partnerships', 'duration': '6 months'},
                ]
            },
            # Business careers
            'business analyst': {
                'title': 'Business Analyst',
                'description': 'Analyze business processes and recommend solutions to improve efficiency.',
                'skills': 'Data Analysis, Process Improvement, Requirements Gathering, SQL, Project Management',
                'salary': '$65,000 - $110,000+',
                'growth': 'High (14% growth expected)',
                'roadmap': [
                    {'step': 'Earn business or related degree', 'duration': '3-4 years'},
                    {'step': 'Learn data analysis tools (Excel, SQL)', 'duration': '3 months'},
                    {'step': 'Study business process modeling', 'duration': '2 months'},
                    {'step': 'Gain experience in business operations', 'duration': '6 months'},
                    {'step': 'Get certified (CBAP or PMI-PBA)', 'duration': '3 months'},
                    {'step': 'Build analytical portfolio', 'duration': '3 months'},
                ]
            },
            'marketing manager': {
                'title': 'Marketing Manager',
                'description': 'Plan and execute marketing strategies to promote products and services.',
                'skills': 'Digital Marketing, SEO, Content Strategy, Analytics, Brand Management',
                'salary': '$70,000 - $140,000+',
                'growth': 'High (10% growth expected)',
                'roadmap': [
                    {'step': 'Earn marketing or business degree', 'duration': '3-4 years'},
                    {'step': 'Learn digital marketing fundamentals', 'duration': '3 months'},
                    {'step': 'Master marketing tools (Google Analytics, Ads)', 'duration': '3 months'},
                    {'step': 'Gain marketing internship or entry role', 'duration': '6 months'},
                    {'step': 'Build marketing campaign portfolio', 'duration': '6 months'},
                    {'step': 'Get marketing certifications', 'duration': '2 months'},
                ]
            },
            'financial analyst': {
                'title': 'Financial Analyst',
                'description': 'Analyze financial data to help businesses make investment decisions.',
                'skills': 'Financial Modeling, Excel, Data Analysis, Risk Assessment, Financial Reporting',
                'salary': '$60,000 - $110,000+',
                'growth': 'High (9% growth expected)',
                'roadmap': [
                    {'step': 'Earn finance or accounting degree', 'duration': '3-4 years'},
                    {'step': 'Learn financial modeling and Excel', 'duration': '3 months'},
                    {'step': 'Study financial analysis techniques', 'duration': '3 months'},
                    {'step': 'Gain internship in finance or accounting', 'duration': '6 months'},
                    {'step': 'Get financial certifications (CFA, CPA)', 'duration': '1-2 years'},
                    {'step': 'Build financial analysis portfolio', 'duration': '6 months'},
                ]
            },
            'project manager': {
                'title': 'Project Manager',
                'description': 'Plan, execute, and oversee projects to ensure successful completion.',
                'skills': 'Project Planning, Risk Management, Team Leadership, Agile/Scrum, Communication',
                'salary': '$70,000 - $130,000+',
                'growth': 'High (7% growth expected)',
                'roadmap': [
                    {'step': 'Earn business or related degree', 'duration': '3-4 years'},
                    {'step': 'Learn project management fundamentals', 'duration': '3 months'},
                    {'step': 'Study Agile and Scrum methodologies', 'duration': '2 months'},
                    {'step': 'Get PMP or Agile certification', 'duration': '3 months'},
                    {'step': 'Gain project management experience', 'duration': '1-2 years'},
                    {'step': 'Build project portfolio and case studies', 'duration': '6 months'},
                ]
            },
            'human resources manager': {
                'title': 'Human Resources Manager',
                'description': 'Oversee HR functions including recruitment, employee relations, and benefits.',
                'skills': 'Recruitment, Employee Relations, HR Policies, Compensation, Training & Development',
                'salary': '$65,000 - $120,000+',
                'growth': 'Moderate (6% growth expected)',
                'roadmap': [
                    {'step': 'Earn HR or business degree', 'duration': '3-4 years'},
                    {'step': 'Learn HR fundamentals and labor laws', 'duration': '3 months'},
                    {'step': 'Gain HR internship or entry-level role', 'duration': '6 months'},
                    {'step': 'Get HR certification (SHRM, PHR)', 'duration': '3 months'},
                    {'step': 'Build experience in various HR functions', 'duration': '2-3 years'},
                    {'step': 'Advance to HR management positions', 'duration': '2-3 years'},
                ]
            },
            'sales manager': {
                'title': 'Sales Manager',
                'description': 'Lead sales teams and develop strategies to achieve revenue targets.',
                'skills': 'Sales Strategy, Team Leadership, Customer Relationship Management, Negotiation',
                'salary': '$60,000 - $140,000+',
                'growth': 'Moderate (5% growth expected)',
                'roadmap': [
                    {'step': 'Start in entry-level sales position', 'duration': '1-2 years'},
                    {'step': 'Learn sales techniques and CRM tools', 'duration': '3 months'},
                    {'step': 'Achieve consistent sales performance', 'duration': '1-2 years'},
                    {'step': 'Develop leadership and coaching skills', 'duration': '6 months'},
                    {'step': 'Get sales management training', 'duration': '3 months'},
                    {'step': 'Advance to sales manager role', 'duration': '1-2 years'},
                ]
            },
            # Education careers
            'teacher': {
                'title': 'Teacher',
                'description': 'Educate students and help them develop knowledge and skills.',
                'skills': 'Curriculum Development, Classroom Management, Communication, Patience, Subject Expertise',
                'salary': '$40,000 - $80,000+',
                'growth': 'Moderate (4% growth expected)',
                'roadmap': [
                    {'step': 'Earn bachelor\'s degree in education', 'duration': '3-4 years'},
                    {'step': 'Complete student teaching program', 'duration': '4 months'},
                    {'step': 'Pass teaching certification exams', 'duration': '2 months'},
                    {'step': 'Obtain state teaching license', 'duration': '1 month'},
                    {'step': 'Gain classroom experience', 'duration': '1 year'},
                    {'step': 'Pursue master\'s degree (optional)', 'duration': '1-2 years'},
                ]
            },
            'instructional designer': {
                'title': 'Instructional Designer',
                'description': 'Design and develop educational programs and materials.',
                'skills': 'Learning Theory, Curriculum Design, eLearning Tools, Assessment Design',
                'salary': '$55,000 - $95,000+',
                'growth': 'High (11% growth expected)',
                'roadmap': [
                    {'step': 'Earn degree in education or instructional design', 'duration': '3-4 years'},
                    {'step': 'Learn eLearning authoring tools', 'duration': '3 months'},
                    {'step': 'Study learning theories and models', 'duration': '3 months'},
                    {'step': 'Build instructional design portfolio', 'duration': '6 months'},
                    {'step': 'Gain experience in educational settings', 'duration': '6 months'},
                    {'step': 'Get instructional design certification', 'duration': '2 months'},
                ]
            },
            'school counselor': {
                'title': 'School Counselor',
                'description': 'Provide academic, career, and personal guidance to students.',
                'skills': 'Counseling, Student Assessment, Career Guidance, Crisis Intervention, Communication',
                'salary': '$50,000 - $85,000+',
                'growth': 'High (10% growth expected)',
                'roadmap': [
                    {'step': 'Earn bachelor\'s degree in psychology or education', 'duration': '4 years'},
                    {'step': 'Complete master\'s in school counseling', 'duration': '2 years'},
                    {'step': 'Complete supervised counseling internship', 'duration': '1 year'},
                    {'step': 'Pass state counseling certification exam', 'duration': '2 months'},
                    {'step': 'Obtain state school counselor license', 'duration': '1 month'},
                    {'step': 'Gain experience in school settings', 'duration': '1-2 years'},
                ]
            },
            'curriculum developer': {
                'title': 'Curriculum Developer',
                'description': 'Design and develop educational curricula and learning materials.',
                'skills': 'Curriculum Design, Educational Standards, Assessment Development, Content Creation',
                'salary': '$55,000 - $90,000+',
                'growth': 'Moderate (6% growth expected)',
                'roadmap': [
                    {'step': 'Earn degree in education or subject area', 'duration': '3-4 years'},
                    {'step': 'Gain teaching experience', 'duration': '2-3 years'},
                    {'step': 'Study curriculum design principles', 'duration': '3 months'},
                    {'step': 'Learn educational technology tools', 'duration': '2 months'},
                    {'step': 'Build curriculum development portfolio', 'duration': '6 months'},
                    {'step': 'Get curriculum design certification', 'duration': '3 months'},
                ]
            },
            'educational administrator': {
                'title': 'Educational Administrator',
                'description': 'Manage educational institutions and oversee academic programs.',
                'skills': 'School Administration, Budget Management, Staff Supervision, Policy Development',
                'salary': '$75,000 - $120,000+',
                'growth': 'Moderate (5% growth expected)',
                'roadmap': [
                    {'step': 'Earn bachelor\'s degree in education', 'duration': '4 years'},
                    {'step': 'Gain teaching experience', 'duration': '3-5 years'},
                    {'step': 'Earn master\'s in educational administration', 'duration': '2 years'},
                    {'step': 'Complete administrative internship', 'duration': '1 year'},
                    {'step': 'Get administrative certification', 'duration': '3 months'},
                    {'step': 'Advance to administrative positions', 'duration': '2-3 years'},
                ]
            },
            'online course creator': {
                'title': 'Online Course Creator',
                'description': 'Design and create online courses for e-learning platforms.',
                'skills': 'Course Design, Video Production, Learning Management Systems, Content Creation',
                'salary': '$40,000 - $100,000+',
                'growth': 'Very High (20% growth expected)',
                'roadmap': [
                    {'step': 'Identify expertise and course topic', 'duration': '1 month'},
                    {'step': 'Learn course design principles', 'duration': '2 months'},
                    {'step': 'Master video production and editing', 'duration': '3 months'},
                    {'step': 'Learn LMS platforms (Udemy, Teachable)', 'duration': '1 month'},
                    {'step': 'Create and launch first course', 'duration': '3 months'},
                    {'step': 'Build course portfolio and student base', 'duration': '6 months'},
                ]
            },
        }
        
        # Interest keywords mapping
        interest_keywords = {
            # Technology keywords
            'technology': ['software developer', 'data scientist', 'web developer', 'cloud engineer'],
            'programming': ['software developer', 'web developer'],
            'data': ['data scientist'],
            'security': ['cybersecurity'],
            'cyber': ['cybersecurity'],
            'web': ['web developer'],
            'cloud': ['cloud engineer'],
            'devops': ['devops engineer'],
            'mobile': ['mobile developer'],
            'app': ['mobile developer'],
            # Healthcare keywords
            'healthcare': ['nurse', 'physician assistant', 'physical therapist', 'pharmacist'],
            'health': ['nurse', 'physician assistant', 'physical therapist'],
            'medical': ['nurse', 'physician assistant', 'medical technologist', 'healthcare administrator'],
            'nursing': ['nurse'],
            'therapy': ['physical therapist'],
            'pharmacy': ['pharmacist'],
            'hospital': ['healthcare administrator', 'nurse'],
            # Creative Arts keywords
            'creative arts': ['graphic designer', 'ui/ux designer', 'video editor', 'animator', 'photographer'],
            'creative': ['graphic designer', 'ui/ux designer', 'video editor', 'animator', 'photographer', 'content creator'],
            'art': ['graphic designer', 'animator', 'photographer'],
            'design': ['graphic designer', 'ui/ux designer'],
            'video': ['video editor'],
            'animation': ['animator'],
            'photography': ['photographer'],
            'content': ['content creator'],
            'social media': ['content creator'],
            # Business keywords
            'business': ['business analyst', 'marketing manager', 'financial analyst', 'project manager'],
            'marketing': ['marketing manager'],
            'analyst': ['business analyst', 'financial analyst'],
            'finance': ['financial analyst'],
            'project': ['project manager'],
            'management': ['project manager', 'human resources manager', 'sales manager'],
            'hr': ['human resources manager'],
            'human resources': ['human resources manager'],
            'sales': ['sales manager'],
            # Education keywords
            'education': ['teacher', 'instructional designer', 'school counselor', 'curriculum developer'],
            'teaching': ['teacher'],
            'instructional': ['instructional designer'],
            'counseling': ['school counselor'],
            'counselor': ['school counselor'],
            'curriculum': ['curriculum developer'],
            'administrator': ['educational administrator'],
            'online': ['online course creator'],
            'course': ['online course creator', 'curriculum developer'],
        }
        
        # Determine career based on message
        suggested_careers = []
        for keyword, careers in interest_keywords.items():
            if keyword in message:
                suggested_careers.extend(careers)
        
        # If no match, check for direct career mentions
        for career_name in careers_db.keys():
            if career_name in message:
                suggested_careers = [career_name]
                break
        
        # Default response
        if not suggested_careers:
            return JsonResponse({
                'type': 'text',
                'message': "Hello! I'm your Career Guidance Assistant. I can help you discover careers based on your interests, provide detailed career information, and create personalized roadmaps. What are you passionate about?",
                'suggestions': ['Technology', 'Healthcare', 'Creative Arts', 'Business', 'Education']
            })
        
        # Return career suggestions (up to 4 careers)
        careers_data = []
        # Remove duplicates while preserving order
        seen = set()
        unique_careers = []
        for career_key in suggested_careers:
            if career_key not in seen:
                seen.add(career_key)
                unique_careers.append(career_key)
        
        for career_key in unique_careers[:4]:  # Limit to 4 careers
            if career_key in careers_db:
                careers_data.append(careers_db[career_key])
        
        if careers_data:
            return JsonResponse({
                'type': 'careers',
                'message': 'Great! Based on your interests, here are some career options that might be perfect for you.',
                'careers': careers_data
            })
        
        return JsonResponse({
            'type': 'text',
            'message': "I can help you with:\n• Finding careers based on your interests\n• Providing detailed career information\n• Creating personalized career roadmaps\n• Salary and growth prospects\n\nWhat would you like to explore today?",
            'suggestions': ['Technology', 'Healthcare', 'Creative Arts', 'Business', 'Education']
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

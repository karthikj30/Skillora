from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import json
from .models import (Course, Instructor, Job, Testimonial, TeamMember, Contact, UserProfile, 
                     Student, Teacher, Company, Internship, InternshipApplication, StudentProfile, 
                     PlacementCell, Mentor, InternshipFeedback, Notification, CourseMaterial, 
                     Assignment, AssignmentSubmission, CourseAnnouncement, StudentProgress)
from .forms import (ContactForm, UserRegistrationForm, StudentProfileForm, TeacherProfileForm, 
                    CompanyProfileForm, UserProfileForm, CourseMaterialForm, AssignmentForm, 
                    CourseAnnouncementForm, AssignmentSubmissionForm, GradeSubmissionForm)
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Q, Count, Avg

def home(request):
    """Home page view - redirects based on user role"""
    if request.user.is_authenticated:
        try:
            profile = UserProfile.objects.get(user=request.user)
            if profile.role == 'teacher':
                return redirect('teacher_home')
            elif profile.role == 'company':
                return redirect('company_home')
            elif profile.role == 'placement_cell':
                return redirect('placement_cell_home')
            elif profile.role == 'mentor':
                return redirect('mentor_home')
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
    # Compute progress stats from JSON field mapping course_id -> percent
    progress_map = student.progress or {}
    progress_values = list(progress_map.values()) if isinstance(progress_map, dict) else []
    avg_progress = round(sum(progress_values) / len(progress_values), 2) if progress_values else 0.0
    completed_courses = 0
    if isinstance(progress_map, dict) and progress_map:
        completed_courses = sum(1 for v in progress_map.values() if float(v) >= 100)

    recommended_courses = Course.objects.exclude(id__in=enrolled_courses.values_list('id', flat=True))[:6]

    # Build completed courses list (>=100%)
    completed_course_ids = []
    if isinstance(progress_map, dict):
        for cid, pct in progress_map.items():
            try:
                if float(pct) >= 100:
                    completed_course_ids.append(int(cid))
            except Exception:
                continue
    completed_courses_qs = Course.objects.filter(id__in=completed_course_ids)

    context = {
        'user_role': 'student',
        'student': student,
        'enrolled_courses': enrolled_courses,
        'recommended_courses': recommended_courses,
        'total_enrolled': enrolled_courses.count(),
        'completed_courses': completed_courses,
        'avg_progress': avg_progress,
        'progress_map': progress_map,
        'progress_map_json': json.dumps(progress_map or {}),
        'completed_courses_list': completed_courses_qs,
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

    progress_map = student.progress or {}
    pct = 0
    try:
        pct = float(progress_map.get(str(course.id), progress_map.get(course.id, 0)))
    except Exception:
        pct = 0
    if pct < 100:
        messages.error(request, 'Complete the course to view certificate.')
        return redirect('student_home')

    context = {
        'student': student,
        'course': course,
        'issued_on': student.enrollment_date.date(),
    }
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
        
        context = {
            'teacher': teacher,
            'courses_created': courses_created,
            'recent_materials': recent_materials,
            'recent_assignments': recent_assignments,
            'recent_submissions': recent_submissions,
            'pending_grading': pending_grading,
            'total_materials': total_materials,
            'total_assignments': total_assignments,
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
def teacher_students(request):
    """Teacher students view"""
    try:
        teacher = Teacher.objects.get(user=request.user)
        teacher.update_stats()
        # Get all students enrolled in teacher's courses
        teacher_courses = Course.objects.filter(instructor=teacher)
        students = Student.objects.filter(enrolled_courses__in=teacher_courses).distinct()
        
        context = {
            'teacher': teacher,
            'students': students,
            'user_role': 'teacher',
        }
        return render(request, 'teacher_students.html', context)
    except Teacher.DoesNotExist:
        messages.error(request, 'Teacher profile not found.')
        return redirect('home')

@login_required
def teacher_payments(request):
    """Teacher payments view"""
    try:
        teacher = Teacher.objects.get(user=request.user)
        # This would typically connect to a payment system
        # For now, showing sample data
        sample_payments = [
            {'course': 'React for Beginners', 'student': 'John Doe', 'amount': 99.99, 'date': '2024-01-15', 'status': 'Completed'},
            {'course': 'JavaScript Essentials', 'student': 'Jane Smith', 'amount': 79.99, 'date': '2024-01-14', 'status': 'Completed'},
            {'course': 'CSS for Styling', 'student': 'Mike Johnson', 'amount': 59.99, 'date': '2024-01-13', 'status': 'Pending'},
        ]
        
        context = {
            'teacher': teacher,
            'payments': sample_payments,
            'user_role': 'teacher',
        }
        return render(request, 'teacher_payments.html', context)
    except Teacher.DoesNotExist:
        messages.error(request, 'Teacher profile not found.')
        return redirect('home')

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
        
        if title and description and category and price:
            try:
                teacher = Teacher.objects.get(user=request.user)
                course = Course.objects.create(
                    title=title,
                    description=description,
                    category=category,
                    price=price,
                    duration=duration,
                    level=level,
                    instructor=teacher
                )
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
        jobs_posted = company.jobs_posted.all()
        context = {
            'company': company,
            'jobs_posted': jobs_posted,
            'user_role': 'company',
        }
        return render(request, 'company_home.html', context)
    except Company.DoesNotExist:
        messages.error(request, 'Company profile not found.')
        return redirect('home')

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
    
    # Filter by job type if provided
    job_type_filter = request.GET.get('job_type')
    if job_type_filter:
        jobs = jobs.filter(job_type=job_type_filter)
    
    context = {
        'jobs': jobs,
        'selected_job_type': job_type_filter,
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
                elif profile.role == 'placement_cell':
                    return redirect('placement_cell_home')
                elif profile.role == 'mentor':
                    return redirect('mentor_home')
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
                elif role == 'placement_cell':
                    PlacementCell.objects.create(
                        user=user,
                        contact_email=user.email,
                        department="Directorate of Technical Education",
                        organization="Government of Rajasthan"
                    )
                elif role == 'mentor':
                    Mentor.objects.create(
                        user=user,
                        department="Computer Science",
                        designation="Assistant Professor",
                        specialization="Software Engineering",
                        experience_years=5
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
            # Compute completed courses for certificate section
            progress_map = role_profile.progress or {}
            completed_ids = []
            if isinstance(progress_map, dict):
                for cid, pct in progress_map.items():
                    try:
                        if float(pct) >= 100:
                            completed_ids.append(int(cid))
                    except Exception:
                        continue
            student_completed_courses = Course.objects.filter(id__in=completed_ids)
        elif profile.role == 'teacher':
            role_profile = Teacher.objects.get(user=request.user)
            profile_form = TeacherProfileForm(instance=role_profile)
        elif profile.role == 'company':
            role_profile = Company.objects.get(user=request.user)
            profile_form = CompanyProfileForm(instance=role_profile)
        else:
            role_profile = None
            profile_form = None
            student_completed_courses = None
            
    except (UserProfile.DoesNotExist, Student.DoesNotExist, Teacher.DoesNotExist, Company.DoesNotExist):
        profile = UserProfile.objects.create(user=request.user, role='student')
        role_profile = Student.objects.create(user=request.user)
        profile_form = UserProfileForm(instance=profile)
    
    if request.method == 'POST':
        if profile_form and profile_form.is_valid():
            profile_form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    
    context = {
        'profile': profile,
        'role_profile': role_profile,
        'profile_form': profile_form,
        'student_completed_courses': student_completed_courses if profile.role == 'student' else None,
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

# Placement Cell Views

@login_required
def placement_cell_home(request):
    """Placement cell dashboard"""
    try:
        placement_cell = PlacementCell.objects.get(user=request.user)
    except PlacementCell.DoesNotExist:
        messages.error(request, 'Placement cell profile not found.')
        return redirect('home')
    
    # Dashboard statistics
    total_internships = Internship.objects.filter(posted_by=placement_cell).count()
    active_internships = Internship.objects.filter(posted_by=placement_cell, status='published').count()
    total_applications = InternshipApplication.objects.filter(internship__posted_by=placement_cell).count()
    pending_approvals = InternshipApplication.objects.filter(
        internship__posted_by=placement_cell,
        status='mentor_approval_pending'
    ).count()
    
    # Recent applications
    recent_applications = InternshipApplication.objects.filter(
        internship__posted_by=placement_cell
    ).order_by('-applied_at')[:10]
    
    # Upcoming deadlines
    upcoming_deadlines = Internship.objects.filter(
        posted_by=placement_cell,
        status='published',
        application_deadline__gt=timezone.now(),
        application_deadline__lt=timezone.now() + timedelta(days=7)
    ).order_by('application_deadline')
    
    context = {
        'placement_cell': placement_cell,
        'total_internships': total_internships,
        'active_internships': active_internships,
        'total_applications': total_applications,
        'pending_approvals': pending_approvals,
        'recent_applications': recent_applications,
        'upcoming_deadlines': upcoming_deadlines,
        'user_role': 'placement_cell',
    }
    return render(request, 'placement_cell/dashboard.html', context)

@login_required
def placement_cell_internships(request):
    """Manage internships for placement cell"""
    try:
        placement_cell = PlacementCell.objects.get(user=request.user)
    except PlacementCell.DoesNotExist:
        messages.error(request, 'Placement cell profile not found.')
        return redirect('home')
    
    internships = Internship.objects.filter(posted_by=placement_cell).order_by('-created_at')
    
    context = {
        'placement_cell': placement_cell,
        'internships': internships,
        'user_role': 'placement_cell',
    }
    return render(request, 'placement_cell/internships.html', context)

@login_required
def create_internship(request):
    """Create new internship posting"""
    try:
        placement_cell = PlacementCell.objects.get(user=request.user)
    except PlacementCell.DoesNotExist:
        messages.error(request, 'Only placement cell can create internships.')
        return redirect('home')
    
    if request.method == 'POST':
        # Get form data
        title = request.POST.get('title')
        company_id = request.POST.get('company')
        internship_type = request.POST.get('internship_type')
        description = request.POST.get('description')
        requirements = request.POST.get('requirements')
        required_skills = request.POST.get('required_skills')
        location = request.POST.get('location')
        duration_months = request.POST.get('duration_months')
        stipend_min = request.POST.get('stipend_min')
        stipend_max = request.POST.get('stipend_max')
        seats_available = request.POST.get('seats_available')
        application_deadline = request.POST.get('application_deadline')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        has_placement_potential = request.POST.get('has_placement_potential') == 'on'
        
        try:
            company = Company.objects.get(id=company_id)
            
            internship = Internship.objects.create(
                title=title,
                company=company,
                internship_type=internship_type,
                description=description,
                requirements=requirements,
                required_skills=required_skills,
                location=location,
                duration_months=int(duration_months),
                stipend_min=float(stipend_min) if stipend_min else None,
                stipend_max=float(stipend_max) if stipend_max else None,
                seats_available=int(seats_available),
                application_deadline=datetime.strptime(application_deadline, '%Y-%m-%dT%H:%M'),
                start_date=datetime.strptime(start_date, '%Y-%m-%d').date(),
                end_date=datetime.strptime(end_date, '%Y-%m-%d').date(),
                has_placement_potential=has_placement_potential,
                posted_by=placement_cell,
                status='published'
            )
            
            messages.success(request, 'Internship created successfully!')
            return redirect('placement_cell_internships')
            
        except Exception as e:
            messages.error(request, f'Error creating internship: {str(e)}')
    
    companies = Company.objects.all()
    context = {
        'companies': companies,
        'user_role': 'placement_cell',
    }
    return render(request, 'placement_cell/create_internship.html', context)

# Mentor Views

@login_required
def mentor_home(request):
    """Mentor dashboard"""
    try:
        mentor = Mentor.objects.get(user=request.user)
    except Mentor.DoesNotExist:
        messages.error(request, 'Mentor profile not found.')
        return redirect('home')
    
    # Get applications requiring mentor approval
    pending_approvals = InternshipApplication.objects.filter(
        mentor=mentor,
        status='mentor_approval_pending'
    ).order_by('-applied_at')
    
    # Get approved applications
    approved_applications = InternshipApplication.objects.filter(
        mentor=mentor,
        status__in=['mentor_approved', 'shortlisted', 'interview_scheduled', 'selected']
    ).order_by('-mentor_approval_date')
    
    # Statistics
    total_mentees = InternshipApplication.objects.filter(mentor=mentor).count()
    pending_count = pending_approvals.count()
    approved_count = approved_applications.count()
    
    context = {
        'mentor': mentor,
        'pending_approvals': pending_approvals,
        'approved_applications': approved_applications,
        'total_mentees': total_mentees,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'user_role': 'mentor',
    }
    return render(request, 'mentor/dashboard.html', context)

@login_required
def mentor_approve_application(request, application_id):
    """Approve or reject student application"""
    try:
        mentor = Mentor.objects.get(user=request.user)
        application = InternshipApplication.objects.get(
            id=application_id,
            mentor=mentor,
            status='mentor_approval_pending'
        )
    except (Mentor.DoesNotExist, InternshipApplication.DoesNotExist):
        messages.error(request, 'Application not found.')
        return redirect('mentor_home')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        comments = request.POST.get('comments', '')
        
        if action == 'approve':
            application.status = 'mentor_approved'
            application.mentor_approval_date = timezone.now()
            application.mentor_comments = comments
            application.save()
            
            # Notify student
            Notification.objects.create(
                recipient=application.student.user,
                notification_type='application_status',
                title='Application Approved by Mentor',
                message=f'Your application for {application.internship.title} has been approved by your mentor.',
                related_application=application
            )
            
            messages.success(request, 'Application approved successfully!')
            
        elif action == 'reject':
            application.status = 'mentor_rejected'
            application.mentor_approval_date = timezone.now()
            application.mentor_comments = comments
            application.save()
            
            # Notify student
            Notification.objects.create(
                recipient=application.student.user,
                notification_type='application_status',
                title='Application Rejected by Mentor',
                message=f'Your application for {application.internship.title} has been rejected by your mentor.',
                related_application=application
            )
            
            messages.success(request, 'Application rejected.')
        
        return redirect('mentor_home')
    
    context = {
        'application': application,
        'user_role': 'mentor',
    }
    return render(request, 'mentor/approve_application.html', context)

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
    
    submissions = AssignmentSubmission.objects.filter(assignment=assignment).order_by('-submitted_at')
    
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
def teacher_student_progress(request, course_id):
    """View student progress in a course"""
    try:
        teacher = Teacher.objects.get(user=request.user)
        course = Course.objects.get(id=course_id, instructor=teacher)
    except (Teacher.DoesNotExist, Course.DoesNotExist):
        messages.error(request, 'Course not found.')
        return redirect('teacher_courses')
    
    # Get or create progress records for all enrolled students
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

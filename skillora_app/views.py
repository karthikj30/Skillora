from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import json
from .models import Course, Instructor, Job, Testimonial, TeamMember, Contact, UserProfile, Student, Teacher, Company
from .forms import ContactForm, UserRegistrationForm, StudentProfileForm, TeacherProfileForm, CompanyProfileForm, UserProfileForm

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
        context = {
            'teacher': teacher,
            'courses_created': courses_created,
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
                    Company.objects.create(user=user)
                
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

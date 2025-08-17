from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
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
                # Student or default - show regular home page
                return student_home(request)
        except UserProfile.DoesNotExist:
            # Fallback to student home if no profile exists
            return student_home(request)
    else:
        # Not logged in - show regular home page
        return student_home(request)

def student_home(request):
    """Student home page view - same as current home page"""
    courses = Course.objects.all()[:6]  # Get latest 6 courses
    testimonials = Testimonial.objects.all()[:4]  # Get latest 4 testimonials
    context = {
        'courses': courses,
        'testimonials': testimonials,
        'user_role': 'student' if request.user.is_authenticated else None,
    }
    return render(request, 'index.html', context)

@login_required
def teacher_home(request):
    """Teacher home page view"""
    try:
        teacher = Teacher.objects.get(user=request.user)
        courses_created = teacher.courses_created.all()
        teacher.update_stats() # Call to update teacher stats
        sample_courses = [ # Sample data for dashboard display
            {'title': 'React for Beginners', 'students': 6},
            {'title': 'JavaScript Essentials', 'students': 3},
            {'title': 'CSS for Styling', 'students': 2},
            {'title': 'Node.js Fundamentals', 'students': 3},
        ]
        context = {
            'teacher': teacher,
            'courses_created': courses_created,
            'sample_courses': sample_courses,
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
        courses = teacher.courses_created.all()
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
        # Get all students enrolled in teacher's courses
        students = set()
        for course in teacher.courses_created.all():
            students.update(course.students_enrolled.all())
        
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
        elif profile.role == 'teacher':
            role_profile = Teacher.objects.get(user=request.user)
            profile_form = TeacherProfileForm(instance=role_profile)
        elif profile.role == 'company':
            role_profile = Company.objects.get(user=request.user)
            profile_form = CompanyProfileForm(instance=role_profile)
        else:
            role_profile = None
            profile_form = None
            
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
    }
    return render(request, 'profile.html', context)

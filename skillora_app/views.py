from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Course, Instructor, Job, Testimonial, TeamMember, Contact, UserProfile
from .forms import ContactForm, UserRegistrationForm

def home(request):
    """Home page view"""
    courses = Course.objects.all()[:6]  # Get latest 6 courses
    testimonials = Testimonial.objects.all()[:4]  # Get latest 4 testimonials
    context = {
        'courses': courses,
        'testimonials': testimonials,
    }
    return render(request, 'index.html', context)

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
            user = form.save()
            # Create user profile
            UserProfile.objects.create(user=user)
            messages.success(request, 'Account created successfully! Please log in.')
            return redirect('login')
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
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    
    if request.method == 'POST':
        # Handle profile update logic here
        pass
    
    context = {
        'profile': profile,
    }
    return render(request, 'profile.html', context)

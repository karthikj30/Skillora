from django.db import models
from django.contrib.auth.models import User

# User Role Choices
USER_ROLES = [
    ('student', 'Student'),
    ('teacher', 'Teacher'),
    ('company', 'Company'),
]

class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    instructor = models.ForeignKey('Teacher', on_delete=models.CASCADE, null=True, blank=True, related_name='courses_taught')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='courses/', null=True, blank=True)
    category = models.CharField(max_length=100)
    duration = models.CharField(max_length=50)
    level = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    students_enrolled = models.ManyToManyField('Student', blank=True, related_name='enrolled_courses')

    def __str__(self):
        return self.title

class Instructor(models.Model):
    name = models.CharField(max_length=100)
    bio = models.TextField()
    image = models.ImageField(upload_to='instructors/', null=True, blank=True)
    specialization = models.CharField(max_length=100)
    experience_years = models.IntegerField()
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)

    def __str__(self):
        return self.name

class Job(models.Model):
    title = models.CharField(max_length=200)
    company = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    description = models.TextField()
    requirements = models.TextField()
    salary_range = models.CharField(max_length=100)
    job_type = models.CharField(max_length=50)  # Full-time, Part-time, Contract
    posted_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} at {self.company}"

class Testimonial(models.Model):
    name = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    company = models.CharField(max_length=100)
    content = models.TextField()
    image = models.ImageField(upload_to='testimonials/', null=True, blank=True)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.position}"

class TeamMember(models.Model):
    name = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    bio = models.TextField()
    image = models.ImageField(upload_to='team/', null=True, blank=True)
    email = models.EmailField()
    linkedin = models.URLField(blank=True)
    twitter = models.URLField(blank=True)

    def __str__(self):
        return self.name

class Contact(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} - {self.subject}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=USER_ROLES, default='student')
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    skills = models.TextField(blank=True)
    experience = models.TextField(blank=True)
    education = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    enrollment_date = models.DateTimeField(auto_now_add=True)
    courses_enrolled = models.ManyToManyField(Course, blank=True)
    progress = models.JSONField(default=dict, blank=True)  # Store course progress
    saved_courses = models.ManyToManyField(Course, blank=True, related_name='saved_by_students')
    
    def __str__(self):
        return f"Student: {self.user.username}"

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    specialization = models.CharField(max_length=100, default="Not specified")
    experience_years = models.IntegerField(default=0)
    bio = models.TextField(blank=True, default="No bio provided")
    courses_created = models.ManyToManyField(Course, blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    is_verified = models.BooleanField(default=False)
    total_students = models.IntegerField(default=0)
    total_courses = models.IntegerField(default=0)
    upcoming_classes = models.IntegerField(default=0)
    student_progress_avg = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    def __str__(self):
        return f"Teacher: {self.user.username}"
    
    def update_stats(self):
        """Update teacher statistics"""
        # Compute stats based on courses where this teacher is the instructor
        instructor_courses = Course.objects.filter(instructor=self)
        self.total_courses = instructor_courses.count()
        # Calculate total students across all instructor courses
        total_students = 0
        for course in instructor_courses:
            total_students += course.students_enrolled.count() if hasattr(course, 'students_enrolled') else 0
        self.total_students = total_students
        self.save()

class Company(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=200)
    industry = models.CharField(max_length=100)
    company_size = models.CharField(max_length=50)
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)
    jobs_posted = models.ManyToManyField(Job, blank=True, related_name='company_posters')
    
    def __str__(self):
        return f"Company: {self.company_name}"

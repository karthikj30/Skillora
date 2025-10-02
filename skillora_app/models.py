from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# User Role Choices
USER_ROLES = [
    ('student', 'Student'),
    ('teacher', 'Teacher'),
    ('company', 'Company'),
    ('placement_cell', 'Placement Cell'),
    ('mentor', 'Mentor'),
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

# Internship/Placement System Models

class PlacementCell(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.CharField(max_length=100, default="Directorate of Technical Education")
    organization = models.CharField(max_length=200, default="Government of Rajasthan")
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20, blank=True)
    office_location = models.TextField(blank=True)
    
    def __str__(self):
        return f"Placement Cell: {self.user.username}"

class Mentor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)
    specialization = models.CharField(max_length=200)
    experience_years = models.IntegerField(default=0)
    max_mentees = models.IntegerField(default=20)
    
    def __str__(self):
        return f"Mentor: {self.user.get_full_name() or self.user.username}"

INTERNSHIP_TYPES = [
    ('internship', 'Internship'),
    ('industrial_training', 'Industrial Training'),
    ('placement', 'Full-time Placement'),
]

INTERNSHIP_STATUS = [
    ('draft', 'Draft'),
    ('published', 'Published'),
    ('closed', 'Closed'),
    ('cancelled', 'Cancelled'),
]

class Internship(models.Model):
    title = models.CharField(max_length=200)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='internships_posted')
    internship_type = models.CharField(max_length=20, choices=INTERNSHIP_TYPES, default='internship')
    description = models.TextField()
    requirements = models.TextField()
    required_skills = models.TextField(help_text="Comma-separated skills")
    department_preference = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=200)
    duration_months = models.IntegerField(help_text="Duration in months")
    stipend_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stipend_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    seats_available = models.IntegerField(default=1)
    seats_filled = models.IntegerField(default=0)
    application_deadline = models.DateTimeField()
    start_date = models.DateField()
    end_date = models.DateField()
    has_placement_potential = models.BooleanField(default=False)
    placement_conversion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Percentage")
    status = models.CharField(max_length=20, choices=INTERNSHIP_STATUS, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    posted_by = models.ForeignKey(PlacementCell, on_delete=models.CASCADE, null=True, blank=True)
    
    def __str__(self):
        return f"{self.title} at {self.company.company_name}"
    
    def get_required_skills_list(self):
        return [skill.strip() for skill in self.required_skills.split(',') if skill.strip()]
    
    def seats_remaining(self):
        return max(0, self.seats_available - self.seats_filled)

APPLICATION_STATUS = [
    ('draft', 'Draft'),
    ('submitted', 'Submitted'),
    ('under_review', 'Under Review'),
    ('mentor_approval_pending', 'Mentor Approval Pending'),
    ('mentor_approved', 'Mentor Approved'),
    ('mentor_rejected', 'Mentor Rejected'),
    ('shortlisted', 'Shortlisted'),
    ('interview_scheduled', 'Interview Scheduled'),
    ('interview_completed', 'Interview Completed'),
    ('selected', 'Selected'),
    ('rejected', 'Rejected'),
    ('withdrawn', 'Withdrawn'),
]

class InternshipApplication(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='internship_applications')
    internship = models.ForeignKey(Internship, on_delete=models.CASCADE, related_name='applications')
    mentor = models.ForeignKey(Mentor, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=30, choices=APPLICATION_STATUS, default='draft')
    cover_letter = models.TextField()
    additional_documents = models.FileField(upload_to='applications/', null=True, blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Mentor approval fields
    mentor_approval_date = models.DateTimeField(null=True, blank=True)
    mentor_comments = models.TextField(blank=True)
    
    # Interview fields
    interview_date = models.DateTimeField(null=True, blank=True)
    interview_location = models.CharField(max_length=200, blank=True)
    interview_notes = models.TextField(blank=True)
    
    # Selection fields
    selection_date = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    class Meta:
        unique_together = ('student', 'internship')
    
    def __str__(self):
        return f"{self.student.user.username} -> {self.internship.title}"

class StudentProfile(models.Model):
    """Extended student profile for internship/placement system"""
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='placement_profile')
    resume = models.FileField(upload_to='resumes/', null=True, blank=True)
    skills = models.TextField(help_text="Comma-separated skills")
    cgpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    department = models.CharField(max_length=100)
    year_of_study = models.IntegerField(choices=[(i, f"Year {i}") for i in range(1, 5)])
    graduation_year = models.IntegerField()
    preferred_locations = models.TextField(help_text="Comma-separated preferred locations")
    preferred_industries = models.TextField(help_text="Comma-separated preferred industries")
    internship_preferences = models.CharField(max_length=20, choices=INTERNSHIP_TYPES, default='internship')
    is_placement_ready = models.BooleanField(default=False)
    placement_preference_salary_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    def __str__(self):
        return f"Profile: {self.student.user.username}"
    
    def get_skills_list(self):
        return [skill.strip() for skill in self.skills.split(',') if skill.strip()]
    
    def get_preferred_locations_list(self):
        return [loc.strip() for loc in self.preferred_locations.split(',') if loc.strip()]
    
    def get_preferred_industries_list(self):
        return [ind.strip() for ind in self.preferred_industries.split(',') if ind.strip()]

FEEDBACK_RATING = [
    (1, 'Poor'),
    (2, 'Below Average'),
    (3, 'Average'),
    (4, 'Good'),
    (5, 'Excellent'),
]

class InternshipFeedback(models.Model):
    application = models.OneToOneField(InternshipApplication, on_delete=models.CASCADE, related_name='feedback')
    supervisor_name = models.CharField(max_length=100)
    supervisor_email = models.EmailField()
    supervisor_designation = models.CharField(max_length=100)
    
    # Performance ratings
    technical_skills_rating = models.IntegerField(choices=FEEDBACK_RATING)
    communication_rating = models.IntegerField(choices=FEEDBACK_RATING)
    teamwork_rating = models.IntegerField(choices=FEEDBACK_RATING)
    punctuality_rating = models.IntegerField(choices=FEEDBACK_RATING)
    overall_rating = models.IntegerField(choices=FEEDBACK_RATING)
    
    # Detailed feedback
    strengths = models.TextField()
    areas_for_improvement = models.TextField()
    additional_comments = models.TextField(blank=True)
    
    # Completion details
    completion_date = models.DateField()
    certificate_issued = models.BooleanField(default=False)
    certificate_file = models.FileField(upload_to='certificates/', null=True, blank=True)
    
    # Placement potential
    recommend_for_placement = models.BooleanField(default=False)
    placement_recommendation_comments = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Feedback: {self.application.student.user.username} - {self.application.internship.title}"

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('application_status', 'Application Status Update'),
        ('interview_scheduled', 'Interview Scheduled'),
        ('deadline_reminder', 'Deadline Reminder'),
        ('mentor_approval', 'Mentor Approval Required'),
        ('new_opportunity', 'New Opportunity'),
        ('feedback_request', 'Feedback Request'),
        ('certificate_ready', 'Certificate Ready'),
        ('new_assignment', 'New Assignment'),
        ('assignment_due', 'Assignment Due'),
        ('new_material', 'New Course Material'),
    ]
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    related_application = models.ForeignKey(InternshipApplication, on_delete=models.CASCADE, null=True, blank=True)
    related_internship = models.ForeignKey(Internship, on_delete=models.CASCADE, null=True, blank=True)
    
    def __str__(self):
        return f"{self.title} - {self.recipient.username}"
    
    class Meta:
        ordering = ['-created_at']

# Teacher Classroom Models

class CourseMaterial(models.Model):
    MATERIAL_TYPES = [
        ('note', 'Note/Document'),
        ('video', 'Video'),
        ('link', 'External Link'),
        ('file', 'File'),
    ]
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='materials')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='materials_created')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    material_type = models.CharField(max_length=10, choices=MATERIAL_TYPES)
    
    # For notes/documents
    content = models.TextField(blank=True)
    
    # For files/videos
    file = models.FileField(upload_to='course_materials/', null=True, blank=True)
    
    # For external links/YouTube videos
    url = models.URLField(blank=True)
    
    # For YouTube videos - store video ID for embedding
    youtube_video_id = models.CharField(max_length=50, blank=True)
    
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"
    
    def get_youtube_embed_url(self):
        if self.youtube_video_id:
            return f"https://www.youtube.com/embed/{self.youtube_video_id}"
        return None
    
    class Meta:
        ordering = ['-created_at']

class Assignment(models.Model):
    ASSIGNMENT_TYPES = [
        ('homework', 'Homework'),
        ('project', 'Project'),
        ('quiz', 'Quiz'),
        ('exam', 'Exam'),
        ('presentation', 'Presentation'),
    ]
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='assignments_created')
    title = models.CharField(max_length=200)
    description = models.TextField()
    assignment_type = models.CharField(max_length=20, choices=ASSIGNMENT_TYPES, default='homework')
    
    # Assignment files/attachments
    attachment = models.FileField(upload_to='assignments/', null=True, blank=True)
    
    # Dates
    assigned_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField()
    
    # Settings
    max_points = models.IntegerField(default=100)
    allow_late_submission = models.BooleanField(default=True)
    is_published = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"
    
    def is_overdue(self):
        from django.utils import timezone
        return timezone.now() > self.due_date
    
    class Meta:
        ordering = ['-created_at']

class AssignmentSubmission(models.Model):
    SUBMISSION_STATUS = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('graded', 'Graded'),
        ('returned', 'Returned'),
    ]
    
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='assignment_submissions')
    
    # Submission content
    submission_text = models.TextField(blank=True)
    submission_file = models.FileField(upload_to='submissions/', null=True, blank=True)
    
    # Submission tracking
    status = models.CharField(max_length=20, choices=SUBMISSION_STATUS, default='draft')
    submitted_at = models.DateTimeField(null=True, blank=True)
    
    # Grading
    points_earned = models.IntegerField(null=True, blank=True)
    feedback = models.TextField(blank=True)
    graded_at = models.DateTimeField(null=True, blank=True)
    graded_by = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.student.user.username} - {self.assignment.title}"
    
    def is_late(self):
        if self.submitted_at and self.assignment.due_date:
            return self.submitted_at > self.assignment.due_date
        return False
    
    def get_grade_percentage(self):
        if self.points_earned is not None and self.assignment.max_points > 0:
            return (self.points_earned / self.assignment.max_points) * 100
        return None
    
    class Meta:
        unique_together = ('assignment', 'student')
        ordering = ['-created_at']

class CourseAnnouncement(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='announcements')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='announcements_created')
    title = models.CharField(max_length=200)
    content = models.TextField()
    is_important = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"
    
    class Meta:
        ordering = ['-created_at']

class StudentProgress(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='course_progress')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='student_progress')
    
    # Progress tracking
    materials_viewed = models.ManyToManyField(CourseMaterial, blank=True)
    assignments_completed = models.ManyToManyField(Assignment, blank=True)
    
    # Overall progress percentage
    progress_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Time tracking
    total_time_spent = models.DurationField(default=timezone.timedelta)
    last_accessed = models.DateTimeField(auto_now=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.student.user.username} - {self.course.title} ({self.progress_percentage}%)"
    
    def update_progress(self):
        """Calculate and update progress percentage"""
        total_materials = self.course.materials.filter(is_published=True).count()
        total_assignments = self.course.assignments.filter(is_published=True).count()
        
        viewed_materials = self.materials_viewed.count()
        completed_assignments = self.assignments_completed.count()
        
        total_items = total_materials + total_assignments
        completed_items = viewed_materials + completed_assignments
        
        if total_items > 0:
            self.progress_percentage = (completed_items / total_items) * 100
        else:
            self.progress_percentage = 0
        
        self.save()
        return self.progress_percentage
    
    class Meta:
        unique_together = ('student', 'course')
        ordering = ['-updated_at']

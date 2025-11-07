from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import (Contact, Student, Teacher, Company, UserProfile, Course, 
                     CourseMaterial, Assignment, CourseAnnouncement, AssignmentSubmission, ScheduledClass, Job)
import re

class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Your Email'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Subject'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Message', 'rows': 5}),
        }

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}))
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}))
    role = forms.ChoiceField(
        choices=[('student', 'Student'), ('teacher', 'Teacher'), ('company', 'Company')],
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Username'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm Password'})

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['bio', 'profile_picture', 'phone', 'address', 'skills', 'experience', 'education']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'skills': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'experience': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'education': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = []  # Student model only has auto-generated fields, no editable fields
        # We'll use UserProfile fields for student information

class TeacherProfileForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = ['specialization', 'experience_years', 'bio']
        widgets = {
            'specialization': forms.TextInput(attrs={'class': 'form-control'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class CompanyProfileForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['company_name', 'industry', 'company_size', 'website', 'description']
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'industry': forms.TextInput(attrs={'class': 'form-control'}),
            'company_size': forms.Select(choices=[
                ('1-10', '1-10 employees'),
                ('11-50', '11-50 employees'),
                ('51-200', '51-200 employees'),
                ('201-500', '201-500 employees'),
                ('500+', '500+ employees'),
            ], attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

# Teacher Classroom Forms

class CourseMaterialForm(forms.ModelForm):
    youtube_url = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://www.youtube.com/watch?v=...'
        }),
        help_text='Paste YouTube video URL here'
    )
    
    class Meta:
        model = CourseMaterial
        fields = ['title', 'description', 'material_type', 'content', 'file', 'url']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Material title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description (optional)'
            }),
            'material_type': forms.Select(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': 'Enter your notes/content here...'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.ppt,.pptx,.mp4,.avi,.mov,.wmv'
            }),
            'url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'External link URL'
            }),
        }
    
    def clean_youtube_url(self):
        youtube_url = self.cleaned_data.get('youtube_url')
        if youtube_url:
            # Extract YouTube video ID from URL
            youtube_regex = r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})'
            match = re.search(youtube_regex, youtube_url)
            if match:
                return match.group(1)
            else:
                raise forms.ValidationError('Please enter a valid YouTube URL')
        return youtube_url
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        youtube_url = self.cleaned_data.get('youtube_url')
        
        if youtube_url and instance.material_type == 'video':
            # Extract video ID and set it
            youtube_regex = r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})'
            match = re.search(youtube_regex, youtube_url)
            if match:
                instance.youtube_video_id = match.group(1)
                instance.url = youtube_url
        
        if commit:
            instance.save()
        return instance

class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['title', 'description', 'assignment_type', 'due_date', 'max_points', 
                 'allow_late_submission', 'attachment']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Assignment title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Assignment instructions and description...'
            }),
            'assignment_type': forms.Select(attrs={'class': 'form-control'}),
            'due_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'max_points': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'value': '100'
            }),
            'allow_late_submission': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'attachment': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.ppt,.pptx,.zip,.rar'
            }),
        }

class CourseAnnouncementForm(forms.ModelForm):
    class Meta:
        model = CourseAnnouncement
        fields = ['title', 'content', 'is_important']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Announcement title'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Announcement content...'
            }),
            'is_important': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

class AssignmentSubmissionForm(forms.ModelForm):
    class Meta:
        model = AssignmentSubmission
        fields = ['submission_text', 'submission_file']
        widgets = {
            'submission_text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': 'Enter your submission text here...'
            }),
            'submission_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.ppt,.pptx,.zip,.rar,.txt,.jpg,.jpeg,.png,.gif,.bmp'
            }),
        }

class GradeSubmissionForm(forms.ModelForm):
    class Meta:
        model = AssignmentSubmission
        fields = ['points_earned', 'feedback']
        widgets = {
            'points_earned': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'feedback': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Feedback for the student...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        assignment = kwargs.pop('assignment', None)
        super().__init__(*args, **kwargs)
        if assignment:
            self.fields['points_earned'].widget.attrs['max'] = assignment.max_points
            self.fields['points_earned'].help_text = f'Maximum points: {assignment.max_points}'

class ScheduledClassForm(forms.ModelForm):
    class Meta:
        model = ScheduledClass
        fields = ['title', 'description', 'scheduled_date', 'duration_minutes', 'course', 
                 'meeting_link', 'meeting_password']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Class title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Class description (optional)'
            }),
            'scheduled_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'duration_minutes': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '15',
                'step': '15',
                'value': '60'
            }),
            'course': forms.Select(attrs={
                'class': 'form-control'
            }),
            'meeting_link': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://zoom.us/j/... or meeting link'
            }),
            'meeting_password': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Meeting password (optional)'
            }),
        }

class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['title', 'company', 'location', 'description', 'requirements', 'salary_range', 'job_type']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Job title'}),
            'company': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Company name'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Location (e.g., Bengaluru / Remote)'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Job description'}),
            'requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Key requirements'}),
            'salary_range': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '₹10-20 LPA'}),
            'job_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full-time / Part-time / Contract / Remote'}),
        }

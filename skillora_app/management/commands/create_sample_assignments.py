from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from skillora_app.models import Teacher, Course, Assignment, CourseAnnouncement, AssignmentSubmission, Student
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Create sample assignments and announcements for testing'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating sample assignments and announcements...'))

        # Get or create a teacher
        try:
            teacher_user = User.objects.filter(userprofile__role='teacher').first()
            if not teacher_user:
                self.stdout.write(self.style.ERROR('No teacher found. Please create a teacher first.'))
                return
            
            teacher = Teacher.objects.get(user=teacher_user)
            self.stdout.write(f'Found teacher: {teacher.user.get_full_name()}')
        except Teacher.DoesNotExist:
            self.stdout.write(self.style.ERROR('Teacher profile not found.'))
            return

        # Get teacher's courses
        courses = Course.objects.filter(instructor=teacher)
        if not courses.exists():
            self.stdout.write(self.style.ERROR('No courses found for teacher. Please create courses first.'))
            return

        course = courses.first()
        self.stdout.write(f'Using course: {course.title}')

        # Create sample assignments
        assignments_created = 0
        assignments_data = [
            {
                'title': 'Introduction to Web Development',
                'description': 'Create a simple HTML page with CSS styling. Include a header, navigation, main content area, and footer.',
                'assignment_type': 'project',
                'max_points': 100,
                'due_date': timezone.now() + timedelta(days=7)
            },
            {
                'title': 'JavaScript Fundamentals Quiz',
                'description': 'Complete a quiz covering JavaScript basics including variables, functions, and DOM manipulation.',
                'assignment_type': 'quiz',
                'max_points': 50,
                'due_date': timezone.now() + timedelta(days=3)
            },
            {
                'title': 'Responsive Design Project',
                'description': 'Build a responsive website that works on desktop, tablet, and mobile devices.',
                'assignment_type': 'project',
                'max_points': 150,
                'due_date': timezone.now() + timedelta(days=14)
            },
            {
                'title': 'React Components Homework',
                'description': 'Create reusable React components for a todo application.',
                'assignment_type': 'homework',
                'max_points': 75,
                'due_date': timezone.now() + timedelta(days=5)
            }
        ]

        for assignment_data in assignments_data:
            assignment, created = Assignment.objects.get_or_create(
                course=course,
                teacher=teacher,
                title=assignment_data['title'],
                defaults={
                    'description': assignment_data['description'],
                    'assignment_type': assignment_data['assignment_type'],
                    'max_points': assignment_data['max_points'],
                    'due_date': assignment_data['due_date'],
                    'is_published': True
                }
            )
            if created:
                assignments_created += 1
                self.stdout.write(f'Created assignment: {assignment.title}')

        # Create sample announcements
        announcements_created = 0
        announcements_data = [
            {
                'title': 'Welcome to the Course!',
                'content': 'Welcome everyone to our Web Development course! I\'m excited to work with all of you this semester. Please make sure to check the course materials and complete the first assignment by next week.',
                'is_important': True
            },
            {
                'title': 'Assignment Due Date Extended',
                'content': 'Due to technical issues with the learning platform, I\'m extending the due date for Assignment 1 by 2 days. The new due date is Friday at 11:59 PM.',
                'is_important': True
            },
            {
                'title': 'Office Hours Update',
                'content': 'My office hours have been updated. I\'ll be available for questions on Tuesdays and Thursdays from 2-4 PM. Feel free to drop by or schedule an appointment.',
                'is_important': False
            },
            {
                'title': 'Project Guidelines',
                'content': 'For the upcoming project, please make sure to follow the coding standards we discussed in class. Code should be well-commented and properly formatted.',
                'is_important': False
            },
            {
                'title': 'Midterm Exam Schedule',
                'content': 'The midterm exam will be held on March 15th from 10 AM to 12 PM in Room 201. Please bring your student ID and a calculator.',
                'is_important': True
            }
        ]

        for announcement_data in announcements_data:
            announcement, created = CourseAnnouncement.objects.get_or_create(
                course=course,
                teacher=teacher,
                title=announcement_data['title'],
                defaults={
                    'content': announcement_data['content'],
                    'is_important': announcement_data['is_important']
                }
            )
            if created:
                announcements_created += 1
                self.stdout.write(f'Created announcement: {announcement.title}')

        # Create some sample submissions if students exist
        students = Student.objects.filter(enrolled_courses=course)
        if students.exists():
            assignments = Assignment.objects.filter(course=course)
            submissions_created = 0
            
            for assignment in assignments[:2]:  # Only for first 2 assignments
                for student in students[:3]:  # Only for first 3 students
                    submission, created = AssignmentSubmission.objects.get_or_create(
                        assignment=assignment,
                        student=student,
                        defaults={
                            'submission_text': f'Submission for {assignment.title} by {student.user.get_full_name()}',
                            'status': 'submitted' if assignment.title == 'Introduction to Web Development' else 'graded',
                            'submitted_at': timezone.now() - timedelta(days=1)
                        }
                    )
                    if created:
                        submissions_created += 1

            self.stdout.write(f'Created {submissions_created} sample submissions')

        self.stdout.write(self.style.SUCCESS(f'Successfully created:'))
        self.stdout.write(f'- {assignments_created} assignments')
        self.stdout.write(f'- {announcements_created} announcements')
        self.stdout.write(f'- Sample submissions for testing')
        
        self.stdout.write(self.style.SUCCESS('Sample data creation complete!'))

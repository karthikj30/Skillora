from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
from skillora_app.models import (
    UserProfile, Company, PlacementCell, Mentor, Student, StudentProfile,
    Internship, InternshipApplication
)

class Command(BaseCommand):
    help = 'Create sample data for internship/placement system'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data for internship/placement system...')
        
        # Create placement cell user
        placement_user, created = User.objects.get_or_create(
            username='placement_cell',
            defaults={
                'email': 'placement@skillora.com',
                'first_name': 'Placement',
                'last_name': 'Cell',
                'is_staff': True
            }
        )
        if created:
            placement_user.set_password('placement123')
            placement_user.save()
            
        # Create placement cell profile
        placement_profile, _ = UserProfile.objects.get_or_create(
            user=placement_user,
            defaults={'role': 'placement_cell'}
        )
        
        placement_cell, _ = PlacementCell.objects.get_or_create(
            user=placement_user,
            defaults={
                'contact_email': 'placement@skillora.com',
                'department': 'Directorate of Technical Education',
                'organization': 'Government of Rajasthan'
            }
        )
        
        # Create mentor user
        mentor_user, created = User.objects.get_or_create(
            username='mentor1',
            defaults={
                'email': 'mentor@skillora.com',
                'first_name': 'Dr. Rajesh',
                'last_name': 'Sharma'
            }
        )
        if created:
            mentor_user.set_password('mentor123')
            mentor_user.save()
            
        # Create mentor profile
        mentor_profile, _ = UserProfile.objects.get_or_create(
            user=mentor_user,
            defaults={'role': 'mentor'}
        )
        
        mentor, _ = Mentor.objects.get_or_create(
            user=mentor_user,
            defaults={
                'department': 'Computer Science',
                'designation': 'Associate Professor',
                'specialization': 'Software Engineering, Web Development',
                'experience_years': 12
            }
        )
        
        # Create company users and companies
        companies_data = [
            {
                'username': 'techcorp',
                'company_name': 'TechCorp Solutions',
                'industry': 'Technology',
                'company_size': '100-500',
                'description': 'Leading software development company specializing in web and mobile applications.'
            },
            {
                'username': 'innovatesoft',
                'company_name': 'InnovateSoft',
                'industry': 'Software Development',
                'company_size': '50-100',
                'description': 'Innovative software solutions for modern businesses.'
            },
            {
                'username': 'datatech',
                'company_name': 'DataTech Analytics',
                'industry': 'Data Science',
                'company_size': '20-50',
                'description': 'Data analytics and machine learning solutions provider.'
            }
        ]
        
        companies = []
        for comp_data in companies_data:
            user, created = User.objects.get_or_create(
                username=comp_data['username'],
                defaults={
                    'email': f"{comp_data['username']}@company.com",
                    'first_name': comp_data['company_name'].split()[0],
                    'last_name': 'Company'
                }
            )
            if created:
                user.set_password('company123')
                user.save()
                
            profile, _ = UserProfile.objects.get_or_create(
                user=user,
                defaults={'role': 'company'}
            )
            
            company, _ = Company.objects.get_or_create(
                user=user,
                defaults={
                    'company_name': comp_data['company_name'],
                    'industry': comp_data['industry'],
                    'company_size': comp_data['company_size'],
                    'description': comp_data['description']
                }
            )
            companies.append(company)
        
        # Create sample internships
        internships_data = [
            {
                'title': 'Full Stack Web Development Internship',
                'company': companies[0],
                'internship_type': 'internship',
                'description': 'Work on real-world web applications using modern technologies. Learn React, Node.js, and database management.',
                'requirements': 'Basic knowledge of HTML, CSS, JavaScript. Familiarity with React is a plus.',
                'required_skills': 'HTML, CSS, JavaScript, React, Node.js, MongoDB',
                'location': 'Jaipur, Rajasthan',
                'duration_months': 6,
                'stipend_min': 15000,
                'stipend_max': 25000,
                'seats_available': 5,
                'has_placement_potential': True,
                'placement_conversion_rate': 70.0
            },
            {
                'title': 'Python Developer Industrial Training',
                'company': companies[1],
                'internship_type': 'industrial_training',
                'description': 'Comprehensive training in Python development, Django framework, and API development.',
                'requirements': 'Basic programming knowledge. Python experience preferred but not required.',
                'required_skills': 'Python, Django, REST API, PostgreSQL, Git',
                'location': 'Delhi, NCR',
                'duration_months': 4,
                'stipend_min': 12000,
                'stipend_max': 20000,
                'seats_available': 8,
                'has_placement_potential': True,
                'placement_conversion_rate': 60.0
            },
            {
                'title': 'Data Science Internship',
                'company': companies[2],
                'internship_type': 'internship',
                'description': 'Work with real datasets, learn machine learning algorithms, and build predictive models.',
                'requirements': 'Strong mathematical background. Knowledge of Python and statistics.',
                'required_skills': 'Python, Pandas, NumPy, Scikit-learn, Machine Learning, Statistics',
                'location': 'Bangalore, Karnataka',
                'duration_months': 5,
                'stipend_min': 18000,
                'stipend_max': 30000,
                'seats_available': 3,
                'has_placement_potential': True,
                'placement_conversion_rate': 80.0
            },
            {
                'title': 'Mobile App Development Internship',
                'company': companies[0],
                'internship_type': 'internship',
                'description': 'Develop mobile applications for Android and iOS using React Native.',
                'requirements': 'Basic knowledge of JavaScript and mobile app concepts.',
                'required_skills': 'React Native, JavaScript, Mobile Development, Firebase',
                'location': 'Mumbai, Maharashtra',
                'duration_months': 4,
                'stipend_min': 14000,
                'stipend_max': 22000,
                'seats_available': 4,
                'has_placement_potential': False,
                'placement_conversion_rate': 0.0
            },
            {
                'title': 'Full-time Software Developer Position',
                'company': companies[1],
                'internship_type': 'placement',
                'description': 'Full-time position for fresh graduates. Work on enterprise software solutions.',
                'requirements': 'Bachelor\'s degree in Computer Science or related field. Strong programming skills.',
                'required_skills': 'Java, Spring Boot, MySQL, Microservices, Docker',
                'location': 'Pune, Maharashtra',
                'duration_months': 12,
                'stipend_min': 35000,
                'stipend_max': 50000,
                'seats_available': 2,
                'has_placement_potential': True,
                'placement_conversion_rate': 100.0
            }
        ]
        
        for internship_data in internships_data:
            # Set dates
            start_date = timezone.now().date() + timedelta(days=30)
            end_date = start_date + timedelta(days=internship_data['duration_months'] * 30)
            application_deadline = timezone.now() + timedelta(days=15)
            
            internship, created = Internship.objects.get_or_create(
                title=internship_data['title'],
                company=internship_data['company'],
                defaults={
                    'internship_type': internship_data['internship_type'],
                    'description': internship_data['description'],
                    'requirements': internship_data['requirements'],
                    'required_skills': internship_data['required_skills'],
                    'location': internship_data['location'],
                    'duration_months': internship_data['duration_months'],
                    'stipend_min': internship_data['stipend_min'],
                    'stipend_max': internship_data['stipend_max'],
                    'seats_available': internship_data['seats_available'],
                    'application_deadline': application_deadline,
                    'start_date': start_date,
                    'end_date': end_date,
                    'has_placement_potential': internship_data['has_placement_potential'],
                    'placement_conversion_rate': internship_data['placement_conversion_rate'],
                    'posted_by': placement_cell,
                    'status': 'published'
                }
            )
            
            if created:
                self.stdout.write(f'Created internship: {internship.title}')
        
        # Create sample student
        student_user, created = User.objects.get_or_create(
            username='student1',
            defaults={
                'email': 'student@skillora.com',
                'first_name': 'Priya',
                'last_name': 'Sharma'
            }
        )
        if created:
            student_user.set_password('student123')
            student_user.save()
            
        student_profile, _ = UserProfile.objects.get_or_create(
            user=student_user,
            defaults={'role': 'student'}
        )
        
        student, _ = Student.objects.get_or_create(
            user=student_user
        )
        
        # Create student placement profile
        student_placement_profile, _ = StudentProfile.objects.get_or_create(
            student=student,
            defaults={
                'skills': 'Python, JavaScript, HTML, CSS, React, Django, Git, MySQL',
                'cgpa': 8.5,
                'department': 'Computer Science Engineering',
                'year_of_study': 3,
                'graduation_year': 2025,
                'preferred_locations': 'Jaipur, Delhi, Bangalore, Pune',
                'preferred_industries': 'Technology, Software Development, Data Science',
                'internship_preferences': 'internship',
                'is_placement_ready': True,
                'placement_preference_salary_min': 30000
            }
        )
        
        self.stdout.write(self.style.SUCCESS('Successfully created sample data!'))
        self.stdout.write('Sample login credentials:')
        self.stdout.write('Placement Cell: placement_cell / placement123')
        self.stdout.write('Mentor: mentor1 / mentor123')
        self.stdout.write('Student: student1 / student123')
        self.stdout.write('Companies: techcorp, innovatesoft, datatech / company123')

from django.core.management.base import BaseCommand
from skillora_app.models import Course, Instructor, Job, Testimonial, TeamMember

class Command(BaseCommand):
    help = 'Load sample data for the Skillora application'

    def handle(self, *args, **options):
        self.stdout.write('Loading sample data...')
        
        # Create sample courses
        courses_data = [
            {
                'title': 'Python Programming Fundamentals',
                'description': 'Learn Python from scratch with hands-on projects and real-world applications.',
                'instructor': 'Dr. Sarah Johnson',
                'price': 99.99,
                'category': 'Programming',
                'duration': '8 weeks',
                'level': 'Beginner'
            },
            {
                'title': 'Data Science with Python',
                'description': 'Master data analysis, visualization, and machine learning with Python.',
                'instructor': 'Prof. Michael Chen',
                'price': 149.99,
                'category': 'Data Science',
                'duration': '12 weeks',
                'level': 'Intermediate'
            },
            {
                'title': 'Web Development with Django',
                'description': 'Build modern web applications using Django framework and best practices.',
                'instructor': 'Alex Rodriguez',
                'price': 129.99,
                'category': 'Web Development',
                'duration': '10 weeks',
                'level': 'Intermediate'
            },
            {
                'title': 'Cloud Computing with AWS',
                'description': 'Learn cloud infrastructure and deployment using Amazon Web Services.',
                'instructor': 'Emma Wilson',
                'price': 179.99,
                'category': 'Cloud Computing',
                'duration': '10 weeks',
                'level': 'Advanced'
            },
            {
                'title': 'Digital Marketing Strategy',
                'description': 'Develop comprehensive digital marketing strategies for business growth.',
                'instructor': 'David Kim',
                'price': 89.99,
                'category': 'Digital Marketing',
                'duration': '6 weeks',
                'level': 'Beginner'
            },
            {
                'title': 'UI/UX Design Principles',
                'description': 'Create user-centered designs with modern design tools and methodologies.',
                'instructor': 'Lisa Thompson',
                'price': 119.99,
                'category': 'Design',
                'duration': '8 weeks',
                'level': 'Intermediate'
            }
        ]
        
        for course_data in courses_data:
            Course.objects.get_or_create(
                title=course_data['title'],
                defaults=course_data
            )
        
        # Create sample instructors
        instructors_data = [
            {
                'name': 'Dr. Sarah Johnson',
                'bio': 'Senior Software Engineer with 10+ years of experience in Python development.',
                'specialization': 'Python Programming',
                'experience_years': 10,
                'rating': 4.8
            },
            {
                'name': 'Prof. Michael Chen',
                'bio': 'Data Scientist and Machine Learning expert with PhD in Computer Science.',
                'specialization': 'Data Science',
                'experience_years': 15,
                'rating': 4.9
            },
            {
                'name': 'Alex Rodriguez',
                'bio': 'Full-stack developer specializing in Django and modern web technologies.',
                'specialization': 'Web Development',
                'experience_years': 8,
                'rating': 4.7
            }
        ]
        
        for instructor_data in instructors_data:
            Instructor.objects.get_or_create(
                name=instructor_data['name'],
                defaults=instructor_data
            )
        
        # Create sample jobs
        jobs_data = [
            {
                'title': 'Python Developer',
                'company': 'TechCorp Inc.',
                'location': 'San Francisco, CA',
                'description': 'We are looking for a skilled Python developer to join our team.',
                'requirements': 'Python, Django, PostgreSQL, 3+ years experience',
                'salary_range': '$80,000 - $120,000',
                'job_type': 'Full-time'
            },
            {
                'title': 'Data Scientist',
                'company': 'DataFlow Analytics',
                'location': 'New York, NY',
                'description': 'Join our data science team to build predictive models.',
                'requirements': 'Python, Machine Learning, Statistics, 5+ years experience',
                'salary_range': '$100,000 - $150,000',
                'job_type': 'Full-time'
            },
            {
                'title': 'Web Developer',
                'company': 'Digital Solutions',
                'location': 'Remote',
                'description': 'Remote web developer position with flexible hours.',
                'requirements': 'Django, React, JavaScript, 2+ years experience',
                'salary_range': '$70,000 - $100,000',
                'job_type': 'Full-time'
            }
        ]
        
        for job_data in jobs_data:
            Job.objects.get_or_create(
                title=job_data['title'],
                company=job_data['company'],
                defaults=job_data
            )
        
        # Create sample testimonials
        testimonials_data = [
            {
                'name': 'John Smith',
                'position': 'Software Developer',
                'company': 'TechStart Inc.',
                'content': 'Skillora helped me transition from a non-tech background to a successful software developer. The Python course was excellent!',
                'rating': 5
            },
            {
                'name': 'Maria Garcia',
                'position': 'Data Analyst',
                'company': 'Analytics Pro',
                'content': 'The data science course gave me the skills I needed to advance my career. Highly recommended!',
                'rating': 5
            },
            {
                'name': 'Robert Johnson',
                'position': 'Web Developer',
                'company': 'Digital Agency',
                'content': 'Great instructors and practical projects. I landed my dream job within 3 months of completing the course.',
                'rating': 4
            }
        ]
        
        for testimonial_data in testimonials_data:
            Testimonial.objects.get_or_create(
                name=testimonial_data['name'],
                position=testimonial_data['position'],
                defaults=testimonial_data
            )
        
        # Create sample team members
        team_data = [
            {
                'name': 'Dr. Emily Watson',
                'position': 'CEO & Founder',
                'bio': 'Former tech executive with 20+ years in education technology.',
                'email': 'emily@skillora.com',
                'linkedin': 'https://linkedin.com/in/emilywatson',
                'twitter': 'https://twitter.com/emilywatson'
            },
            {
                'name': 'Mark Davis',
                'position': 'CTO',
                'bio': 'Technology leader with expertise in scalable learning platforms.',
                'email': 'mark@skillora.com',
                'linkedin': 'https://linkedin.com/in/markdavis',
                'twitter': 'https://twitter.com/markdavis'
            },
            {
                'name': 'Jennifer Lee',
                'position': 'Head of Content',
                'bio': 'Curriculum specialist with passion for skill-based learning.',
                'email': 'jennifer@skillora.com',
                'linkedin': 'https://linkedin.com/in/jenniferlee',
                'twitter': 'https://twitter.com/jenniferlee'
            }
        ]
        
        for team_data_item in team_data:
            TeamMember.objects.get_or_create(
                name=team_data_item['name'],
                position=team_data_item['position'],
                defaults=team_data_item
            )
        
        self.stdout.write(
            self.style.SUCCESS('Successfully loaded sample data!')
        )

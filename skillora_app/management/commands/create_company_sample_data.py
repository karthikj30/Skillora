from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from skillora_app.models import Company, Student, StudentProfile, UserProfile, PlacementRecord, DashboardStats, DepartmentStats
from datetime import datetime, date, timedelta
import random

class Command(BaseCommand):
    help = 'Create sample data for company dashboard testing'

    def handle(self, *args, **options):
        # Create a test company user if it doesn't exist
        try:
            company_user = User.objects.get(username='testcompany@example.com')
        except User.DoesNotExist:
            company_user = User.objects.create_user(
                username='testcompany@example.com',
                email='testcompany@example.com',
                first_name='Test',
                last_name='Company',
                password='testpass123'
            )
            
            # Create user profile
            UserProfile.objects.create(
                user=company_user,
                role='company',
                phone='+1234567890'
            )
            
            # Create company
            company = Company.objects.create(
                user=company_user,
                company_name='Tech Solutions Inc',
                industry='Technology',
                company_size='100-500',
                website='https://techsolutions.com',
                description='Leading technology solutions provider'
            )
            
            self.stdout.write(self.style.SUCCESS('Created test company user'))
        else:
            company = Company.objects.get(user=company_user)
            self.stdout.write(self.style.SUCCESS('Using existing test company'))

        # Create sample students
        departments = ['CSE', 'IOTIS', 'ECE', 'ME']
        batch_years = [2021, 2022, 2023, 2024]
        
        for i in range(20):
            try:
                student_user = User.objects.get(username=f'student{i}@example.com')
            except User.DoesNotExist:
                student_user = User.objects.create_user(
                    username=f'student{i}@example.com',
                    email=f'student{i}@example.com',
                    first_name=f'Student{i}',
                    last_name='Test',
                    password='testpass123'
                )
                
                # Create user profile
                UserProfile.objects.create(
                    user=student_user,
                    role='student',
                    phone=f'+123456789{i:02d}'
                )
                
                # Create student
                student = Student.objects.create(user=student_user)
                
                # Create student profile
                department = random.choice(departments)
                batch_year = random.choice(batch_years)
                cgpa = round(random.uniform(6.0, 9.5), 2)
                
                StudentProfile.objects.create(
                    student=student,
                    phone=f'+123456789{i:02d}',
                    department=department,
                    graduation_year=batch_year,
                    cgpa=cgpa,
                    is_placement_ready=random.choice([True, False])
                )
                
                self.stdout.write(self.style.SUCCESS(f'Created student {i}'))

        # Create sample placement records
        students = Student.objects.all()
        job_titles = ['Software Engineer', 'Data Analyst', 'Product Manager', 'UX Designer', 'DevOps Engineer']
        
        for i in range(10):
            student = random.choice(students)
            job_title = random.choice(job_titles)
            package_amount = random.randint(300000, 1500000)
            stipend_amount = random.randint(15000, 50000)
            placement_date = date.today() - timedelta(days=random.randint(1, 365))
            
            PlacementRecord.objects.create(
                company=company,
                student=student,
                job_title=job_title,
                package_amount=package_amount,
                stipend_amount=stipend_amount,
                placement_date=placement_date,
                iqac_status=random.choice(['pending', 'approved', 'rejected'])
            )
            
            self.stdout.write(self.style.SUCCESS(f'Created placement record {i}'))

        # Create dashboard stats
        total_students = Student.objects.count()
        total_placements = PlacementRecord.objects.filter(company=company).count()
        placed_students = PlacementRecord.objects.filter(company=company).values('student').distinct().count()
        placement_rate = (placed_students / total_students * 100) if total_students > 0 else 0
        
        DashboardStats.objects.update_or_create(
            company=company,
            defaults={
                'total_students': total_students,
                'total_offers': total_placements,
                'placement_rate': round(placement_rate, 2),
                'placed_students': placed_students,
                'not_placed': total_students - placed_students,
                'higher_studies': random.randint(5, 15),
                'entrepreneurs': random.randint(2, 8),
                'family_business': random.randint(3, 10),
                'competitive_exam': random.randint(8, 20),
                'highest_package': 1500000,
                'average_package': 750000,
                'max_stipend': 50000,
                'iqac_approved': PlacementRecord.objects.filter(company=company, iqac_status='approved').count(),
                'iqac_pending': PlacementRecord.objects.filter(company=company, iqac_status='pending').count(),
                'iqac_rejected': PlacementRecord.objects.filter(company=company, iqac_status='rejected').count(),
                'partner_companies': random.randint(10, 50)
            }
        )
        
        # Create department stats
        for department in departments:
            for batch_year in batch_years:
                dept_students = Student.objects.filter(placement_profile__department=department, placement_profile__graduation_year=batch_year)
                total_dept_students = dept_students.count()
                placed_dept_students = PlacementRecord.objects.filter(company=company, student__in=dept_students).values('student').distinct().count()
                placement_percentage = (placed_dept_students / total_dept_students * 100) if total_dept_students > 0 else 0
                
                DepartmentStats.objects.update_or_create(
                    company=company,
                    department_name=department,
                    batch_year=batch_year,
                    defaults={
                        'total_students': total_dept_students,
                        'placed_students': placed_dept_students,
                        'placement_percentage': round(placement_percentage, 2)
                    }
                )

        self.stdout.write(self.style.SUCCESS('Successfully created sample data for company dashboard'))

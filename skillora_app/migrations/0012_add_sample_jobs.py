from django.db import migrations
from django.utils import timezone


def add_sample_jobs(apps, schema_editor):
    Job = apps.get_model('skillora_app', 'Job')

    # title, company, location, description, requirements, salary_range, job_type, posted_date (YYYY, M, D)
    samples = [
        ("Software Engineer", "TechNova", "Bengaluru", "Build scalable web services.", "3+ years in Python/Django.", "₹12-18 LPA", "Full-time", (2025, 9, 5)),
        ("Data Analyst", "InsightWorks", "Mumbai", "Analyze business data and build dashboards.", "Excel, SQL, PowerBI/Tableau.", "₹6-10 LPA", "Full-time", (2025, 9, 12)),
        ("Frontend Developer", "PixelCraft", "Remote", "Develop responsive UIs.", "React, TypeScript, CSS.", "₹10-16 LPA", "Remote", (2025, 9, 22)),
        ("Backend Developer", "CloudForge", "Hyderabad", "Design REST APIs and microservices.", "Node.js/Go, Docker, Kubernetes.", "₹12-20 LPA", "Full-time", (2025, 10, 3)),
        ("DevOps Engineer", "ShipIt", "Pune", "CI/CD pipelines and infra automation.", "AWS, Terraform, GitHub Actions.", "₹14-22 LPA", "Full-time", (2025, 10, 10)),
        ("UI/UX Designer", "DesignHub", "Delhi", "Product design and prototyping.", "Figma, user research, prototyping.", "₹8-14 LPA", "Contract", (2025, 10, 18)),
        ("Mobile App Developer", "AppVenture", "Chennai", "Build high-quality Android/iOS apps.", "Flutter/React Native.", "₹10-18 LPA", "Full-time", (2025, 10, 25)),
        ("ML Engineer", "DeepVision", "Bengaluru", "Deploy ML models to production.", "Python, TensorFlow/PyTorch, MLOps.", "₹16-28 LPA", "Full-time", (2025, 11, 2)),
        ("Product Manager", "BrightPath", "Mumbai", "Drive product roadmap and execution.", "2+ years PM, strong comms.", "₹18-30 LPA", "Full-time", (2025, 11, 10)),
        ("Technical Writer", "DocuWise", "Remote", "Create developer documentation.", "APIs, Markdown, Diagrams.", "₹7-12 LPA", "Remote", (2025, 11, 18)),
    ]

    for title, company, location, description, requirements, salary, job_type, (y, m, d) in samples:
        # Avoid duplicates by title+company
        job, created = Job.objects.get_or_create(
            title=title,
            company=company,
            defaults={
                'location': location,
                'description': description,
                'requirements': requirements,
                'salary_range': salary,
                'job_type': job_type,
            }
        )
        # Force-set posted_date into the desired 2025 window
        aware_dt = timezone.make_aware(timezone.datetime(y, m, d, 10, 0, 0))
        Job.objects.filter(id=job.id).update(posted_date=aware_dt)


def remove_sample_jobs(apps, schema_editor):
    Job = apps.get_model('skillora_app', 'Job')
    companies = [
        "TechNova", "InsightWorks", "PixelCraft", "CloudForge", "ShipIt",
        "DesignHub", "AppVenture", "DeepVision", "BrightPath", "DocuWise"
    ]
    Job.objects.filter(company__in=companies).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('skillora_app', '0011_jobapplication'),
    ]

    operations = [
        migrations.RunPython(add_sample_jobs, remove_sample_jobs),
    ]



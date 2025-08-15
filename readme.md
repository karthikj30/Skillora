# Skillora - Django Learning Platform

A comprehensive learning platform that connects skill development with job opportunities. Built with Django framework.

## Features

- **Course Management**: Browse and enroll in skill-based courses
- **Job Matching**: Find job opportunities that match your skills
- **User Authentication**: Secure login and registration system
- **Instructor Profiles**: Learn from industry experts
- **Testimonials**: Success stories from learners
- **Team Management**: Meet the Skillora team
- **Contact System**: Get in touch with support
- **Admin Panel**: Full administrative control

## Project Structure

```
Skillora/
├── manage.py                 # Django management script
├── requirements.txt          # Python dependencies
├── README.md                # Project documentation
├── skillora_project/        # Django project settings
│   ├── __init__.py
│   ├── settings.py          # Django settings
│   ├── urls.py              # Main URL configuration
│   ├── wsgi.py              # WSGI configuration
│   └── asgi.py              # ASGI configuration
├── skillora_app/            # Django application
│   ├── __init__.py
│   ├── admin.py             # Admin interface configuration
│   ├── apps.py              # App configuration
│   ├── forms.py             # Django forms
│   ├── models.py            # Database models
│   ├── urls.py              # App URL patterns
│   └── views.py             # View functions
├── templates/               # HTML templates
│   ├── base.html            # Base template
│   ├── index.html           # Home page
│   ├── about.html           # About page
│   ├── courses.html         # Courses listing
│   ├── single.html          # Course detail
│   ├── jobs.html            # Job listings
│   ├── instructor.html      # Instructor profiles
│   ├── team.html            # Team page
│   ├── testimonial.html     # Testimonials
│   ├── contact.html         # Contact page
│   ├── login.html           # Login page
│   └── signup.html          # Registration page
└── static/                  # Static files
    ├── css/                 # Stylesheets
    ├── js/                  # JavaScript files
    ├── img/                 # Images
    └── lib/                 # Third-party libraries
```

## Database Models

- **Course**: Course information, pricing, and details
- **Instructor**: Instructor profiles and expertise
- **Job**: Job listings and requirements
- **Testimonial**: Success stories and reviews
- **TeamMember**: Team member information
- **Contact**: Contact form submissions
- **UserProfile**: Extended user profile information

## Installation and Setup

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Step 1: Clone or Download the Project

```bash
# If using git
git clone <repository-url>
cd Skillora

# Or download and extract the project files
```

### Step 2: Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Database Setup

```bash
# Create database migrations
python manage.py makemigrations

# Apply migrations to create database tables
python manage.py migrate
```

### Step 5: Create Superuser (Admin)

```bash
python manage.py createsuperuser
```

### Step 6: Run Development Server

```bash
python manage.py runserver
```

The application will be available at `http://127.0.0.1:8000/`

## Usage

### Accessing the Application

- **Home Page**: `http://127.0.0.1:8000/`
- **Admin Panel**: `http://127.0.0.1:8000/admin/`
- **Courses**: `http://127.0.0.1:8000/courses/`
- **Jobs**: `http://127.0.0.1:8000/jobs/`
- **About**: `http://127.0.0.1:8000/about/`
- **Contact**: `http://127.0.0.1:8000/contact/`

### Admin Panel Features

1. **Course Management**: Add, edit, and manage courses
2. **Instructor Management**: Manage instructor profiles
3. **Job Listings**: Post and manage job opportunities
4. **User Management**: Manage user accounts and profiles
5. **Content Management**: Handle testimonials, team members, and contact submissions

### Adding Sample Data

You can add sample data through the Django admin panel or create a data migration:

```bash
python manage.py shell
```

```python
from skillora_app.models import Course, Instructor, Job, Testimonial

# Add sample courses
Course.objects.create(
    title="Python Programming Fundamentals",
    description="Learn Python from scratch",
    instructor="John Doe",
    price=99.99,
    category="Programming",
    duration="8 weeks",
    level="Beginner"
)

# Add more sample data as needed
```

## Configuration

### Environment Variables

Create a `.env` file in the project root for sensitive settings:

```
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Static Files

Static files are automatically served in development. For production:

```bash
python manage.py collectstatic
```

### Database

The project uses SQLite by default. For production, consider using PostgreSQL or MySQL by updating the database settings in `settings.py`.

## Features Overview

### For Learners
- Browse skill-based courses
- View course details and pricing
- Read instructor profiles
- Access job opportunities
- Submit contact inquiries

### For Instructors
- Profile management
- Course creation and management
- Student interaction

### For Employers
- Post job opportunities
- Browse candidate profiles
- Connect with skilled professionals

### For Administrators
- Full content management
- User administration
- Analytics and reporting
- System configuration

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions:
- Email: info@skillora.com
- Phone: +012 345 67890
- Address: 123 Skill Street, Learning City, LC 12345

## Future Enhancements

- Payment integration
- Video streaming for courses
- Advanced job matching algorithms
- Mobile application
- API for third-party integrations
- Advanced analytics and reporting
- Multi-language support
- Course completion certificates
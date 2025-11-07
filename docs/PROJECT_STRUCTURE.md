# Skillora Project Structure

This document outlines the organized structure of the Skillora Django project.

## Root Directory Structure

```
Skillora/
├── assets/                     # Development assets (SCSS, etc.)
│   ├── media/
│   │   └── videos/            # Source video files
│   └── scss/                  # SCSS source files
│       └── bootstrap/         # Bootstrap SCSS source
├── docs/                      # Project documentation
├── scripts/                   # Utility scripts
│   └── setup.py              # Project setup script
├── skillora_app/             # Main Django application
│   ├── management/           # Custom Django commands
│   ├── migrations/           # Database migrations
│   ├── templatetags/         # Custom template tags
│   ├── admin.py             # Django admin configuration
│   ├── apps.py              # App configuration
│   ├── forms.py             # Django forms
│   ├── models.py            # Database models
│   ├── urls.py              # URL patterns
│   └── views.py             # View functions
├── skillora_project/         # Django project configuration
│   ├── settings.py          # Project settings
│   ├── urls.py              # Main URL configuration
│   ├── wsgi.py              # WSGI configuration
│   └── asgi.py              # ASGI configuration
├── static/                   # Static files (served in production)
│   ├── css/                 # Compiled CSS files
│   ├── js/                  # JavaScript files
│   ├── lib/                 # Third-party libraries
│   ├── img/                 # Images organized by category
│   │   ├── banners/         # Banner and carousel images
│   │   ├── categories/      # Category images
│   │   ├── courses/         # Course images
│   │   ├── icons/           # Icon images
│   │   ├── team/            # Team member images
│   │   └── testimonials/    # Testimonial images
│   └── media/
│       └── videos/          # Video files
├── templates/               # Django templates
├── db.sqlite3              # SQLite database
├── manage.py               # Django management script
├── requirements.txt        # Python dependencies
└── README.md              # Project documentation
```

## Directory Purposes

### `/assets/`
Contains development assets that are not directly served:
- **scss/**: SCSS source files for custom styling
- **media/videos/**: Source video files for development

### `/docs/`
Project documentation including:
- API documentation
- Setup guides
- Architecture decisions

### `/scripts/`
Utility scripts for project management:
- **setup.py**: Automated project setup script

### `/static/`
Static files served by Django:
- **css/**: Compiled CSS files
- **js/**: JavaScript files
- **lib/**: Third-party JavaScript libraries
- **img/**: Images organized by purpose
- **media/videos/**: Video files accessible via web

### `/templates/`
Django HTML templates organized by functionality

### `/skillora_app/`
Main Django application containing:
- Models, views, forms
- Custom management commands
- Template tags
- URL patterns

### `/skillora_project/`
Django project configuration files

## Benefits of This Structure

1. **Clear Separation**: Development assets vs. production static files
2. **Organized Media**: Images categorized by purpose for easy maintenance
3. **Scalable**: Easy to add new apps and organize growing codebase
4. **Standard**: Follows Django best practices
5. **Maintainable**: Clear hierarchy makes navigation intuitive

## File Naming Conventions

- **Images**: Use descriptive names with category prefixes
- **Templates**: Use lowercase with hyphens for multi-word names
- **Static files**: Organize by type and purpose
- **Python files**: Follow PEP 8 naming conventions

## Development Workflow

1. SCSS files in `/assets/scss/` are compiled to `/static/css/`
2. Media files are organized by category in `/static/img/`
3. Templates reference static files using Django's static tag
4. Custom management commands are in `/skillora_app/management/commands/`

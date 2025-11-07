#!/usr/bin/env python
"""
Setup script for Skillora Django project
This script helps with initial project setup and database initialization
"""

import os
import sys
import subprocess
import django
from django.core.management import execute_from_command_line

def run_command(command):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running command '{command}': {e}")
        return None

def setup_project():
    """Main setup function"""
    print("🚀 Setting up Skillora Django Project...")
    
    # Check if Django is installed
    try:
        import django
        print("✅ Django is installed")
    except ImportError:
        print("❌ Django is not installed. Installing requirements...")
        if run_command("pip install -r requirements.txt"):
            print("✅ Requirements installed successfully")
        else:
            print("❌ Failed to install requirements")
            return False
    
    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skillora_project.settings')
    django.setup()
    
    # Create migrations
    print("📝 Creating database migrations...")
    if run_command("python manage.py makemigrations"):
        print("✅ Migrations created successfully")
    else:
        print("❌ Failed to create migrations")
        return False
    
    # Apply migrations
    print("🗄️ Applying migrations to database...")
    if run_command("python manage.py migrate"):
        print("✅ Database setup completed")
    else:
        print("❌ Failed to apply migrations")
        return False
    
    # Create superuser if it doesn't exist
    print("👤 Checking for superuser...")
    try:
        from django.contrib.auth.models import User
        if not User.objects.filter(is_superuser=True).exists():
            print("⚠️ No superuser found. You can create one with:")
            print("   python manage.py createsuperuser")
        else:
            print("✅ Superuser already exists")
    except Exception as e:
        print(f"⚠️ Could not check superuser status: {e}")
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Create a superuser: python manage.py createsuperuser")
    print("2. Run the development server: python manage.py runserver")
    print("3. Visit http://127.0.0.1:8000/ to see your application")
    print("4. Visit http://127.0.0.1:8000/admin/ to access the admin panel")
    
    return True

if __name__ == "__main__":
    setup_project()

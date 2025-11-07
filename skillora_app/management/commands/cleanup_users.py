from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from skillora_app.models import UserProfile, Student, Teacher, Company

class Command(BaseCommand):
    help = 'Clean up unnecessary users and fix user data'

    def add_arguments(self, parser):
        parser.add_argument('--delete', action='store_true', help='Actually delete the users')

    def handle(self, *args, **options):
        # Get all users
        users = User.objects.all()
        self.stdout.write(f"Total users found: {users.count()}")
        
        # Clean up users without proper profiles or with invalid roles
        users_to_delete = []
        for user in users:
            try:
                profile = user.userprofile
                if profile.role not in ['student', 'teacher', 'company']:
                    users_to_delete.append(user)
                    self.stdout.write(f"Invalid role user: {user.username} ({user.email}) - Role: {profile.role}")
            except:
                # User has no profile
                users_to_delete.append(user)
                self.stdout.write(f"No profile user: {user.username} ({user.email})")
        
        self.stdout.write(f"\nUsers to delete: {len(users_to_delete)}")
        
        if options['delete']:
            for user in users_to_delete:
                self.stdout.write(f"Deleting: {user.username}")
                user.delete()
            self.stdout.write(f"Deleted {len(users_to_delete)} users")
        else:
            self.stdout.write("Use --delete flag to actually delete these users")
        
        # Show remaining users
        remaining_users = User.objects.all()
        self.stdout.write(f"\nRemaining users: {remaining_users.count()}")
        for user in remaining_users:
            try:
                profile = user.userprofile
                self.stdout.write(f"User: {user.username} | Email: {user.email} | Role: {profile.role}")
            except:
                self.stdout.write(f"User: {user.username} | Email: {user.email} | No Profile")
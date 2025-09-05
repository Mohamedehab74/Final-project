from django.core.management.base import BaseCommand
from projects.models import Category

class Command(BaseCommand):
    help = 'Add sample categories to the database'

    def handle(self, *args, **options):
        categories = [
            'Technology',
            'Art & Design',
            'Music',
            'Film & Video',
            'Games',
            'Publishing',
            'Food & Craft',
            'Fashion',
            'Health & Fitness',
            'Education',
            'Environment',
            'Community',
            'Science',
            'Sports',
            'Travel',
        ]
        
        created_count = 0
        for category_name in categories:
            category, created = Category.objects.get_or_create(name=category_name)
            if created:
                created_count += 1
                self.stdout.write(f'Created category: {category_name}')
            else:
                self.stdout.write(f'Category already exists: {category_name}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully processed {len(categories)} categories. {created_count} new categories created.')
        )

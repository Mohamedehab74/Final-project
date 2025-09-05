#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from projects.models import Project, Category
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

def test_search():
    print("Testing search functionality...")
    
    # Check if we have any projects
    projects = Project.objects.all()
    print(f"Total projects in database: {projects.count()}")
    
    if projects.count() == 0:
        print("No projects found. Creating test project...")
        
        # Create a test user
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User',
                'is_active': True
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
            print(f"Created test user: {user.username}")
        
        # Create a test category
        category, created = Category.objects.get_or_create(
            name='Technology',
            defaults={'description': 'Technology projects'}
        )
        if created:
            print(f"Created test category: {category.name}")
        
        # Create a test project
        project = Project.objects.create(
            owner=user,
            title='Test Technology Project',
            details='This is a test project for technology',
            total_target=1000.00,
            category=category,
            tags='technology test python',
            status='active'
        )
        print(f"Created test project: {project.title}")
    
    # Test search functionality
    search_query = 'technology'
    print(f"\nSearching for: '{search_query}'")
    
    results = Project.objects.filter(
        Q(title__icontains=search_query) |
        Q(tags__icontains=search_query) |
        Q(details__icontains=search_query) |
        Q(category__name__icontains=search_query) |
        Q(owner__first_name__icontains=search_query) |
        Q(owner__last_name__icontains=search_query)
    ).distinct()
    
    print(f"Found {results.count()} projects:")
    for project in results:
        print(f"  - {project.title} (by {project.owner.first_name} {project.owner.last_name})")
        print(f"    Tags: {project.tags}")
        print(f"    Category: {project.category.name if project.category else 'None'}")
    
    # Test case-insensitive search
    search_query_upper = 'TECHNOLOGY'
    print(f"\nSearching for: '{search_query_upper}' (uppercase)")
    
    results_upper = Project.objects.filter(
        Q(title__icontains=search_query_upper) |
        Q(tags__icontains=search_query_upper) |
        Q(details__icontains=search_query_upper) |
        Q(category__name__icontains=search_query_upper) |
        Q(owner__first_name__icontains=search_query_upper) |
        Q(owner__last_name__icontains=search_query_upper)
    ).distinct()
    
    print(f"Found {results_upper.count()} projects (case-insensitive):")
    for project in results_upper:
        print(f"  - {project.title}")

if __name__ == '__main__':
    test_search()

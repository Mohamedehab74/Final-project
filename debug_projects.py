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

User = get_user_model()

def debug_projects():
    print("Debugging projects in database...")
    
    # Check all projects
    projects = Project.objects.all()
    print(f"Total projects: {projects.count()}")
    
    for i, project in enumerate(projects, 1):
        print(f"\nProject {i}:")
        print(f"  ID: {project.id}")
        print(f"  Title: '{project.title}'")
        print(f"  Details: '{project.details[:100]}...'")
        print(f"  Tags: '{project.tags}'")
        print(f"  Category: '{project.category.name if project.category else 'None'}'")
        print(f"  Owner: '{project.owner.first_name} {project.owner.last_name}'")
        print(f"  Status: '{project.status}'")
    
    # Check all categories
    categories = Category.objects.all()
    print(f"\nTotal categories: {categories.count()}")
    for category in categories:
        print(f"  - {category.name}: {category.description}")

if __name__ == '__main__':
    debug_projects()

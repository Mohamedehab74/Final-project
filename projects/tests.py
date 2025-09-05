from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import Project, Category
from decimal import Decimal
from datetime import datetime, timedelta

User = get_user_model()

class SearchTestCase(TestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        # Make sure the user is active
        self.user.is_active = True
        self.user.save()
        
        # Create test category
        self.category = Category.objects.create(name='Technology')
        
        # Create test projects
        self.project1 = Project.objects.create(
            owner=self.user,
            title='Test Project 1',
            details='This is a test project about technology',
            category=self.category,
            total_target=Decimal('1000.00'),
            tags='technology python django',
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(days=30)
        )
        
        self.project2 = Project.objects.create(
            owner=self.user,
            title='Another Project',
            details='This is another project about art',
            category=self.category,
            total_target=Decimal('500.00'),
            tags='art design',
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(days=30)
        )
        
        self.client = Client()
    
    def test_search_by_title(self):
        """Test searching projects by title"""
        response = self.client.get(reverse('all_projects'), {'search': 'Test Project'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Project 1')
        self.assertNotContains(response, 'Another Project')
    
    def test_search_by_tag(self):
        """Test searching projects by tag"""
        response = self.client.get(reverse('all_projects'), {'search': 'python'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Project 1')
        self.assertNotContains(response, 'Another Project')
    
    def test_search_by_description(self):
        """Test searching projects by description"""
        response = self.client.get(reverse('all_projects'), {'search': 'art'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Another Project')
        self.assertNotContains(response, 'Test Project 1')
    
    def test_search_by_category(self):
        """Test searching projects by category"""
        response = self.client.get(reverse('all_projects'), {'search': 'Technology'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Project 1')
        self.assertContains(response, 'Another Project')
    
    def test_search_by_creator_name(self):
        """Test searching projects by creator name"""
        response = self.client.get(reverse('all_projects'), {'search': 'Test'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Project 1')
        self.assertContains(response, 'Another Project')
    
    def test_search_no_results(self):
        """Test search with no matching results"""
        response = self.client.get(reverse('all_projects'), {'search': 'nonexistent'})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Test Project 1')
        self.assertNotContains(response, 'Another Project')
    
    def test_search_suggestions_endpoint(self):
        """Test the search suggestions AJAX endpoint"""
        response = self.client.get(reverse('search_suggestions'), {'q': 'test'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('suggestions', response.json())
    
    def test_home_search(self):
        """Test search functionality on home page"""
        # Login the user first
        login_success = self.client.login(username='testuser', password='testpass123')
        self.assertTrue(login_success, "User login failed")
        response = self.client.get(reverse('home'), {'search': 'technology'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Project 1')

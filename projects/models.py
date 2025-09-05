from django.db import models
from django.conf import settings

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Project(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    details = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    total_target = models.DecimalField(max_digits=10, decimal_places=2)
    tags = models.CharField(max_length=200, blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    # Keep the main image field for backward compatibility
    image = models.ImageField(upload_to='project_images/', blank=True, null=True)
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    featured = models.BooleanField(default=False, help_text="Mark this project as featured to display it on the home page")

    def __str__(self):
        return self.title
    
    def get_main_image(self):
        """Get the main image (first image or the old image field)"""
        if self.image:
            return self.image
        first_image = self.projectimage_set.first()
        return first_image.image if first_image else None
    
    def get_all_images(self):
        """Get all images for this project"""
        images = list(self.projectimage_set.all())
        if self.image:
            # Add the old image field as the first image if it exists
            images.insert(0, type('Image', (), {'image': self.image})())
        return images
    
    def get_average_rating(self):
        """Calculate the average rating for this project"""
        ratings = self.projectrating_set.all()
        if ratings.exists():
            return sum(rating.rating for rating in ratings) / ratings.count()
        return 0
    
    def get_rating_count(self):
        """Get the total number of ratings for this project"""
        return self.projectrating_set.count()
    
    def get_user_rating(self, user):
        """Get the rating given by a specific user"""
        try:
            return self.projectrating_set.get(user=user).rating
        except ProjectRating.DoesNotExist:
            return None
    
    def get_donation_percentage(self):
        """Calculate the percentage of target amount raised"""
        total_donations = sum(donation.amount for donation in self.donation_set.all())
        if self.total_target > 0:
            return (total_donations / self.total_target) * 100
        return 0
    
    def can_be_cancelled(self):
        """Check if project can be cancelled (less than 25% raised)"""
        return self.status == 'active' and self.get_donation_percentage() < 25
    
    def is_cancelled(self):
        """Check if project is cancelled"""
        return self.status == 'cancelled'
    
    def get_similar_projects(self, limit=4):
        """Get similar projects based on tags and category"""
        if not self.tags:
            # If no tags, return projects from the same category
            if self.category:
                return Project.objects.filter(
                    category=self.category,
                    status='active'
                ).exclude(id=self.id).order_by('-start_time')[:limit]
            return Project.objects.none()
        
        # Split tags and clean them
        current_tags = [tag.strip().lower() for tag in self.tags.split() if tag.strip()]
        
        if not current_tags:
            return Project.objects.none()
        
        # Find projects with similar tags
        similar_projects = []
        
        # First priority: projects with exact tag matches
        for tag in current_tags:
            tag_projects = Project.objects.filter(
                tags__icontains=tag,
                status='active'
            ).exclude(id=self.id)
            
            for project in tag_projects:
                if project not in similar_projects:
                    similar_projects.append(project)
                    if len(similar_projects) >= limit:
                        break
            if len(similar_projects) >= limit:
                break
        
        # If we don't have enough projects, add projects from the same category
        if len(similar_projects) < limit and self.category:
            category_projects = Project.objects.filter(
                category=self.category,
                status='active'
            ).exclude(id=self.id).exclude(id__in=[p.id for p in similar_projects])
            
            for project in category_projects:
                if project not in similar_projects:
                    similar_projects.append(project)
                    if len(similar_projects) >= limit:
                        break
        
        return similar_projects[:limit]


class ProjectImage(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='project_images/')
    caption = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-is_primary', 'created_at']
    
    def __str__(self):
        return f"Image for {self.project.title}"
    
    def save(self, *args, **kwargs):
        # If this image is marked as primary, unmark others
        if self.is_primary:
            ProjectImage.objects.filter(project=self.project).update(is_primary=False)
        super().save(*args, **kwargs)


class Comment(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.username} on {self.project.title}"
    
    def get_replies(self):
        """Get all replies to this comment"""
        return Comment.objects.filter(parent=self).order_by('timestamp')
    
    def is_reply(self):
        """Check if this comment is a reply to another comment"""
        return self.parent is not None
    
    def get_reply_count(self):
        """Get the number of replies to this comment"""
        return self.get_replies().count()



class Donation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    project = models.ForeignKey('Project', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} donated {self.amount} to {self.project.title}"


class ProjectReport(models.Model):
    REPORT_REASONS = [
        ('inappropriate', 'Inappropriate Content'),
        ('spam', 'Spam or Misleading'),
        ('violence', 'Violence or Harmful'),
        ('copyright', 'Copyright Violation'),
        ('other', 'Other'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    reason = models.CharField(max_length=20, choices=REPORT_REASONS)
    description = models.TextField(help_text="Please provide details about the issue")
    timestamp = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['user', 'project']  # One report per user per project
    
    def __str__(self):
        return f"Report by {self.user.username} on {self.project.title}"


class CommentReport(models.Model):
    REPORT_REASONS = [
        ('inappropriate', 'Inappropriate Content'),
        ('spam', 'Spam or Misleading'),
        ('harassment', 'Harassment or Bullying'),
        ('hate_speech', 'Hate Speech'),
        ('other', 'Other'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)
    reason = models.CharField(max_length=20, choices=REPORT_REASONS)
    description = models.TextField(help_text="Please provide details about the issue")
    timestamp = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['user', 'comment']  # One report per user per comment
    
    def __str__(self):
        return f"Report by {self.user.username} on comment by {self.comment.user.username}"


class ProjectRating(models.Model):
    RATING_CHOICES = [
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Good'),
        (4, '4 - Very Good'),
        (5, '5 - Excellent'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True, help_text="Optional comment about your rating")
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'project']  # One rating per user per project
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user.username} rated {self.project.title} with {self.rating} stars"
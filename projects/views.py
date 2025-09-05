from django.shortcuts import render, redirect
from .forms import ProjectForm
from django.contrib.auth.decorators import login_required
from .models import Project, Donation, Comment, ProjectReport, CommentReport, ProjectRating, ProjectImage, Category
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse

@login_required
def my_projects_view(request):
    user = request.user
    my_projects = Project.objects.filter(owner=user)
    return render(request, 'my_projects.html', {'projects':my_projects})

def all_projects_view(request):
    category_id = request.GET.get('category')
    search_query = request.GET.get('search', '').strip()
    categories = Category.objects.all()

    projects = Project.objects.all()
    selected_category = None

    if category_id:
        projects = projects.filter(category_id=category_id)
        selected_category = Category.objects.get(id=category_id)

    if search_query:
        # Enhanced search with multiple fields
        projects = projects.filter(
            Q(title__icontains=search_query) |
            Q(tags__icontains=search_query) |
            Q(details__icontains=search_query) |
            Q(category__name__icontains=search_query) |
            Q(owner__first_name__icontains=search_query) |
            Q(owner__last_name__icontains=search_query)
        ).distinct()
        
        # Order results by relevance (title matches first, then other fields)
        from django.db.models import Case, When, IntegerField
        projects = projects.annotate(
            relevance=Case(
                When(title__icontains=search_query, then=3),
                When(tags__icontains=search_query, then=2),
                When(details__icontains=search_query, then=1),
                default=0,
                output_field=IntegerField(),
            )
        ).order_by('-relevance', '-start_time')

    context = {
        'projects': projects,
        'categories': categories,
        'selected_category': selected_category,
        'search_query': search_query,
        'search_results_count': projects.count() if search_query else None,
    }
    return render(request, 'all_projects.html', context)

@login_required
def create_project(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES) 
        if form.is_valid():
            try:
                project = form.save(commit=False)
                project.owner = request.user  
                project.save()
                
                messages.success(request, f'Project "{project.title}" created successfully!')
                return redirect('project_detail', project_id=project.id)
            except Exception as e:
                messages.error(request, f'Error creating project: {str(e)}')
        else:
            # Print form errors for debugging
            print("Form errors:", form.errors)
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = ProjectForm()
   
    return render(request, 'form.html', {'form': form, 'title': 'Create Project'})

def project_detail_view(request, project_id):
    try:
        project = Project.objects.get(id=project_id)
        # Get total donations for this project
        donations = project.donation_set.all()
        total_donations = sum(donation.amount for donation in donations)
        # Calculate progress percentage
        progress_percentage = (total_donations / project.total_target) * 100 if project.total_target > 0 else 0
        # Get comments for this project (only top-level comments, not replies)
        comments = project.comment_set.filter(parent__isnull=True).order_by('-timestamp')
        
        # Get all images for this project
        project_images = project.projectimage_set.all()
        
        # Get rating information
        average_rating = project.get_average_rating()
        rating_count = project.get_rating_count()
        user_rating = None
        if request.user.is_authenticated:
            user_rating = project.get_user_rating(request.user)
        
        # Get similar projects
        similar_projects = project.get_similar_projects(limit=4)
        
        context = {
            'project': project,
            'total_donations': total_donations,
            'progress_percentage': min(progress_percentage, 100),
            'comments': comments,
            'donation_count': donations.count(),
            'average_rating': average_rating,
            'rating_count': rating_count,
            'user_rating': user_rating,
            'donation_percentage': project.get_donation_percentage(),
            'project_images': project_images,
            'similar_projects': similar_projects,
        }
        return render(request, 'project_detail.html', context)
    except Project.DoesNotExist:
        return redirect('all_projects')

@login_required
def donate_view(request, project_id):
    try:
        project = Project.objects.get(id=project_id)
        
        # Check if project is cancelled
        if project.is_cancelled():
            return redirect('project_detail', project_id=project_id)
        
        if request.method == 'POST':
            amount = request.POST.get('amount')
            if amount and float(amount) > 0:
                # Create donation
                donation = Donation.objects.create(
                    user=request.user,
                    project=project,
                    amount=float(amount)
                )
                return redirect('project_detail', project_id=project_id)
        
        # Calculate donation data for display
        donations = project.donation_set.all()
        total_donations = sum(donation.amount for donation in donations)
        progress_percentage = (total_donations / project.total_target) * 100 if project.total_target > 0 else 0
        
        context = {
            'project': project,
            'total_donations': total_donations,
            'progress_percentage': min(progress_percentage, 100),
            'donation_count': donations.count(),
        }
        return render(request, 'donate.html', context)
    except Project.DoesNotExist:
        return redirect('all_projects')

@login_required
def add_comment_view(request, project_id):
    try:
        project = Project.objects.get(id=project_id)
        
        # Check if project is cancelled
        if project.is_cancelled():
            return redirect('project_detail', project_id=project_id)
        
        if request.method == 'POST':
            content = request.POST.get('content')
            if content and content.strip():
                # Create comment
                comment = Comment.objects.create(
                    user=request.user,
                    project=project,
                    content=content.strip()
                )
        return redirect('project_detail', project_id=project_id)
    except Project.DoesNotExist:
        return redirect('all_projects')

@login_required
def add_reply_view(request, comment_id):
    try:
        comment = Comment.objects.get(id=comment_id)
        project = comment.project
        
        # Check if project is cancelled
        if project.is_cancelled():
            return redirect('project_detail', project_id=project.id)
        
        if request.method == 'POST':
            content = request.POST.get('content')
            if content and content.strip():
                # Create reply
                reply = Comment.objects.create(
                    user=request.user,
                    project=project,
                    parent=comment,
                    content=content.strip()
                )
        return redirect('project_detail', project_id=project.id)
    except Comment.DoesNotExist:
        return redirect('all_projects')

@login_required
def report_project_view(request, project_id):
    try:
        project = Project.objects.get(id=project_id)
        
        # Check if user already reported this project
        existing_report = ProjectReport.objects.filter(user=request.user, project=project).first()
        if existing_report:
            return render(request, 'report_already_submitted.html', {
                'item_type': 'project',
                'item_name': project.title
            })
        
        if request.method == 'POST':
            reason = request.POST.get('reason')
            description = request.POST.get('description')
            
            if reason and description and description.strip():
                # Create report
                report = ProjectReport.objects.create(
                    user=request.user,
                    project=project,
                    reason=reason,
                    description=description.strip()
                )
                return render(request, 'report_submitted.html', {
                    'item_type': 'project',
                    'item_name': project.title
                })
        
        return render(request, 'report_project.html', {'project': project})
    except Project.DoesNotExist:
        return redirect('all_projects')

@login_required
def report_comment_view(request, comment_id):
    try:
        comment = Comment.objects.get(id=comment_id)
        
        # Check if user already reported this comment
        existing_report = CommentReport.objects.filter(user=request.user, comment=comment).first()
        if existing_report:
            return render(request, 'report_already_submitted.html', {
                'item_type': 'comment',
                'item_name': f'comment by {comment.user.first_name}'
            })
        
        if request.method == 'POST':
            reason = request.POST.get('reason')
            description = request.POST.get('description')
            
            if reason and description and description.strip():
                # Create report
                report = CommentReport.objects.create(
                    user=request.user,
                    comment=comment,
                    reason=reason,
                    description=description.strip()
                )
                return render(request, 'report_submitted.html', {
                    'item_type': 'comment',
                    'item_name': f'comment by {comment.user.first_name}'
                })
        
        return render(request, 'report_comment.html', {'comment': comment})
    except Comment.DoesNotExist:
        return redirect('all_projects')

@login_required
def rate_project_view(request, project_id):
    try:
        project = Project.objects.get(id=project_id)
        
        if request.method == 'POST':
            rating = request.POST.get('rating')
            comment = request.POST.get('comment', '').strip()
            
            if rating and rating.isdigit() and 1 <= int(rating) <= 5:
                rating_value = int(rating)
                
                # Check if user already rated this project
                existing_rating, created = ProjectRating.objects.get_or_create(
                    user=request.user,
                    project=project,
                    defaults={'rating': rating_value, 'comment': comment}
                )
                
                if not created:
                    # Update existing rating
                    existing_rating.rating = rating_value
                    existing_rating.comment = comment
                    existing_rating.save()
                
                return redirect('project_detail', project_id=project_id)
        
        # Get user's existing rating if any
        try:
            user_rating = project.projectrating_set.get(user=request.user)
        except ProjectRating.DoesNotExist:
            user_rating = None
        
        return render(request, 'rate_project.html', {
            'project': project,
            'user_rating': user_rating
        })
    except Project.DoesNotExist:
        return redirect('all_projects')

@login_required
def cancel_project_view(request, project_id):
    try:
        project = Project.objects.get(id=project_id)
        
        # Check if user is the project owner
        if project.owner != request.user:
            return redirect('project_detail', project_id=project_id)
        
        # Check if project can be cancelled
        if not project.can_be_cancelled():
            return render(request, 'cannot_cancel_project.html', {
                'project': project,
                'donation_percentage': project.get_donation_percentage()
            })
        
        if request.method == 'POST':
            # Cancel the project
            project.status = 'cancelled'
            project.save()
            return render(request, 'project_cancelled.html', {
                'project': project
            })
        
        return render(request, 'cancel_project_confirm.html', {
            'project': project,
            'donation_percentage': project.get_donation_percentage()
        })
    except Project.DoesNotExist:
        return redirect('all_projects')

def home_view(request):
    # Get featured and top projects
    featured_projects = Project.objects.filter(featured=True, status='active').order_by('-start_time')[:6]
    latest_projects = Project.objects.filter(status='active').order_by('-start_time')[:6]
    
    # Get top rated projects
    from django.db.models import Avg
    top_projects = Project.objects.filter(status='active').annotate(
        avg_rating=Avg('projectrating__rating')
    ).filter(avg_rating__isnull=False).order_by('-avg_rating')[:6]
    
    context = {
        'featured_projects': featured_projects,
        'top_projects': top_projects,
        'latest_projects': latest_projects,
    }
    return render(request, 'home.html', context)

def search_suggestions(request):
    """AJAX endpoint for search suggestions and results"""
    try:
        query = request.GET.get('q', '').strip()
        if len(query) < 2:
            return JsonResponse({'suggestions': [], 'projects': []})
        
        # Get actual project results - case insensitive
        projects = Project.objects.filter(
            Q(title__icontains=query) |
            Q(tags__icontains=query) |
            Q(details__icontains=query) |
            Q(category__name__icontains=query) |
            Q(owner__first_name__icontains=query) |
            Q(owner__last_name__icontains=query)
        ).distinct()[:10]
        
        # Serialize projects
        from django.urls import reverse
        project_data = []
        for project in projects:
            try:
                main_image = project.get_main_image()
                project_data.append({
                    'id': project.id,
                    'title': project.title,
                    'owner_name': f"{project.owner.first_name} {project.owner.last_name}",
                    'description': project.details[:150] + '...' if len(project.details) > 150 else project.details,
                    'image_url': main_image.url if main_image else '',
                    'tags': [tag.strip() for tag in project.tags.split()] if project.tags else [],
                    'url': reverse('project_detail', args=[project.id]),
                    'category': project.category.name if project.category else 'General',
                    'donation_percentage': project.get_donation_percentage(),
                    'total_target': float(project.total_target),
                })
            except Exception as e:
                # Skip projects that cause errors
                continue
        
        return JsonResponse({
            'suggestions': [],
            'projects': project_data
        })
    except Exception as e:
        # Return empty results if there's an error
        return JsonResponse({
            'suggestions': [],
            'projects': []
        })



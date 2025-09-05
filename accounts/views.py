from django.shortcuts import render, redirect
from .forms import RegisterForm
from django.contrib.auth.decorators import login_required
from projects.models import Donation, Project, Category
from django.contrib import messages
from django.contrib.auth import logout, authenticate, login
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from .models import CustomUser, ActivationToken
from django.http import Http404
from django.db.models import Q

def landing_view(request):
    """Landing page - first page users see"""
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'landing.html')

@login_required
def home_view(request):
    """Home page for authenticated users"""
    search_query = request.GET.get('search', '').strip()
    projects = Project.objects.all()
    
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
        
        # Order results by relevance
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
    
    # Get featured and top projects for non-search results
    featured_projects = None
    top_projects = None
    latest_projects = None
    
    if not search_query:
        featured_projects = Project.objects.filter(featured=True, status='active').order_by('-start_time')[:6]
        latest_projects = Project.objects.filter(status='active').order_by('-start_time')[:6]
        
        # Get top rated projects
        from django.db.models import Avg
        top_projects = Project.objects.filter(status='active').annotate(
            avg_rating=Avg('projectrating__rating')
        ).filter(avg_rating__isnull=False).order_by('-avg_rating')[:6]
    
    context = {
        'projects': projects,
        'search_query': search_query,
        'search_results_count': projects.count() if search_query else None,
        'featured_projects': featured_projects,
        'top_projects': top_projects,
        'latest_projects': latest_projects,
    }
    return render(request, 'home.html', context)

@login_required
def profile_view(request):
    user = request.user
    # Get user's projects
    from projects.models import Project
    projects = Project.objects.filter(owner=user).order_by('-start_time')
    return render(request, 'profile.html', {'user': user, 'projects': projects})

def send_activation_email(request, user, activation_token):
    """Send activation email to user"""
    activation_url = f"{request.scheme}://{request.get_host()}/activate/{activation_token.token}/"
    
    # Render email template
    html_message = render_to_string('activation_email.html', {
        'user': user,
        'activation_url': activation_url
    })
    
    # Strip HTML for plain text version
    plain_message = strip_tags(html_message)
    
    # Send email
    send_mail(
        subject='Activate Your Account',
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST, request.FILES)
        if form.is_valid():
            # Create user but don't save yet
            user = form.save(commit=False)
            user.is_active = False  # User must activate via email
            user.save()
            
            # Create activation token
            activation_token = ActivationToken.objects.create(user=user)
            
            # Send activation email
            try:
                send_activation_email(request, user, activation_token)
                messages.success(request, 'Account created successfully! Please check your email to activate your account.')
            except Exception as e:
                # If email fails, delete the user and token
                activation_token.delete()
                user.delete()
                messages.error(request, 'Error sending activation email. Please try again.')
                return render(request, 'form.html', {'form': form, 'title':'Register'})
            
            return redirect('login')  
    else:
        form = RegisterForm()
    return render(request, 'form.html', {'form': form, 'title':'Register'})

def activate_account(request, token):
    """Activate user account using token"""
    try:
        activation_token = ActivationToken.objects.get(token=token)
        
        # Check if token is expired
        if activation_token.is_expired():
            activation_token.delete()
            return render(request, 'activation_expired.html')
        
        # Check if user is already activated
        if activation_token.user.is_active:
            activation_token.delete()
            return render(request, 'activation_invalid.html')
        
        # Activate the user
        user = activation_token.user
        user.is_active = True
        user.save()
        
        # Delete the activation token
        activation_token.delete()
        
        return render(request, 'activation_success.html', {'user': user})
        
    except ActivationToken.DoesNotExist:
        return render(request, 'activation_invalid.html')

@login_required
def home_view(request):
    # Get top 5 highest-rated active projects
    from projects.models import Project
    from django.db.models import Avg
    
    top_projects = Project.objects.filter(
        status='active'
    ).annotate(
        avg_rating=Avg('projectrating__rating')
    ).filter(
        avg_rating__isnull=False
    ).order_by('-avg_rating')[:5]
    
    # Get latest 5 projects
    latest_projects = Project.objects.filter(
        status='active'
    ).order_by('-start_time')[:5]
    
    # Get featured projects (admin-selected)
    featured_projects = Project.objects.filter(
        status='active',
        featured=True
    ).order_by('-start_time')[:5]
    
    return render(request, 'home.html', {
        'top_projects': top_projects,
        'latest_projects': latest_projects,
        'featured_projects': featured_projects
    })

def login_view(request):
    if request.user.is_authenticated:
        print(f"User already authenticated: {request.user}")
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        print(f"Login attempt for username: {username}")
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Check if user account is activated
            if not user.is_active:
                messages.error(request, 'Your account is not activated. Please check your email for the activation link.')
                return render(request, 'login.html')
            
            login(request, user)
            print(f"User logged in successfully: {user}")
            messages.success(request, f'Welcome back, {user.first_name}!')
            return redirect('home')
        else:
            print("Login failed: Invalid credentials")
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'login.html')

def logout_view(request):
    print(f"Logout view called by user: {request.user}")
    logout(request)
    print("User logged out successfully")
    messages.success(request, 'You have been successfully logged out.')
    return redirect('login')

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import EditProfileForm

@login_required
def edit_profile_view(request):
    if request.method == 'POST':
        form = EditProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = EditProfileForm(instance=request.user)
    return render(request, 'edit_profile.html',{'form':form})

@login_required
def my_donations_view(request):
    donations = Donation.objects.filter(user=request.user)
    return render(request, 'my_donations.html', {'donations':donations})

@login_required
def delete_account_view(request):
    if request.method == 'POST':
        # Delete the user account
        user = request.user
        user.delete()
        return redirect('login')
    return render(request, 'delete_account.html')
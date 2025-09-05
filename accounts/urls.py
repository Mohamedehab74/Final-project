from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_view, name='landing'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('login/', views.login_view, name='login'),
    path('home/', views.home_view, name='home'),
    path('profile/', views.profile_view, name='profile'),
    path('edit/', views.edit_profile_view, name='edit_profile'),
    path('donations/', views.my_donations_view, name='my_donations'),
    path('delete-account/', views.delete_account_view, name='delete_account'),
    path('activate/<uuid:token>/', views.activate_account, name='activate_account'),
]

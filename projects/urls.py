from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_project, name='create_project'),
    path('all/', views.all_projects_view, name='all_projects'),
    path('my-projects/', views.my_projects_view, name='my_projects'),
    path('search-suggestions/', views.search_suggestions, name='search_suggestions'),
    path('<int:project_id>/', views.project_detail_view, name='project_detail'),
    path('<int:project_id>/donate/', views.donate_view, name='donate'),
    path('<int:project_id>/comment/', views.add_comment_view, name='add_comment'),
    path('comment/<int:comment_id>/reply/', views.add_reply_view, name='add_reply'),
    path('<int:project_id>/report/', views.report_project_view, name='report_project'),
    path('comment/<int:comment_id>/report/', views.report_comment_view, name='report_comment'),
    path('<int:project_id>/rate/', views.rate_project_view, name='rate_project'),
    path('<int:project_id>/cancel/', views.cancel_project_view, name='cancel_project'),
]
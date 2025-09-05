from django.contrib import admin
from .models import Category, Project, Comment, Donation, ProjectReport, CommentReport, ProjectRating, ProjectImage

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'owner', 'category', 'total_target', 'status', 'featured', 'start_time', 'end_time']
    list_filter = ['status', 'category', 'featured', 'start_time', 'end_time']
    search_fields = ['title', 'details', 'owner__username']
    readonly_fields = ['get_donation_percentage']
    list_editable = ['featured']
    actions = ['mark_as_featured', 'unmark_as_featured']
    
    def mark_as_featured(self, request, queryset):
        updated = queryset.update(featured=True)
        self.message_user(request, f'{updated} project(s) marked as featured.')
    mark_as_featured.short_description = "Mark selected projects as featured"
    
    def unmark_as_featured(self, request, queryset):
        updated = queryset.update(featured=False)
        self.message_user(request, f'{updated} project(s) unmarked as featured.')
    unmark_as_featured.short_description = "Unmark selected projects as featured"

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'project', 'content', 'timestamp']
    list_filter = ['timestamp']
    search_fields = ['content', 'user__username', 'project__title']

@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ['user', 'project', 'amount', 'timestamp']
    list_filter = ['timestamp']
    search_fields = ['user__username', 'project__title']

@admin.register(ProjectReport)
class ProjectReportAdmin(admin.ModelAdmin):
    list_display = ['user', 'project', 'reason', 'timestamp', 'is_resolved']
    list_filter = ['reason', 'is_resolved', 'timestamp']
    search_fields = ['user__username', 'project__title', 'description']

@admin.register(CommentReport)
class CommentReportAdmin(admin.ModelAdmin):
    list_display = ['user', 'comment', 'reason', 'timestamp', 'is_resolved']
    list_filter = ['reason', 'is_resolved', 'timestamp']
    search_fields = ['user__username', 'comment__content', 'description']

@admin.register(ProjectRating)
class ProjectRatingAdmin(admin.ModelAdmin):
    list_display = ['user', 'project', 'rating', 'timestamp']
    list_filter = ['rating', 'timestamp']
    search_fields = ['user__username', 'project__title', 'comment']

@admin.register(ProjectImage)
class ProjectImageAdmin(admin.ModelAdmin):
    list_display = ['project', 'caption', 'is_primary', 'created_at']
    list_filter = ['is_primary', 'created_at']
    search_fields = ['project__title', 'caption']
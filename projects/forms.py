from django import forms
from .models import Project, ProjectImage

class ProjectForm(forms.ModelForm):
    start_time = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))
    end_time = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))
    
    # Single image field
    image = forms.ImageField(
        required=True,
        help_text="Upload an image for your project (required)"
    )

    class Meta:
        model = Project
        fields = [
            'title', 'details', 'category', 'total_target',
            'tags', 'start_time', 'end_time', 'image'
        ]
        
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if start_time and end_time and start_time >= end_time:
            raise forms.ValidationError("End time must be after start time.")
        
        return cleaned_data

class ProjectImageForm(forms.ModelForm):
    class Meta:
        model = ProjectImage
        fields = ['image', 'caption', 'is_primary']
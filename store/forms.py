from django import forms
from .models import ReviewsRating

class ReviewForm(forms.ModelForm):
    class Meta:
        model = ReviewsRating
        fields = ['subject', 'review', 'rating']
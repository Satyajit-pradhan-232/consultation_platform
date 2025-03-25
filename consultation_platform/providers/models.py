from django.db import models
from users.models import User

class Provider(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='provider_profile')
    specialty = models.CharField(max_length=100)
    rate_per_minute = models.DecimalField(max_digits=5, decimal_places=2)
    availability = models.JSONField(default=list)
    is_verified = models.BooleanField(default=False)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)

    def __str__(self):
        return f'Provider: {self.user.first_name} {self.user.last_name}\n {self.user.email} ({self.specialty})'
    
    def update_avergae_rating(self, rating):
        '''
        Calculates and updates the average rating of the provider
        should be called after adding/updating a rating
        '''
        from ratings.models import Rating

        ratings = Rating.objects.filter(provider=self)
        
        if ratings.exists():
            total_rating = sum([rating.rating for rating in ratings])
            self.average_rating = total_rating / ratings.count()
        else:
            self.average_rating = 0.0
        
        self.save()

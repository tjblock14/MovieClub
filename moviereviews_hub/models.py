from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User  # For logins
from django.contrib.postgres.fields import ArrayField


# Create your models here.

# Information about a movie. This will be submitted by a user in the future. Things needed are the movie title, director,
# starring actors, and the main genres of the movie
class Movie(models.Model):
    title = models.CharField(max_length = 200)
    director = ArrayField(models.CharField(max_length = 100), default = list)

    actors = ArrayField(models.CharField(max_length=100), default = list)      # default = list to avoid an issue I was having where
                                                                               # every character was separated by a comma
    genres = ArrayField(models.CharField(max_length = 150), default = list)
    slug = models.SlugField(max_length = 200, unique = True, blank = True) # Automatically assigns a slug value to the title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)  # Slugifying removes punctiation from title and replaces spaces with dashes for better url format
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title

# This will contain all of the reviews on a movie
class Review(models.Model):
    movie = models.ForeignKey(Movie, on_delete = models.CASCADE)  # If a movie is deleted, delete all reviews associated with it
    couple_id = models.CharField(max_length = 20) # Track which couple this review is from
    reviewer = models.CharField(max_length = 15)  # Track whose review this is
    rating = models.FloatField()
    rating_justification = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    # contains_spoiler = models.BooleanField(default = false)  probably will be handled elsewhere
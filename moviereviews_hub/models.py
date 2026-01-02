from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User  # For logins
from django.contrib.postgres.fields import ArrayField
from django.db.models import Q

# Create your models here.

# Information about a movie. This will be submitted by a user in the future. Things needed are the movie title, director,
# starring actors, and the main genres of the movie
class Movie(models.Model):
    TMDB_Api_ID = models.PositiveIntegerField(null = True, blank = True, db_index = True)
    
    title = models.CharField(max_length = 200)
    director = ArrayField(models.CharField(max_length = 100), default = list)
    actors = ArrayField(models.CharField(max_length=200), default = list)      # default = list to avoid an issue I was having where                                                                           # every character was separated by a comma
    genres = ArrayField(models.CharField(max_length = 150), default = list)
    
    release_yr = models.PositiveSmallIntegerField(null = True, blank = True)
    runtime = models.PositiveSmallIntegerField(null = True, blank = True)
    poster_url = models.CharField(max_length = 255, blank = True, default = "")
    
    slug = models.SlugField(max_length = 200, unique = True, blank = True) # Automatically assigns a slug value to the title

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields = ["TMDB_Api_ID"],
                condition = Q(TMDB_Api_ID__isnull = False),
                name = "unique_movie_tmdb_api_Id_not_null"
            )
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title) or "movie"   # Slugifying removes punctuation and replaces spaces with dashes for better URL format
            candidate = base
            i = 2

            # Ensure uniqueness across all movies. If "heat" exists, try "heat-2", "heat-3", ...
            while Movie.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                candidate = f"{base}-{i}"
                i += 1

            self.slug = candidate
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title

# This will contain all of the reviews on a movie
class Review(models.Model):
    movie     = models.ForeignKey(Movie, on_delete = models.CASCADE)  # If a movie is deleted, delete all reviews associated with it
    couple_id = models.CharField(max_length = 20) # Track which couple this review is from
    reviewer  = models.CharField(max_length = 15)  # Track whose review this is
    rating    = models.FloatField(null=True, blank=True)
    rating_justification = models.TextField(blank=True, default="")
    user      = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    # contains_spoiler = models.BooleanField(default = false)  probably will be handled elsewhere
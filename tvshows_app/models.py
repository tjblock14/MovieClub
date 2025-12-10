from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator

#=======================================================
# This contains all of the information that we want to 
# store in the database about a Tv show
#=======================================================
class TvShow(models.Model):
    TvMazeAPIid = models.PositiveIntegerField(unique = True, db_index = True)
    title       = models.CharField(max_length = 255)
    slug        = models.SlugField(max_length = 300, unique = True)
    summary     = models.TextField(blank = True)
    genres      = models.JSONField(default = list, blank = True)
    image_url   = models.URLField(blank = True)
    premiered   = models.DateField(null = True, blank = True)
    creators    = models.JSONField(default = list, blank = True)
    status      = models.CharField(max_length = 64, blank = True)
    #created_at  = models.DateTimeField(auto_now_add = True)
    #updated_at  = models.DateTimeField(auto_now = True)

    class Meta:
        ordering = ["title"]

    def save(self, *a, **kw):
        if not self.slug:
            self.slug = slugify(f"{self.title}-{self.TvMazeAPIid}")
        return super().save(*a, **kw)
    
    def __str__(self): 
        return self.title

#=======================================================
# This contains all of the information that we want to 
# store in the database about a season of a Tv show
#=======================================================
class Season(models.Model):
    show                = models.ForeignKey(TvShow, on_delete = models.CASCADE, related_name = "seasons")
    season_number       = models.PositiveIntegerField(validators = [MinValueValidator(1)])
    TvMazeAPI_season_id =  models.PositiveIntegerField(unique = True, db_index = True)
    summary             = models.TextField(blank = True)
    season_release_year = models.PositiveIntegerField(null = True, blank = True)
    season_episode_cnt  = models.PositiveIntegerField(default = 1, validators= [MinValueValidator(1)])

    class Meta:
        unique_together = (("show", "season_number"),)
        ordering = ["season_number"]
    
    def __str__(self):
        return f"{self.show.title} - S{self.season_number}"

#=======================================================
# This contains all of the information that we want to 
# store in the database about an episode of a Tv show
#=======================================================   
class Episode(models.Model):
    season_number = models.ForeignKey(Season, on_delete = models.CASCADE, related_name = "episodes")
    episode_number = models.PositiveIntegerField(validators = [MinValueValidator(1)])
    TvMazeAPI_episode_id = models.PositiveIntegerField(unique = True, db_index = True)
    episode_title        = models.CharField(max_length = 255, blank = True)
    air_date             = models.DateField(null = True, blank = True)
    episode_runtime      = models.PositiveIntegerField(null = True, blank = True)
    summary              = models.TextField(blank = True)

    class Meta:
        unique_together = (("season_number", "episode_number"),)
        ordering = ["episode_number"]

    def __str__(self):
        return f"{self.season_number.show.title} - S{self.season_number.season_number:02}:E{self.episode_number}"
    

from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Q

#---------------------------------------------------------------------------------------------
# MODEL: 
#    TvShowRatingsAndReviews
# PURPOSE: 
#    Each instance of this model represents a single rating/review entry related to either a 
#    whole TV show, one season of a TV show, or one episode of a TV show
#---------------------------------------------------------------------------------------------
class TvShowRatingsAndReviews(models.Model):
    
    # Prepare an array type that is used to internally identify which item the current review is referring to
    TARGET_SHOW = 'show'
    TARGET_SEASON = 'season'
    TARGET_EPISODE = 'episode'

    # Valid types for reviews. First item is the database value, second item is a human readable label
    TARGET_TYPES_t = [
        (TARGET_SHOW, 'Show'),
        (TARGET_SEASON, 'Season'),
        (TARGET_EPISODE, 'Episode')
    ]

    # Store which entity the current review is for
    target_type = models.CharField(max_length = 10, choices = TARGET_TYPES_t)


    tv_show_type = models.ForeignKey(
        'TvShow', # TV show model linked to this model
        related_name = 'reviews', # all reviews for a show accessible with ShowTitle.reviews.all()
        on_delete = models.CASCADE, # if a show is deleted, delete related reviews too
        null = True, # field can be empty
        blank = True
    )

    tv_season_type = models.ForeignKey(
        'Season', # Season model linked to this model
        related_name = 'reviews', # all reviews for a show accessible with SeasonNum.reviews.all()
        on_delete = models.CASCADE, # if a season is deleted, delete related reviews too
        null = True,
        blank = True
    )

    tv_episode_type = models.ForeignKey(
        'Episode', # Episode model linked to this model
        related_name = 'reviews', # all reviews for a show accessible with EpisodeNum.reviews.all()
        on_delete = models.CASCADE, # if a episode is deleted, delete related reviews too
        null = True,
        blank = True
    )

    # Link each review to the user that wrote it
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, # Works with custom user model???
        on_delete = models.CASCADE, # If user is deleted, so are their reviews
        related_name = 'tvshow_reviews' # user.tvshows_reviews.all() will give all of this users reviews
    )

    # Store which couple the user review should be apart of
    couple_slug = models.SlugField(max_length = 100, blank = True)

    # Where the actual numeric rating will be stored
    rating = models.FloatField(
        validators = [
            MinValueValidator(0),
            MaxValueValidator(10)
        ]
    )

    rating_justification = models.TextField(
        blank = True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields = [
                    'reviewer', 'tv_show_type' # the combination of the reviewer and the TV show must be unique
                ],
                condition = Q(tv_show_type__isnull = False), # only applies when tv_show has a value associated with it
                name = 'unique_show_review_per_user'
            ),
            models.UniqueConstraint(
                fields = [
                    'reviewer', 'tv_season_type' # the combination of the reviewer and the season must be unique
                ],
                condition = Q(tv_season_type__isnull = False),
                name = 'unique_season_review_per_user'
            ),
            models.UniqueConstraint(
                fields = [
                    'reviewer', 'tv_episode_type' # the combination of the reviewer and the episode must be unique
                ],
                condition = Q(tv_episode_type__isnull = False),
                name = 'unique_episode_review_per_user'
            )
        ]

    def clean(self):
        from django.core.exceptions import ValidationError

        # Possible foreign key fields, every show will reference exactly one of these
        targets = [
            self.tv_show_type,
            self.tv_season_type,
            self.tv_episode_type
        ]

        # Adds 1 for each foreign key field that is filled. If 0 or greateer than 1, raise an error
        if sum(1 for t in targets if t is not None) != 1:
            raise ValidationError("Exactly one of tv_show, tv_season, or tv_episode types must be set")
        
        # The target type must match which foreign key is used
        if self.target_type == self.TARGET_SHOW and not self.tv_show_type:
            raise ValidationError("target_type 'show' requires 'tv_show_type'")
        if self.target_type == self.TARGET_SEASON and not self.tv_season_type:
            raise ValidationError("target_type 'season; requires 'tv_season_type'")
        if self.target_type == self.TARGET_EPISODE and not self.tv_episode_type:
            raise ValidationError("target_type 'episode' requires 'tv_episode_type'")
        
    # String representation of the object
    def __str__(self):
        if self.tv_show_type:
            target = f"Show: {self.tv_show_type.title}"
        elif self.tv_season_type:
            target = f"Season {self.tv_season_type.season_number} of {self.tv_show_type.title}"
        elif self.tv_episode_type:
            target = f"S{self.tv_season_type.season_number} E{self.tv_episode_type.episode_number} of {self.tv_show_type.title}"

        return f"{self.reviewer} - {target} - {self.rating}"
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
    #status      = models.CharField(max_length = 64, blank = True)
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
    
from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Review, Movie  # Include any other models you want visible

admin.site.register(Review)
admin.site.register(Movie)

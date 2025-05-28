#from django.shortcuts import render
from rest_framework import viewsets
from .models import Movie, Review
from .serializers import MovieSerializer, ReviewSerializer

# Create your views here.

# Creates REST API for movies (POST, DELETE, UPDATE, etc.)
class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all()           # Get all movies from database
    serializer_class = MovieSerializer       # Use movie serializer to convert the data

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()          # Get all reviews
    serializer_class = ReviewSerializer      # Use review serializer to covert data
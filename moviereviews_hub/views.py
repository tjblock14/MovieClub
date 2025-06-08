#from django.shortcuts import render
from rest_framework import viewsets
from .models import Movie, Review
from .serializers import MovieSerializer, ReviewSerializer
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .permissions import IsReviewOwnerOrReadOnly

# ===================================================
#  Create your views here.
# Views are the code that is ran when a user clicks a url or searches a specific url
# ====================================================

# Creates REST API for movies (POST, DELETE, UPDATE, etc.)
class MovieViewSet(viewsets.ModelViewSet):
    queryset         = Movie.objects.all()   # Get all movies from database
    serializer_class = MovieSerializer       # Use movie serializer to convert the data
    lookup_field     = 'slug'               # Use url/<slugified title> rather than url/<id>

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()          # Get all reviews, visible to everyone
    serializer_class = ReviewSerializer      # Use review serializer to covert data
    permission_classes = [IsAuthenticatedOrReadOnly, IsReviewOwnerOrReadOnly]

    # when a user is submitting a review, automatically attach the logged in user to their review field
    def perform_create(self, serializer):
            # set the user and the reviewer the user that is logged in
            user=self.request.user,
            username=self.request.user.username

            user_to_couple = {
                 "trevor" : "TrevorTaylor",
                 "taylor" : "TrevorTaylor",
                 "marissa" : "MarissaNathan",
                 "nathan" : "MarissaNathan",
                 "sierra" : "SierraBenett",
                 "benett" : "SierraBenett"
            }

            couple_id = user_to_couple.get(username, "uncategorized")

            serializer.save( 
                 user = user,
                 reviewer = username,
                 couple_id = couple_id
            )

# ========================================
# Function based views (custom logic for the different couples pages)
# ========================================

from rest_framework.decorators import api_view
from rest_framework.response import Response

# Map each slug to a couple ID that is used in the database
COUPLE_SLUG_TO_ID_MAP = {
    "tt" : "TrevorTaylor",
    "mn" : "MarissaNathan",
    "sb" : "SierraBenett"
}

# =================================================
# This function returns a list of all movies from the database and the reviews left by the specified couple
# PARAMETERS
#   - HTTP request object (must be 'GET' for this function)
#   - couple_slug is the slug from the URL path (tt, mn, sb)
# 
# RETURNS
#   - a list of python dictionaries with each one containing movie information and the reviews from that specific couple
#       - dictionary stores like this key : value
# =================================================
@api_view(['GET'])
def couple_specific_reviews(request, couple_slug):
    # Convert the slug to the couple ID used in the database
    couple_id = COUPLE_SLUG_TO_ID_MAP.get(couple_slug.lower())

    # If the slug does not match any couple ID in the database, return an error
    if not couple_id:
        return Response({"error": "Invalid couple slug"}, status = 400)
    
    # Get all movies in the database
    movies_in_database = Movie.objects.all()

    # Initialize a list that will be separated per movie with the couple's reviews included
    response_data = []

    # For each movie, get reviews by both members of specified couple, return blank if no review
    for movie in movies_in_database:
        # Filter through the review table in database, returns reviews that belong to current movie and are written by current couple
        reviews = Review.objects.filter(movie = movie, couple_id = couple_id)

        # Create an empty dictionary that will contain the reviews from each person as a key-value pair
        reviewer_reviews = {}

        # Loops through the list of reviews for specified movies. This should just be two reviews since reviews is already filtered above
        for review in reviews:
            # Normalize the reviewer name by stripping any spaces and capitalizing the first letter
            normalized_reviewer_name = review.reviewer.strip().capitalize()

            reviewer_reviews[normalized_reviewer_name] = {
                "rating" : review.rating,
                "review" : review.rating_justification
            }

        response_data.append({
            "title"    : movie.title,
            "director" : movie.director,
            "actors"   : movie.starring_actors,
            "genres"   : movie.genres,
            "reviews"  : reviewer_reviews   # The reviews left by this couple
        })

    # Return the final list with movie info and couple reviews as JSON
    return Response({"results" :response_data} )
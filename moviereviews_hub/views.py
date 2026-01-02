# from django.shortcuts import render
import os
import requests

from django.utils.functional import SimpleLazyObject
from django.utils.text import slugify

from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response

from django.db.models import Avg, Count

from .models import Movie, Review
from .serializers import MovieSerializer, ReviewSerializer, CustomTokenObtainPairSerializer
from .permissions import IsReviewOwnerOrReadOnly
from rest_framework_simplejwt.views import TokenObtainPairView


# ===================================================
#  Create your views here.
# Views are the code that is ran when a user clicks a url or searches a specific url
# ====================================================

# Creates REST API for movies (POST, DELETE, UPDATE, etc.)
class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all()          # Get all movies from database
    serializer_class = MovieSerializer      # Use movie serializer to convert the data
    lookup_field = 'slug'                  # Use url/<slugified title> rather than url/<id>
    permission_classes = [IsAuthenticatedOrReadOnly]

    def create(self, request, *args, **kwargs):
        print("DEBUG incoming request.data:", request.data)  # 👈 Logs the raw input

        response = super().create(request, *args, **kwargs)

        # Print what got saved to the DB
        slug = response.data.get('slug')
        if slug:
            movie = Movie.objects.get(slug=slug)
            print("POST-SAVE DB VALUE:")
            print("  director:", movie.director, type(movie.director))
            print("  genres  :", movie.genres, type(movie.genres))

        return response

    # POST /api/movies/import_from_tmdb/
    @action(detail=False, methods=["post"], url_path="import_from_tmdb", permission_classes=[IsAuthenticated])
    def import_from_tmdb(self, request):
        tmdb_id = request.data.get("tmdb_id")
        if not tmdb_id:
            return Response({"detail": "tmdb_id required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            tmdb_id = int(tmdb_id)
        except (TypeError, ValueError):
            return Response({"detail": "tmdb_id must be an integer"}, status=status.HTTP_400_BAD_REQUEST)

        # If already imported, return it
        existing = Movie.objects.filter(TMDB_Api_ID=tmdb_id).first()
        if existing:
            return Response(self.get_serializer(existing).data, status=status.HTTP_200_OK)

        TMDB_KEY = os.environ.get("TMDB_API_KEY")
        if not TMDB_KEY:
            return Response({"detail": "TMDB_API_KEY not configured"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # ---- Fetch TMDB movie details ----
        try:
            details_res = requests.get(
                f"https://api.themoviedb.org/3/movie/{tmdb_id}",
                params={"api_key": TMDB_KEY, "language": "en-US"},
                timeout=15,
            )
            details_res.raise_for_status()
            details = details_res.json()
        except Exception as e:
            return Response({"detail": f"TMDB details failed: {e}"}, status=status.HTTP_502_BAD_GATEWAY)

        # ---- Fetch TMDB credits ----
        credits = {}
        try:
            credits_res = requests.get(
                f"https://api.themoviedb.org/3/movie/{tmdb_id}/credits",
                params={"api_key": TMDB_KEY, "language": "en-US"},
                timeout=15,
            )
            credits_res.raise_for_status()
            credits = credits_res.json()
        except Exception:
            credits = {}  # not fatal

        title = details.get("title") or details.get("original_title") or f"Movie {tmdb_id}"

        # Director(s)
        directors = []
        for p in (credits.get("crew") or []):
            if p.get("job") == "Director" and p.get("name"):
                directors.append(p["name"])
        # keep unique + stable ordering
        directors = list(dict.fromkeys(directors))

        # Top cast (first 10)
        actors = [c.get("name") for c in (credits.get("cast") or [])[:10] if c.get("name")]

        # Genres
        genres = [g.get("name") for g in (details.get("genres") or []) if g.get("name")]

        # Release year (TMDB uses release_date: "YYYY-MM-DD")
        release_date = details.get("release_date") or ""
        release_yr = None
        if len(release_date) >= 4 and release_date[:4].isdigit():
            release_yr = int(release_date[:4])

        runtime = details.get("runtime")

        # Poster
        poster_path = details.get("poster_path") or ""
        poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else ""

        movie = Movie.objects.create(
            TMDB_Api_ID=tmdb_id,
            title=title,
            director=directors,
            actors=actors,
            genres=genres,
            release_yr=release_yr,
            runtime=runtime,
            poster_url=poster_url,
            # NOTE: you already have robust slug generation in Movie.save(),
            # so don’t force slug here unless you want tmdb_id baked in.
        )

        return Response(self.get_serializer(movie).data, status=status.HTTP_201_CREATED)



class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()          # Get all reviews, visible to everyone
    serializer_class = ReviewSerializer      # Use review serializer to covert data
    permission_classes = [IsAuthenticatedOrReadOnly, IsReviewOwnerOrReadOnly]

    # when a user is submitting a review, automatically attach the logged in user to their review field
    def perform_create(self, serializer):
        user = self.request.user
        username = self.request.user.username

        if isinstance(user, SimpleLazyObject):
            user = user._wrapped

        user_to_couple = {
            "trevor": "TrevorTaylor",
            "taylor": "TrevorTaylor",
            "marissa": "MarissaNathan",
            "nathan": "MarissaNathan",
            "sierra": "SierraBenett",
            "benett": "SierraBenett",
            "rob": "MomDad",
            "terry": "MomDad",
            "mia": "MiaLogan",
            "logan": "MiaLogan"
        }

        couple_id = user_to_couple.get(username, "uncategorized")

        serializer.save(
            user=user,
            reviewer=username,
            couple_id=couple_id
        )


# ========================================
# Function based views (custom logic for the different couples pages)
# ========================================

# Map each slug to a couple ID that is used in the database
COUPLE_SLUG_TO_ID_MAP = {
    "tt": "TrevorTaylor",
    "mn": "MarissaNathan",
    "sb": "SierraBenett",
    "mom_dad": "MomDad",
    "ml": "MiaLogan",
}

@api_view(['GET'])
def couple_specific_reviews(request, couple_slug):
    couple_id = COUPLE_SLUG_TO_ID_MAP.get(couple_slug.lower())
    if not couple_id:
        return Response({"error": "Invalid couple slug"}, status=400)

    movies_in_database = Movie.objects.all()
    response_data = []

    for movie in movies_in_database:
        reviews = Review.objects.filter(movie=movie, couple_id=couple_id)

        reviewer_reviews = {}
        for review in reviews:
            normalized_reviewer_name = review.reviewer.strip().capitalize()
            reviewer_reviews[normalized_reviewer_name] = {
                "rating": review.rating,
                "review": review.rating_justification
            }

        response_data.append({
            "title": movie.title,
            "director": movie.director,
            "actors": movie.actors,
            "genres": movie.genres,
            "reviews": reviewer_reviews,
            "movie_id": movie.id
        })

    return Response({"results": response_data})


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


@api_view(["GET"])
def club_average_ratings(_request):
    movie_query_set = (
        Review.objects.values(
            "movie__id",
            "movie__title",
            "movie__director",
            "movie__actors",
            "movie__genres"
        )
        .annotate(
            avg_rating=Avg("rating"),
            num_reviews=Count("id")
        )
    )

    results = []
    for movie in movie_query_set:
        results.append({
            "movie_id": movie["movie__id"],
            "title": movie["movie__title"],
            "director": movie.get("movie__director"),
            "actors": movie.get("movie__actors"),
            "genres": movie.get("movie__genres"),
            "avg_rating": round(movie["avg_rating"], 2) if movie["avg_rating"] is not None else None,
            "num_reviews": movie["num_reviews"]
        })

    return Response({"results": results})

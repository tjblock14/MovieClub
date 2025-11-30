from django.shortcuts import render
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework import viewsets, status

from .serializers import TvShowSerializer, SeasonSerializer, EpisodeSerializer
from .models import TvShow, Season, Episode

import requests

from django.utils.text import slugify



class TvShowViewSet(viewsets.ModelViewSet):
    queryset = TvShow.objects.all().prefetch_related("seasons__episodes")
    serializer_class = TvShowSerializer
    lookup_field = "slug"

    # POST /api/shows/import_from_tvmaze/
    @action(detail=False, methods=["post"], url_path="import_from_tvmaze")
    def import_from_tvmaze(self, request):
        tvmaze_id = request.data.get("tvmaze_id")
        if not tvmaze_id:
            return Response({"detail": "tvmaze_id required"}, status=400)

        # Check if already exists
        existing = TvShow.objects.filter(TvMazeAPIid=tvmaze_id).first()
        if existing:
            return Response(self.get_serializer(existing).data, status=200)

        # 1️⃣ Fetch show details
        try:
            r = requests.get(f"https://api.tvmaze.com/shows/{tvmaze_id}", timeout=10)
            r.raise_for_status()
        except Exception:
            return Response({"detail": "TVMaze /shows/{id} failed"}, status=502)
        show_data = r.json()

        title = show_data.get("name") or f"Show {tvmaze_id}"
        show = TvShow.objects.create(
            TvMazeAPIid=tvmaze_id,
            title=title,
            slug=slugify(f"{title}-{tvmaze_id}"),
            summary=show_data.get("summary") or "",
            genres=show_data.get("genres") or [],
            image_url=(show_data.get("image") or {}).get("original")
                      or (show_data.get("image") or {}).get("medium") or "",
            premiered=show_data.get("premiered"),
        )

        # 2️⃣ Fetch seasons
        try:
            s = requests.get(f"https://api.tvmaze.com/shows/{tvmaze_id}/seasons", timeout=10)
            s.raise_for_status()
        except Exception:
            return Response({"detail": "TVMaze /shows/{id}/seasons failed"}, status=502)
        seasons_json = s.json()

        season_map = {}
        for sn in seasons_json:
            season = Season.objects.create(
                show=show,
                season_number=sn.get("number") or 0,
                TvMazeAPI_season_id=sn.get("id"),
                summary=sn.get("summary") or "",
                season_release_year=(sn.get("premiereDate") or "")[:4] or None,
                season_episode_cnt=sn.get("episodeOrder") or 0,
            )
            season_map[sn.get("id")] = season

        # 3️⃣ Fetch episodes for each season
        for tvmaze_season_id, season in season_map.items():
            try:
                e = requests.get(f"https://api.tvmaze.com/seasons/{tvmaze_season_id}/episodes", timeout=10)
                e.raise_for_status()
            except Exception:
                continue
            eps = e.json()
            Episode.objects.bulk_create([
                Episode(
                    season_number=season,  # your current FK name
                    episode_number=ep.get("number") or 0,
                    TvMazeAPI_episode_id=ep.get("id"),
                    episode_title=ep.get("name") or "",
                    air_date=ep.get("airdate"),
                    episode_runtime=ep.get("runtime"),
                    summary=ep.get("summary") or "",
                )
                for ep in eps
                if ep.get("id") and not Episode.objects.filter(TvMazeAPI_episode_id=ep["id"]).exists()
            ])

        return Response(self.get_serializer(show).data, status=201)


class SeasonViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Season.objects.select_related("show")
    serializer_class = SeasonSerializer

class EpisodeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Episode.objects.select_related("season_number", "season_number__show")
    serializer_class = EpisodeSerializer


from rest_framework import viewsets, permissions
from .models import TvShowRatingsAndReviews
from .serializers import TvShowReviewSerializer

# Create a viewset that inherits the Model View set
class TvShowReviewsViewSet(viewsets.ModelViewSet):
    serializer_class = TvShowReviewSerializer # Serializer to use for input/output validation
    permission_classes = [permissions.IsAuthenticatedOrReadOnly] # controls access, only logged in users can edit

    # What reviews to return when someone performs a GET request
    def get_queryset(self):
        qs = TvShowRatingsAndReviews.objects.select_related( # select_related tells Django to prefetch related objects in the same database query
            'tv_show_type', 'tv_season_type', 'tv_episode_type', 'reviewer'
        )

        # Pull query parameters from the request URL
        target_type = self.request.query_params.get('target_type')
        show_id = self.request.query_params.get('show_id')
        season_id = self.request.query_params.get('season_id')
        episode_id = self.request.query_params.get('episode_id')
        couple_slug = self.request.query_params.get('couple_slug')

        # Add a .filter to the query if the user provided that parameter
        if target_type:
            qs = qs.filter(target_type = target_type)
        if show_id:
            qs = qs.filter(tv_show_type_id = show_id) # Only include reviews whose tv_show_type foreign key has this ID
        if season_id:
            qs = qs.filter(tv_season_type_id = season_id)
        if episode_id:
            qs = qs.filter(tv_episode_type_id = episode_id)
        if couple_slug:
            qs = qs.filter(couple_slug = couple_slug)

        return qs # Return the filtered queryset, returning relevant reviews
    
    # Called when a POST request happens (A new review)
    def perform_create(self, serializer):
        # Gaurantee that reviewer is set is serializer.create
        serializer.save(reviewer = self.request.user) # .save() triggers create() logic, inserting the record


#=======================================================
# Function based views (custom logic for the different couples pages)
#=======================================================
from rest_framework.decorators import api_view
from rest_framework.response import Response

# Use the same slug to ID map for couples
from moviereviews_hub.views import COUPLE_SLUG_TO_ID_MAP

from .models import TvShow, Season, Episode, TvShowRatingsAndReviews

# Helper function to get the "normalized" name of the reviewer
def get_normalized_reviewer_name(user):
    """
    Return a reviewer name like 'Trevor', 'Taylor' from the User object.
    Uses username; change to first_name if you prefer.
    """
    name = (user.username or "").strip()
    return name.capitalize()

# =================================================
# This function returns a list of all tv shows from the database and the reviews left by the specified couple
# PARAMETERS
#   - HTTP request object (must be 'GET' for this function)
#   - couple_slug is the slug from the URL path (tt, mn, sb)
# 
# RETURNS
#   - a list of python dictionaries with each one containing Tv show/season/episode information and the reviews from that specific couple
#       - dictionary stores like this key : value
# =================================================
@api_view(['GET'])
def tvShow_reviews_by_couple(request, couple_slug):
    # First, convert the slug to the couple ID used in the database
    slug = couple_slug.lower()

    if slug not in COUPLE_SLUG_TO_ID_MAP:
        return Response({"error":"Invalid couple slug"}, status = 400)
    
    # Get all of the Tv Shows in the database
    all_TvShows = TvShow.objects.all()

    # Initialize a list that will be separated per show with the couple's reviews included
    response_data = []

    # For every show in the datatbase, grab reviews by both members of the couple
    for show in all_TvShows:
        # Filter through the review table in database, returns reviews that belong to current tv show and are written by current couple
        reviews = TvShowRatingsAndReviews.objects.filter(
                                    target_type = TvShowRatingsAndReviews.TARGET_SHOW,
                                    tv_show_type = show,
                                    couple_slug = slug
        ).select_related("reviewer")

         # Create an empty dictionary that will contain the reviews from each person as a key-value pair
        reviewer_reviews = {}

        for review in reviews:
            reviewer_name = get_normalized_reviewer_name(review.reviewer)

            reviewer_reviews[reviewer_name] = {
                "rating" : review.rating,
                "review" : review.review_justification
            }

        response_data.append(
            {
                "id" : show.id,
                "title" : show.title,
                "summary" : show.summary,
                "genres" : show.genres,
                "premiered" : show.premiered,
                "image_url" : show.image_url,
                "reviews" : reviewer_reviews
            }
        )

    return Response({"results" : response_data})


@api_view(['GET'])
def tvSeason_reviews_by_couple(request, couple_slug):
    slug = couple_slug.lower()

    if slug not in COUPLE_SLUG_TO_ID_MAP:
        return Response({"error":"Invalid couple slug"}, status = 400)
    
    # Get all seasons and also load the related TV show for all seasons in the database
    all_seasons = Season.objects.select_related('show').all()

    response_data = []

    for season in all_seasons:
        reviews = TvShowRatingsAndReviews.objects.filter(
                                target_type = TvShowRatingsAndReviews.TARGET_SEASON,
                                tv_season_type = season,
                                couple_slug = slug
        ).select_related("reviewer")

        reviewer_reviews = {}

        for review in reviews:
            reviewer_name = get_normalized_reviewer_name(review.reviewer)

            reviewer_reviews[reviewer_name] = {
                "rating" : review.rating,
                "review" : review.review_justification
            }

            show = season.show

        response_data.append(
            {
                "show_title" : show.title,
                "season_number" : season.season_number,
                "season_summary" : season.summary,
                "release_year" : season.season_release_year,
                "episode_cnt" : season.season_episode_cnt,
                "season_id" : season.id,
                "show_id" : show.id,
                "reviews" : reviewer_reviews
            }
        )

    return Response({"results" : response_data})
        

@api_view(['GET'])
def tvEpisode_reviews_by_couple(request, couple_slug):
    slug = couple_slug.lower()

    if slug not in COUPLE_SLUG_TO_ID_MAP:
        return Response({"error":"Invalid couple slug"}, status = 400)
    
    all_episodes = Episode.objects.select_related('season_number', 'season_number__show').all()

    response_data = []

    for episode in all_episodes:
        reviews = TvShowRatingsAndReviews.objects.filter(
                        target_type = TvShowRatingsAndReviews.TARGET_EPISODE,
                        tv_episode_type = episode,
                        couple_slug = slug
        ).select_related("reviewer")

        reviewer_reviews = {}

        for review in reviews:
            reviewer_name = get_normalized_reviewer_name(review.reviewer)

            reviewer_reviews[reviewer_name] = {
                "rating" : review.rating,
                "review" : review.review_justification
            }

            season = episode.season_number
            show = season.show

        response_data.append(
            {
                "show_title" : show.title,
                "season_number" : season.season_number,
                "episode_number" : episode.episode_number,
                "episode_title" : episode.episode_title,
                "air_date" : episode.air_date,
                "runtime" : episode.episode_runtime,
                "summary" : episode.summary,
                "show_id" : show.id,
                "season_id" : season.id,
                "episode_id" : episode.id,
                "reviews" : reviewer_reviews
            }
        )

    return Response({"results" : response_data})
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MovieViewSet, ReviewViewSet, couple_specific_reviews  # couple specific reviews needed for function based view
from .views import club_average_ratings # Average club rating for all movies

router = DefaultRouter()
router.register(r'movies', MovieViewSet, basename = 'movie')
router.register(r'reviews', ReviewViewSet)

urlpatterns = [
    path('', include(router.urls)),

    # This path will return all movies in the database along with all the reviews by a specific couple based on the slug (tt, mn, sb)
    path('couple_reviews/<slug:couple_slug>/', couple_specific_reviews),

    # This path returns every movie with its club average rating
    path('club_average/', club_average_ratings, name = 'club_average')
]

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MovieViewSet, ReviewViewSet, couple_specific_reviews

router = DefaultRouter()
router.register(r'movies', MovieViewSet, basename='movie')
router.register(r'reviews', ReviewViewSet)

# Add per-couple routes that support PATCH by ID
router.register(r'couple_reviews/tt', ReviewViewSet, basename='tt_reviews')
router.register(r'couple_reviews/mn', ReviewViewSet, basename='mn_reviews')
router.register(r'couple_reviews/sb', ReviewViewSet, basename='sb_reviews')

urlpatterns = [
    path('', include(router.urls)),

    # Move your function-based view to its own route
    path('combined_reviews/<slug:couple_slug>/', couple_specific_reviews),
]

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TvShowViewSet, SeasonViewSet, EpisodeViewSet

router = DefaultRouter()
router.register("shows", TvShowViewSet, basename = "tv-show")
router.register("seasons", SeasonViewSet, basename = "tv-season")
router.register("episodes", EpisodeViewSet, basename = "tv-episode")

urlpatterns = [
    path("", include(router.urls)),
]
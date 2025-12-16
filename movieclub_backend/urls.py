"""
URL configuration for movieclub_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# movieclub_backend/urls.py
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from moviereviews_hub.views import MovieViewSet, ReviewViewSet, couple_specific_reviews, CustomTokenObtainPairView, club_average_ratings
from tvshows_app.views import TvShowViewSet, SeasonViewSet, EpisodeViewSet, TvShowReviewsViewSet
from tvshows_app.views import tvShow_reviews_by_couple #, tvSeason_reviews_by_couple, tvEpisode_reviews_by_couple

router = DefaultRouter()
router.register(r'movies', MovieViewSet, basename='movie')
router.register(r'reviews', ReviewViewSet, basename='review')
router.register(r'shows', TvShowViewSet, basename='tv-show')
router.register(r'seasons', SeasonViewSet, basename='tv-season')
router.register(r'episodes', EpisodeViewSet, basename='tv-episode')
router.register(r'tv-reviews', TvShowReviewsViewSet, basename='tv-reviews')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/couple_reviews/<slug:couple_slug>/', couple_specific_reviews),
    path('api-auth/', include('rest_framework.urls')),
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # TV Review endpoints
    path('api/tv/couple/shows/<slug:couple_slug>/', tvShow_reviews_by_couple, name='tv_shows_by_couple'),
    # path('api/tv/couple/seasons/<slug:couple_slug>/', tvSeason_reviews_by_couple, name='tv_seasons_by_couple'),
    # path('api/tv/couple/episodes/<slug:couple_slug>/', tvEpisode_reviews_by_couple, name='tv_episodes_by_couple'),

    # This path returns every movie with its club average rating
    path('api/club_average/', club_average_ratings, name = 'club_average'),
]

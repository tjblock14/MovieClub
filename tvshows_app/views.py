from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import viewsets

from .serializers import TvShowSerializer, SeasonSerializer, EpisodeSerializer
from .models import TvShow, Season, Episode


class TvShowViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TvShow.objects.all().prefetch_related("seasons__episodes")
    serializer_class = TvShowSerializer
    lookup_field = "slug"

class SeasonViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Season.objects.select_related("show")
    serializer_class = SeasonSerializer

class EpisodeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Episode.objects.select_related("season_number", "season_number__show")
    serializer_class = EpisodeSerializer
from rest_framework import serializers
from .models import TvShow, Season, Episode

class EpisodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Episode
        fields = [
            "id",
            "season_number",
            "episode_number",
            "TvMazeAPI_episode_id",
            "episode_title",
            "air_date",
            "episode_runtime",
            "summary"
        ]

class SeasonSerializer(serializers.ModelSerializer):
    episodes = EpisodeSerializer(many = True, read_only = True)

    class Meta:
        model = Season
        fields = [
            "id",
            "show",
            "season_number",
            "TvMazeAPI_season_id",
            "summary",
            "season_release_year",
            "season_episode_cnt",
            "episodes"
        ]

class TvShowSerializer(serializers.ModelSerializer):
    seasons = SeasonSerializer(many = True, read_only = True)

    class Meta:
        model = TvShow

        fields = [
            "id",
            "TvMazeAPIid",
            "title",
            "slug",
            "summary",
            "genres",
            "image_url",
            "premiered",
            "seasons"
        ]
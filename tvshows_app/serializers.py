from rest_framework import serializers
from .models import TvShow, Season, Episode, TvShowRatingsAndReviews

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


# Tv show reviews serializer
class TvShowReviewSerializer(serializers.ModelSerializer):
    # Virtual field for incoming requests
    target_id = serializers.IntegerField(write_only = True, required = False)

    class Meta:
        model = TvShowRatingsAndReviews

        # Fields included in the API input/output
        fields = [
            'id',
            'target_type',
            'tv_show_type',
            'tv_season_type',
            'tv_episode_type',
            'target_id',
            'rating',
            'review_justification',
            'reviewer',
            'couple_slug',
        ]

        # Clients cannot set the reviewer field
        read_only_fields = ['reviewer']

    def validate(self, attrs):
        target_type = attrs.get('target_type')   # Get what the client sent
        target_id = attrs.pop('target_id', None) # Remove target_id from attrs so the ModelSerializer does not get confused later

        # Map the target_id to the correct foreign key
        if target_id is not None:
            if target_type == TvShowRatingsAndReviews.TARGET_SHOW:
                attrs['tv_show_type'] = TvShow.objects.get(pk = target_id)
            elif target_type == TvShowRatingsAndReviews.TARGET_SEASON:
                attrs['tv_season_type'] = Season.objects.get(pk = target_id)
            elif target_type == TvShowRatingsAndReviews.TARGET_EPISODE:
                attrs['tv_episode_type'] = Episode.objects.get(pk = target_id)

        # Shortcut variable so that we do not have to keep calling attrs.get() later
        tv_show = attrs.get('tv_show_type')
        season = attrs.get('tv_season_type')
        episode = attrs.get('tv_episode_type')

        # Count how many of the three possible target types are not null.
        # There should be one and only one.
        targets = [tv_show, season, episode]
        if sum(1 for t in targets if t is not None) != 1:
            raise serializers.ValidationError("One and only one of tv_show, season, or episode must be set")
        
        # Make sure that the correct combination is made, make sure show goes to tv_show_type, season to tv_season_type, and same for episode
        # Basically, ensure weird issues do not occur
        if target_type == TvShowRatingsAndReviews.TARGET_SHOW and not tv_show:
            raise serializers.ValidationError("target_type 'show; requires tv_show_type")
        if target_type == TvShowRatingsAndReviews.TARGET_SEASON and not season:
            raise serializers.ValidationError("target_type 'season' requires tv_season_type")
        if target_type == TvShowRatingsAndReviews.TARGET_EPISODE and not episode:
            raise serializers.ValidationError("target_type 'episode' requires tv_episode_type")
        return attrs
    
    def create(self, validated_data):
        request = self.context.get('request')

        # Check if the user is logged in
        if request and request.user and request.user.is_authenticated:
            validated_data['reviewer'] = request.user
        return super().create(validated_data)
    
    # Called when someones sends a put or patch request
    def update(self, instance, validated_data):
        # Go through each field name and remove it from validated_data if it is not present
        for field in ('tv_show_type', 'tv_season_type', 'tv_episode_type', 'target_type'):
            validated_data.pop(field, None) # Delete this key if it exists
        return super().update(instance, validated_data) # only update fields that remain in validated_data
    


from rest_framework import serializers
from .models import Movie, Review  # Import my models
import json

# =============================================
# Serializers are used to convert python objects/model instances to JSON so they can be sent as API responses to the Squarespace/wordpress site
# They also do the opposite in converting incoming JSON to python objects/model instances
# ===============================================

import json
from rest_framework import serializers

def _clean_array_field(value, field_name):
    # Case 1: Already valid list
    if isinstance(value, list):
        # Fix case where it's a list with one stringified list inside
        if len(value) == 1 and isinstance(value[0], str):
            try:
                parsed = json.loads(value[0])
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
        return value

    # Case 2: JSON stringified list
    elif isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass

    raise serializers.ValidationError(f"Invalid format for '{field_name}' — expected a list of strings.")


# Serializer for the Movie model
class MovieSerializer(serializers.ModelSerializer):

    # Expect a list of items, and each item will be a string
    director = serializers.ListField(child=serializers.CharField())
    actors = serializers.ListField(child=serializers.CharField())
    genres = serializers.ListField(child=serializers.CharField())


    def validate_director(self, value):
        return _clean_array_field(value, 'director')

    def validate_genres(self, value):
        return _clean_array_field(value, 'genres')

    def validate(self, data):
        print("SERIALIZER DEBUG - validated incoming data:")
        for key, value in data.items():
            print(f"  {key}: {value} (type: {type(value)})")

        # --------------------------------------------------
        # This part checks for a duplicate entry by checking 
        # both the title and director fields
        #---------------------------------------------------
        title_in = (data.get('title') or '').strip().lower() # Grab the title from payload, remove trailing spaces, make lowercase
        directors_in = sorted([(d or '').strip().lower() for d in (data.get('director') or [])]) # Grab director list, strip and lowercase each one

        # Only run if both present, kind of redundant since all fields are required for a new movie submission
        if title_in and directors_in:
            query_set = Movie.objects.filter(title__iexact=title_in) # Create a set of all movies with the same title

            # Be sure to exclude itself from the set so it does not read itself and think its a duplicate
            # This prevents any unforseen issues with an update (POST or PATCH)
            if self.instance and getattr(self.instance, 'pk', None):
                query_set = query_set.exclude(pk=self.instance.pk)

            # Iterate through all movies with the same title, grab ony the columns we need for this
            for m in query_set.only('id', 'title', 'director'):
                existing_directors = sorted([(d or '').strip().lower() for d in (m.director or [])]) # Perform same operations on directors as comparison directors
                
                # If the submitted movie's director equals the stored directors with the same title, it is a duplicate
                if existing_directors == directors_in:
                    # Key is 'duplicate' so the frontend can show a friendly message
                    raise serializers.ValidationError({"duplicate": "Movie already exists."})



        return super().validate(data)

    class Meta:
        model = Movie       # Map to this model
        fields = '__all__'  # Include all fields from the model
        extra_kwargs = { # Make all required fields for form submissions
            'title': {'required': True},
            'director': {'required': True},
            'actors': {'required': True},
            'genres': {'required': True},
        }

# Serializer for the Review model
class ReviewSerializer(serializers.ModelSerializer):

    # Allow these to be blank for when a user on the site submits new review/rating for new movie
    rating = serializers.FloatField(required=False, allow_null=True)
    rating_justification = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Review
        fields = '__all__'
        read_only_fields = ['user', 'reviewer', 'couple_id']

# your_app/serializers.py

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # ? Add custom claims
        token['username'] = user.username

        return token

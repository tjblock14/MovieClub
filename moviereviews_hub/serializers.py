from rest_framework import serializers
from .models import Movie, Review  # Import my models

# =============================================
# Serializers are used to convert python objects/model instances to JSON so they can be sent as API responses to the Squarespace/wordpress site
# They also do the opposite in converting incoming JSON to python objects/model instances
# ===============================================


# Serializer for the Movie model
class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie       # Map to this model
        fields = '__all__'  # Include all fields from the model

    title = serializers.CharField(required=True)
    director = serializers.CharField(required=True)
    actors = serializers.ListField(child=serializers.CharField(), required=True)
    genres = serializers.ListField(child=serializers.CharField(), required=True)

# Serializer for the Review model
class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = '__all__'
        read_only_fields = ['user', 'reviewer', 'couple_id']
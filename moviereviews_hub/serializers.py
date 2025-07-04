from rest_framework import serializers
from .models import Movie, Review  # Import my models

# =============================================
# Serializers are used to convert python objects/model instances to JSON so they can be sent as API responses to the Squarespace/wordpress site
# They also do the opposite in converting incoming JSON to python objects/model instances
# ===============================================


# Serializer for the Movie model
class MovieSerializer(serializers.ModelSerializer):

    # Expect a list of items, and each item will be a string
    director = serializers.ListField(child=serializers.CharField())
    actors = serializers.ListField(child=serializers.CharField())
    genres = serializers.ListField(child=serializers.CharField())

    def validate(self, data):
        print("SERIALIZER DEBUG - validated incoming data:")
        for key, value in data.items():
            print(f"  {key}: {value} (type: {type(value)})")
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
    class Meta:
        model = Review
        fields = '__all__'
        read_only_fields = ['user', 'reviewer', 'couple_id']
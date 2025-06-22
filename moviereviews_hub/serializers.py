from rest_framework import serializers
from .models import Movie, Review  # Import my models

# =============================================
# Serializers are used to convert python objects/model instances to JSON so they can be sent as API responses to the Squarespace/wordpress site
# They also do the opposite in converting incoming JSON to python objects/model instances
# ===============================================

# Helper field that accepts either a list or a comma-separated string
class FlexibleListField(serializers.ListField):
    def to_internal_value(self, data):
        print("🚨 FlexibleListField triggered for:", data)  # <== Add this line

        if isinstance(data, str):
            try:
                # Try parsing as JSON array
                import json
                parsed = json.loads(data)
                if isinstance(parsed, list):
                    return parsed
            except:
                # If it’s just a comma-separated string
                return [s.strip() for s in data.split(',')]
        return super().to_internal_value(data)


# Serializer for the Movie model
class MovieSerializer(serializers.ModelSerializer):

    # Expect a list of items, and each item will be a string
    director = FlexibleListField(child=serializers.CharField())
    actors = FlexibleListField(child=serializers.CharField())
    genres = FlexibleListField(child=serializers.CharField())

    class Meta:
        model = Movie       # Map to this model
        fields = '__all__'  # Include all fields from the model
        extra_kwargs = {
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
from rest_framework import serializers
from .models import ImageSeries, ImageUpload, Annotation


class AnnotationSerializer(serializers.ModelSerializer):
    """Serializer for polygon annotations."""

    class Meta:
        model = Annotation
        fields = ['id', 'image', 'label', 'polygon_points', 'color', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_polygon_points(self, value):
        """Ensure polygon_points is a list of {x, y} objects."""
        if not isinstance(value, list) or len(value) < 3:
            raise serializers.ValidationError("Polygon must have at least 3 points.")
        for point in value:
            if not isinstance(point, dict) or 'x' not in point or 'y' not in point:
                raise serializers.ValidationError("Each point must have 'x' and 'y' keys.")
        return value


class ImageUploadSerializer(serializers.ModelSerializer):
    """Serializer for uploaded images with nested annotations."""
    annotations = AnnotationSerializer(many=True, read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ImageUpload
        fields = ['id', 'series', 'image', 'image_url', 'filename', 'order', 'uploaded_at', 'annotations']
        read_only_fields = ['id', 'uploaded_at', 'filename']

    def get_image_url(self, obj):
        if not obj.image:
            return None
        url = obj.image.url
        # Cloudinary returns an absolute https URL; local storage returns a
        # relative path that we make absolute using the request.
        if url.startswith(('http://', 'https://')):
            return url
        request = self.context.get('request')
        return request.build_absolute_uri(url) if request else url


class ImageSeriesSerializer(serializers.ModelSerializer):
    """Serializer for image series with image count."""
    image_count = serializers.SerializerMethodField()

    class Meta:
        model = ImageSeries
        fields = ['id', 'name', 'description', 'image_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_image_count(self, obj):
        return obj.images.count()


class ImageSeriesDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for series including all images."""
    images = ImageUploadSerializer(many=True, read_only=True)

    class Meta:
        model = ImageSeries
        fields = ['id', 'name', 'description', 'images', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

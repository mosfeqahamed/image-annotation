from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from .models import ImageSeries, ImageUpload, Annotation
from .serializers import (
    ImageSeriesSerializer,
    ImageSeriesDetailSerializer,
    ImageUploadSerializer,
    AnnotationSerializer,
)


class ImageSeriesViewSet(viewsets.ModelViewSet):
    """ViewSet for managing image series."""
    serializer_class = ImageSeriesSerializer

    def get_queryset(self):
        return ImageSeries.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ImageSeriesDetailSerializer
        return ImageSeriesSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'], url_path='upload',
            parser_classes=[MultiPartParser, FormParser])
    def upload_images(self, request, pk=None):
        """Upload one or more images to a series."""
        series = self.get_object()
        files = request.FILES.getlist('images')

        if not files:
            return Response(
                {'error': 'No images provided.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        uploaded = []
        current_max_order = series.images.count()

        for i, file in enumerate(files):
            image = ImageUpload.objects.create(
                series=series,
                image=file,
                filename=file.name,
                order=current_max_order + i,
            )
            uploaded.append(image)

        serializer = ImageUploadSerializer(
            uploaded, many=True, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ImageUploadViewSet(viewsets.ModelViewSet):
    """ViewSet for managing individual images."""
    serializer_class = ImageUploadSerializer

    def get_queryset(self):
        return ImageUpload.objects.filter(series__user=self.request.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        return context


class AnnotationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing annotations on images."""
    serializer_class = AnnotationSerializer

    def get_queryset(self):
        queryset = Annotation.objects.filter(image__series__user=self.request.user)
        image_id = self.request.query_params.get('image')
        if image_id:
            queryset = queryset.filter(image_id=image_id)
        return queryset

    @action(detail=False, methods=['post'], url_path='bulk-save')
    def bulk_save(self, request):
        """Save multiple annotations at once for an image."""
        image_id = request.data.get('image_id')
        annotations_data = request.data.get('annotations', [])

        if not image_id:
            return Response(
                {'error': 'image_id is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            image = ImageUpload.objects.get(
                id=image_id, series__user=request.user
            )
        except ImageUpload.DoesNotExist:
            return Response(
                {'error': 'Image not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Validate all incoming annotations *before* touching the database so a
        # single invalid entry can't wipe out the existing annotations.
        serializers = []
        for ann_data in annotations_data:
            serializer = AnnotationSerializer(data={
                'image': image.id,
                'label': ann_data.get('label', 'Unlabeled'),
                'polygon_points': ann_data.get('polygon_points', []),
                'color': ann_data.get('color', '#FF0000'),
            })
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            serializers.append(serializer)

        # Atomically replace the image's annotations.
        with transaction.atomic():
            Annotation.objects.filter(image=image).delete()
            created = []
            for serializer in serializers:
                serializer.save()
                created.append(serializer.data)

        return Response(created, status=status.HTTP_201_CREATED)

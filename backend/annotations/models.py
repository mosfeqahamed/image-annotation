from django.db import models
from django.contrib.auth.models import User


class ImageSeries(models.Model):
    """A named collection/series of images."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='series')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Image Series'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.images.count()} images)"


class ImageUpload(models.Model):
    """An uploaded image belonging to a series."""
    series = models.ForeignKey(ImageSeries, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='annotations/')
    filename = models.CharField(max_length=255)
    order = models.IntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'uploaded_at']

    def __str__(self):
        return f"{self.filename} (Series: {self.series.name})"


class Annotation(models.Model):
    """A polygon annotation drawn on an image."""
    image = models.ForeignKey(ImageUpload, on_delete=models.CASCADE, related_name='annotations')
    label = models.CharField(max_length=100, default='Unlabeled')
    polygon_points = models.JSONField()  # List of {x: float, y: float} points
    color = models.CharField(max_length=9, default='#FF0000')  # Hex color with optional alpha
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.label} on {self.image.filename}"

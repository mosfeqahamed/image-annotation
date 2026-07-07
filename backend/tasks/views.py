from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Task
from .serializers import TaskSerializer, TaskReorderSerializer


class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing tasks.
    Supports CRUD + filtering by date + reorder (drag-and-drop).
    """
    serializer_class = TaskSerializer

    def get_queryset(self):
        """Return tasks for the authenticated user, optionally filtered by date."""
        queryset = Task.objects.filter(user=self.request.user)
        date = self.request.query_params.get('date')
        if date:
            queryset = queryset.filter(due_date=date)
        return queryset

    def perform_create(self, serializer):
        """Assign the task to the authenticated user."""
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['patch'], url_path='reorder')
    def reorder(self, request, pk=None):
        """Update task status and order (used for drag-and-drop)."""
        task = self.get_object()
        serializer = TaskReorderSerializer(data=request.data)
        if serializer.is_valid():
            task.status = serializer.validated_data['status']
            task.order = serializer.validated_data['order']
            task.save()
            return Response(TaskSerializer(task).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='bulk-reorder')
    def bulk_reorder(self, request):
        """Bulk update task orders after drag-and-drop."""
        items = request.data.get('items', [])
        if not isinstance(items, list):
            return Response(
                {'error': 'items must be a list'},
                status=status.HTTP_400_BAD_REQUEST
            )

        for item in items:
            task_id = item.get('id')
            new_status = item.get('status')
            new_order = item.get('order')
            if task_id is not None:
                try:
                    task = Task.objects.get(id=task_id, user=request.user)
                    if new_status:
                        task.status = new_status
                    if new_order is not None:
                        task.order = new_order
                    task.save()
                except Task.DoesNotExist:
                    pass

        return Response({'message': 'Reorder successful'})

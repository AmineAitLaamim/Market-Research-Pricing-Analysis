from django.http import StreamingHttpResponse
from rest_framework import permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from apps.search.models import Search
from .utils import generate_csv_rows

class ExportCSVView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, id):
        search = get_object_or_404(Search, pk=id)

        # Verify ownership
        if search.user != request.user:
            raise PermissionDenied("You do not have permission to access this search.")

        # Check status
        if search.status != Search.Status.COMPLETED:
            return Response(
                {"error": "Search not completed yet"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Generate streaming response
        response = StreamingHttpResponse(
            generate_csv_rows(search),
            content_type="text/csv"
        )
        response['Content-Disposition'] = f'attachment; filename="search_{search.id}_results.csv"'
        return response

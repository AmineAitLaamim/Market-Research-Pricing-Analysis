from django.urls import path
from .views import ExportCSVView

app_name = "export"

urlpatterns = [
    path('csv/<int:id>/', ExportCSVView.as_view(), name='export-csv'),
]

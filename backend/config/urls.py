from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({"status": "ok"})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('healthz/', health_check),
    path('api/auth/', include('apps.authentication.urls')),
    path('api/search/', include('apps.search.urls')),
    path('api/analytics/', include('apps.search.analytics_urls')),
    path('api/export/', include('apps.export.urls')),
]

import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from apps.search.models import Search, AnalysisResult
from apps.search.views import SearchPCAView
from rest_framework.test import APIRequestFactory
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.first()
s = Search.objects.order_by('-id').first()

factory = APIRequestFactory()
request = factory.get('/')
request.user = user

view = SearchPCAView.as_view()
response = view(request, pk=s.id)
print(f'SearchID: {s.id}')
print(f'Query: {s.query}')
print(f'Response Data: {response.data}')

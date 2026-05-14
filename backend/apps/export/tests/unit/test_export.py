import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from apps.search.models import Search, RawPrice, AnalysisResult

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def test_user(db, django_user_model):
    return django_user_model.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="password123"
    )

@pytest.fixture
def other_user(db, django_user_model):
    return django_user_model.objects.create_user(
        username="otheruser",
        email="other@example.com",
        password="password123"
    )

@pytest.fixture
def completed_search(db, test_user):
    search = Search.objects.create(
        user=test_user,
        query="test query",
        platforms=["jumia"],
        status=Search.Status.COMPLETED
    )
    
    rp = RawPrice.objects.create(
        search=search,
        platform="jumia",
        title="Test Product",
        price="10.00",
        currency="USD",
        exchange_rate=10.0,
        url="http://example.com",
        seller_rating=4.5,
        condition="new"
    )
    
    AnalysisResult.objects.create(
        raw_price=rp,
        cluster_kmeans=1,
        cluster_dbscan=0,
        is_anomaly=False,
        deal_score=85.5
    )
    
    return search

@pytest.fixture
def pending_search(db, test_user):
    return Search.objects.create(
        user=test_user,
        query="test pending",
        platforms=["jumia"],
        status=Search.Status.PENDING
    )

@pytest.mark.django_db
class TestExportCSVAPI:
    def test_export_completed_search(self, api_client, test_user, completed_search):
        api_client.force_authenticate(user=test_user)
        url = reverse("export:export-csv", kwargs={"id": completed_search.id})
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "text/csv"
        assert response["Content-Disposition"] == f'attachment; filename="search_{completed_search.id}_results.csv"'
        
        # Read streaming response content
        content = b"".join(response.streaming_content).decode('utf-8')
        lines = content.strip().split('\r\n')
        
        assert len(lines) == 2  # header + 1 data row
        
        header = lines[0]
        assert header == "title,platform,price,currency,price_in_mad,seller_rating,condition,cluster_kmeans,cluster_dbscan,is_anomaly,deal_score,url"
        
        data_row = lines[1]
        assert data_row == "Test Product,jumia,10.00,USD,100.0,4.5,new,1,0,False,85.5,http://example.com"

    def test_export_pending_search(self, api_client, test_user, pending_search):
        api_client.force_authenticate(user=test_user)
        url = reverse("export:export-csv", kwargs={"id": pending_search.id})
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {"error": "Search not completed yet"}

    def test_export_wrong_user(self, api_client, other_user, completed_search):
        api_client.force_authenticate(user=other_user)
        url = reverse("export:export-csv", kwargs={"id": completed_search.id})
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_export_unauthenticated(self, api_client, completed_search):
        url = reverse("export:export-csv", kwargs={"id": completed_search.id})
        response = api_client.get(url)
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]


import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from apps.search.models import Search, AnalysisResult, RawPrice

s = Search.objects.order_by('-id').first()
print(f'SearchID: {s.id}')
print(f'Query: {s.query}')

items = RawPrice.objects.filter(search=s)
print(f'RawPrice items count: {len(items)}')

ars = AnalysisResult.objects.filter(raw_price__search=s)
print(f'AnalysisResult count: {len(ars)}')

if ars.exists():
    ar = ars.first()
    print(f'Sample AR Fields: {ar.__dict__}')
    
    clusters = list(ars.values_list('cluster_dbscan', flat=True))
    print(f'Unique Cluster IDs: {set(clusters)}')
    print(f'Clusters (first 10): {clusters[:10]}')

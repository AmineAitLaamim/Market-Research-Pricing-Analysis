import csv
import io
from apps.search.models import RawPrice

def generate_csv_rows(search):
    # CSV header
    header = [
        "title",
        "platform",
        "price",
        "currency",
        "price_in_mad",
        "seller_rating",
        "condition",
        "cluster_kmeans",
        "cluster_dbscan",
        "is_anomaly",
        "deal_score",
        "url"
    ]
    
    # We use a StringIO buffer to properly escape CSV fields, then yield its string value
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    
    writer.writerow(header)
    yield buffer.getvalue()
    buffer.seek(0)
    buffer.truncate(0)
    
    # Fetch all raw prices for the search, including related analysis results
    raw_prices = RawPrice.objects.filter(search=search).prefetch_related('analysis_results')
    
    for rp in raw_prices:
        # Compute price in MAD
        price_in_mad = round(float(rp.price) * rp.exchange_rate, 2)
        
        # Get analysis results if they exist
        an = rp.analysis_results.first()
        cluster_kmeans = ""
        cluster_dbscan = ""
        is_anomaly = ""
        deal_score = ""
        if an:
            cluster_kmeans = an.cluster_kmeans if an.cluster_kmeans is not None else ""
            cluster_dbscan = an.cluster_dbscan if an.cluster_dbscan is not None else ""
            is_anomaly = an.is_anomaly
            deal_score = round(an.deal_score, 2) if an.deal_score is not None else ""
            
        row = [
            rp.title,
            rp.platform,
            rp.price,
            rp.currency,
            price_in_mad,
            rp.seller_rating if rp.seller_rating is not None else "",
            rp.condition if rp.condition is not None else "",
            cluster_kmeans,
            cluster_dbscan,
            is_anomaly,
            deal_score,
            rp.url
        ]
        writer.writerow(row)
        yield buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)

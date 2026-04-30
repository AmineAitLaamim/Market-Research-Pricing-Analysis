import pytest
import os
from backend.scraper.avito import extract_avito_results

def test_extract_avito_results_success():
    # Construct path to the sample HTML file
    sample_path = os.path.join(os.path.dirname(__file__), "../../samples/avito_sample.html")
    
    with open(sample_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    results = extract_avito_results(html_content)

    # In our sample, script 0 is BreadcrumbList, script 1 has price 0, scripts 2-9 should have products
    # Wait, script 1 was Geely Ex5 Emi which had price 0.
    # Let's see how many actually had price > 0.
    
    assert len(results) > 0
    
    # Check first actual result
    item = results[0]
    assert "platform" in item
    assert item["platform"] == "avito"
    assert item["price"] > 0
    assert "currency" in item
    assert item["currency"] == "MAD"
    assert "url" in item
    assert "title" in item

def test_extract_avito_results_empty():
    html_content = "<html><body><div class='no-products'></div></body></html>"
    results = extract_avito_results(html_content)
    assert len(results) == 0

def test_extract_avito_results_invalid_json():
    html_content = """
    <html><body>
    <script type="application/ld+json">{ "invalid": json }</script>
    </body></html>
    """
    results = extract_avito_results(html_content)
    assert len(results) == 0

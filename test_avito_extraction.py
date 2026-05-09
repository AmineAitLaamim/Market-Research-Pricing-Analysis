"""Test the Avito extraction against saved HTML pages."""
import json
from parsel import Selector

# Read saved HTML files
print("=== Loading saved HTML pages ===")
with open(r"html\avito_html\Annonces pour iphone à Marrakech à vendre - Avito.html", encoding="utf-8") as f:
    iphone_html = f.read()
print(f"iPhone page: {len(iphone_html):,} bytes")

with open(r"html\avito_html\Voitures - Avito Maroc _ Avito Véhicules.html", encoding="utf-8") as f:
    cars_html = f.read()
print(f"Cars page:    {len(cars_html):,} bytes")

# Check __NEXT_DATA__ structure
print("\n=== __NEXT_DATA__ structure (iPhone page) ===")
iphone_sel = Selector(text=iphone_html)
next_data_str = iphone_sel.css("script#__NEXT_DATA__::text").get()
if next_data_str:
    parsed = json.loads(next_data_str)
    props = parsed.get("props", {}).get("pageProps", {})
    component_props = props.get("componentProps", {})
    ads = component_props.get("ads", {})
    print(f"componentProps.ads type: {type(ads).__name__}")
    if isinstance(ads, dict):
        print(f"  keys: {list(ads.keys())}")
        for k, v in ads.items():
            if isinstance(v, list):
                print(f"  '{k}': list of {len(v)} items")
                if v and isinstance(v[0], dict):
                    item0 = v[0]
                    print(f"    listId: {item0.get('listId', 'N/A')}")
                    print(f"    subject: {item0.get('subject', 'N/A')}")
            elif isinstance(v, dict):
                print(f"  '{k}': dict with keys {list(v.keys())[:5]}")

# Test the extraction
print("\n=== Testing extract_avito_results ===")
from backend.scraper.avito import extract_avito_results

# iPhone page
print("\n--- iPhone page ---")
res = extract_avito_results(iphone_html, query="iphone")
print(f"Total results: {len(res)}")
for r in res[:5]:
    extras = ""
    if r.get("seller_name"):
        extras += f" seller={r['seller_name']}"
    if r.get("category"):
        extras += f" cat={r['category']}"
    print(f"  {r['title']} - {r['price']} MAD{extras}")

# Cars page  
print("\n--- Cars page ---")
res2 = extract_avito_results(cars_html)
print(f"Total results: {len(res2)}")
for r in res2[:5]:
    print(f"  {r['title']} - {r['price']} MAD")

# Test the old JSON-LD fallback (remove __NEXT_DATA__ to verify)
print("\n=== Testing JSON-LD fallback ===")
import copy
iphone_no_next = iphone_html.replace('<script id="__NEXT_DATA__"', '<script id="__NEXT_DATA_OLD"')
res3 = extract_avito_results(iphone_no_next, query="iphone")
print(f"JSON-LD results: {len(res3)}")

# Test CSS only (remove both __NEXT_DATA__ and JSON-LD)
print("\n=== Testing CSS-only fallback ===")
import re
iphone_css_only = re.sub(
    r'<script[^>]*type="application/ld\+json"[^>]*>.*?</script>',
    "",
    iphone_no_next,
    flags=re.DOTALL,
)
res4 = extract_avito_results(iphone_css_only, query="iphone")
print(f"CSS-only results: {len(res4)}")
for r in res4[:3]:
    print(f"  {r['title']} - {r['price']} MAD")
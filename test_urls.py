from backend.scraper.avito import _build_search_url

print("Search URL for iphone:", _build_search_url("iphone"))
print("Search URL for iphone page 2:", _build_search_url("iphone", page=2))
print("Search URL for voiture:", _build_search_url("voiture"))
print("Search URL for iphone 13:", _build_search_url("iphone 13"))
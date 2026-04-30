from parsel import Selector
import os

file_path = 'html/avito_html/Annonces pour iphone à Marrakech à vendre - Avito.html'

if os.path.exists(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        sel = Selector(content)
        
        # Find elements that have the listing-like class we saw earlier
        # In the previous run, we saw sc-b57yxx-1
        cards = sel.css('div.sc-b57yxx-1')
        if cards:
            print(f"Found {len(cards)} cards. Inspecting first card HTML:")
            # Get the outer HTML of the first card's parent (the <a> tag)
            first_card = cards[1] # index 0 was IPTV, let's look at index 1 which was an iPhone
            parent_a = first_card.xpath('ancestor::a[1]')
            if parent_a:
                print(parent_a.get()[:2000]) # Print up to 2000 chars of the card HTML
            else:
                print("No parent <a> found for card")
                print(first_card.get()[:2000])
else:
    print("File not found")

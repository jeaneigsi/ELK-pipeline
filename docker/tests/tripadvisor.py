from scrapling.fetchers import StealthyFetcher  
  
def scrape_multiple_pages(start_page=0, num_clicks=4):  
    all_products = []  
    current_page = start_page  
      
    for i in range(num_clicks + 1):  # +1 pour inclure la page de départ  
        # url = f'https://www.jumia.ma/vetements-femme/?page={current_page}' 
        url=f'https://www.tripadvisor.fr/Restaurants-g293732-oa{current_page}-Casablanca_Casablanca_Settat.html' 
          
        page = StealthyFetcher.fetch(  
            url,  
            headless=True,  
            block_images=True,  
            disable_resources=True,  
            network_idle=True,  
            humanize=True,  
            geoip=True  
        )  
          
        # Extraire les produits de cette page  
        products = page.find_all('span')  
        print(f"Page {current_page}: {len(products)} produits trouvés")  
          
        for product in products:  
            name = product.css_first('a[href*="/Restaurant_Review"].BMQDV::text')  
            price = product.css_first('div[data-automation="bubbleRatingValue"]::text')  
            all_products.append({'nom': name, 'prix': price, 'page': current_page})  
          
        current_page += 30  
      
    return all_products  
  
# Utilisation  
StealthyFetcher.auto_match = True  
all_products = scrape_multiple_pages(start_page=2, num_clicks=4)  
  
for product in all_products:  
    print(f"Nom: {product['nom']}")  
    print(f"Prix: {product['prix']}")  
    print(f"Page: {product['page']}")  
    print("-----")
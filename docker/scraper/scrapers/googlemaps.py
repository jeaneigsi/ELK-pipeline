import logging
import re
import requests
import concurrent.futures
from scrapling.fetchers import StealthyFetcher

logger = logging.getLogger(__name__)
StealthyFetcher.auto_match = True  

def reverse_geocode(lat: str, lon: str) -> str | None:
    """
    Appelle Nominatim pour obtenir l'adresse complète (display_name)
    à partir des coordonnées.
    """
    url = (
        "https://nominatim.openstreetmap.org/reverse"
        f"?format=json&lat={lat}&lon={lon}&zoom=16&addressdetails=1"
    )
    headers = {
        "User-Agent": "YourApp/1.0 (your_email@example.com)"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get('display_name')
    except Exception as e:
        logger.warning(f"Reverse geocoding failed for {lat},{lon}: {e}")
        return None

def enrich_restaurant_info(restaurant):
    """
    Récupère des informations complémentaires pour un restaurant:
    - numéro de téléphone
    - site web
    - réseaux sociaux
    
    Prend un dictionnaire restaurant et retourne le même dictionnaire enrichi
    """
    if not restaurant.get('name'):
        return restaurant
        
    restaurant_name = restaurant['name']
    logger.info(f"Enrichissement des données pour: {restaurant_name}")
    query = restaurant_name.replace(" ", "+")
    url = f"https://www.google.com/search?q={query}"
    
    try:
        # Lancer la requête via StealthyFetcher
        page = StealthyFetcher.fetch(
            url,
            headless=True,
            network_idle=True,
        )
        
        # Numéro de téléphone
        phone_pattern = r'(0[567](?:[\s.-]?\d{2}){4})'
        phone_element = page.find_by_regex(phone_pattern, first_match=True)
        phone = phone_element.re_first(phone_pattern) if phone_element else None
        
        # Site officiel
        site_element = page.css_first('div.yuRUbf a:not([href*="instagram.com"]):not([href*="facebook.com"]):not([href*="tripadvisor.com"]):not([href*="google.com"])')
        site = site_element.attrib.get("href") if site_element else None
        
        # Réseaux sociaux
        social_domains = ("facebook.com", "instagram.com", "twitter.com", "linkedin.com", "youtube.com")
        socials = []
        for a in page.css("a[href]"):
            href = a.attrib.get("href")
            if href and any(domain in href for domain in social_domains):
                socials.append(href)
        socials = list(dict.fromkeys(socials))  # Supprimer les doublons
        
        # Ajouter les nouvelles informations au dictionnaire restaurant
        restaurant['telephone'] = phone
        restaurant['site_web'] = site
        restaurant['reseaux_sociaux'] = socials
        
        return restaurant
    except Exception as e:
        logger.warning(f"Enrichissement échoué pour {restaurant_name}: {e}")
        restaurant['telephone'] = None
        restaurant['site_web'] = None
        restaurant['reseaux_sociaux'] = []
        return restaurant

def scrape_google_maps(url: str) -> list[dict]:
    """  
    Scraper pour Google Maps (recherche restaurants) qui extrait 
    les informations de base des restaurants.
    """  
  
    def scroll_until_no_new_results(page, max_scrolls=20):    
        previous_count = 0    
        for _ in range(max_scrolls):    
            # Use Playwright's query_selector_all instead of css()  
            cards = page.query_selector_all('div[role="article"]')    
            if len(cards) <= previous_count:    
                break    
            previous_count = len(cards)    
            page.mouse.wheel(0, 1000)    
            page.wait_for_timeout(800)    
        return page   
  
    # 1) Chargement de la page avec scroll  
    page = StealthyFetcher.fetch(  
        url,  
        headless=True,  
        disable_resources=True,  
        network_idle=True,  
        page_action=scroll_until_no_new_results,  
        timeout=90000  
    )  
    logger.info(f"Lancement du scraping : {url}")  
  
    # 2) Sélection des cartes de restaurants  
    cards = page.css('div.Nv2PK.THOPZb.CpccDe')  
    if len(cards) < 5:  
        logger.warning(f"⚠️ Seulement {len(cards)} cartes trouvées.")  
    logger.info(f"Nombre total de cartes après scroll : {len(cards)}")  
  
    restaurants = []  
    for card in cards:  
        # Nom - Fixed: TextHandler doesn't need .strip()  
        name_el = card.css_first('div.qBF1Pd::text')  
        name = str(name_el).strip() if name_el else None  
  
        # URL de la fiche - Fixed: This returns string directly  
        href = card.css_first('a.hfpxzc::attr(href)')  
        full_url = f"https://www.google.com{href}" if href else None  
  
        # Note et avis - Fixed: TextHandler handling  
        rating_el = card.css_first('span.MW4etd::text')  
        rating = str(rating_el).strip() if rating_el else None  
        review_el = card.css_first('span.UY7F9::text')  
        review_count = str(review_el).strip().strip('()') if review_el else None  
  
        # Fourchette de prix - This part is correct  
        price_range = None  
        for span in card.css('span'):  
            txt = span.text.strip()  
            if txt.startswith('MAD'):  
                price_range = txt  
                break  
  
        # Type de cuisine - Fixed: TextHandler handling  
        cuisine_el = card.css_first('div.W4Efsd > div.W4Efsd span span::text')  
        cuisine = str(cuisine_el).strip() if cuisine_el else None  
  
        # Rest of the code remains the same...  
        lat, lng = None, None  
        if full_url:  
            m = re.search(r'!3d([-\d\.]+)!4d([-\d\.]+)', full_url)  
            if m:  
                lat, lng = m.group(1), m.group(2)  
  
        address = None  
        if lat and lng:  
            address = reverse_geocode(lat, lng)  
        
        # Créer l'objet restaurant de base
        restaurant = {  
            'name': name,  
            'url': full_url,  
            'rating': rating,  
            'review_count': review_count,  
            'cuisine': cuisine,  
            'price_range': price_range,  
            'address': address,  
            'latitude': lat,  
            'longitude': lng,  
            'source': 'googlemaps'  
        }
        
        restaurants.append(restaurant)  
  
    logger.info(f"Total de restaurants extraits : {len(restaurants)}")  
    return restaurants

def enrich_restaurants_parallel(restaurants, max_workers=5):
    """
    Enrichit une liste de restaurants en parallèle en utilisant des threads
    """
    enriched_restaurants = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Soumettre tous les restaurants pour enrichissement
        future_to_restaurant = {executor.submit(enrich_restaurant_info, restaurant): restaurant for restaurant in restaurants}
        
        # Collecter les résultats au fur et à mesure qu'ils sont terminés
        for future in concurrent.futures.as_completed(future_to_restaurant):
            restaurant = future_to_restaurant[future]
            try:
                enriched_restaurant = future.result()
                enriched_restaurants.append(enriched_restaurant)
            except Exception as e:
                logger.error(f"Erreur lors de l'enrichissement pour {restaurant.get('name', 'inconnu')}: {e}")
                # Ajouter quand même le restaurant non enrichi
                enriched_restaurants.append(restaurant)
    
    return enriched_restaurants

def scrape(url: str, use_parallel=True, max_workers=5) -> list[dict]:
    """
    Fonction principale qui combine le scraping de Google Maps et l'enrichissement des données
    """
    # Première étape : récupérer les informations de base des restaurants
    restaurants = scrape_google_maps(url)
    
    # Deuxième étape : enrichir les données des restaurants
    if use_parallel:
        logger.info(f"Enrichissement des données en parallèle pour {len(restaurants)} restaurants...")
        return enrich_restaurants_parallel(restaurants, max_workers)
    else:
        logger.info(f"Enrichissement des données séquentiel pour {len(restaurants)} restaurants...")
        enriched_restaurants = []
        for restaurant in restaurants:
            enriched_restaurant = enrich_restaurant_info(restaurant)
            enriched_restaurants.append(enriched_restaurant)
        return enriched_restaurants
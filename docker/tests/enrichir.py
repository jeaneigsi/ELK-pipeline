from scrapling.fetchers import StealthyFetcher  
from scrapling import Adaptor  # Correct import  
  
def scrape_with_scrapling(restaurant_name, save_path="marea_search.html"):  
    # 1) Construire l'URL Google Search  
    query = restaurant_name.replace(" ", "+")  
    url = f"https://www.google.com/search?q={query}"  
  
    # 2) Lancer la requête via StealthyFetcher  
    page = StealthyFetcher.fetch(  
        url,  
        headless=True,  
        network_idle=True,  

    )  
    html = page.html_content  # Correct property access  
  
    # 3) Sauvegarder le HTML rendu  
    # with open(save_path, "w", encoding="utf-8") as f:  
    #     f.write(html)  
  
    # 4) Use the page directly (it's already an Adaptor)  
    # No need to create a separate parser  
  
    # 5) Numéro de téléphone  
    phone_pattern = r'(0[567](?:[\s.-]?\d{2}){4})'  
    phone_element = page.find_by_regex(phone_pattern, first_match=True)  
    phone = phone_element.re_first(phone_pattern) if phone_element else None
  
  
    # 6) Site officiel  
    site_element = page.css_first('div.yuRUbf a:not([href*="instagram.com"]):not([href*="facebook.com"]):not([href*="tripadvisor.com"]):not([href*="google.com"])')  
    site = site_element.attrib.get("href") if site_element else None
  
    # 7) Réseaux sociaux  
    social_domains = ("facebook.com", "instagram.com", "twitter.com", "linkedin.com", "youtube.com")  
    socials = []  
    for a in page.css("a[href]"):  
        href = a.attrib.get("href")  
        if href and any(domain in href for domain in social_domains):  
            socials.append(href)  
    socials = list(dict.fromkeys(socials))  
  
    return {  
        "telephone": phone,  
        "site_web": site,  
        "reseaux_sociaux": socials  
    }


if __name__ == "__main__":
    infos = scrape_with_scrapling("Restaurant Dar El Medina Casablanca")
    print("Téléphone       :", infos["telephone"])
    print("Site web        :", infos["site_web"])
    print("Réseaux sociaux :", infos["reseaux_sociaux"])
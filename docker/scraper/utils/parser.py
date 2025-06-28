import json
import os
import logging
from datetime import datetime
from utils.sender import send_to_kafka, close_kafka_sender

# Compteur pour les identifiants uniques
COUNTER_FILE = "output/counter.txt"

def get_next_id():
    """Génère un identifiant unique incrémental commençant par 000001"""
    if not os.path.exists(COUNTER_FILE):
        # Créer le répertoire si nécessaire
        os.makedirs(os.path.dirname(COUNTER_FILE), exist_ok=True)
        # Initialiser le compteur
        with open(COUNTER_FILE, "w") as f:
            f.write("1")
        return "000001"
    
    with open(COUNTER_FILE, "r") as f:
        counter = int(f.read().strip())
    
    # Incrémenter et sauvegarder
    with open(COUNTER_FILE, "w") as f:
        f.write(str(counter + 1))
    
    # Formater avec des zéros au début
    return f"{counter:06d}"

def parse_item(item):
    """Transforme un élément scrapé au format requis"""
    
    # Générer un identifiant unique
    unique_id = get_next_id()
    
    # Extraire les coordonnées du scraper
    lat = float(item.get("latitude", 0)) if item.get("latitude") else 0
    lng = float(item.get("longitude", 0)) if item.get("longitude") else 0
    
    # Récupérer le numéro de téléphone enrichi ou utiliser une valeur par défaut
    phone_number = item.get("telephone", "12345676543")
    if not phone_number:
        phone_number = "12345676543"
    
    # Construire le payload au format demandé
    payload = {
        "company_name": item.get("name", "Unknown"),
        "company_RC": unique_id,
        "address": {
            "address_line": item.get("address", "test address"),
            "address_line2": "test address_line2",
            "city": item.get("city", "Lahore"),
            "country": "Maroc",
            "zip": "54000"
        },
        "email": "test@test.com",
        "phone_number": phone_number,
        "language": "fr",
        "coordinates": {
            "lat": lat,
            "lang": lng
        },
        # Ajouter les informations enrichies
        "website": item.get("site_web"),
        "social_networks": item.get("reseaux_sociaux", []),
        "rating": item.get("rating"),
        "review_count": item.get("review_count"),
        "cuisine": item.get("cuisine"),
        "price_range": item.get("price_range")
    }
    
    return payload

def process_city_results(items, city):
    """Traite tous les résultats d'une ville et les sauvegarde dans un seul fichier"""
    if not items:
        logging.warning(f"Aucun résultat trouvé pour {city}")
        return
    
    # Créer le répertoire output s'il n'existe pas
    os.makedirs("output", exist_ok=True)
    
    # Traiter chaque élément
    processed_items = []
    for item in items:
        # Ajouter la ville si elle n'est pas déjà présente
        if "city" not in item:
            item["city"] = city
        
        # Transformer l'élément
        processed_item = parse_item(item)
        processed_items.append(processed_item)
        
        # Envoyer à Kafka
        if send_to_kafka(processed_item):
            logging.info(f"Données envoyées à Kafka pour {processed_item['company_name']} (ID: {processed_item['company_RC']})")
        else:
            logging.error(f"Échec de l'envoi à Kafka pour {processed_item['company_RC']}")
    
    # Sauvegarder tous les résultats dans un seul fichier JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"output/{city}_{timestamp}.json"
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(processed_items, f, ensure_ascii=False, indent=2)
    
    logging.info(f"Résultats sauvegardés dans {output_file}: {len(processed_items)} éléments")
    
    return processed_items 
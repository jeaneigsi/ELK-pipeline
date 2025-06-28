import json
import os
import argparse
from core.loader import load_scraper
from core.runner import run_scraper
from utils.parser import process_city_results
from utils.sender import close_kafka_sender
import logging
import signal
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

# Gestion propre de l'arrêt du programme
def signal_handler(sig, frame):
    logging.info("Arrêt du scraper...")
    close_kafka_sender()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def main():
    # Analyser les arguments de ligne de commande
    parser = argparse.ArgumentParser(description="Scraper de données pour restaurants")
    parser.add_argument("--parallel", action="store_true", help="Activer le traitement parallèle")
    parser.add_argument("--workers", type=int, default=5, help="Nombre de workers pour le traitement parallèle")
    args = parser.parse_args()
    
    try:
        # Créer le dossier output s'il n'existe pas
        os.makedirs("output", exist_ok=True)
        
        with open("config/sources.json", encoding="utf-8") as f:
            sources = json.load(f)
        with open("config/villes_maroc.json", encoding="utf-8") as f:
            villes = [v["city"] for v in json.load(f)]

        for src in sources:
            if "{param}" in src["url"]:
                for ville in villes:
                    url = src["url"].replace("{param}", ville)
                    logging.info(f"Scraping pour la ville : {ville}")
                    scraper = load_scraper(src["scraper"])
                    
                    # Utiliser les paramètres de parallélisme si disponibles dans le scraper
                    if hasattr(scraper, "scrape") and "use_parallel" in scraper.scrape.__code__.co_varnames:
                        items = run_scraper(scraper, url, use_parallel=args.parallel, max_workers=args.workers)
                    else:
                        items = run_scraper(scraper, url)
                    
                    # Traiter tous les résultats de cette ville en une seule fois
                    process_city_results(items, ville)
                    
                    logging.info(f"Traitement terminé pour {ville}: {len(items)} éléments")
            else:
                scraper = load_scraper(src["scraper"])
                
                # Utiliser les paramètres de parallélisme si disponibles dans le scraper
                if hasattr(scraper, "scrape") and "use_parallel" in scraper.scrape.__code__.co_varnames:
                    items = run_scraper(scraper, src["url"], use_parallel=args.parallel, max_workers=args.workers)
                else:
                    items = run_scraper(scraper, src["url"])
                
                # Traiter tous les résultats en une seule fois
                process_city_results(items, "unknown_city")
                
                logging.info(f"Traitement terminé: {len(items)} éléments")
    finally:
        # Fermer proprement la connexion Kafka à la fin
        close_kafka_sender()


if __name__ == "__main__":
    main()
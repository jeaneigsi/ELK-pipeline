import json
import os
import logging
import argparse
from core.loader import load_scraper
from core.runner import run_scraper
import signal
import sys
from datetime import datetime

# Configuration des logs pour affichage en console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Gestion propre de l'arrêt du programme
def signal_handler(sig, frame):
    logging.info("Arrêt du scraper...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def save_results(items, city):
    """Sauvegarde les résultats dans un fichier JSON"""
    if not items:
        logger.warning(f"Aucun résultat trouvé pour {city}")
        return
    
    # Créer le dossier output s'il n'existe pas
    os.makedirs("output", exist_ok=True)
    
    # Sauvegarder les résultats bruts
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"output/{city}_raw_{timestamp}.json"
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Résultats bruts sauvegardés dans {output_file}: {len(items)} éléments")
    
    return items

def main():
    # Analyser les arguments de ligne de commande
    parser = argparse.ArgumentParser(description="Test du scraper de données pour restaurants")
    parser.add_argument("--parallel", action="store_true", help="Activer le traitement parallèle")
    parser.add_argument("--workers", type=int, default=5, help="Nombre de workers pour le traitement parallèle")
    parser.add_argument("--ville", type=str, help="Ville spécifique à scraper (optionnel)")
    parser.add_argument("--scraper", type=str, default="googlemaps", help="Scraper à utiliser (par défaut: googlemaps)")
    args = parser.parse_args()
    
    try:
        # Créer le dossier output s'il n'existe pas
        os.makedirs("output", exist_ok=True)
        
        # Charger les configurations
        with open("config/sources.json", encoding="utf-8") as f:
            sources = json.load(f)
        
        # Si une ville spécifique est fournie, ne traiter que celle-là
        if args.ville:
            villes = [args.ville]
            logger.info(f"Mode test: scraping uniquement pour la ville {args.ville}")
        else:
            # Sinon charger toutes les villes du fichier de configuration
            with open("config/villes_maroc.json", encoding="utf-8") as f:
                villes = [v["city"] for v in json.load(f)]

        # Trouver la source correspondant au scraper demandé
        scraper_source = None
        for src in sources:
            if src["scraper"] == args.scraper:
                scraper_source = src
                break
        
        if not scraper_source:
            logger.error(f"Scraper '{args.scraper}' non trouvé dans les sources")
            return
        
        # Parcourir les villes sélectionnées
        for ville in villes:
            if "{param}" in scraper_source["url"]:
                url = scraper_source["url"].replace("{param}", ville)
                logger.info(f"Scraping pour la ville : {ville} avec {args.scraper}")
                
                # Charger le scraper
                scraper = load_scraper(args.scraper)
                
                # Utiliser les paramètres de parallélisme si disponibles
                if hasattr(scraper, "scrape") and "use_parallel" in scraper.scrape.__code__.co_varnames:
                    logger.info(f"Mode parallèle: {'activé' if args.parallel else 'désactivé'} avec {args.workers} workers")
                    items = run_scraper(scraper, url, use_parallel=args.parallel, max_workers=args.workers)
                else:
                    items = run_scraper(scraper, url)
                
                # Ajouter la ville aux résultats
                for item in items:
                    if "city" not in item:
                        item["city"] = ville
                
                # Sauvegarder les résultats
                save_results(items, ville)
                
                logger.info(f"Traitement terminé pour {ville}: {len(items)} éléments")
            else:
                # Cas d'une URL sans paramètre de ville
                logger.info(f"Scraping pour {scraper_source['url']} avec {args.scraper}")
                scraper = load_scraper(args.scraper)
                
                # Utiliser les paramètres de parallélisme si disponibles
                if hasattr(scraper, "scrape") and "use_parallel" in scraper.scrape.__code__.co_varnames:
                    logger.info(f"Mode parallèle: {'activé' if args.parallel else 'désactivé'} avec {args.workers} workers")
                    items = run_scraper(scraper, scraper_source["url"], use_parallel=args.parallel, max_workers=args.workers)
                else:
                    items = run_scraper(scraper, scraper_source["url"])
                
                # Sauvegarder les résultats
                save_results(items, "general")
                
                logger.info(f"Traitement terminé: {len(items)} éléments")
            
            # Si on teste une seule ville, pas besoin de continuer la boucle
            if args.ville:
                break
                
    except Exception as e:
        logger.exception(f"Erreur lors de l'exécution: {str(e)}")

if __name__ == "__main__":
    main()

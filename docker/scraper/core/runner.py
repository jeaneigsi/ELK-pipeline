from scrapling.fetchers import StealthyFetcher  # ou StealthyFetcher


def run_scraper(module, url: str, **kwargs):
    """
    Appelle la fonction scrape(url) du module scraper et renvoie la liste des items.
    Permet de passer des paramètres supplémentaires à la fonction scrape.
    """
    return module.scrape(url, **kwargs)
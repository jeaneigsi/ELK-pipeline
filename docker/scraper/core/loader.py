import importlib


def load_scraper(name: str):
    """
    Charge dynamiquement le module `scrapers.{name}`.
    """
    return importlib.import_module(f"scrapers.{name}")
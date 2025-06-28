FROM python:3.10-slim

WORKDIR /app

# Copier les fichiers de dépendances
COPY requirements.txt .
# Installer les dépendances système nécessaires pour Playwright
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       libgtk-3-0 libxtst6 libxss1 libasound2 libnss3 \
       fonts-liberation libatk1.0-0 libcairo-gobject2 \
       libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 \
    && rm -rf /var/lib/apt/lists/*



# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Installer Playwright, scrapling et camoufox
RUN pip install playwright scrapling camoufox
RUN playwright install firefox
# Removed build-time execution of scrapling & camoufox to speed up image build

# Copier le code source
COPY . .

# Créer le dossier pour les sorties
RUN mkdir -p output

# Commande par défaut avec le parallélisme activé
CMD ["bash", "-c", "scrapling install && camoufox fetch && playwright install-deps && python main.py --parallel --workers 4"]
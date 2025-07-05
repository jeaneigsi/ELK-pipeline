#!/usr/bin/env bash
# Nettoie le dossier output en supprimant tous les fichiers JSON sauf un.
# Par défaut, le script conserve le fichier JSON le plus récent.
# Utilisation :
#   ./clean_output.sh [fichier_a_conserver]
#   - fichier_a_conserver (optionnel) : nom du fichier JSON à conserver.
#     S'il n'est pas fourni, le script détecte automatiquement le fichier JSON le plus récent.

set -euo pipefail

# Répertoire absolu du script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

OUTPUT_DIR="$SCRIPT_DIR/scraper/output"

if [[ ! -d "$OUTPUT_DIR" ]]; then
  echo "Erreur : le dossier output n'existe pas ($OUTPUT_DIR)" >&2
  exit 1
fi

# Sélection du fichier à conserver
if [[ $# -ge 1 ]]; then
  KEEP_FILE="$1"
  if [[ ! -f "$OUTPUT_DIR/$KEEP_FILE" ]]; then
    echo "Erreur : le fichier spécifié à conserver n'existe pas : $KEEP_FILE" >&2
    exit 1
  fi
else
  # Déterminer le JSON le plus récent (par date de modification)
  KEEP_FILE=$(ls -1t "$OUTPUT_DIR"/*.json | head -n 1 | xargs -n1 basename)
fi

echo "Conservation du fichier : $KEEP_FILE"

# Boucle sur tous les fichiers JSON et suppression sauf celui à conserver
find "$OUTPUT_DIR" -maxdepth 1 -type f -name '*.json' ! -name "$KEEP_FILE" -print -delete

echo "Nettoyage terminé. Contenu restant :"
ls -lh "$OUTPUT_DIR" 
#!/bin/bash

sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

echo "Version de Docker Compose:"
docker-compose --version

echo "Démarrage de la pipeline ELK avec Kafka..."
docker-compose up -d

echo "Attente du démarrage des services et configuration de Kafka Connect..."
./setup-kafka-connect.sh

echo "Tous les services sont démarrés et configurés."
echo ""
echo "Interfaces disponibles:"
echo "- Kibana: http://localhost:5601"
echo "- Elasticsearch: http://localhost:9200"
echo "- Kafka Connect: http://localhost:8083"
echo ""
echo "Pour voir les logs du scraper:"
echo "docker-compose logs -f scraper"
echo ""
echo "Pour arrêter tous les services:"
echo "docker-compose down" 
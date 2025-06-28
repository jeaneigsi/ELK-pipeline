#!/bin/bash

# Vérification que Kafka et Elasticsearch sont en état "running"
echo "Vérification de l'état de Kafka et Elasticsearch..."
MAX_RETRIES=30
RETRY_INTERVAL=10
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
  KAFKA_STATUS=$(docker ps --filter "name=kafka" --format "{{.Status}}" | grep -c "Up")
  ES_STATUS=$(docker ps --filter "name=elasticsearch" --format "{{.Status}}" | grep -c "Up")
  
  if [ $KAFKA_STATUS -gt 0 ] && [ $ES_STATUS -gt 0 ]; then
    echo "Kafka et Elasticsearch sont prêts!"
    break
  else
    echo "En attente de Kafka et Elasticsearch... ($((RETRY_COUNT+1))/$MAX_RETRIES)"
    RETRY_COUNT=$((RETRY_COUNT+1))
    sleep $RETRY_INTERVAL
  fi
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
  echo "ERREUR: Timeout en attendant Kafka et Elasticsearch"
  exit 1
fi

# Attendre que Kafka Connect soit prêt
echo "Attente du démarrage de Kafka Connect..."
while ! curl -s http://localhost:8083/ > /dev/null; do
  sleep 5
done

echo "Kafka Connect est prêt, création du connecteur Elasticsearch..."

# Créer le connecteur Elasticsearch
curl -X POST -H "Content-Type: application/json" --data '{
  "name": "elasticsearch-sink",
  "config": {
    "connector.class": "io.confluent.connect.elasticsearch.ElasticsearchSinkConnector",
    "tasks.max": "1",
    "topics": "scraper-data",
    "key.ignore": "true",
    "connection.url": "http://elasticsearch:9200",
    "type.name": "_doc",
    "value.converter": "org.apache.kafka.connect.json.JsonConverter",
    "value.converter.schemas.enable": "false",
    "schema.ignore": "true",
    "behavior.on.null.values": "ignore",
    "behavior.on.malformed.documents": "warn",
    "write.method": "insert",
    "max.retries": "5",
    "retry.backoff.ms": "5000"
  }
}' http://localhost:8083/connectors

echo "Configuration terminée." 
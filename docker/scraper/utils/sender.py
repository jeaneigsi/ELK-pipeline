import json
import logging
from kafka import KafkaProducer
from kafka.errors import KafkaError

# Configuration du logger
logger = logging.getLogger(__name__)

class KafkaSender:
    """Classe pour envoyer des données à Kafka"""
    
    def __init__(self, bootstrap_servers='kafka:9092', topic='scraper-data'):
        """Initialise le producteur Kafka"""
        self.topic = topic
        self.producer = None
        self.bootstrap_servers = bootstrap_servers
        self._connect()
    
    def _connect(self):
        """Établit la connexion avec le broker Kafka"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',
                retries=3
            )
            logger.info(f"Connecté au broker Kafka: {self.bootstrap_servers}")
        except Exception as e:
            logger.error(f"Erreur de connexion à Kafka: {str(e)}")
            self.producer = None
    
    def send(self, data):
        """Envoie les données à Kafka"""
        if not self.producer:
            logger.error("Producteur Kafka non disponible")
            return False
        
        try:
            future = self.producer.send(self.topic, data)
            # Attendre la confirmation d'envoi (optionnel)
            record_metadata = future.get(timeout=10)
            logger.debug(f"Message envoyé à {record_metadata.topic}, partition {record_metadata.partition}, offset {record_metadata.offset}")
            return True
        except KafkaError as e:
            logger.error(f"Erreur lors de l'envoi à Kafka: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Exception lors de l'envoi à Kafka: {str(e)}")
            return False
    
    def close(self):
        """Ferme la connexion au producteur Kafka"""
        if self.producer:
            self.producer.flush()
            self.producer.close()
            logger.info("Connexion au producteur Kafka fermée")

# Instance globale du sender
kafka_sender = None

def get_kafka_sender():
    """Retourne l'instance du sender Kafka, en la créant si nécessaire"""
    global kafka_sender
    if kafka_sender is None:
        kafka_sender = KafkaSender()
    return kafka_sender

def send_to_kafka(data):
    """Envoie les données à Kafka"""
    sender = get_kafka_sender()
    return sender.send(data)

def close_kafka_sender():
    """Ferme la connexion au sender Kafka"""
    global kafka_sender
    if kafka_sender:
        kafka_sender.close()
        kafka_sender = None
            
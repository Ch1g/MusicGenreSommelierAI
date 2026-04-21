import pika

BROKER_HOST = "message-broker"

def get_connection() -> pika.BlockingConnection:
    return pika.BlockingConnection(pika.ConnectionParameters(BROKER_HOST))

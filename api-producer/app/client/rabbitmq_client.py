import os
from urllib.parse import quote
import pika


username = os.getenv("RABBITMQ_USER")
password = os.getenv("RABBITMQ_PASSWORD")
host = "rabbitmq"
port = 5672
vhost = "/"
vhost_encoded = quote(vhost, safe="")
rabbitMqUrl = f"pyamqp://{username}:{password}@{host}:{port}/{vhost_encoded}"


def get_connection():
  return pika.BlockingConnection(
    pika.ConnectionParameters(
      host=host,
      port=port,
      virtual_host=vhost,
      credentials=pika.PlainCredentials(username, password),
    )
  )
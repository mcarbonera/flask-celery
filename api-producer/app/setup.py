from celery import Celery, Task
from flask import Flask
import pika
import psycopg2
import time
from .client.rabbitmq_client import rabbitMqUrl, get_connection
from .client.postgres_client import get_pg_connection

def celery_init_app(app: Flask) -> Celery:
  class FlaskTask(Task):
    def __call__(self, *args: object, **kwargs: object) -> object:
      with app.app_context():
        return self.run(*args, **kwargs)

  celery_app = Celery(app.name, task_cls=FlaskTask)
  celery_app.config_from_object(app.config["CELERY"])
  celery_app.set_default()

  app.extensions["celery"] = celery_app
  return celery_app


def create_app() -> Flask:
  wait_for_postgres()
  wait_for_rabbitmq()
  app = Flask(__name__)
  app.config.from_mapping(
    CELERY=dict(
      broker_url=rabbitMqUrl,
      result_backend="redis://redis",
      task_ignore_result=True,
      task_routes={
        'app.tasks.duplicate_chinook': {'queue': 'duplicate_queue'},
        'app.tasks.update_write_back': {'queue': 'write_back_queue'},
      }
    ),
  )
  app.config.from_prefixed_env()
  celery_init_app(app)
  return app


def wait_for_postgres(retry_interval=2, timeout=60):
  start_time = time.time()
  while True:
    try:
      connection = get_pg_connection()
      connection.close()
      print("✅ PostgreSQL is ready!")
      break
    except psycopg2.OperationalError:
      if time.time() - start_time > timeout:
        raise Exception("❌ Timed out waiting for PostgreSQL after {timeout} seconds.")
      print("⏳ Waiting for PostgreSQL...")
      time.sleep(retry_interval)


def wait_for_rabbitmq(retry_interval=2, timeout=60):
  start_time = time.time()
  while True:
    try:
      connection = get_connection()
      connection.close()
      print("✅ RabbitMQ is ready!")
      break
    except pika.exceptions.AMQPConnectionError:
      elapsed = time.time() - start_time
      if elapsed > timeout:
        raise TimeoutError(f"❌ Timed out waiting for RabbitMQ after {timeout} seconds.")
      print("⏳ Waiting for RabbitMQ...")
      time.sleep(retry_interval)
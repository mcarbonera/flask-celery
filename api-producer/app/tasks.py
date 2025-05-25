from .setup import create_app
from celery import shared_task
from .duplicate_db_service.duplicate_chinook import duplicate_albums
from .update_write_back_service.update_write_back import write_album


flask_app = create_app()
celery_app = flask_app.extensions["celery"]


@shared_task(ignore_result=False)
def duplicate_chinook():
  duplicate_albums()


@shared_task(ignore_result=False)
def update_write_back(album):
  write_album(album)
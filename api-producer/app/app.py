from .tasks import flask_app, duplicate_chinook, update_write_back
from celery.result import AsyncResult
from flask import request, jsonify
from .album_service.album_service import getAlbumById, updateAlbumOnRedis
from .album_service.producer_service import generate_work_load


# MARK: Status Task
@flask_app.get("/get_task_result")
def get_task_result() -> dict[str, object]:
  result_id = request.args.get('result_id')
  result = AsyncResult(result_id)
  if result.ready():
    # Task completed
    if result.successful():
      return {
        "ready": result.ready(),
        "successful": result.successful(),
        "value": result.result,
      }
    else:
    # Task completed with an error
      return jsonify({'status': 'ERROR', 'error_message': str(result.result)})
  else:
    # Task is still pending
    return jsonify({'status': 'Pending'})


# MARK: Duplicar database
@flask_app.route('/duplicate_database', methods=['GET'])
def duplicate_database():
  # Duplicate postgresql data. (Enviar para task executar)
  result = duplicate_chinook.delay()
  return f'Duplication task started (id.: {result.id})'


# MARK: Get Items
@flask_app.route('/album', methods=['GET'])
def get_album():
  album_id = request.args.get('album_id')
  return getAlbumById(album_id)


# MARK: Atualizar
@flask_app.route('/update-album', methods=['GET'])
def update_albums():
  tasksQueued = []
  workload = generate_work_load()
  for data in workload:
    # Update primeiro no cache (write back)
    updateAlbumOnRedis(data)
    # Colocar tarefas na fila para update do DB (assíncrono).
    result = update_write_back.delay(data)
    tasksQueued.append(result.id)
  return tasksQueued
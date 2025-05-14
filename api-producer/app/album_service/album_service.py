import ast
from typing import Any
from ..client.redis_client import REDIS_CLIENT
from ..client.postgres_client import get_pg_connection


def exec_sql(query: str) -> list[tuple[Any, ...]]:
  connection = get_pg_connection()
  cursor = connection.cursor()
  cursor.execute(query)
  if query.strip().lower().startswith(("insert", "update", "delete")):
    connection.commit()

  try:
    return [item[0] for item in cursor.fetchall()]
  except Exception as err:
    print(err)
    connection.close()
    return


def getAllAlbums():
  query = f"""
    SELECT alb.album_id
    FROM album alb;
  """
  return exec_sql(query)


def getAlbumById(album_id):
  # Busca no cache do Redis
  nome = getAlbumByIdFromRedis(album_id)
  # Se não tiver nada, busca do postgres
  if(nome == None):
    album = getAlbumByIdFromDb(album_id)
    if(len(album) == 0):
      return "404 Not Found"
    albumParsed = ast.literal_eval(album[0])

    albumObj = {'album_id': albumParsed[0], 'title': albumParsed[1]}
    updateAlbumOnRedis(albumObj)
    return albumObj
  return {'album_id': int(album_id), 'title': nome.decode('utf-8')}


def getAlbumByIdFromRedis(album_id):
  return REDIS_CLIENT.get(f"sql:album-title:{album_id}")


def getAlbumByIdFromDb(album_id):
  query = f"""
    SELECT alb
    FROM album alb
    WHERE alb.album_id = {album_id};
  """
  return exec_sql(query)


def updateAlbumOnRedis(album):
  REDIS_CLIENT.set(f"sql:album-title:{album['album_id']}", album['title'], ex=3600)


def updateAlbumOnDatabase(album):
  query = f"""
    UPDATE album
    SET title = '{album['title']}'
    WHERE album_id = {album['album_id']};
  """
  return exec_sql(query)
from .album_service import getAllAlbums
import random


def generate_work_load():
  idsToUpdate = getAllAlbums()
  workload = []
  for id in idsToUpdate:
    randomNumber = str(random.randint(0, 99999))
    message = {
      "album_id": id,
      "title": "write through! ("+randomNumber+")",
    }
    workload.append(message)
  return workload

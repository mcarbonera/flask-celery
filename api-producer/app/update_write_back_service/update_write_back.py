from ..album_service.album_service import updateAlbumOnDatabase


def write_album(album):
  # Na estrategia Write Back,
  # Cache é atualizado primeiro, de modo síncrono
  # Banco é atualizado de modo assíncrono
  return updateAlbumOnDatabase(album)
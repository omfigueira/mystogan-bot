import typing as t
from pydantic import BaseModel, Field


LITERALS = t.Literal['spotify', 'youtube', 'soundcloud', 'apple_music']

class Song(BaseModel):
    title: str = Field(..., description="Título de la canción")
    url: str = Field(..., description="URL de la canción")
    
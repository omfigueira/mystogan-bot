from abc import ABC, abstractmethod
from discord.ext import commands

class MusicProviderRepository(ABC):
    
    @abstractmethod
    async def play(self, ctx: commands.Context, query: str):
        """
        Método para reproducir una canción o playlist.
        :param ctx: Contexto del comando de Discord.
        :param query: Consulta de búsqueda o URL de la canción/playlist.
        """
        raise NotImplementedError("Este método debe ser implementado por la subclase.")
from abc import ABC, abstractmethod

import discord


class DiscordRepository(ABC):
    
    @abstractmethod
    async def cleanup(self, guild: discord.Guild):
        """
        Método para limpiar la sesión de un servidor.
        :param guild_id: ID del servidor a limpiar.
        """
        raise NotImplementedError("Este método debe ser implementado por la subclase.")

    @abstractmethod
    async def start_disconnect_timer(self, guild: discord.Guild):
        """
        Método para iniciar un temporizador de desconexión.
        :param guild: Objeto Guild de Discord.
        """
        raise NotImplementedError("Este método debe ser implementado por la subclase.")
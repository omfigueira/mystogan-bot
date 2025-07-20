import asyncio
import logging
import discord
from src.domain.discord.repository import DiscordRepository


class SessionRepository(DiscordRepository):
    def __init__(self, logger: logging.Logger):
        self.queues = {}
        self.current_views = {}
        self.history = {}
        self.logger = logger
        self.logger.info("SessionRepository inicializado.")

    async def cleanup(self, guild: discord.Guild):
        if guild.voice_client:
            await guild.voice_client.disconnect()
        guild_id = guild.id
        self.queues.pop(guild_id, None)
        self.history.pop(guild_id, None)
        view_info = self.current_views.pop(guild_id, None)
        if view_info:
            view_info['view'].stop()
            try:
                msg = await view_info['channel'].fetch_message(view_info['message_id'])
                await msg.delete()
            except discord.NotFound: pass
        self.logger.info(f"Limpieza completada para el servidor: {guild.name}")

    async def start_disconnect_timer(self, guild: discord.Guild):
        self.logger.info(f"Iniciando temporizador de 3 minutos para desconexión en {guild.name}.")
        await asyncio.sleep(180)
        vc = guild.voice_client
        if vc and not vc.is_playing() and not self.queues.get(guild.id):
            self.logger.info(f"Bot inactivo en {guild.name}. Desconectando.")
            await self._cleanup(guild)
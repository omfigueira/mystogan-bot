import asyncio
import logging
import typing
import discord
from discord.ext import commands
from src.domain.discord.repository import DiscordRepository
from src.domain.music_providers.entity import LITERALS
from src.domain.music_providers.repository import MusicProviderRepository

class CommandView(commands.Cog, name="CommandView"):
    def __init__(
        self, 
        bot: commands.Bot,
        music_provider: typing.Dict[LITERALS, MusicProviderRepository],
        discord_repository: DiscordRepository,
        logger: logging.Logger
    ):
        self.bot = bot
        self.logger = logger
        self.music_provider = music_provider
        self.discord_repository = discord_repository
        self.logger.info("CommandView creada.")

    @commands.command(name='play', help='Reproduce una canción. ex: !play <nombre de la canción>')
    async def view_command(self, ctx: commands.Context, *, query: str):
        self.logger.info(f"Comando 'play' invocado por {ctx.author}.")
        await ctx.typing()

        self.logger.info(f"Intentando conectar al canal de voz de {ctx.author}.")
        await self._connect_channel(ctx)
        self.logger.info(f"Conectado al canal de voz: {ctx.voice_client.channel.name}.")

        provider = await self._get_provider(query)

        if not provider:
            self.logger.error("Proveedor de música no encontrado.")
            await ctx.send("Proveedor de música no encontrado. Por favor, verifica el enlace o el nombre de la canción.")
            return await ctx.channel.guild.voice_client.disconnect()
        
        self.logger.info(f"Reproduciendo canción: {query}.")
        await provider.play(ctx, query)

    @commands.command(name='queue', help='Muestra la cola de reproducción actual.')
    async def queue(self, ctx: commands.Context):
        self.logger.info(f"Comando !queue recibido de {ctx.author}.")
        guild_id = ctx.guild.id
        if self.discord_repository.queues.get(guild_id):
            embed = discord.Embed(title="🎶 Cola de Reproducción", color=discord.Color.purple())
            queue_list = "\n".join(f"**{i+1}.** {song['title']}" for i, song in enumerate(self.discord_repository.queues[guild_id][:10]))
            embed.description = queue_list
            if len(self.discord_repository.queues[guild_id]) > 10:
                embed.set_footer(text=f"... y {len(self.discord_repository.queues[guild_id]) - 10} más.")
            await ctx.send(embed=embed)
        else:
            await ctx.send("La cola está vacía.")

    # --- FUNCIÓN ON_VOICE_STATE_UPDATE MODIFICADA ---
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.id == self.bot.user.id and before.channel is not None and after.channel is None:
            self.logger.info(f"Bot desconectado del canal de voz en {before.channel.guild.name}.")
            await self.discord_repository.cleanup(before.channel.guild)
        
        if before.channel is not None:
            vc = before.channel.guild.voice_client
            if vc and vc.channel == before.channel and len(vc.channel.members) == 1:
                self.logger.info(f"Bot se ha quedado solo en {vc.channel.name}. Iniciando temporizador.")
                await self.discord_repository.start_disconnect_timer(before.channel.guild)
        
    async def _connect_channel(self, ctx: commands.Context):
        voice_channel = ctx.author.voice.channel
        
        if not voice_channel:
            return await ctx.send("¡Necesitas estar en un canal de voz!")
        
        vc = ctx.voice_client

        if not vc:
            try:
                vc = await voice_channel.connect(timeout=30.0)
            except asyncio.TimeoutError:
                return await ctx.send("No me pude conectar al canal de voz. Inténtalo de nuevo.")
        elif vc.channel != voice_channel:
            return await ctx.send("Ya estoy en otro canal de voz.")
        
    async def _get_provider(self, search: str) -> typing.Optional[MusicProviderRepository]:
        link = search.lower()
        self.logger.info(f"Buscando proveedor para el enlace: {link}")
        if 'youtube' in link or 'youtu.be' in link:
            self.logger.info("Proveedor de YouTube encontrado.")
            return self.music_provider['youtube']
        elif 'spotify' in link:
            self.logger.info("Proveedor de Spotify encontrado.")
            return self.music_provider['spotify']
        elif 'soundcloud' in link:
            self.logger.info("Proveedor de SoundCloud encontrado.")
            return self.music_provider['soundcloud']
        elif 'apple_music' in link:
            self.logger.info("Proveedor de Apple Music encontrado.")
            return self.music_provider['apple_music']
        else:
            self.logger.warning("Proveedor de música no encontrado.")
            return None
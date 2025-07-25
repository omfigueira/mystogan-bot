

import asyncio
import logging
import discord
import yt_dlp
from src.domain.discord.repository import DiscordRepository
from src.infraestructure.adapter.discord.music_player_view import MusicPlayerView
from discord.ext import commands
from imageio_ffmpeg import get_ffmpeg_exe
from src.domain.music_providers.repository import MusicProviderRepository
from pathlib import Path


class YouTubeMusicProviderRepository(MusicProviderRepository):

    def __init__(
        self, 
        bot: commands.Bot,
        discord_repository: DiscordRepository,
        logger: logging.Logger
    ):
        self.bot = bot
        self.logger = logger
        self.discord_repository = discord_repository
        project_root = Path(__file__).parent.parent.parent.parent
        self.cookie_file_path = project_root / 'cookies.txt'
        self.logger.info(f"Ruta de cookies configurada en: {self.cookie_file_path}")
        self.logger.info("YouTubeMusicProviderRepository inicializado.")
            
    async def play(self, ctx: commands.Context, query: str):
        # Opciones para una búsqueda inicial muy rápida (flat extraction)
        ydl_opts = {
            'format': 'bestaudio/best', 'quiet': True, 'no_warnings': True,
            'default_search': 'ytmsearch', 'extract_flat': 'in_playlist'
        }
        
        loop = asyncio.get_event_loop()
        try:
            # La búsqueda inicial sigue siendo en un hilo para no bloquear
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = await loop.run_in_executor(None, lambda: ydl.extract_info(query, download=False))
        except Exception as e:
            self.logger.error(f"Error en la búsqueda inicial: {e}")
            return await ctx.send("Ocurrió un error al buscar la canción o playlist.")

        if not info:
            return await ctx.send("No se encontraron resultados.")

        entries = list(info.get('entries', [info]))
        if not entries:
            return await ctx.send("No se encontraron resultados.")
        
        guild_id = ctx.guild.id
        if guild_id not in self.discord_repository.queues:
            self.discord_repository.queues[guild_id] = []
        
        # Añadimos las canciones a la cola solo con la información mínima
        songs_added = []
        for entry in entries:
            songs_added.append({
                'id': entry.get('id'),
                'title': entry.get('title', 'Título Desconocido'),
                'webpage_url': entry.get('url') # Usamos la URL de la página
            })

        self.discord_repository.queues[guild_id].extend(songs_added)
        
        if len(songs_added) > 1:
            await ctx.send(f"✅ Se han añadido **{len(songs_added)}** canciones de la playlist a la cola.")
        else:
            await ctx.send(f"✅ **{songs_added[0]['title']}** añadido a la cola.")

        # Si no está sonando nada, inicia la reproducción
        if not ctx.voice_client.is_playing():
            self.logger.info("Iniciando reproducción de la primera canción en la cola.") 
            if self.discord_repository.actual_actions.get(guild_id) != 'bucle':
                self.discord_repository.actual_actions[guild_id] = 'skip'
            self._play_next(ctx)

    def _get_song_info(self, action: str, guild_id: str):
        self.logger.info(f"Obteniendo información de la canción para la acción: {action} en el servidor: {guild_id}")
        if action == 'bucle':
            return self.discord_repository.history[guild_id][-1]
        elif action == 'skip':
            info_song = self.discord_repository.queues[guild_id].pop(0)
            if not self.discord_repository.history.get(guild_id):
                self.discord_repository.history[guild_id] = []
            self.discord_repository.history[guild_id].append(info_song)
            return info_song
        elif action == 'back':
            info_song = self.discord_repository.history[guild_id].pop(-1)
            self.discord_repository.queues[guild_id].insert(0, info_song)
            return self.discord_repository.history[guild_id][-1]

    def _play_next(self, ctx: commands.Context):
        self.logger.info("Reproduciendo la siguiente canción en la cola.")
        guild_id = ctx.guild.id
        vc = ctx.voice_client
        if not vc: return

        if self.discord_repository.queues.get(guild_id):
            self.logger.info(f"Cola de reproducción para {ctx.guild.name}: {len(self.discord_repository.queues[guild_id])} canciones.")
            song_info = self._get_song_info(self.discord_repository.actual_actions.get(guild_id, 'skip'), guild_id)
            self.logger.info(f"Reproduciendo canción _get_song_info: {song_info['title']}")

            if not song_info:
                self.logger.info("No hay más canciones en la cola. Desconectando.")
                return asyncio.run_coroutine_threadsafe(self.discord_repository.cleanup(ctx.guild), self.bot.loop)
            # --- LÓGICA DE CARGA PEREZOSA ---
            # Ahora buscamos los detalles completos justo antes de reproducir
            self.logger.info(f"Carga perezosa: Obteniendo detalles para '{song_info['title']}'...")
            try:
                ydl_opts = {'format': 'bestaudio/best', 'quiet': True, 'no_warnings': True}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    detailed_info = ydl.extract_info(song_info.get('webpage_url') or song_info.get('id'), download=False)
            except Exception as e:
                self.logger.error(f"No se pudieron obtener los detalles de '{song_info['title']}': {e}")
                self._play_next(ctx) # Intenta con la siguiente canción
                return
            # --- FIN DE LA LÓGICA ---
            
            song_to_play = {
                'title': detailed_info.get('title', 'Título Desconocido'), 'url': detailed_info.get('url'),
                'thumbnail': detailed_info.get('thumbnail'), 'duration_string': detailed_info.get('duration_string', 'N/A'),
                'webpage_url': detailed_info.get('webpage_url')
            }

            if not song_to_play.get('url'):
                self.logger.error(f"La canción '{song_to_play['title']}' no tiene URL de audio. Saltando.")
                self._play_next(ctx)
                return

            ffmpeg_options = {
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                'options': '-vn'
            }
            
            source = discord.FFmpegPCMAudio(song_to_play['url'], executable=get_ffmpeg_exe(), **ffmpeg_options)
            vc.play(source, after=lambda e: self._handle_after_play(e, ctx))
            asyncio.run_coroutine_threadsafe(self._send_player_message(ctx, song_to_play), self.bot.loop)
        else:
            asyncio.run_coroutine_threadsafe(self.discord_repository.start_disconnect_timer(ctx.guild), self.bot.loop)

    async def _send_player_message(self, ctx, song):
        guild_id = ctx.guild.id
        embed = discord.Embed(
            title="🎵 Reproduciendo ahora", 
            description=f"[{song.get('title', 'Título Desconocido')}]({song.get('webpage_url')})", 
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=song.get('thumbnail'))
        embed.add_field(name="Duración", value=song.get('duration_string', 'N/A'), inline=False)
        combined_list = list(self.discord_repository.history.get(guild_id, []) + self.discord_repository.queues.get(guild_id, []))
        
        total_history = len(self.discord_repository.history.get(guild_id, []))
        self.logger.info(f'combined_list: {len(combined_list)}, total_history: {total_history}')
        if not combined_list:
            queue_list = "No hay canciones en la cola o en el historial."
        else:
            lines = []
            try:
            # 3. Toma hasta 10 canciones de la lista combinada para mostrarlas
                initial = 0 if (total_history - 5) <= 0 else total_history - 5
                finish = 10 if total_history < 5 else total_history + 5
                self.logger.info(f"Mostrando canciones del índice {initial} al {finish} de la lista combinada.")
                songs_to_show = combined_list[initial: finish]
            except Exception as e:
                self.logger.exception(f"Error al procesar la lista combinada: {e}")
                songs_to_show = []
            self.logger.info(f"Mostrando {len(songs_to_show)} canciones de la lista combinada.")
            # 4. Usa enumerate() para crear la lista numerada de forma limpia y automática.
            for i, song in enumerate(songs_to_show):
                # Acorta los títulos largos para evitar que el embed se rompa
                title = song.get('title', 'Título Desconocido')
                if len(title) > 60:
                    title = title[:57] + "..."
                if total_history == (initial + i + 1):
                    lines.append(f"🎶 {title}")
                else:
                    lines.append(f"**{initial + i + 1}** {title}")

            # 5. Calcula cuántas canciones más quedan y añade el pie de página si es necesario.
            remaining_count = len(combined_list) - finish 
            if remaining_count > 0:
                lines.append(f"\n... y {remaining_count} más.")

            # 6. Une todas las líneas en un solo string al final, la forma más eficiente.
            queue_list = "\n".join(lines)

        embed.add_field(name="🎼 Cola de Reproducción", value=queue_list)
        view_info = self.discord_repository.current_views.get(guild_id)

        if view_info:
            try:
                msg = await view_info['channel'].fetch_message(view_info['message_id'])
                await msg.edit(embed=embed, view=view_info['view'])
                return
            except discord.NotFound: pass
        
        view = MusicPlayerView(self.bot, ctx, self.discord_repository, self.logger)
        player_message = await ctx.send(embed=embed, view=view)
        self.discord_repository.current_views[guild_id] = {'view': view, 'message_id': player_message.id, 'channel': player_message.channel}

    def _handle_after_play(self, error, ctx):
        if error:
            self.logger.error(f"Error después de reproducir: {error}")
        self.logger.info("Reproducción finalizada, buscando la siguiente canción en la cola.")
        self._play_next(ctx)

    def _search_and_extract(self, search: str):
        """Función síncrona para la búsqueda inicial. Se ejecuta en un hilo separado."""
        self.logger.info(f"[HILO] Iniciando búsqueda para: '{search}'")
        ydl_opts = {
            'format': 'bestaudio/best',
            'default_search': 'ytmsearch',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': 'in_playlist',
            'cookiefile': self.cookie_file_path,  # Si tienes cookies, puedes usarlas aquí
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(search, download=False)
                self.logger.info(f"[HILO] Búsqueda para '{search}' completada con éxito.")
                return info
            except Exception as e:
                self.logger.error(f"[HILO] Error en _search_and_extract con '{search}': {e}")
                return None
            
    def _process_entries(self, entries: list):
        """Función síncrona para obtener detalles de cada canción."""
        self.logger.info(f"[HILO] Iniciando procesamiento detallado de {len(entries)} canciones.")
        songs_to_add = []
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'cookiefile': self.cookie_file_path,  # Si tienes cookies, puedes usarlas aquí
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            for i, entry in enumerate(entries):
                self.logger.info(f"[HILO] Procesando entrada {i+1}/{len(entries)}: {entry.get('title', 'N/A')}")
                if i > 10:
                    break
                try:
                    url_to_extract = entry.get('url') or entry.get('webpage_url') or entry.get('id')
                    if not url_to_extract:
                        self.logger.warning(f"[HILO] La entrada no tiene URL o ID. Saltando.")
                        continue
                    
                    detailed_info = ydl.extract_info(url_to_extract, download=False)
                    songs_to_add.append({
                        'title': detailed_info.get('title', 'Título Desconocido'),
                        'url': detailed_info.get('url'),
                        'thumbnail': detailed_info.get('thumbnail'),
                        'duration_string': detailed_info.get('duration_string', 'N/A'),
                        'webpage_url': detailed_info.get('webpage_url')
                    })
                except Exception as e:
                    self.logger.error(f"[HILO] No se pudo procesar la entrada detallada: {entry.get('title', 'N/A')}. Error: {e}")
                    continue
        self.logger.info(f"[HILO] Procesamiento detallado completado. Se obtuvieron {len(songs_to_add)} canciones válidas.")
        return songs_to_add
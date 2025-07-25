import discord
from discord.ext import commands
import logging

from domain.discord.repository import DiscordRepository


class MusicPlayerView(discord.ui.View):
    def __init__(
            self, 
            bot: commands.Bot, 
            ctx: commands.Context,
            discord_repository: DiscordRepository,
            logger: logging.Logger = logging.getLogger("discord")
        ):
        super().__init__(timeout=None)
        self.bot = bot
        self.ctx = ctx
        self.cog = bot.get_cog('MusicCog')
        self.discord_repository = discord_repository
        self.logger = logger
        self.logger.info("MusicPlayerView creada.")

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.voice and interaction.user.voice.channel == self.ctx.voice_client.channel:
            return True
        await interaction.response.send_message("Debes estar en el mismo canal de voz que el bot.", ephemeral=True)
        return False

    @discord.ui.button(label="Pausa", style=discord.ButtonStyle.secondary, custom_id="pause_resume", emoji="⏯️", row=0)
    async def pause_resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = self.ctx.voice_client
        if vc.is_playing():
            vc.pause()
            button.label = "Reanudar"
            self.logger.info(f"Música pausada por {interaction.user}.")
        elif vc.is_paused():
            vc.resume()
            button.label = "Pausa"
            self.logger.info(f"Música reanudada por {interaction.user}.")
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Bucle", style=discord.ButtonStyle.primary, emoji="🔁", row=1)
    async def repeat(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = self.ctx.voice_client
        if self.discord_repository.actual_actions[self.ctx.guild.id] == 'bucle':
            self.discord_repository.actual_actions[self.ctx.guild.id] = 'skip'
            button.style = discord.ButtonStyle.primary
        else:
            self.discord_repository.actual_actions[self.ctx.guild.id] = 'bucle'
            button.style = discord.ButtonStyle.success
        if vc and (vc.is_playing() or vc.is_paused()):
            await interaction.response.defer()
            vc.stop()
            self.logger.info(f"Canción retrocedida por {interaction.user}.")
            await interaction.response.send_message("Canción retrocedida.", ephemeral=True)
        else:
            await interaction.response.send_message("No hay nada que retroceder. El bot se desconectara.", ephemeral=True)
            await self.cog.cleanup(self.ctx.guild)

    @discord.ui.button(label="Retroceder", style=discord.ButtonStyle.primary, emoji="⏪", row=0)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = self.ctx.voice_client
        
        if vc and (vc.is_playing() or vc.is_paused()):
            if self.discord_repository.actual_actions.get(self.ctx.guild.id) == 'bucle':
                await interaction.response.send_message("No se puede retroceder en modo bucle.", ephemeral=True)
                return
            if len(self.discord_repository.history.get(self.ctx.guild.id)) < 2:
                await interaction.response.send_message("No hay canciones para retroceder.", ephemeral=True)
                return
            await interaction.response.defer()
            self.discord_repository.actual_actions[self.ctx.guild.id] = 'back'
            vc.stop()
            self.logger.info(f"Canción retrocedida por {interaction.user}.")
            await interaction.response.send_message("Canción retrocedida.", ephemeral=True)
        else:
            await interaction.response.send_message("No hay nada que retroceder. El bot se desconectara.", ephemeral=True)
            await self.cog.cleanup(self.ctx.guild)

    @discord.ui.button(label="Saltar", style=discord.ButtonStyle.primary, emoji="⏭️", row=0)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = self.ctx.voice_client
        if vc and (vc.is_playing() or vc.is_paused()):
            if self.discord_repository.actual_actions.get(self.ctx.guild.id) == 'bucle':
                await interaction.response.send_message("No se puede saltar en modo bucle.", ephemeral=True)
                return
            await interaction.response.defer()
            self.discord_repository.actual_actions[self.ctx.guild.id] = 'skip'
            vc.stop()
            self.logger.info(f"Canción saltada por {interaction.user}.")
        else:
            await interaction.response.send_message("No hay nada que saltar. El bot se desconectara.", ephemeral=True)
            await self.cog.cleanup(self.ctx.guild)

    @discord.ui.button(label="Detener", style=discord.ButtonStyle.danger, emoji="⏹️", row=1)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.logger.info(f"Reproducción detenida por {interaction.user}.")
        vc = self.ctx.voice_client
        if vc:
            await vc.disconnect()
            await self.discord_repository.cleanup(self.ctx.guild)
        else:
            self.logger.warning("No hay un cliente de voz conectado.")
        await interaction.response.send_message("Música detenida y bot desconectado.", ephemeral=True)

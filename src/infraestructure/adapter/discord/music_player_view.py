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

    @discord.ui.button(label="Pausa", style=discord.ButtonStyle.secondary, custom_id="pause_resume", emoji="⏯️")
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

    @discord.ui.button(label="Retroceder", style=discord.ButtonStyle.primary, custom_id="back", emoji="⏪", disabled=True)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = self.ctx.voice_client
        if vc and (vc.is_playing() or vc.is_paused()):
            vc.stop()
            self.logger.info(f"Canción retrocedida por {interaction.user}.")
            await interaction.response.send_message("Canción retrocedida.", ephemeral=True)
        else:
            await interaction.response.send_message("No hay nada que retroceder. El bot se desconectara.", ephemeral=True)
            await self.cog.cleanup(self.ctx.guild)

    @discord.ui.button(label="Saltar", style=discord.ButtonStyle.primary, custom_id="skip", emoji="⏭️")
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = self.ctx.voice_client
        if vc and (vc.is_playing() or vc.is_paused()):
            await interaction.response.defer()
            vc.stop()
            self.logger.info(f"Canción saltada por {interaction.user}.")
        else:
            await interaction.response.send_message("No hay nada que saltar. El bot se desconectara.", ephemeral=True)
            await self.cog.cleanup(self.ctx.guild)

    @discord.ui.button(label="Detener", style=discord.ButtonStyle.danger, custom_id="stop", emoji="⏹️")
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.logger.info(f"Reproducción detenida por {interaction.user}.")
        await self.discord_repository.cleanup(self.ctx.guild)
        await interaction.response.send_message("Música detenida y bot desconectado.", ephemeral=True)

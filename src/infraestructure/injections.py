import logging
import discord
from dotenv import load_dotenv
from discord.ext import commands
from dependency_injector import containers, providers

load_dotenv()

def setup_logger():
    """Función para configurar y devolver una única instancia del logger."""
    # --- CORRECCIÓN CLAVE: Usa un nombre único para tu logger ---
    logger = logging.getLogger("MystoganBot") 
    # --------------------------------------------------------
    
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        file_handler = logging.FileHandler(filename='bot_music.log', encoding='utf-8', mode='w')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    return logger

def create_intents():
    """Crea y configura el objeto discord.Intents."""
    intents = discord.Intents.default()
    intents.message_content = True
    intents.voice_states = True
    return intents

class Container(containers.DeclarativeContainer):
    config = providers.Configuration()
    logger = providers.Singleton(setup_logger)
    intents = providers.Singleton(create_intents)
    bot = providers.Singleton(
        commands.Bot,
        command_prefix='!',
        intents=intents,
        help_command=None
    )
    session_repository = providers.Singleton(
        'src.infraestructure.discord.session.SessionRepository',
        logger=logger
    )
    youtube_music_provider = providers.Singleton(
        'src.infraestructure.music_providers.youtube.YouTubeMusicProviderRepository',
        bot=bot,
        discord_repository=session_repository,
        logger=logger
    )
    music_providers = providers.Dict({
        'youtube': youtube_music_provider
    })
    command_view = providers.Singleton(
        'src.infraestructure.adapter.discord.command_view.CommandView',
        bot=bot,
        music_provider=music_providers,
        discord_repository=session_repository,
        logger=logger
    )
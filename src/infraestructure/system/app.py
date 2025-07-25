import asyncio
from src.infraestructure.injections import Container

async def main():
    container = Container()
    container.wire(packages=["src.infraestructure"])

    container.config.BOT_DISCORD_TOKEN.from_env('BOT_DISCORD_TOKEN', required=True)
    
    bot = container.bot()
    logger = container.logger()
    command_view = container.command_view()
    
    logger.info("Contenedor inicializado. Iniciando bot...")
    
    @bot.event
    async def on_ready():
        logger.info(f'Bot {bot.user} está listo y conectado.')

    await bot.add_cog(command_view)
    await bot.start(container.config.BOT_DISCORD_TOKEN())

if __name__ == '__main__':
    asyncio.run(main())
import logging

# Configuración básica
logger = logging.getLogger('prueba')
logger.setLevel(logging.INFO)

# Formato
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Manejador de consola
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

# Manejador de archivo
file_handler = logging.FileHandler('test.log', mode='w')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Mensajes de prueba
logger.info("Este es un mensaje de prueba.")
logger.warning("Esta es una advertencia de prueba.")

print("Script de prueba de log finalizado.")
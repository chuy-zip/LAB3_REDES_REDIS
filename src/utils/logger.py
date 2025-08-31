import logging
import os
from datetime import datetime

def setup_logger(name, log_file=None, level=logging.INFO):
    """
    Configura y devuelve un logger con el nombre especificado.
    """
    # Crear el logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Evitar que los mensajes se propaguen al logger raíz
    logger.propagate = False
    
    # Limpiar handlers existentes
    if logger.handlers:
        logger.handlers = []
    
    # Formato para los mensajes de log (más visible)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Handler para consola con colores (opcional)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Handler para archivo (si se especifica)
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger
import logging

def setup_logger(name, log_filename, level=logging.ERROR):

    logger = logging.getLogger(name)
    logger.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    file_handler = logging.FileHandler(log_filename, mode='a')
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    return logger

meteo_logger = setup_logger('CustomSYNOPLogger', 'meteo_logs.log')
hydro_logger = setup_logger('CustomHydroLogger', 'hydro_logs.log')

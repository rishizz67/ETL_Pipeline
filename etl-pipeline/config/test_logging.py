
from logging_config import setup_logger

logger = setup_logger()

logger.info("ETL pipeline logging system initialized.")
logger.warning("This is a sample warning.")
logger.error("This is a sample error.")

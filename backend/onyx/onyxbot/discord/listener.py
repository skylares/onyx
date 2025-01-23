from onyx.context.search.retrieval.search_runner import download_nltk_data
from onyx.onyxbot.discord.discord_bot_handler import DiscordbotHandler
from onyx.utils.logger import setup_logger
from onyx.utils.variable_functionality import set_is_ee_based_on_env_variable

logger = setup_logger()

if __name__ == "__main__":
    logger.info("Starting DiscordbotHandler")
    tenant_handler = DiscordbotHandler()

    set_is_ee_based_on_env_variable()

    logger.info("Verifying query preprocessing (NLTK) data is downloaded")
    download_nltk_data()

    try:
        tenant_handler.run()
    except Exception:
        logger.exception("Fatal error in main thread")
        tenant_handler.shutdown(None, None)

import logging
from src.client import Client
from src.config import Config


def main():
    config = Config("./data/config.ini")
    logging.basicConfig(level=config.log_level_get(), format='%(asctime)s %(message)s')
    client = Client(config)
    client.start_processing()


if __name__ == "__main__":
    main()

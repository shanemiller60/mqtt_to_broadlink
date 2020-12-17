from src.client import Client
from src.config import Config


def main():
    config = Config("./data/config.ini")

    client = Client(config)
    client.connect()
    client.loop_forever()
    #client.test()


if __name__ == "__main__":
    main()

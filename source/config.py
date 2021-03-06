from typing import Optional
import os


class Config:
    SERVER_HOST: str
    SERVER_PORT: int

    DB_NAME: str
    DB_HOST: str
    DB_USER: str
    DB_PASSWORD: str

    TEMP_DB_NAME: str
    TEMP_DB_HOST: str
    TEMP_DB_USER: str
    TEMP_DB_PASSWORD: str

    DSN: str

    TOR_PROXIES: str

    FLIBUSTA_CHANNEL_HOST: str
    FLIBUSTA_CHANNEL_PORT: int

    @classmethod
    def configure(cls):
        cls.SERVER_HOST = os.environ.get('SERVER_HOST', 'localhost')
        cls.SERVER_PORT = os.environ.get('SERVER_PORT', 7770)

        cls.DB_NAME = os.environ.get('DB_NAME', 'flibusta')
        cls.DB_HOST = os.environ.get('DB_HOST', 'localhost')
        cls.DB_PORT = os.environ.get('DB_PORT', 5432)
        cls.DB_USER = os.environ.get('DB_USER', 'flibusta')
        cls.DB_PASSWORD = os.environ['DB_PASSWORD']

        cls.TEMP_DB_NAME = os.environ.get("TEMP_DB_NAME", "temp")
        cls.TEMP_DB_HOST = os.environ.get("TEMP_DB_HOST", "localhost")
        cls.TEMP_DB_USER = os.environ.get("TEMP_DB_USER", "root")
        cls.TEMP_DB_PASSWORD = os.environ["TEMP_DB_PASSWORD"]

        cls.FLIBUSTA_CHANNEL_HOST = os.environ.get('FLIBUSTA_CHANNEL_HOST', 'localhost')
        cls.FLIBUSTA_CHANNEL_PORT = os.environ.get('FLIBUSTA_CHANNEL_PORT', 7080)

        cls.DSN = f"postgresql://{cls.DB_HOST}:5432/{cls.DB_USER}"

        cls.TOR_PROXIES = os.environ.get('TOR_PROXIES', "http://localhost:8118")


Config.configure()

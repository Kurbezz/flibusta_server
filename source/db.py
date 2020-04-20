from typing import List, Optional, Type
import pathlib
from abc import ABC
from datetime import date
import asyncio

import asyncpg
from aiohttp import web

from config import Config as config


async def preapare_db(*args, **kwargs) -> asyncpg.pool.Pool:
    pool = await asyncpg.create_pool(user=config.DB_USER, password=config.DB_PASSWORD,
                                     database=config.DB_NAME, host=config.DB_HOST,
                                     port=config.DB_PORT)

    for _class in [AuthorAnnotationsBD, AuthorsBD, BookAnnotationsBD, BooksDB, 
                   SequenceBD, SequenceNameBD, TablesCreator]:  # type: Type[ConfigurableDB]
        _class.configurate(pool)

    await TablesCreator.create_tables()

    return pool


SQL_FOLDER = pathlib.Path("./sql")


class ConfigurableDB(ABC):
    pool: asyncpg.pool.Pool

    @classmethod
    def configurate(cls, pool: asyncpg.pool.Pool):
        cls.pool = pool


class TablesCreator(ConfigurableDB):
    CREATE_BOOK_TABLE = open(SQL_FOLDER / "create_book_table.sql").read().format(config.DB_USER)
    CREATE_AUTHOR_TABLE = open(SQL_FOLDER / "create_author_table.sql").read().format(config.DB_USER)
    CREATE_BOOK_AUTHOR_TABLE = open(SQL_FOLDER / "create_book_author_table.sql").read().format(config.DB_USER)
    CREATE_SEQUENCE_NAME_TABLE = open(SQL_FOLDER / "create_sequence_name_table.sql").read().format(config.DB_USER)
    CREATE_SEQUENCE_TABLE = open(SQL_FOLDER / "create_sequence_table.sql").read().format(config.DB_USER)
    CREATE_BOOK_ANNOTATION_TABLE = open(SQL_FOLDER / "create_book_annotation_table.sql").read().format(config.DB_USER)
    CREATE_AUTHOR_ANNOTATION_TABLE = open(
        SQL_FOLDER / "create_author_annotation_table.sql").read().format(config.DB_USER)

    @classmethod
    async def create_tables(cls):
        await cls.pool.execute(cls.CREATE_BOOK_TABLE)
        await cls.pool.execute(cls.CREATE_AUTHOR_TABLE)
        await cls.pool.execute(cls.CREATE_BOOK_AUTHOR_TABLE)
        await cls.pool.execute(cls.CREATE_SEQUENCE_NAME_TABLE)
        await cls.pool.execute(cls.CREATE_SEQUENCE_TABLE)
        await cls.pool.execute(cls.CREATE_BOOK_ANNOTATION_TABLE)
        await cls.pool.execute(cls.CREATE_AUTHOR_ANNOTATION_TABLE)


class BooksDB(ConfigurableDB):
    BOOK_BY_ID = open(SQL_FOLDER / "book_by_id.sql").read()
    BOOK_SEARCH = open(SQL_FOLDER / "book_search.sql").read()
    BOOK_RANDOM = open(SQL_FOLDER / "book_random.sql").read()
    BOOK_UPDATE_LOG_RANGE = open(SQL_FOLDER / "book_update_log_range.sql").read()

    @classmethod
    async def by_id(cls, book_id: int):
        async with cls.pool.acquire() as conn:  # type: asyncpg.Connection
            result = await conn.fetch(cls.BOOK_BY_ID, book_id)
            return result[0]["json_build_object"] if result else None

    @classmethod
    async def search(cls, query: str, allowed_langs: List[str], limit: int, page: int) -> str:
        return (await cls.pool.fetch(cls.BOOK_SEARCH, allowed_langs, query, limit, limit * (page - 1)))[0]["json"]

    @classmethod
    async def random(cls, allowed_langs: List[str]):
        return (await cls.pool.fetch(cls.BOOK_RANDOM, allowed_langs))[0]["json"]

    @classmethod
    async def update_log_range(cls, start_date: date, end_date: date, allowed_langs: List[str], limit: int, page: int) -> str:
        return (await cls.pool.fetch(cls.BOOK_UPDATE_LOG_RANGE, allowed_langs, start_date, end_date,
                                     limit, limit * (page - 1)))[0]["json"]


class AuthorsBD(ConfigurableDB):
    AUTHOR_BY_ID = open(SQL_FOLDER / "author_by_id.sql").read()
    AUTHOR_SEARCH = open(SQL_FOLDER / "author_search.sql").read()
    AUTHOR_RANDOM = open(SQL_FOLDER / "author_random.sql").read()

    @classmethod
    async def by_id(cls, author_id: int, allowed_langs: List[str], limit: int, page: int) -> str:
        return (await cls.pool.fetch(cls.AUTHOR_BY_ID, allowed_langs, author_id, limit, limit * (page - 1)))[0]["json"]

    @classmethod
    async def search(cls, query: str, allowed_langs: List[str], limit: int, page: int) -> str:
        return (await cls.pool.fetch(cls.AUTHOR_SEARCH, query, 
                                     allowed_langs,limit, limit * (page - 1)))[0]["json"]

    @classmethod
    async def random(cls, allowed_langs: List[str]):
        return (await cls.pool.fetch(cls.AUTHOR_RANDOM, allowed_langs))[0]["json"]


class SequenceNameBD(ConfigurableDB):
    SEQUENCENAME_BY_ID = open(SQL_FOLDER / "sequencename_by_id.sql").read()
    SEQUENCENAME_SEARCH = open(SQL_FOLDER / "sequencename_search.sql").read()
    SEQUENCENAME_RANDOM = open(SQL_FOLDER / "sequencename_random.sql").read()

    @classmethod
    async def by_id(cls, allowed_langs, seq_id: int, limit: int, page: int) -> str:
        return (await cls.pool.fetch(cls.SEQUENCENAME_BY_ID, allowed_langs, seq_id, limit, 
                                     limit * (page - 1)))[0]["json"]

    @classmethod
    async def search(cls, allowed_langs, query: str, limit: int, page: int):
        return (await cls.pool.fetch(cls.SEQUENCENAME_SEARCH, query, allowed_langs, limit, 
                                     limit * (page - 1)))[0]["json"]

    @classmethod
    async def random(cls, allowed_langs: List[str]):
        return (await cls.pool.fetch(cls.SEQUENCENAME_RANDOM, allowed_langs))[0]["json_build_object"]


class SequenceBD(ConfigurableDB):
    SEQUENCE_BY_BOOK_ID = open(SQL_FOLDER / "sequence_by_book_id.sql").read()

    @classmethod
    async def by_book_id(cls, book_id: int):
        async with cls.pool.acquire() as conn:  # type: asyncpg.Connection
            result = (await conn.fetch(cls.SEQUENCE_BY_BOOK_ID, book_id))[0]
            return result["array_agg"] if result["array_agg"] else []


class BookAnnotationsBD(ConfigurableDB):
    BOOK_ANNOTATION_BY_ID = open(SQL_FOLDER / "book_annotation_by_id.sql").read()

    @classmethod
    async def by_id(cls, book_id: int):
        async with cls.pool.acquire() as conn:  # type: asyncpg.Connection
            result = (await conn.fetch(cls.BOOK_ANNOTATION_BY_ID, book_id))
            return result[0]["json_build_object"] if result else None


class AuthorAnnotationsBD(ConfigurableDB):
    AUTHOR_ANNOTATION_BY_ID = open(SQL_FOLDER / "author_annotation_by_id.sql").read()

    @classmethod
    async def by_id(cls, author_id: int):
        async with cls.pool.acquire() as conn:  # type: asyncpg.Connection
            result = (await conn.fetch(cls.AUTHOR_ANNOTATION_BY_ID, author_id))
            return result[0]["json_build_object"] if result else None

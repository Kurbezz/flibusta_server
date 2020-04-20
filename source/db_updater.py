from typing import Set

import asyncio
import gzip
import os
import platform

import pymysql
import aiomysql
import aiohttp
from aioify import aioify
import asyncpg

from db import preapare_db

from typing import Optional
import os


class Config:
    DB_NAME: str
    DB_HOST: str
    DB_USER: str
    DB_PASSWORD: str

    TEMP_DB_NAME: str
    TEMP_DB_HOST: str
    TEMP_DB_USER: str
    TEMP_DB_PASSWORD: str

    @classmethod
    def configure(cls):
        cls.DB_NAME = os.environ.get('DB_NAME', 'flibusta')
        cls.DB_HOST = os.environ.get('DB_HOST', 'localhost')
        cls.DB_USER = os.environ.get('DB_USER', 'flibusta')
        cls.DB_PASSWORD = os.environ['DB_PASSWORD']

        cls.TEMP_DB_NAME = os.environ.get("TEMP_DB_NAME", "temp")
        cls.TEMP_DB_HOST = os.environ.get("TEMP_DB_HOST", "127.0.0.1")
        cls.TEMP_DB_USER = os.environ.get("TEMP_DB_USER", "root")
        cls.TEMP_DB_PASSWORD = os.environ["TEMP_DB_PASSWORD"]


Config.configure()


files = ['lib.libavtor.sql',
         'lib.libbook.sql',
         'lib.libavtorname.sql',
         'lib.libtranslator.sql',
         'lib.libseqname.sql',
         'lib.libseq.sql',
         'lib.b.annotations.sql',
         'lib.b.annotations_pics.sql',
         'lib.a.annotations.sql',
         'lib.a.annotations_pics.sql']


decompress = aioify(gzip.decompress)


async def run(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()


async def processing_file(file_: str):
    print(f"Process file {file_}...")
    await run(f"wget -O - http://flibusta.is/sql/{file_}.gz | gunzip | mysql -h {Config.TEMP_DB_HOST} -u {Config.TEMP_DB_USER} -p\"{Config.TEMP_DB_PASSWORD}\" {Config.TEMP_DB_NAME}")
    print(f"{file_} processed!")


async def clean_authors(pool):
    await clean_translators(pool)

    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            print("Clean author")
            await cursor.execute(
                "DELETE FROM temp.libavtorname WHERE AvtorId NOT IN (SELECT AvtorId FROM temp.libavtor) AND "
                "AvtorId NOT IN (SELECT TranslatorId FROM temp.libtranslator);"
            )

    await asyncio.gather(
        clean_author_annotations(pool),
        clean_author_annotations_pics(pool)
    )


async def clean_translators(pool):
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            print("Clean translator")
            await cursor.execute(
                "DELETE FROM temp.libtranslator WHERE BookId NOT IN (SELECT BookId FROM temp.libbook);"
            )


async def clean_book_authors(pool):
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            print("Clean book-author")
            await cursor.execute(
                "DELETE FROM temp.libavtor WHERE BookId NOT IN (SELECT BookId FROM temp.libbook);"
            )
    await clean_authors(pool)


async def clean_sequence_names(pool):
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            print("Clean sequence names")
            await cursor.execute(
                "DELETE FROM temp.libseqname WHERE SeqId NOT IN (SELECT SeqId FROM temp.libseq);"
            )


async def clean_sequence(pool):
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                "DELETE FROM temp.libseq WHERE BookId NOT IN (SELECT BookId FROM temp.libbook);"
            )
    await clean_sequence_names(pool)
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                "DELETE FROM temp.libseq WHERE SeqId NOT IN (SELECT SeqId FROM temp.libseqname);"
            )


async def clean_book_annotations(pool):
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            print("Clean book annotations")
            try:
                await cursor.execute(
                    "DELETE FROM temp.libbannotations WHERE BookId NOT IN (SELECT BookId FROM temp.libbook);"
                )
            except aiomysql.ProgrammingError as e:
                print(e)


async def clean_book_annotations_pics(pool):
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            print("Clean book annotations pics")
            try:
                await cursor.execute(
                    "DELETE FROM temp.libbpics WHERE BookId NOT IN (SELECT BookId FROM temp.libbook);"
                )
            except aiomysql.ProgrammingError as e:
                print(e)


async def clean_author_annotations(pool):
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            print("Clean author annotations")
            try:
                await cursor.execute(
                    "DELETE FROM temp.libaannotations WHERE AvtorId NOT IN (SELECT AvtorId FROM temp.libavtorname);"
                )
            except aiomysql.ProgrammingError as e:
                print(e)


async def clean_author_annotations_pics(pool):
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            print("Clean author annotations pics")
            try:
                await cursor.execute(
                    "DELETE FROM temp.libapics WHERE AvtorId NOT IN (SELECT AvtorId FROM temp.libavtorname);"
                )
            except aiomysql.ProgrammingError as e:
                print(e)


async def clean(pool):
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            print("Clean books")
            await cursor.execute(
                "DELETE FROM temp.libbook WHERE Deleted<>0 OR (Lang<>'ru' AND Lang<>'uk' AND Lang<>'be')"
                "OR (FileType<>'djvu' AND FileType<>'pdf' AND FileType<>'doc' AND FileType<>'fb2'"
                "AND FileType<>'epub' AND FileType<>'mobi');")
    await asyncio.gather(
        clean_book_authors(pool),
        clean_sequence(pool),
        clean_book_annotations(pool),
        clean_book_annotations_pics(pool)
    )


def remove_wrong_ch(s: str):
        return s.replace(";", "").replace("\n", " ")

def remove_dots(s: str):
    return s.replace('.', '')


books_updated = False
authors_updated = False
sequences_updated = False


async def update_books(mysql_pool, postgres_pool):
    print("Getting books...")
    async with mysql_pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("SELECT BookId, Title, Lang, FileType, Time FROM temp.libbook;")
            result = await cursor.fetchall()
    print("Books has get!")

    print("Update books...")
    await postgres_pool.executemany(
        "INSERT INTO book (id, title, lang, file_type, search_content, uploaded) VALUES ($1, cast($2 as varchar), $3, $4, to_tsvector($2), $5) "
        "ON CONFLICT (id) DO UPDATE SET title = EXCLUDED.title, lang = EXCLUDED.lang, file_type = EXCLUDED.file_type, search_content = EXCLUDED.search_content, uploaded = EXCLUDED.uploaded",
        [(r[0], remove_wrong_ch(remove_dots(r[1])), remove_wrong_ch(remove_dots(r[2])), remove_wrong_ch(r[3]), r[4]) for r in result]
    )
    print("Books updated!")

    global books_updated
    books_updated = True
    await update_book_annotations(mysql_pool, postgres_pool)

    await postgres_pool.execute("REINDEX TABLE book;")


async def update_translators(mysql_pool, postgres_pool):
    while not authors_updated or not books_updated:
        await asyncio.sleep(.5)

    print("Getting translators...")
    async with mysql_pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("SELECT BookId, TranslatorId, Pos FROM temp.libtranslator;")
            result = await cursor.fetchall()
    print("Translators has get!")

    print("Updating translators...")
    await postgres_pool.executemany(
        "INSERT INTO translator (book_id, translator_id, pos) VALUES ($1, $2, $3) "
        "ON CONFLICT (book_id, translator_id) DO UPDATE SET pos = EXCLUDED.pos",
        [(r[0], r[1], r[2]) for r in result]
    )
    print("Translators updated!")


async def update_authors(mysql_pool, postgres_pool):
    print("Getting authors...")
    async with mysql_pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("SELECT AvtorId, FirstName, MiddleName, LastName FROM temp.libavtorname;")
            result = await cursor.fetchall()
    print("Authors has get!")

    print("Update authors...")
    await postgres_pool.executemany(
        "INSERT INTO author (id, first_name, middle_name, last_name, search_content) VALUES ($1, $2, $3, $4, to_tsvector($5)) "
        "ON CONFLICT (id) DO UPDATE SET first_name = EXCLUDED.first_name, middle_name = EXCLUDED.middle_name, last_name = EXCLUDED.last_name, search_content = EXCLUDED.search_content",
        [(
            r[0], remove_dots(remove_wrong_ch(r[1])), 
            remove_dots(remove_wrong_ch(r[2])), 
            remove_dots(remove_wrong_ch(r[3])), 
            " ".join([remove_dots(remove_wrong_ch(r[1])), remove_dots(remove_wrong_ch(r[2])), remove_dots(remove_wrong_ch(r[3]))])) for r in result]
    )
    print("Authors updated!")

    global authors_updated
    authors_updated = True

    await update_author_annotations(mysql_pool, postgres_pool)

    await postgres_pool.execute("REINDEX TABLE author;")


async def update_book_author(mysql_pool, postgres_pool):
    while not books_updated or not authors_updated:
        await asyncio.sleep(.5)

    print("Getting book-author links...")
    async with mysql_pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("SELECT BookId, AvtorId FROM temp.libavtor;")
            result = await cursor.fetchall()
    print("Book-author links has get!")

    print("Update book authors...")
    await postgres_pool.executemany(
        "INSERT INTO bookauthor (book_id, author_id) VALUES ($1, $2) "
        "ON CONFLICT (book_id, author_id) DO NOTHING",
        [(r[0], r[1]) for r in result]
    )
    print("Book authors updated!")

    await postgres_pool.execute("REINDEX TABLE bookauthor;")


async def update_sequence(mysql_pool, postgres_pool):
    while not books_updated or not sequences_updated:
            await asyncio.sleep(1)

    print("Getting sequences...")
    async with mysql_pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("SELECT BookId, SeqId, SeqNumb FROM temp.libseq;")
            result = await cursor.fetchall()
    print("Sequences has get!")

    print("Update sequence...")
    await postgres_pool.executemany(
        "INSERT INTO seq (book_id, seq_id, num) VALUES ($1, $2, $3)"
        "ON CONFLICT (book_id, seq_id) DO NOTHING",
        [(r[0], r[1], r[2]) for r in result]
    )
    print("Sequence updated!")

    await postgres_pool.execute("REINDEX TABLE seq;")

async def update_sequence_names(mysql_pool, postgres_pool):
    print("Getting sequence names...")
    async with mysql_pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("SELECT SeqId, SeqName FROM temp.libseqname;")
            result = await cursor.fetchall()
    print("Sequence names has get!")

    print("Update sequence names...")
    await postgres_pool.executemany(
        "INSERT INTO seqname (seq_id, name, search_content) VALUES ($1, cast($2 as varchar), to_tsvector($2)) "
        "ON CONFLICT (seq_id) DO UPDATE SET name = EXCLUDED.name, search_content = EXCLUDED.search_content",
        [(r[0], r[1]) for r in result]
    )
    print("Sequence names updated!")

    global sequences_updated
    sequences_updated = True

    await postgres_pool.execute("REINDEX TABLE seqname;")


async def update_book_annotations(mysql_pool, postgres_pool):
    try:
        print("Getting book annotations...")
        async with mysql_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT BookId, Title, Body FROM temp.libbannotations;")
                result = await cursor.fetchall()
        print("Book annotations has get!")

        print("Update book annotations...")
        await postgres_pool.executemany(
            "INSERT INTO book_annotation (book_id, title, body) VALUES ($1, cast($2 as varchar), cast($3 as varchar)) "
            "ON CONFLICT (book_id) DO UPDATE SET title = EXCLUDED.title, body = EXCLUDED.body",
            [(r[0], r[1], r[2]) for r in result]
        )
        print("Book annotations updated!")

        await postgres_pool.execute("REINDEX TABLE book_annotation;")
    except aiomysql.ProgrammingError as e:
        print(e)

    await update_book_annotations_pics(mysql_pool, postgres_pool)


async def update_book_annotations_pics(mysql_pool, postgres_pool):
    try:
        print("Getting book annotation pics...")
        async with mysql_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT BookId, File FROM temp.libbpics;")
                result = await cursor.fetchall()
        print("Book annotation pics has get!")

        print("Update book annotations pics...")
        await postgres_pool.executemany(
            "UPDATE book_annotation SET file = cast($2 as varchar) WHERE book_id = $1",
            [(r[0], r[1]) for r in result]
        )
        print("Book annotations pics updated!")
    except aiomysql.ProgrammingError as e:
        print(e)


async def update_author_annotations(mysql_pool, postgres_pool):
    try:
        print("Getting author annotations...")
        async with mysql_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT AvtorId, Title, Body FROM temp.libaannotations;")
                result = await cursor.fetchall()
        print("Author annotations has get!")

        print("Update author annotations...")
        await postgres_pool.executemany(
            "INSERT INTO author_annotation (author_id, title, body) VALUES ($1, cast($2 as varchar), cast($3 as varchar)) "
            "ON CONFLICT (author_id) DO UPDATE SET title = EXCLUDED.title, body = EXCLUDED.body",
            [(r[0], r[1], r[2]) for r in result]
        )
        print("Author annotations updated!")

        await update_author_annotations_pics(mysql_pool, postgres_pool)
    except aiomysql.ProgrammingError as e:
        print(e)

    await postgres_pool.execute("REINDEX TABLE author_annotation;")


async def update_author_annotations_pics(mysql_pool, postgres_pool):
    try:
        print("Getting author annotation pics...")
        async with mysql_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT AvtorId, File FROM temp.libapics;")
                result = await cursor.fetchall()
        print("Author annotations pics has get!")

        print("Update author annotations pics...")
        await postgres_pool.executemany(
            "UPDATE author_annotation SET file = cast($2 as varchar) WHERE author_id = $1",
            [(r[0], r[1]) for r in result]
        )
        print("Author annotations pics updated!")
    except aiomysql.ProgrammingError as e:
        print(e)


async def update(mysql_pool, postgres_pool):
    await asyncio.gather(
        update_books(mysql_pool, postgres_pool),
        update_authors(mysql_pool, postgres_pool),
        update_translators(mysql_pool, postgres_pool),
        update_sequence_names(mysql_pool, postgres_pool),
        update_book_author(mysql_pool, postgres_pool),
        update_sequence(mysql_pool, postgres_pool)
    )


async def delete_books(postgres_pool: asyncpg.pool.Pool, books_ids_to_delete: Set[int]):
    await asyncio.gather(
        postgres_pool.executemany(
            "DELETE FROM bookauthor WHERE book_id = $1", [(x, ) for x in books_ids_to_delete]
        ),
        postgres_pool.executemany(
            "DELETE FROM seq WHERE book_id = $1", [(x, ) for x in books_ids_to_delete]
        ),
        postgres_pool.executemany(
            "DELETE FROM book_annotation WHERE book_id = $1", [(x, ) for x in books_ids_to_delete]
        ),
        postgres_pool.executemany(
            "DELETE FROM translator WHERE book_id = $1", [(x, ) for x in books_ids_to_delete]
        )
    )
    await postgres_pool.executemany(
        "DELETE FROM book WHERE id = $1", [(x, ) for x in books_ids_to_delete]
    )


async def postgres_clean_books(mysql_pool: aiomysql.Pool, postgres_pool: asyncpg.pool.Pool):
    async with mysql_pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("SELECT BookId FROM temp.libbook")
            mysql_books_ids = set([x[0] for x in (await cursor.fetchall())])
    postgres_books_ids = set([x["id"] for x in (await postgres_pool.fetch("SELECT id FROM book"))])

    books_ids_to_delete = postgres_books_ids - mysql_books_ids
    await delete_books(postgres_pool, books_ids_to_delete)


async def delete_authors(postgres_pool: asyncpg.pool.Pool, authors_ids_to_delete: Set[int]):
    await asyncio.gather(
        postgres_pool.executemany(
            "DELETE FROM bookauthor WHERE author_id = $1", [(x, ) for x in authors_ids_to_delete]
        ),
        postgres_pool.executemany(
            "DELETE FROM author_annotation WHERE author_id = $1", [(x, ) for x in authors_ids_to_delete]
        ),
        postgres_pool.executemany(
            "DELETE FROM translator WHERE translator_id = $1", [(x, ) for x in authors_ids_to_delete]
        )
    )
    await postgres_pool.executemany(
        "DELETE FROM author WHERE id = $1", [(x, ) for x in authors_ids_to_delete]
    )


async def postgres_clean_authors(mysql_pool: aiomysql.Pool, postgres_pool: asyncpg.pool.Pool):
    async with mysql_pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("SELECT AvtorId from temp.libavtor")
            mysql_authors_ids = set([x[0] for x in (await cursor.fetchall())])
    postgres_authors_ids = set([x["id"] for x in (await postgres_pool.fetch("SELECT id FROM author"))])

    authors_ids_to_delete = postgres_authors_ids - mysql_authors_ids
    await delete_authors(postgres_pool, authors_ids_to_delete)


async def delete_seqs(postgres_pool: asyncpg.pool.Pool, seqs_ids_to_delete: Set[int]):
    await postgres_pool.executemany(
        "DELETE FROM seq WHERE seq_id = $1", [(x, ) for x in seqs_ids_to_delete]
    )
    await postgres_pool.executemany(
        "DELETE FROM seqname WHERE seq_id = $1", [(x, ) for x in seqs_ids_to_delete]
    )


async def postgres_clean_sequences(mysql_pool: aiomysql.Pool, postgres_pool: asyncpg.pool.Pool):
    async with mysql_pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("SELECT SeqId FROM temp.libseqname")
            mysql_seqs_ids = set([x[0] for x in (await cursor.fetchall())])
    postgres_seqs_ids = set([x["seq_id"] for x in (await postgres_pool.fetch("SELECT seq_id FROM seqname"))])

    seqs_ids_to_delete = postgres_seqs_ids - mysql_seqs_ids
    await delete_seqs(postgres_pool, seqs_ids_to_delete)


async def clean_postgres(mysql_pool, postgres_pool):
    await asyncio.gather(
        postgres_clean_books(mysql_pool, postgres_pool),
        postgres_clean_authors(mysql_pool, postgres_pool),
        postgres_clean_sequences(mysql_pool, postgres_pool)
    )


async def main():
    loop = asyncio.get_event_loop()

    pool = await aiomysql.create_pool(
        host=Config.TEMP_DB_HOST,
        port=3306,
        user=Config.TEMP_DB_USER,
        password=Config.TEMP_DB_PASSWORD,
        loop=loop
    )

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                await cur.execute("DROP DATABASE temp;")
            except pymysql.err.InternalError:
                pass
    
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("CREATE DATABASE temp;")
            print("Create temp database...")

    pool.close()
    await pool.wait_closed()

    await asyncio.gather(*[processing_file(file_) for file_ in files])

    mysql_pool = await aiomysql.create_pool(
        host=Config.TEMP_DB_HOST,
        port=3306,
        user=Config.TEMP_DB_USER,
        db=Config.TEMP_DB_NAME,
        password=Config.TEMP_DB_PASSWORD,
        loop=loop
    )

    postgres_pool = await asyncpg.create_pool(
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        host=Config.DB_HOST,
        min_size=10,
        max_size=25
    )

    await preapare_db()

    await clean(mysql_pool)

    await update(mysql_pool, postgres_pool)
    await clean_postgres(mysql_pool, postgres_pool)


if __name__ == "__main__":
    if platform.system() == "Linux":
        try:
            import uvloop

            uvloop.install()
        except ImportError:
            print("Install uvloop for best speed!")

    asyncio.run(main())

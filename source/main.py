import ujson as json
from datetime import date
import asyncio
from aiohttp.web_response import json_response
from aiohttp import web

from db import BooksDB, AuthorsBD, AuthorAnnotationsBD, BookAnnotationsBD, SequenceBD, SequenceNameBD, preapare_db, DownloadDB
from config import Config as config
from utils import get_filename, download, download_image


class BookHandler:
    @staticmethod
    async def by_id(request: web.Request):
        id_ = request.match_info.get("id", None)
        if id_ is None:
            raise web.HTTPBadRequest
        response = await BooksDB.by_id(int(id_))
        if not response:
            raise web.HTTPNoContent
        return json_response(body=response)

    @staticmethod
    async def search(request: web.Request):
        query = request.match_info.get("query", None)
        allowed_langs = request.match_info.get("allowed_langs", None)
        limit = request.match_info.get("limit", None)
        page = request.match_info.get("page", None)
        if None in [query, allowed_langs, limit, page]:
            raise web.HTTPBadRequest
        response = await BooksDB.search(query, json.loads(allowed_langs),
                                        int(limit), int(page))
        if not response:
            raise web.HTTPNoContent
        return json_response(body=response.encode())

    @staticmethod
    async def random(request: web.Request):
        allowed_langs = request.match_info.get("allowed_langs", None)
        if not allowed_langs:
            raise web.HTTPBadRequest
        response = await BooksDB.random(json.loads(allowed_langs))
        if not response:
            raise web.HTTPNoContent
        return json_response(body=response)

    @staticmethod
    async def download(request: web.Request):
        # ToDO: try download from telegram if book exists in channel
        book_id = request.match_info.get("id", None)
        file_type = request.match_info.get("type", None)
        if book_id is None and file_type is None:
            raise web.HTTPBadRequest

        book = json.loads(await BooksDB.by_id(int(book_id)))

        if not book:
            raise web.HTTPNoContent

        book_bytes = await download(book_id, file_type)
        if not book_bytes:
            raise web.HTTPNoContent
        response = web.Response(body=book_bytes)
        filename = await get_filename(book, file_type)
        response.headers.add("Content-Disposition",
                             f"attachment; filename={filename}")
        return response

    @staticmethod
    async def update_log_range(request: web.Request):
        request_start_date = request.match_info.get("start_date", None)
        request_end_date = request.match_info.get("end_date", None)
        allowed_langs = request.match_info.get("allowed_langs", None)
        limit = request.match_info.get("limit", None)
        page = request.match_info.get("page", None)
        if None in [request_start_date, request_end_date, allowed_langs, limit, page]:
            raise web.HTTPBadRequest

        try:
            request_start_date = date.fromisoformat(request_start_date)
            request_end_date = date.fromisoformat(request_end_date)
        except ValueError:
            raise web.HTTPBadRequest

        response = await BooksDB.update_log_range(request_start_date, request_end_date, 
                                                  json.loads(allowed_langs), int(limit), int(page))
        if not response:
            raise web.HTTPNoContent
        return json_response(body=response.encode())


class AuthorHandler:
    @staticmethod
    async def by_id(request: web.Request):
        id_ = request.match_info.get("id", None)
        allowed_langs = request.match_info.get("allowed_langs", None)
        limit = request.match_info.get("limit", None)
        page = request.match_info.get("page", None)
        if None in [id_, allowed_langs, limit, page]:
            raise web.HTTPBadRequest
        response = await AuthorsBD.by_id(int(id_), json.loads(allowed_langs), int(limit), int(page))
        return json_response(body=response.encode())

    @staticmethod
    async def search(request: web.Request):
        query = request.match_info.get("query", None)
        allowed_langs = request.match_info.get("allowed_langs", None)
        limit = request.match_info.get("limit", None)
        page = request.match_info.get("page", None)
        if None in [query, allowed_langs, limit, page]:
            raise web.HTTPBadRequest
        response = await AuthorsBD.search(query, json.loads(allowed_langs),
                                          int(limit), int(page))
        return json_response(body=response.encode())

    @staticmethod
    async def random(request: web.Request):
        allowed_langs = request.match_info.get("allowed_langs", None)
        if allowed_langs is None:
            raise web.HTTPBadRequest
        response = await AuthorsBD.random(json.loads(allowed_langs))
        if not response:
            raise web.HTTPNoContent
        return json_response(body=response)


class SequenceHandler:
    @staticmethod
    async def by_id(request: web.Request):
        id_ = request.match_info.get("id", None)
        allowed_langs = request.match_info.get("allowed_langs", None)
        limit = request.match_info.get("limit", None)
        page = request.match_info.get("page", None)
        if None in [id_, allowed_langs, limit, page]:
            raise web.HTTPBadRequest
        response = await SequenceNameBD.by_id(json.loads(allowed_langs), int(id_), int(limit), int(page))
        if not response:
            raise web.HTTPNoContent
        return json_response(body=response.encode())

    @staticmethod
    async def search(request: web.Request):
        query = request.match_info.get("query", None)
        allowed_langs = request.match_info.get("allowed_langs", None)
        limit = request.match_info.get("limit", None)
        page = request.match_info.get("page", None)
        if None in [query, allowed_langs, limit, page]:
            raise web.HTTPBadRequest
        response = await SequenceNameBD.search(json.loads(allowed_langs), query, int(limit), int(page))
        if not response:
            raise web.HTTPNoContent
        return json_response(body=response)

    @staticmethod
    async def random(request: web.Request):
        allowed_langs = request.match_info.get("allowed_langs", None)
        if allowed_langs is None:
            raise web.HTTPBadRequest
        response = await SequenceNameBD.random(json.loads(allowed_langs))
        if not response:
            raise web.HTTPNoContent
        return json_response(body=response)


class BookAnnotationHandler:
    @staticmethod
    async def by_id(request: web.Request):
        id_ = request.match_info.get("id", None)
        if id_ is None:
            raise web.HTTPBadRequest
        response = await BookAnnotationsBD.by_id(int(id_))
        if not response:
            raise web.HTTPNoContent
        return json_response(body=response)

    @staticmethod
    async def image(request: web.Request):
        id_ = request.match_info.get("id", None)
        if id_ is None:
            raise web.HTTPBadRequest
        response = await BookAnnotationsBD.by_id(int(id_))
        if not response:
            raise web.HTTPNoContent
        path = json.loads(response)['file']
        if path == None:
            raise web.HTTPNoContent
        image = await download_image("book", path)
        if not image:
            raise web.HTTPNoContent
        result = web.Response(body=image)
        result.headers.add("Content-Type", "image/png")
        return result


class AuthorAnnotationHandler:
    @staticmethod
    async def by_id(request: web.Request):
        id_ = request.match_info.get("id", None)
        if id_ is None:
            raise web.HTTPBadRequest
        response = await AuthorAnnotationsBD.by_id(int(id_))
        if not response:
            raise web.HTTPNoContent
        return json_response(body=response)

    @staticmethod
    async def image(request: web.Request):
        id_ = request.match_info.get("id", None)
        if id_ is None:
            raise web.HTTPBadRequest
        response = await AuthorAnnotationsBD.by_id(int(id_))
        if not response:
            raise web.HTTPNoContent
        path = json.loads(response)['file']
        if path == None:
            raise web.HTTPNoContent
        image = await download_image("author", path)
        if not image:
            raise web.HTTPNoContent
        result = web.Response(body=image)
        result.headers.add("Content-Type", "image/png")
        return result


class DownloadCounterHandler:
    @staticmethod
    async def update(request: web.Request):
        book_id = request.match_info.get("book_id", None)
        user_id = request.match_info.get("user_id", None)

        if book_id is None or user_id is None:
            raise web.HTTPBadRequest

        await DownloadDB.update(int(book_id), int(user_id))
        return web.Response()

    @staticmethod
    async def get_top_n(request: web.Request):
        pass


if __name__ == "__main__":
    import platform

    if platform.system() == "Linux":
        try:
            import uvloop

            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
            print("Use uvloop!")
        except ImportError:
            print("Install uvloop for best speed!")

    app = web.Application()

    app.on_startup.append(preapare_db)

    app.add_routes((
        web.get("/book/{id}", BookHandler.by_id),
        web.get("/book/search/{allowed_langs}/{limit}/{page}/{query}", BookHandler.search),
        web.get("/book/download/{id}/{type}", BookHandler.download),
        web.get("/book/random/{allowed_langs}", BookHandler.random),
        web.get("/book/update_log_range/{start_date}/{end_date}/{allowed_langs}/{limit}/{page}", 
                BookHandler.update_log_range),
        web.get("/author/search/{allowed_langs}/{limit}/{page}/{query}", AuthorHandler.search),
        web.get("/author/{id}/{allowed_langs}/{limit}/{page}", AuthorHandler.by_id),
        web.get("/author/random/{allowed_langs}", AuthorHandler.random),
        web.get("/sequence/{id}/{allowed_langs}/{limit}/{page}", SequenceHandler.by_id),
        web.get("/sequence/search/{allowed_langs}/{limit}/{page}/{query}", SequenceHandler.search),
        web.get("/sequence/random/{allowed_langs}", SequenceHandler.random),
        web.get("/annotation/book/{id}", BookAnnotationHandler.by_id),
        web.get("/annotation/book/image/{id}", BookAnnotationHandler.image),
        web.get("/annotation/author/{id}", AuthorAnnotationHandler.by_id),
        web.get("/annotation/author/image/{id}", AuthorAnnotationHandler.image),
        web.get("/download_counter/update/{book_id}/{user_id}", DownloadCounterHandler.update),
        web.get("/download_counter/get_top_n/{n}/{allowed_langs}/{start_date}/{end_date}", 
                DownloadCounterHandler.get_top_n)
    ))

    web.run_app(app, host=config.SERVER_HOST, port=config.SERVER_PORT)

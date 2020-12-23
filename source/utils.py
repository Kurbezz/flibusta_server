from typing import Optional
import zipfile
import io
import asyncio
from aiohttp import ClientTimeout
import concurrent

import transliterate as transliterate
import aiohttp

from config import Config
from exceptions import *


process_pool_executor = concurrent.futures.ProcessPoolExecutor(2)


def get_short_name(author) -> str:
    temp = ''
    if author['last_name']:
        temp += author['last_name']
    if author['first_name']:
        if temp:
            temp += " "
        temp += author['first_name'][0]
    if author['middle_name']:
        if temp:
            temp += " "
        temp += author['middle_name'][0]
    return temp


async def get_filename(book, file_type: str) -> str:
    filename = '_'.join([get_short_name(a) for a in book["authors"]]) + '_-_' if book["authors"] else ''
    filename += book["title"] if book["title"][-1] != ' ' else book["title"][:-1]
    filename = transliterate.translit(filename, 'ru', reversed=True)

    for c in "(),….’!\"?»«':":
        filename = filename.replace(c, '')

    for c, r in (('—', '-'), ('/', '_'), ('№', 'N'), (' ', '_'), ('–', '-'), ('á', 'a'), (' ', '_')):
        filename = filename.replace(c, r)

    return filename + '.' + file_type


def unzip(file_bytes: bytes, file_type: str):
    zip_file = zipfile.ZipFile(io.BytesIO(file_bytes))
    for name in zip_file.namelist():  # type: str
        if file_type in name.lower():
            return zip_file.read(name)
    raise FileNotFoundError


def zip_file(filename, content):
    buffer = io.BytesIO()
    zip_file = zipfile.ZipFile(buffer, 'w', zipfile.ZIP_BZIP2, False)
    zip_file.writestr(filename, content)

    for zfile in zip_file.filelist:
        zfile.create_system = 0

    buffer.seek(0)

    return buffer.read()


async def download(book_id: int, file_type: str, type_:int=3, retry:int=3):
    # type 0: flibustahezeous3.onion
    # type 1: flibusta.appspot.com
    # type 2: flibusta.is
    # type 3: flibs.in
    while type_ > 0:
        print(f"download {book_id} {file_type} {type_} {retry}")
        url: str = ""
        cookies: Optional[dict] = None
        proxy: Optional[str] = None

        if type_ in (0, 1, 2):
            basic_url = None
            if type_ == 0:
                basic_url = "http://flibustahezeous3.onion"
            elif type_ == 1:
                basic_url = "https://flibusta.appspot.com"
            elif type_ == 2:
                basic_url = "http://flibusta.is"
            else:
                raise Exception()

            if type_ == 0:
                proxy = Config.TOR_PROXIES

            if file_type in ("fb2", "epub", "mobi"):
                url = basic_url + f"/b/{book_id}/{file_type}"
            else:
                url = basic_url + f"/b/{book_id}/download"

            if type_ in [1]:
                cookies = {'SESS717db4750c98b34dc0a0cf14a0c49e88': 'dfd17c8195cecd84a6fc02392729bfc5'}

        elif type_ == 3:
            url = f"https://flibs.in/d?b={book_id}&f={file_type}"

        try:
            async with aiohttp.ClientSession(cookies=cookies, timeout=ClientTimeout(total=60 * 60)) as session:
                async with session.get(url, allow_redirects=True, max_redirects=50, proxy=proxy) as resp:  # type: aiohttp.ClientResponse
                    if resp.headers.get("Content-Type") and "text/html" in resp.headers.get("Content-Type") or resp.status != 200:
                        if "Мы зарегистрировали подозрительный трафик, исходящий из вашей сети." in await resp.text():
                            raise CaptchaException("Captcha")
                        raise NotBookException("NotBookException")
                    if resp.headers.get("Content-Type") == "application/zip":
                        return await asyncio.get_event_loop().run_in_executor(
                            process_pool_executor, unzip, await resp.read(), file_type)
                    return await resp.content.read()
        except (aiohttp.ServerDisconnectedError, aiohttp.ClientOSError, aiohttp.ClientPayloadError,
                aiohttp.client_exceptions.ClientConnectorError, zipfile.BadZipFile,
                CaptchaException, NotBookException, FileNotFoundError) as e:
            print(e)

        retry -= 1

        if retry <= 0:
            type_ -= 1
            retry = 3

    return None


async def download_image(type_: str, path: str):
    proxy: Optional[str] = None
    pfix: Optional[str] = None
    if type_ == "book":
        pfix = "ib"
    elif type_ == "author":
        pfix = "ia"
    url = f"https://flibusta.is/{pfix}/{path}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, allow_redirects=True, proxy=proxy, max_redirects=50) as resp:
                if resp.status != 200:
                    return None
                return await resp.content.read()
    except aiohttp.client_exceptions.ServerDisconnectedError:
        return None

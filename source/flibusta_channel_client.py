from typing import Optional
from aiohttp import request
from aiohttp.client_exceptions import ClientConnectionError

from config import Config


class FlibustaChannelClient:
    @classmethod
    async def download(cls, book_id: int, file_type: str) -> Optional[bytes]:
        try:
            async with request(
                "GET",
                f"http://{Config.FLIBUSTA_CHANNEL_HOST}:{Config.FLIBUSTA_CHANNEL_PORT}/download/{book_id}/{file_type}"
            ) as response:
                if response.status == 200:
                    return await response.content.read()
                else:
                    return None
        except ClientConnectionError:
            return None

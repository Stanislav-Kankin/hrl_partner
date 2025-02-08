import aiohttp
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class BitrixAPI:
    def __init__(self, webhook_base_url: str):
        self.webhook_base_url = webhook_base_url

    async def _call_method(self, method: str, params: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        url = f"{self.webhook_base_url}/{method}"
        logger.info(f"Request URL: {url}")
        logger.info(f"Request Params: {params}")

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, json=params or {}) as response:
                    data = await response.json()
                    logger.info(f"API Response: {data}")  # Логируем полный ответ
                    if 'error' in data:
                        logger.error(f"API Error: {data.get('error_description', 'Unknown error')}")
                        return None
                    return data
            except aiohttp.ClientError as e:
                logger.error(f"Request failed: {e}")
                return None

    async def get_deal(self, deal_id: str) -> Optional[Dict]:
        response = await self._call_method('crm.deal.get', {'id': deal_id})
        logger.info(f"API Response: {response}")
        return response

import aiohttp
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class BitrixAPI:
    def __init__(self, webhook_base_url: str):
        self.webhook_base_url = webhook_base_url

    async def _call_method(
            self,
            method: str,
            params: Optional[Dict] = None
            ) -> Optional[Dict[str, Any]]:
        url = f"{self.webhook_base_url}/{method}"
        logger.info(f"Request URL: {url}")
        logger.info(f"Request Params: {params}")

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, json=params or {}) as response:
                    data = await response.json()
                    logger.info(f"API Response: {data}")
                    if 'error' in data:
                        logger.error(
                            f"API Error: {data.get(
                                'error_description', 'Unknown error'
                                )}"
                            )
                        return None
                    return data
            except aiohttp.ClientError as e:
                logger.error(f"Request failed: {e}")
                return None

    async def get_deal(self, deal_id: str) -> Optional[Dict]:
        response = await self._call_method('crm.deal.get', {'id': deal_id})
        logger.info(f"API Response: {response}")
        return response

    async def get_user(self, user_id: str) -> Optional[Dict]:
        response = await self._call_method('user.get', {'ID': user_id})
        if response is None:
            logger.error(f"Failed to retrieve user data for ID: {user_id}")
        return response

    async def get_company_info(self, company_id: str) -> Optional[Dict]:
        response = await self._call_method(
            'crm.company.get', {'ID': company_id}
            )
        return response

    async def get_deal_stage(self, stage_id: str) -> Optional[Dict]:
        response = await self._call_method('crm.deal.stage.list', {})
        stage_info = next(
            (stage for stage in response.get(
                'result', []
                ) if stage['STATUS_ID'] == stage_id), {}
            )
        return {'result': stage_info}

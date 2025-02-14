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

    async def get_dealreg_by_id(self, dealreg_id: str) -> Optional[Dict]:
        """
        Получает смарт-процесс DealReg по его ID.
        """
        response = await self._call_method('crm.item.get', {
            'entityTypeId': 183,  # ID сущности DealReg
            'id': dealreg_id
        })
        return response

    async def get_company_info(self, company_id: str) -> Optional[Dict]:
        """
        Получает информацию о компании по её ID.
        """
        response = await self._call_method('crm.company.get', {'id': company_id})
        return response

    async def get_user(self, user_id: str) -> Optional[Dict]:
        """
        Получает информацию о пользователе по его ID.
        """
        response = await self._call_method('user.get', {'ID': user_id})
        if response is None:
            logger.error(f"Failed to retrieve user data for ID: {user_id}")
        return response

    async def get_deal_stage(self, stage_id: str) -> Optional[Dict]:
        """
        Получает информацию о стадии сделки по её ID.
        """
        response = await self._call_method('crm.status.list', {
            'filter': {'ENTITY_ID': 'DEAL_STAGE'}, 'select': [
                'STATUS_ID', 'NAME']})
        if response is None:
            logger.error(f"Failed to retrieve deal stages for ID: {stage_id}")
            return {'result': {}}
        stage_info = next((
            stage for stage in response.get(
                'result', []) if stage['STATUS_ID'] == stage_id), {})
        return {'result': stage_info}
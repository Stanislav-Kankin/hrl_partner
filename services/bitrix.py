import requests
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class BitrixAPI:
    def __init__(self, webhook_base_url: str):
        self.webhook_base_url = webhook_base_url

    def _call_method(
            self, method: str, params: Optional[Dict] = None
            ) -> Optional[Dict[str, Any]]:
        """
        Вызов метода Bitrix24 API.
        """
        url = f"{self.webhook_base_url}/{method}"
        try:
            response = requests.post(url, json=params or {})
            logger.info(f"Bitrix24 API Request URL: {url}")
            logger.info(f"Bitrix24 API Request Params: {params}")
            response.raise_for_status()
            data = response.json()

            if 'error' in data:
                logger.error(f"Bitrix24 API Error: {data.get(
                    'error_description', 'Unknown error')}")
                return None

            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Request to Bitrix24 failed: {e}")
            return None

    def get_deal(self, deal_id: str) -> Optional[Dict]:
        """
        Получение информации о сделке по её ID.
        """
        response = self._call_method('crm.deal.get', {'id': deal_id})
        logger.info(f"Bitrix24 API Response: {response}")
        return response

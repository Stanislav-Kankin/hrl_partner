import requests
import logging
import os
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

    def get_contact(
            self, phone: Optional[str] = None,
            email: Optional[str] = None,
            partner_id: Optional[str] = None
            ) -> Optional[Dict]:
        """
        Поиск контакта по телефону, email или partner_id.
        """
        filter_params = {}
        if phone: filter_params['PHONE'] = phone
        if email: filter_params['EMAIL'] = email
        if partner_id: filter_params['UF_PARTNER_ID'] = partner_id

        return self._call_method('crm.contact.list', {
            'filter': filter_params,
            'select': ['ID', 'NAME', 'UF_PARTNER_ID']
        })

    def check_inn(self, inn: str) -> Optional[Dict]:
        """
        Проверка ИНН в компаниях.
        """
        return self._call_method('crm.company.list', {
            'filter': {'UF_INN': inn},
            'select': ['ID', 'TITLE']
        })

    def create_lead(self, title: str, contact_id: str, inn: str) -> Optional[Dict]:
        """
        Создание лида в Bitrix24.
        """
        return self._call_method('crm.lead.add', {
            'fields': {
                'TITLE': title,
                'NAME': f"Заявка от партнера {contact_id}",
                'STATUS_ID': 'NEW',
                'SOURCE_ID': 'PARTNER_BOT',
                'UF_CRM_INN': inn,
                'CONTACT_ID': contact_id
            }
        })

    def create_deal(self, title: str, contact_id: str, inn: str) -> Optional[Dict]:
        """
        Создание сделки в Bitrix24.
        """
        return self._call_method('crm.deal.add', {
            'fields': {
                'TITLE': title,
                'TYPE_ID': 'SALE',
                'CONTACT_ID': contact_id,
                'UF_CRM_INN': inn,
                'STAGE_ID': 'NEW'
            }
        })

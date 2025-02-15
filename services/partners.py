# Словарь с партнёрами и их ссылками
PARTNERS = {
    "НН": "https://b24-drzxem.bitrix24site.ru/crm_form_1kuge/",
    "СБЕР РЕШЕНИЯ": "https://b24-lpcw1z.bitrix24site.ru/crm_form_842ad/",
    "БФТ": "https://b24-lpcw1z.bitrix24site.ru/crm_form_qs4ax/",
    "МТС": "https://b24-lpcw1z.bitrix24site.ru/crm_form_e44pd/"
}

# Словарь с пользователями для авторизации
USERS = {
    "Станислав Какнин": {
        "name": "Станислав",
        "last_name": "Канкин",
        "email": "stanislav@example.com",
        "phone_num": "89111234455",
        "allowed_partners": ["НН"]
    },
    "Иван Иванов": {
        "name": "Иван",
        "last_name": "Иванов",
        "email": "ivan@example.com",
        "phone_num": "89221234567",
        "allowed_partners": ["БФТ"]
    },
    "admin admin": {
        "name": "admin",
        "last_name": "admin",
        "email": "admin",
        "phone_num": "1",
        "allowed_partners": [
            "НН",
            "СБЕР РЕШЕНИЯ",
            "БФТ",
            "МТС"
            ]
    },
}

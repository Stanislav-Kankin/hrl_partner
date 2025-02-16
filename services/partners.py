import json
import os

# Словарь с партнёрами и их ссылками
PARTNERS = {
    "НН": "https://b24-drzxem.bitrix24site.ru/crm_form_1kuge/",
    "СБЕР РЕШЕНИЯ": "https://b24-lpcw1z.bitrix24site.ru/crm_form_842ad/",
    "БФТ": "https://b24-lpcw1z.bitrix24site.ru/crm_form_qs4ax/",
    "МТС": "https://b24-lpcw1z.bitrix24site.ru/crm_form_e44pd/"
}

# Путь к файлу с пользователями
USERS_FILE = "users.json"

# Загрузка пользователей из файла
if os.path.exists(USERS_FILE):
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        USERS = json.load(f)
else:
    USERS = {
        "Станислав Канкин": {
            "name": "Станислав",
            "last_name": "Канкин",
            "email": "skankin@hr-link.ru",
            "phone_num": "89898553407",
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
            "allowed_partners": ["НН", "СБЕР РЕШЕНИЯ", "БФТ", "МТС"]
        },
    }


# Функция для сохранения пользователей в файл
def save_users():
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(USERS, f, ensure_ascii=False, indent=4)

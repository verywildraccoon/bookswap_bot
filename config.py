import json
from aiogram import Bot

pending_admin_requests={}
pending_moderator_requests={}
pending_listings = {}

def load_config():
    try:
        with open ('config.json', 'r', encoding="utf-8") as file:
            data = json.load(file)

            if 'admins' in data:
                new_admins = {}
                for user_id_str, info in data["admins"].items():
                    user_id_int = int(user_id_str)
                    new_admins[user_id_int] = info
                data["admins"] = new_admins

            if 'moderators' in data:
                new_moderators = {}
                for user_id_str, info in data["moderators"].items():
                    user_id_int = int(user_id_str)
                    new_moderators[user_id_int] = info
                data["moderators"] = new_moderators

        return data
    except FileNotFoundError:
        return {}

def save_config(data):
    with open('config.json', 'w', encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

def try_parse_int(argument):
    if argument is None:
        return None
    try:
        return int(argument)
    except ValueError:
        return None

data = load_config()
BOT_TOKEN = data.get('bot_token')
SUPER_ADMIN_ID = try_parse_int(data.get('super_admin_id', None))
GROUP_ID = data.get('group_id')
MODERATORS = data.get('moderators', {})
ADMINS = data.get('admins', {})
MODERATION_ENABLED = data.get('moderation_enabled', True)

bot = Bot(token=BOT_TOKEN)
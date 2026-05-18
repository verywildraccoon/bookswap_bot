from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_type_keyboard():
    button_sale = InlineKeyboardButton(text="Продажа", callback_data="type_sale")
    button_swap = InlineKeyboardButton(text="Обмен", callback_data="type_swap")
    button_gift = InlineKeyboardButton(text="Даром", callback_data="type_gift")
    button_search = InlineKeyboardButton(text="Ищу", callback_data="type_search")

    return InlineKeyboardMarkup(
    inline_keyboard=[
        [button_sale, button_swap],
        [button_gift, button_search],
    ]
)

def get_listing_confirmation_keyboard():
    button_publish = InlineKeyboardButton(text="Опубликовать", callback_data="confirm_publish")
    button_cancel = InlineKeyboardButton(text="Отменить", callback_data="confirm_cancel")

    return InlineKeyboardMarkup(
    inline_keyboard=[
        [button_publish, button_cancel],
    ]
)

def get_admin_confirmation_keyboard(user_id):
    button_approve = InlineKeyboardButton(text="Одобрить", callback_data=f"approve_admin_{user_id}")
    button_decline = InlineKeyboardButton(text="Отклонить", callback_data=f"reject_admin_{user_id}")

    return InlineKeyboardMarkup(
    inline_keyboard=[
        [button_approve, button_decline],
    ]
)

def get_moderator_confirmation_keyboard(user_id):
    button_approve = InlineKeyboardButton(text="Одобрить", callback_data=f"approve_mod_{user_id}")
    button_decline = InlineKeyboardButton(text="Отклонить", callback_data=f"reject_mod_{user_id}")

    return InlineKeyboardMarkup(
    inline_keyboard=[
        [button_approve, button_decline],
    ]
)

def get_listing_moderation_keyboard(listing_id):
    button_approve = InlineKeyboardButton(text="Одобрить", callback_data=f"approve_listing_{listing_id}")
    button_decline = InlineKeyboardButton(text="Отклонить", callback_data=f"reject_listing_{listing_id}")

    return InlineKeyboardMarkup(
    inline_keyboard=[
        [button_approve, button_decline],
    ]
    )
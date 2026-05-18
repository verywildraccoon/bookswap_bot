from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
import keyboards
import uuid

from config import bot
import config

router = Router()

class Listing(StatesGroup):
    waiting_listing_type = State()
    waiting_photo = State()
    waiting_price = State()
    waiting_district = State()
    waiting_contact = State()
    waiting_comment = State()
    waiting_confirmation = State()

class Moderation(StatesGroup):
    waiting_reason = State()

TYPE_LABELS = {
    "type_sale": "продажа",
    "type_swap": "обмен",
    "type_gift": "даром",
    "type_search": "ищу",
}

async def form_listing_card(state: FSMContext):
    caption = []
    user_data = await state.get_data()
    listing_type = user_data.get('listing_type')
    price = user_data.get('price')
    district = user_data.get('district')
    contact = user_data.get('contact')
    comment = user_data.get('comment')
    photo = user_data.get('photo_id')
    
    caption.append(f"Тип объявления: {listing_type}")
    if price is not None:
        caption.append(f"Цена: {price}")
    if district is not None:
        caption.append(f"Район: {district}")
    caption.append(f"Контакт: {contact}")
    if comment is not None:
        caption.append(f"Комментарий: {comment}")

    caption = ("\n".join(caption))
    
    return caption, photo

async def send_listing_to_user(message: Message, state: FSMContext):
    caption, photo = await form_listing_card(state)
    if photo is not None:
        await message.answer_photo(photo=photo, caption = caption)
    else:
        await message.answer(caption)

async def ask_publish_confirmation(message: Message, state: FSMContext):
    await state.set_state(Listing.waiting_confirmation)
    keyboard = keyboards.get_listing_confirmation_keyboard()
    await message.answer("Опубликовать объявление?", reply_markup=keyboard)

async def send_listing_to_group(callback: CallbackQuery, state: FSMContext):
    caption, photo = await form_listing_card(state)
    username = callback.from_user.username
    full_name = callback.from_user.full_name

    if username is not None: 
        group_caption = caption + "\n\n" + "Автор объявления: @" + username
    else:
        group_caption = caption + "\n\n" + "Автор объявления: " + full_name
    
    if photo is not None:
        await bot.send_photo(chat_id=config.GROUP_ID, photo=photo, caption=group_caption)
    else:
        await bot.send_message(chat_id=config.GROUP_ID, text=group_caption)

async def send_listing_to_moderator(callback: CallbackQuery, state: FSMContext):
    caption, photo = await form_listing_card(state)
    username = callback.from_user.username
    full_name = callback.from_user.full_name
    user_id = callback.from_user.id
    unique_id = uuid.uuid4().hex[:8]
    
    keyboard = keyboards.get_listing_moderation_keyboard(unique_id)

    config.pending_listings[unique_id] = {
        "author": {"user_id": user_id, "username" : username, "full_name":full_name},
        "caption" : caption,
        "photo" : photo
        }

    if username is not None: 
        mod_caption = "⏳ Новое объявление на модерации:\n\n" + caption + "\n\n" + "Автор объявления: @" + username
    else:
        mod_caption = "⏳ Новое объявление на модерации:\n\n" + caption + "\n\n" + "Автор объявления: " + full_name
    
    for moderator_id in config.MODERATORS:
        if photo is not None:
            await bot.send_photo(chat_id=moderator_id, photo=photo, caption=mod_caption, reply_markup=keyboard)
        else:
            await bot.send_message(chat_id=moderator_id, text=mod_caption, reply_markup=keyboard)

@router.message(CommandStart())
async def handle_start(message: Message):
    if message.chat.type == "private":
        await message.answer(f"Привет, {message.from_user.full_name}! Я помогу создать аккуратное объявление для чата \"Книгообмен Астана\" - продать, обменять, отдать или найти книгу. \n\n"
        f"Чтобы начать - /new. \n"
        f"Все команды - /help."
        )
    else:
        await message.answer("Я работаю только в личных сообщениях. Напишите мне в ЛС, чтобы создать объявление.")

@router.message(Command("help"), F.chat.type == "private")
async def handle_help(message: Message):
    await message.answer(
        "Команды для всех пользователей:\n"
        "/new — создать новое объявление\n"
        "/cancel — отменить создание объявления\n"
        "/skip — пропустить необязательный шаг при создании объявления\n"
        "/help — показать эту справку\n\n"  

        "Команды для модераторов и администраторов:\n"  
        "/list_moderators — показать список модераторов\n"
        "/request_moderator — подать заявку на роль модератора\n"
        "/list_admins — показать список администраторов\n"
        "/request_admin — подать заявку на роль администратора\n\n"

        "Команды для администраторов:\n" 
        "/remove_moderator <id> — удалить модератора\n"
        "/moderation_on — включить модерацию\n"
        "/moderation_off — отключить модерацию\n\n"

        "Команды для супер администратора:\n"
        "/register_group — зарегистрировать группу для публикаций\n"
        "/remove_admin <id> — удалить администратора"
        )

#Этап создания нового объявления
@router.message(Command("new"), F.chat.type == "private")
async def handle_new(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(Listing.waiting_listing_type)
    await message.answer("Создание нового объявления.")
    keyboard = keyboards.get_type_keyboard()
    await message.answer("Какой у вас тип объявления?", reply_markup=keyboard)

@router.message(Command("cancel"), F.chat.type == "private")
async def handle_cancel(message: Message, state: FSMContext):
    current_state = await state.get_state() 
    if current_state is None:
        await message.answer("Сейчас вам нечего отменять. Чтобы начать новое объявление - /new.")
    else:
        await state.clear()
        await message.answer(
            "Создание объявления отменено.\n\n"
            "Чтобы начать заново — /new."
            )

#Этап выбора типа объявления
@router.callback_query(F.data.in_(TYPE_LABELS.keys()), F.message.chat.type == "private")
async def got_listing_type(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.delete()
    label = TYPE_LABELS[callback.data]
    await state.update_data(listing_type=label)
    await state.set_state(Listing.waiting_photo)
    if label == "ищу":
        await callback.message.answer(
            f"Вы выбрали тип объявления: {label}.\n\n"
            "Если у вас есть обложка искомой книги - пришлите фото, если нет - /skip."
            )
    else:
        await callback.message.answer(
            f"Вы выбрали тип объявления: {label}.\n\n"
            "Пришлите фото книги.")

#Не нажали на кнопку, а прислали текст или прислали текстовую команду
@router.message(Listing.waiting_listing_type, F.chat.type == "private")   
async def got_listing_type_hint(message: Message, state: FSMContext):
    await message.answer("Пожалуйста, выберите тип объявления одной из кнопок выше.")

#Пропуск этапа получения фото для объявлений типа "ищу"
@router.message(Listing.waiting_photo, Command("skip"), F.chat.type == "private")
async def skip_photo(message: Message, state: FSMContext):
    user_data = await state.get_data()
    listing_type = user_data.get('listing_type')
    if listing_type == "ищу":
        await message.answer("Хорошо, пропускаем фото. \n\n" 
                             "В каком районе удобно встретиться? Можете написать /skip, чтобы пропустить.")
        await state.set_state(Listing.waiting_district)
    elif listing_type in ("продажа", "обмен", "даром"):
        await message.answer("Фото обязательно для этого типа объявления. Пожалуйста, пришлите фото книги.")

#Этап получения фото
@router.message(Listing.waiting_photo, F.photo, F.chat.type == "private")
async def got_photo(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    await state.update_data(photo_id=photo_id)
    user_data = await state.get_data()
    listing_type = user_data.get('listing_type')
    if listing_type == "продажа":
        await state.set_state(Listing.waiting_price)
        await message.answer(
            "Фото принято. \n\n"
            "Укажите цену в тенге. Если книг несколько - можете указать диапазон цен (например, 500–1500) или минимальную цену."
        )
    elif listing_type == "ищу":
        await state.set_state(Listing.waiting_district)
        await message.answer("Фото принято. \n\n"
                             "В каком районе удобно встретиться? Можете написать /skip, чтобы пропустить.")
    elif listing_type in ("даром", "обмен"): 
        await state.set_state(Listing.waiting_district)
        await message.answer("Фото принято. \n\n"
                             "Из какого района можно забрать книгу?")

#Не прислали фото, ошибка
@router.message(Listing.waiting_photo, F.chat.type == "private")
async def not_a_photo(message: Message, state: FSMContext):
    await message.answer("Это не похоже на фото. Пожалуйста, пришлите изображение книги. Если хотите выйти - /cancel.")

#Пропуск этапа обозначения цены
@router.message(Listing.waiting_price, Command("skip"), F.chat.type == "private")
async def skip_price(message: Message, state: FSMContext):
    await message.answer("Цена обязательна для объявления о продаже. Укажите цену в тенге - можно диапазон или минимальную.")

#Этап обозначения цены
@router.message(Listing.waiting_price, F.chat.type == "private")   
async def got_price(message: Message, state: FSMContext):
    await state.update_data(price=message.text)
    await state.set_state(Listing.waiting_district)
    await message.answer("Цена записана.\n\n" 
                         "Укажите район из которого можно забрать книгу(и).")

#Пропуск этапа с обозначением района для объявлений типа "ищу"
@router.message(Listing.waiting_district, Command("skip"), F.chat.type == "private")
async def skip_district(message: Message, state: FSMContext):
    user_data = await state.get_data()
    listing_type = user_data.get('listing_type')
    if listing_type == "ищу":
        await message.answer("Хорошо, район не указан.\n\n"
                            "Укажите номер телефона или ваш телеграм @username для связи.")
        await state.set_state(Listing.waiting_contact)
    elif listing_type in ("продажа", "обмен", "даром"):
        await message.answer("Район нужен — без него непонятно, откуда забрать книгу. Пожалуйста, укажите.")

#Этап предоставления района
@router.message(Listing.waiting_district, F.chat.type == "private")   
async def got_district(message: Message, state: FSMContext):
    await state.update_data(district=message.text)
    await state.set_state(Listing.waiting_contact)
    await message.answer("Район записан.\n\n"
                         "Укажите номер телефона или ваш телеграм @username для связи.")

#Пропуск этапа предоставления контактов
@router.message(Listing.waiting_contact, Command("skip"), F.chat.type == "private")
async def skip_contact(message: Message, state: FSMContext):
    await message.answer("Контакт обязателен - без него никто не сможет с вами связаться. Укажите номер телефона или ваш телеграм @username для связи.")

#Этап предоставления контактов
@router.message(Listing.waiting_contact, F.chat.type == "private")
async def got_contact(message: Message, state: FSMContext):
    await state.update_data(contact=message.text)
    await state.set_state(Listing.waiting_comment)
    
    user_data = await state.get_data()
    listing_type = user_data.get('listing_type')

    if listing_type == "ищу": 
        await message.answer("Контакт записан. \n\n"
                             "Опишите книгу, которую ищете: автор, название, тематика. Это обязательное поле для объявлений типа «Ищу».")
    else: 
        await message.answer("Контакт записан.\n\n"
                             "Можете добавить комментарий: состояние книги, важные детали. Или /skip, если ничего добавить не хотите.")

#Пропуск этапа предоставления комментариев + формируем объявление
@router.message(Listing.waiting_comment, Command("skip"), F.chat.type == "private")
async def skip_comment(message: Message, state: FSMContext):
    user_data = await state.get_data()
    listing_type = user_data.get('listing_type')

    if listing_type == "ищу":
        await message.answer("Описание книги обязательно для типа «Ищу». Пожалуйста, опишите.")
    else:
        await send_listing_to_user(message, state)
        await ask_publish_confirmation(message, state)

#Этап предоставления комментариев + формируем объявление
@router.message(Listing.waiting_comment, F.chat.type == "private")
async def got_comment(message: Message, state: FSMContext):
    await state.update_data(comment=message.text)
    await send_listing_to_user(message, state)
    await ask_publish_confirmation(message, state)

#Этап просмотра объявления + отмена
@router.callback_query(F.data == "confirm_cancel", F.message.chat.type == "private")
async def cancel_listing(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.delete()
    await callback.message.answer(
        "Объявление отменено.\n\n"
        "Чтобы создать новое - /new"
        )
    await state.clear()

#Этап просмотра объявления + согласование 
@router.callback_query(F.data == "confirm_publish", F.message.chat.type == "private")
async def confirm_listing(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.delete()
    
    if config.MODERATORS and config.MODERATION_ENABLED:
        await send_listing_to_moderator(callback, state)
        await callback.message.answer(
            "⏳ Объявление отправлено на модерацию. Я уведомлю вас о решении.\n\n"
            "Чтобы создать ещё одно - /new." 
            )
    elif config.GROUP_ID is not None:
        await send_listing_to_group(callback, state)
        await callback.message.answer(
            "✅ Объявление опубликовано в группе!\n\n"
            "Чтобы создать ещё одно - /new." 
            )
    else:
        await callback.message.answer("Бот не настроен на публикацию. Свяжитесь с админом.")
    await state.clear()

@router.callback_query(F.data.startswith("approve_listing_"), F.message.chat.type == "private")
async def approve_listing(callback: CallbackQuery):
    await callback.answer()
    await callback.message.delete()

    listing_id = callback.data.split("approve_listing_")[1]
    listing = config.pending_listings.pop(listing_id, None)
    
    if listing is None:
        await callback.message.answer("Объявление не найдено. Возможно, бот перезапускался.")
        return
    
    user_id = listing["author"]["user_id"]
    username = listing["author"]["username"]
    full_name = listing["author"]["full_name"]
    caption = listing["caption"]
    photo = listing["photo"]
        
    if username is not None: 
         group_caption = caption + "\n\n" + "Автор объявления: @" + username
    else:
        group_caption = caption + "\n\n" + "Автор объявления: " + full_name

    await bot.send_message(chat_id=user_id, text=f"✅ Ваше объявление одобрено и опубликовано в группе.")
    await callback.message.answer(f"✅ Объявление от {full_name} опубликовано.")

    if photo is not None:
        await bot.send_photo(chat_id=config.GROUP_ID, photo=photo, caption=group_caption)
    else: 
        await bot.send_message(chat_id=config.GROUP_ID, text=group_caption)

@router.callback_query(F.data.startswith("reject_listing_"), F.message.chat.type == "private")
async def reject_listing(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.delete()

    listing_id = callback.data.split("reject_listing_")[1]

    if listing_id not in config.pending_listings: 
        await callback.message.answer("Объявление не найдено. Возможно, бот перезапускался.")
        return
    
    await state.update_data(listing_id=listing_id)
    await state.set_state(Moderation.waiting_reason)
    await callback.message.answer(f"Напишите причину отклонения. Или /skip, если без причины.") 

@router.message(Moderation.waiting_reason, Command("skip"), F.chat.type == "private")
async def skip_rejection_reason(message: Message, state: FSMContext):
    user_data = await state.get_data()
    listing_id = user_data.get('listing_id')
    listing = config.pending_listings.pop(listing_id, None)

    if listing is None:
        await message.answer("Объявление не найдено. Возможно, бот перезапускался.")
        return
    
    user_id = listing["author"]["user_id"]
    full_name = listing["author"]["full_name"]
    text = "❌ Ваше объявление отклонено модератором."

    await bot.send_message(chat_id=user_id, text=text)
    await message.answer(f"❌ Объявление от {full_name} отклонено.")
    await state.clear()

@router.message(Moderation.waiting_reason, F.chat.type == "private")
async def got_rejection_reason(message: Message, state: FSMContext):
    user_data = await state.get_data()
    listing_id = user_data.get('listing_id')
    listing = config.pending_listings.pop(listing_id, None)
    
    if listing is None:
        await message.answer("Объявление не найдено. Возможно, бот перезапускался.")
        return

    user_id = listing["author"]["user_id"]
    full_name = listing["author"]["full_name"]
    rejection_reason = message.text
    text=(
    "❌ Ваше объявление отклонено модератором.\n\n"
    f"Причина: {rejection_reason}"
    )
    
    await bot.send_message(chat_id=user_id, text=text)
    await message.answer(f"❌ Объявление от {full_name} отклонено.")
    await state.clear()
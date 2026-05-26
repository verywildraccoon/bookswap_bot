from aiogram import F, Router
from aiogram.filters import  Command, CommandObject
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import keyboards, config
from config import bot, load_config, save_config,try_parse_int

router = Router()

@router.message(Command("request_admin"), F.chat.type == "private")
async def handle_request_admin(message: Message, state: FSMContext):
    if message.from_user.id in config.ADMINS:
        await message.answer("Вы уже являетесь админом.")
        return

    await message.answer("Запрос на роль админинстратора отправлен администратору. Я уведомлю вас о решении.")
    
    user_id = message.from_user.id
    full_name = message.from_user.full_name
    config.pending_admin_requests[user_id]={"full_name": full_name}

    text = (f"📨 Новая заявка на администратора:\n\n"
    f"От: {full_name}\n"
    f"ID: {user_id}\n\n"
    "Одобрить?")
    keyboard = keyboards.get_admin_confirmation_keyboard(user_id)

    await bot.send_message(chat_id=config.SUPER_ADMIN_ID, text=text, reply_markup=keyboard)

@router.callback_query(F.data.startswith("approve_admin_"), F.message.chat.type == "private")
async def approve_admin_request(callback: CallbackQuery):
    await callback.answer()
    await callback.message.delete()

    new_admin_id = int(callback.data.split("approve_admin_")[1])

    if new_admin_id in config.ADMINS:
        await callback.message.answer("Администратор уже добавлен.")
        return
    
    request = config.pending_admin_requests.pop(new_admin_id, None)
    if request is None:
        await callback.message.answer("Заявка не найдена. Возможно, она устарела (бот перезапускался). Попросите пользователя подать заявку снова.")
        return
    
    full_name = request["full_name"]
    data = load_config()
    config.ADMINS[new_admin_id] = {"full_name" : full_name}
    data['admins'] = config.ADMINS
    save_config(data)

    await callback.message.answer(f"✅ {full_name} назначен(а) администратором")
    await bot.send_message(chat_id=new_admin_id, text="Ваша заявка одобрена. \n\n" 
    "Теперь вы администратор группы. Вы можете удалять или добавлять новых модераторов.")

@router.callback_query(F.data.startswith("reject_admin_"), F.message.chat.type == "private")
async def reject_admin_request(callback: CallbackQuery):
    await callback.answer()
    await callback.message.delete()

    applicant_id = int(callback.data.split("reject_admin_")[1])
    request = config.pending_admin_requests.pop(applicant_id, None)

    if request is None:
        await callback.message.answer("Заявка не найдена. Возможно, она устарела (бот перезапускался). Попросите пользователя подать заявку снова.")
        return

    full_name = request["full_name"]
    await callback.message.answer(f"❌ Заявка от {full_name} отклонена.")
    await bot.send_message(chat_id=applicant_id, text="К сожалению, ваша заявка на администратора отклонена.")

@router.message(Command("list_admins"), F.chat.type == "private")
async def handle_list_admins(message: Message):
    if message.from_user.id != config.SUPER_ADMIN_ID and message.from_user.id not in config.ADMINS and message.from_user.id not in config.MODERATORS:
        await message.answer("У вас нет прав на эту команду.")
        return
    
    output = ""

    if not config.ADMINS:
        await message.answer("Администраторов нет.")
        return
    
    for admin_id, info in config.ADMINS.items():
        full_name = info["full_name"]
        output = output + f"\n- Имя: {full_name} (ID: {admin_id})" 
        
    await message.answer(f"Администраторы: {output}") 

@router.message(Command("remove_admin"), F.chat.type == "private")
async def handle_remove_admin(message: Message, command: CommandObject):
    
    if message.from_user.id != config.SUPER_ADMIN_ID:
        await message.answer("У вас нет прав на эту команду.")
        return
    
    argument = command.args
    admin_id = try_parse_int(argument)

    if admin_id is None:
        await message.answer("Укажите корректный ID.")
        return
    
    if admin_id not in config.ADMINS:
        await message.answer("Пользователь не является администратором.")
        return
    
    removed_data = config.ADMINS.pop(admin_id)
    removed_admin_full_name = removed_data["full_name"]

    data = load_config()
    data['admins'] = config.ADMINS
    save_config(data)

    await message.answer(f"✅ Администратор {removed_admin_full_name} удалён.")
    await bot.send_message(chat_id=admin_id, text="Вы больше не являетесь администратором группы.")

@router.message(Command("request_moderator"), F.chat.type == "private")
async def handle_request_moderator(message: Message, state: FSMContext):
    if message.from_user.id in config.MODERATORS:
        await message.answer("Вы уже являетесь модератором.")
        return

    await message.answer("Запрос на роль модератора отправлен админу. Я уведомлю вас о решении.")
    user_id = message.from_user.id
    full_name = message.from_user.full_name
    config.pending_moderator_requests[user_id]={"full_name": full_name}

    text = (f"📨 Новая заявка на модератора:\n\n"
    f"От: {full_name}\n"
    f"ID: {user_id}\n\n"
    "Одобрить?")
    keyboard = keyboards.get_moderator_confirmation_keyboard(user_id)

    for admin_id in config.ADMINS:
        await bot.send_message(chat_id=admin_id, text=text, reply_markup=keyboard)
    if config.SUPER_ADMIN_ID not in config.ADMINS:
        await bot.send_message(chat_id=config.SUPER_ADMIN_ID, text=text, reply_markup=keyboard)

@router.message(Command("list_moderators"), F.chat.type == "private")
async def handle_list_moderators(message: Message):
    if message.from_user.id != config.SUPER_ADMIN_ID and message.from_user.id not in config.ADMINS and message.from_user.id not in config.MODERATORS:
        await message.answer("У вас нет прав на эту команду.")
        return
    
    output = ""

    if not config.MODERATORS:
        await message.answer("Модераторов нет.")
        return
    
    for moderator_id, info in config.MODERATORS.items():
        full_name = info["full_name"]
        output = output + f"\n- Имя: {full_name} (ID: {moderator_id})" 
        
    await message.answer(f"Модераторы: {output}") 

@router.message(Command("remove_moderator"), F.chat.type == "private")
async def handle_remove_moderator(message: Message, command: CommandObject):
    if message.from_user.id not in config.ADMINS and message.from_user.id != config.SUPER_ADMIN_ID:
        await message.answer("У вас нет прав на эту команду.")
        return
    
    argument = command.args
    moderator_id = try_parse_int(argument)

    if moderator_id is None:
        await message.answer("Укажите корректный ID.")
        return
    
    if moderator_id not in config.MODERATORS:
        await message.answer("Пользователь не является модератором.")
        return
    
    removed_data = config.MODERATORS.pop(moderator_id)
    removed_moderator_full_name = removed_data["full_name"]

    data = load_config()
    data['moderators'] = config.MODERATORS
    save_config(data)

    await message.answer(f"✅ Модератор {removed_moderator_full_name} удалён.")
    await bot.send_message(chat_id=moderator_id, text="Вы больше не являетесь модератором группы.")

@router.message(Command("moderation_on"), F.chat.type == "private")
async def handle_moderation_on(message: Message):
    
    if message.from_user.id not in config.ADMINS and message.from_user.id != config.SUPER_ADMIN_ID:
        await message.answer("У вас нет прав на эту команду.")
        return

    if config.MODERATION_ENABLED:
        await message.answer("Режим модерации уже активирован.")
        return
    
    config.MODERATION_ENABLED = True
    data = load_config()
    data['moderation_enabled'] = True
    save_config(data)
    await message.answer("✅ Режим модерации активирован.")

@router.message(Command("moderation_off"), F.chat.type == "private")
async def handle_moderation_off(message: Message):
    
    if message.from_user.id != config.SUPER_ADMIN_ID and message.from_user.id not in config.ADMINS:
        await message.answer("У вас нет прав на эту команду.")
        return

    if not config.MODERATION_ENABLED:
        await message.answer("Режим модерации уже деактивирован.")
        return
    
    config.MODERATION_ENABLED = False
    data = load_config()
    data['moderation_enabled'] = False
    save_config(data)
    await message.answer("✅ Режим модерации деактивирован.")

@router.callback_query(F.data.startswith("approve_mod_"), F.message.chat.type == "private")
async def approve_moderator_request(callback: CallbackQuery):
    await callback.answer()
    await callback.message.delete()
    new_moderator_id = int(callback.data.split("approve_mod_")[1])

    if new_moderator_id in config.MODERATORS:
        await callback.message.answer("Модератор уже добавлен.")
        return
    
    request = config.pending_moderator_requests.pop(new_moderator_id, None)
    if request is None:
        await callback.message.answer("Заявка не найдена. Возможно, она устарела (бот перезапускался). Попросите пользователя подать заявку снова.")
        return
    
    full_name = request["full_name"]
    data = load_config()
    config.MODERATORS[new_moderator_id] = {"full_name" : full_name}
    data['moderators'] = config.MODERATORS
    save_config(data)

    await callback.message.answer(f"✅ {full_name} назначен(а) модератором")
    await bot.send_message(chat_id=new_moderator_id, text="Ваша заявка одобрена. \n\n" 
    "Теперь вы модератор объявлений. Вы будете получать новые объявления для проверки и сможете одобрять или отклонять их.")

@router.callback_query(F.data.startswith("reject_mod_"), F.message.chat.type == "private")
async def reject_moderator_request(callback: CallbackQuery):
    await callback.answer()
    await callback.message.delete()

    applicant_id = int(callback.data.split("reject_mod_")[1])

    request = config.pending_moderator_requests.pop(applicant_id, None)
    if request is None:
        await callback.message.answer("Заявка не найдена. Возможно, она устарела (бот перезапускался). Попросите пользователя подать заявку снова.")
        return
    full_name = request["full_name"]
    await callback.message.answer(f"❌ Заявка от {full_name} отклонена.")
    await bot.send_message(chat_id=applicant_id, text="К сожалению, ваша заявка на модератора отклонена.")

@router.message(Command("register_group"), F.chat.type != "private")
async def handle_register_group(message: Message):
    if message.chat.type == "private":
        await message.answer("Эта команда выполняется в группе, которую нужно зарегистрировать как целевой чат для публикаций.")
        return
    if message.from_user.id != config.SUPER_ADMIN_ID:
         await message.answer("У вас нет прав на эту команду.")
         return
    if config.GROUP_ID == message.chat.id:
        await message.answer("Эта группа уже зарегистрирована.")
        return        
    config.GROUP_ID = message.chat.id
    data = load_config()
    data["group_id"] = config.GROUP_ID
    save_config(data)
    await message.answer("✅ Группа зарегистрирована. Объявления будут публиковаться сюда.")
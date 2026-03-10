import os
import asyncio
import random
import logging
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from urllib.parse import quote

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Папка для загрузок
DOWNLOADS_FOLDER = Path("downloads")
DOWNLOADS_FOLDER.mkdir(exist_ok=True)

# Инициализация бота
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Состояния для поиска крайнего
class ScapegoatStates(StatesGroup):
    waiting_name = State()
    waiting_options = State()
    spinning = State()

# Состояния для порчи на понос
class PonosOrderStates(StatesGroup):
    waiting_victim = State()
    waiting_reason = State()
    waiting_details = State()

# Состояния для дать в облака
class CloudsStates(StatesGroup):
    waiting_username = State()

# Состояния для скачивания трека
class TrackStates(StatesGroup):
    waiting_artist = State()
    waiting_title = State()

# Состояния для Режима Полины
class PolinaStates(StatesGroup):
    waiting_username = State()
    waiting_reason = State()

# Хранилище данных для каждого пользователя
user_data = {}

# Варианты способов пукнуть
FART_METHODS = [
    "тихо пустил(а) шептуна в лужу",
    "оподливился(лась)",
    "дал(а) в облака",
    "пустил(а) ветра в поле",
    "сыграл(а) симфонию",
    "насмешил(а) портки",
    "забитбоксил(а) попой",
    "хопхэй лалалэйнул(а)"
]

# Главное меню
def get_main_keyboard():
    """Возвращает клавиатуру с основными функциями"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👹 Найди крайнего", callback_data="scapegoat")],
        [InlineKeyboardButton(text="💩 Порча на понос", callback_data="ponos_order")],
        [InlineKeyboardButton(text="💨 Дать в облака", callback_data="clouds")],
        [InlineKeyboardButton(text="😈 Режим Полины", callback_data="polina_mode")],
        [InlineKeyboardButton(text="🤬 Жалобы на пидарасов", callback_data="complaint")]
    ])

# ============ НАЙДИ КРАЙНЕГО ============

@dp.callback_query(F.data == "scapegoat")
async def scapegoat_start(query: types.CallbackQuery, state: FSMContext):
    """Начало поиска крайнего - запрос названия"""
    user_id = query.from_user.id
    await state.set_state(ScapegoatStates.waiting_name)
    
    # Очищаем старые данные
    if user_id in user_data:
        user_data[user_id].pop('scapegoat', None)
    
    # Отправляем в ЛС пользователю
    await bot.send_message(
        user_id,
        "Введи название для сеанса (например: 'Кто крайний?'):"
    )
    await query.answer()

@dp.message(ScapegoatStates.waiting_name)
async def scapegoat_name_received(message: types.Message, state: FSMContext):
    """Получение названия сеанса"""
    user_id = message.from_user.id
    
    if user_id not in user_data:
        user_data[user_id] = {}
    
    user_data[user_id]['scapegoat'] = {
        'name': message.text,
        'options': []
    }
    
    await state.set_state(ScapegoatStates.waiting_options)
    # Отправляем в ЛС
    await message.answer(
        "Введи варианты через запятую (например: Вася, Петя, Маша):"
    )

@dp.message(ScapegoatStates.waiting_options)
async def scapegoat_options_received(message: types.Message, state: FSMContext):
    """Получение вариантов"""
    user_id = message.from_user.id
    text = message.text.strip()
    
    # Парсим варианты через запятую
    options = [opt.strip() for opt in text.split(',') if opt.strip()]
    
    if not options:
        # Ошибка в ЛС
        await message.answer("Введи хотя бы один вариант!")
        return
    
    user_data[user_id]['scapegoat']['options'] = options
    
    await state.set_state(ScapegoatStates.spinning)
    await spin_scapegoat(message.from_user.id, state)

async def spin_scapegoat(user_id: int, state: FSMContext):
    """Запуск поиска крайнего со счётчиком"""
    scapegoat_data = user_data[user_id]['scapegoat']
    name = scapegoat_data['name']
    options = scapegoat_data['options']
    # Используем group_chat_id вместо scapegoat_chat_id
    chat_id = user_data[user_id].get('group_chat_id')
    
    # Отправляем счётчик в ЛС
    spinning_message = await bot.send_message(
        user_id,
        "👹 Ищем крайнего...\n\n" + "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(options)])
    )
    
    # Имитируем прокрутку в ЛС
    for i in range(10):
        await asyncio.sleep(0.3)
        random_option = random.choice(options)
        try:
            await bot.edit_message_text(
                f"👹 Ищем крайнего...\n\n**Сейчас выбирается: {random_option}**",
                user_id,
                spinning_message.message_id,
                parse_mode="Markdown"
            )
        except:
            pass
    
    # Финальный результат
    scapegoat = random.choice(options)
    
    # Обновляем сообщение в ЛС
    await bot.edit_message_text(
        f"✅ Крайний найден!\n\n**Сегодня в {name} побеждает {scapegoat}**",
        user_id,
        spinning_message.message_id,
        parse_mode="Markdown"
    )
    
    # ✅ ТОЛЬКО финальный результат отправляем в группу
    if chat_id:
        await bot.send_message(
            chat_id,
            f"👹 **Сегодня в {name} побеждает {scapegoat}**",
            parse_mode="Markdown"
        )
    
    await state.clear()

# ============ ПОРЧА НА ПОНОС ============

@dp.callback_query(F.data == "ponos_order")
async def ponos_order_start(query: types.CallbackQuery, state: FSMContext):
    """Начало порчи на понос"""
    user_id = query.from_user.id
    await state.set_state(PonosOrderStates.waiting_victim)
    
    # Отправляем в ЛС
    await bot.send_message(
        user_id,
        "Введи имя жертвы поноса:"
    )
    await query.answer()

@dp.message(PonosOrderStates.waiting_victim)
async def ponos_victim_received(message: types.Message, state: FSMContext):
    """Получение имени жертвы"""
    user_id = message.from_user.id
    
    if user_id not in user_data:
        user_data[user_id] = {}
    
    user_data[user_id]['ponos'] = {
        'victim': message.text,
        'username': message.from_user.username or message.from_user.first_name
    }
    
    await state.set_state(PonosOrderStates.waiting_reason)
    # Отправляем в ЛС
    await message.answer("Почему он/она должен обосраться? (Введи причину)")

@dp.message(PonosOrderStates.waiting_reason)
async def ponos_reason_received(message: types.Message, state: FSMContext):
    """Получение причины"""
    user_id = message.from_user.id
    
    user_data[user_id]['ponos']['reason'] = message.text
    
    await state.set_state(PonosOrderStates.waiting_details)
    # Отправляем в ЛС
    await message.answer("Опиши подробности:")

@dp.message(PonosOrderStates.waiting_details)
async def ponos_details_received(message: types.Message, state: FSMContext):
    """Получение подробностей и отправка в чат"""
    user_id = message.from_user.id
    
    user_data[user_id]['ponos']['details'] = message.text
    
    # Формируем пост
    ponos_data = user_data[user_id]['ponos']
    victim = ponos_data['victim']
    reason = ponos_data['reason']
    details = ponos_data['details']
    username = ponos_data['username']
    # Используем group_chat_id вместо ponos_chat_id
    chat_id = user_data[user_id].get('group_chat_id')
    
    # Формируем текст с @username
    username_mention = f"@{username}" if not username.startswith("@") else username
    
    post_text = (
        f"💩 **Пиздец!!** Только что обнаружилось, что {victim} обосрался(лась) "
        f"при загадочных обстоятельствах: {details}\n\n"
        f"{username_mention} выдвинул предположение, что это произошло потому, что {reason}"
    )
    
    # ✅ ТОЛЬКО финальный результат отправляем в группу
    if chat_id:
        await bot.send_message(
            chat_id,
            post_text,
            parse_mode="Markdown"
        )
    
    # Отправляем подтверждение в ЛС
    await message.answer("✅ Порча выполнена! Пост отправлен в чат.")
    
    await state.clear()

# ============ ДАТЬ В ОБЛАКА ============

@dp.callback_query(F.data == "clouds")
async def clouds_start(query: types.CallbackQuery, state: FSMContext):
    """Начало функции дать в облака"""
    user_id = query.from_user.id
    await state.set_state(CloudsStates.waiting_username)
    
    # Отправляем в ЛС
    await bot.send_message(
        user_id,
        "Введи юзернейм (или имя) того, кто пукнет:"
    )
    await query.answer()

@dp.message(CloudsStates.waiting_username)
async def clouds_username_received(message: types.Message, state: FSMContext):
    """Получение юзернейма и отправка в чат"""
    user_id = message.from_user.id
    username = message.text
    # Используем group_chat_id вместо clouds_chat_id
    chat_id = user_data[user_id].get('group_chat_id')
    
    # Выбираем случайный способ пукнуть
    fart_method = random.choice(FART_METHODS)
    
    # Формируем сообщение
    fart_post = f"💨 **{username}** {fart_method}"
    
    # ✅ ТОЛЬКО финальный результат отправляем в группу
    if chat_id:
        await bot.send_message(
            chat_id,
            fart_post,
            parse_mode="Markdown"
        )
    
    # Отправляем подтверждение в ЛС
    await message.answer("✅ Пост отправлен в чат!")
    
    await state.clear()

# ============ РЕЖИМ ПОЛИНЫ ============

@dp.callback_query(F.data == "polina_mode")
async def polina_mode_start(query: types.CallbackQuery, state: FSMContext):
    """Начало Режима Полины"""
    user_id = query.from_user.id
    await state.set_state(PolinaStates.waiting_username)
    
    # Очищаем старые данные
    if user_id in user_data:
        user_data[user_id].pop('polina', None)
    
    # Отправляем в ЛС
    await bot.send_message(
        user_id,
        "Кого бы послать нахуй?🤔"
    )
    await query.answer()

@dp.message(PolinaStates.waiting_username)
async def polina_username_received(message: types.Message, state: FSMContext):
    """Получение юзернейма"""
    user_id = message.from_user.id
    
    if user_id not in user_data:
        user_data[user_id] = {}
    
    user_data[user_id]['polina'] = {
        'username': message.text
    }
    
    await state.set_state(PolinaStates.waiting_reason)
    # Отправляем в ЛС
    await message.answer("Введи причину:")

@dp.message(PolinaStates.waiting_reason)
async def polina_reason_received(message: types.Message, state: FSMContext):
    """Получение причины и отправка в чат"""
    user_id = message.from_user.id
    
    user_data[user_id]['polina']['reason'] = message.text
    
    # Формируем данные
    polina_data = user_data[user_id]['polina']
    username = polina_data['username']
    reason = polina_data['reason']
    # Используем group_chat_id вместо polina_chat_id
    chat_id = user_data[user_id].get('group_chat_id')
    
    # Форматируем юзернейм
    username_mention = f"{username}"
    
    # Формируем сообщение
    post_text = f"**{username_mention}** иди нахуй !! потому что *{reason}*"
    
    # ✅ ТОЛЬКО финальный результат отправляем в группу
    if chat_id:
        await bot.send_message(
            chat_id,
            post_text,
            parse_mode="Markdown"
        )
    
    # Отправляем подтверждение в ЛС
    await message.answer("✅ Послание отправлено в чат!")
    
    await state.clear()


# ============ ЖАЛОБЫ НА ПИДАРАСОВ ============

class ComplaintStates(StatesGroup):

    waiting_name = State()

    waiting_cabinet = State()

    waiting_reason = State()



@dp.callback_query(F.data == "complaint")

async def complaint_start(query: types.CallbackQuery, state: FSMContext):

    """Начало функции Жалобы на пидарасов"""

    user_id = query.from_user.id

    await state.set_state(ComplaintStates.waiting_name)

    

    if user_id in user_data:

        user_data[user_id].pop("complaint", None)

    

    await bot.send_message(

        user_id,

        "Какой клиент заебал тебя сегодня, солнышко?"

    )

    await query.answer()



@dp.message(ComplaintStates.waiting_name)

async def complaint_name_received(message: types.Message, state: FSMContext):

    """Получение имени клиента"""

    user_id = message.from_user.id

    

    if user_id not in user_data:

        user_data[user_id] = {}

    

    user_data[user_id]["complaint"] = {

        "name": message.text

    }

    

    await state.set_state(ComplaintStates.waiting_cabinet)

    await message.answer("а что за кабинет?")



@dp.message(ComplaintStates.waiting_cabinet)

async def complaint_cabinet_received(message: types.Message, state: FSMContext):

    """Получение кабинета"""

    user_id = message.from_user.id

    

    user_data[user_id]["complaint"]["cabinet"] = message.text

    

    await state.set_state(ComplaintStates.waiting_reason)

    await message.answer("и что эта пародия на говно тебе сделала?")



@dp.message(ComplaintStates.waiting_reason)

async def complaint_reason_received(message: types.Message, state: FSMContext):

    """Получение причины и отправка в чат"""

    user_id = message.from_user.id

    

    user_data[user_id]["complaint"]["reason"] = message.text

    

    complaint_data = user_data[user_id]["complaint"]

    name = complaint_data["name"]

    cabinet = complaint_data["cabinet"]

    reason = complaint_data["reason"]

    

    chat_id = user_data[user_id].get("group_chat_id", user_id)

    

    endings = [

        "Наведём на них порчу на понос?",

        "Обоссать и на мороз!",

        "По сусалам их старыми носками!!",

        "Чтоб им обосраться прелюдно",

        "Ноги им переломать!",

        "Долбоёбы самоутверждаются, блять!",

        "Оттаял кусок говна по весне.."

    ]

    random_ending = random.choice(endings)

    

    post_text = (

        f"ВАЖНОЕ ОБЪЯВЛЕНИЕ!! *{name}* из кабинета *{cabinet}* имеет наглость обидеть наших лапусечек!\n"

        f"*{reason}*\n"

        f"{random_ending}"

    )

    

    import base64

    from aiogram.types import BufferedInputFile

    

    img_base64 = "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"

    photo_bytes = base64.b64decode(img_base64)

    photo = BufferedInputFile(photo_bytes, filename="pidaras.jpg")

    

    if chat_id:

        await bot.send_photo(

            chat_id=chat_id,

            photo=photo,

            caption=post_text,

            parse_mode="Markdown"

        )

    

    await message.answer("✅ Жалоба отправлена в чат!")

    await state.clear()


# ============ ОСНОВНЫЕ КОМАНДЫ ============

@dp.message(Command("start"))
async def start_command(message: types.Message):
    """Команда /start"""
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Если команда в группе (chat_id != user_id)
    if chat_id != user_id:
        # Сохраняем ID группы для последующих операций
        if user_id not in user_data:
            user_data[user_id] = {}
        user_data[user_id]['group_chat_id'] = chat_id
        
        # Удаляем сообщение /start из группы
        try:
            await bot.delete_message(chat_id, message.message_id)
            logger.info(f"Сообщение /start удалено из группы {chat_id}")
        except Exception as e:
            logger.warning(f"Не удалось удалить сообщение /start: {e}")
        
        # Отправляем приветствие в ЛС
        await bot.send_message(
            user_id,
            f"Привет, {message.from_user.first_name}! 👋\n\n"
            f"Я бот для дегродских развлечений в этом ебаном чате. Выбери функцию:",
            reply_markup=get_main_keyboard()
        )
    else:
        # Если команда в ЛС, просто отправляем меню
        await message.answer(
            f"Привет, {message.from_user.first_name}! 👋\n\n"
            f"Я бот для дегродских развлечений в этом ебаном чате. Выбери функцию:",
            reply_markup=get_main_keyboard()
        )

@dp.message(Command("help"))
async def help_command(message: types.Message):
    """Команда /help"""
    help_text = (
        "📖 **Доступные функции:**\n\n"
        "👹 **Найди крайнего** - создай сеанс и выбери крайнего\n"
        "💩 **Порча на понос** - напиши смешной пост о ком-то\n"
        "💨 **Дать в облака** - смешной пост о пуке\n"
        "😈 **Режим Полины** - пошли кого-то нахуй\n\n"
        "Используй /start для начала"
    )
    await message.answer(help_text, parse_mode="Markdown")

@dp.message()
async def echo_handler(message: types.Message):
    """Обработчик остальных сообщений"""
    await message.answer(
        "Используй /start для начала или выбери функцию из меню",
        reply_markup=get_main_keyboard()
    )

# ============ POLLING ============

async def main():
    """Главная функция для запуска бота с polling"""
    logger.info("Бот запущен с использованием polling")
    
    try:
        # Удаляем вебхук если он был установлен
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Вебхук удален")
    except Exception as e:
        logger.warning(f"Ошибка при удалении вебхука: {e}")
    
    # Запускаем polling
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")

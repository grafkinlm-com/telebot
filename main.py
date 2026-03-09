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
        [InlineKeyboardButton(text="👹 Найди крайнего, ёпт", callback_data="scapegoat")],
        [InlineKeyboardButton(text="💩 Порча на понос", callback_data="ponos_order")],
        [InlineKeyboardButton(text="💨 Дать в облака", callback_data="clouds")]
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
    
    await query.message.edit_text(
        "Введи название для сеанса (например: 'Кто крайний?'):",
        reply_markup=None
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
        'options': [],
        'chat_id': message.chat.id  # Сохраняем chat_id для отправки финального результата в чат
    }
    
    await state.set_state(ScapegoatStates.waiting_options)
    # Отправляем в ЛС пользователю
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
        # Отправляем ошибку в ЛС
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
    chat_id = scapegoat_data['chat_id']
    
    # Отправляем счётчик в ЛС пользователю (не в чат!)
    spinning_message = await bot.send_message(
        user_id,  # ✅ Отправляем в ЛС
        "👹 Ищем крайнего...\n\n" + "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(options)])
    )
    
    # Имитируем прокрутку - редактируем сообщение в ЛС
    for i in range(10):
        await asyncio.sleep(0.3)
        random_option = random.choice(options)
        try:
            await bot.edit_message_text(
                f"👹 Ищем крайнего...\n\n**Сейчас выбирается: {random_option}**",
                user_id,  # ✅ Редактируем в ЛС
                spinning_message.message_id,
                parse_mode="Markdown"
            )
        except:
            pass
    
    # Финальный результат
    scapegoat = random.choice(options)
    
    # Обновляем статус в ЛС
    await bot.edit_message_text(
        f"✅ Крайний найден!\n\n**Сегодня в {name} побеждает {scapegoat}**",
        user_id,  # ✅ Обновляем в ЛС
        spinning_message.message_id,
        parse_mode="Markdown"
    )
    
    # ✅ ТОЛЬКО ФИНАЛЬНЫЙ РЕЗУЛЬТАТ отправляем в общий чат
    await bot.send_message(
        chat_id,  # Отправляем в общий чат
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
    
    await query.message.edit_text(
        "Введи имя жертвы поноса:",
        reply_markup=None
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
        'chat_id': message.chat.id,
        'username': message.from_user.username or message.from_user.first_name
    }
    
    await state.set_state(PonosOrderStates.waiting_reason)
    await message.answer("Почему он/она должен обосраться? (Введи причину)")

@dp.message(PonosOrderStates.waiting_reason)
async def ponos_reason_received(message: types.Message, state: FSMContext):
    """Получение причины"""
    user_id = message.from_user.id
    
    user_data[user_id]['ponos']['reason'] = message.text
    
    await state.set_state(PonosOrderStates.waiting_details)
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
    chat_id = ponos_data['chat_id']
    
    # Формируем текст с @username
    username_mention = f"@{username}" if not username.startswith("@") else username
    
    post_text = (
        f"💩 **Пиздец!!** Только что обнаружилось, что {victim} обосрался(лась) "
        f"при загадочных обстоятельствах: {details}\n\n"
        f"{username_mention} выдвинул предположение, что это произошло потому, что {reason}"
    )
    
    # Отправляем в чат
    await bot.send_message(
        chat_id,
        post_text,
        parse_mode="Markdown"
    )
    
    # Отправляем подтверждение в личку
    await message.answer("✅ Порча выполнена! Пост отправлен в чат.")
    
    await state.clear()

# ============ ДАТЬ В ОБЛАКА ============

@dp.callback_query(F.data == "clouds")
async def clouds_start(query: types.CallbackQuery, state: FSMContext):
    """Начало функции дать в облака"""
    user_id = query.from_user.id
    await state.set_state(CloudsStates.waiting_username)
    
    await query.message.edit_text(
        "Введи юзернейм (или имя) того, кто пукнет:",
        reply_markup=None
    )
    await query.answer()

@dp.message(CloudsStates.waiting_username)
async def clouds_username_received(message: types.Message, state: FSMContext):
    """Получение юзернейма и отправка в чат"""
    user_id = message.from_user.id
    username = message.text
    chat_id = message.chat.id
    
    # Выбираем случайный способ пукнуть
    fart_method = random.choice(FART_METHODS)
    
    # Формируем сообщение
    fart_post = f"💨 **{username}** {fart_method}"
    
    # Отправляем в чат
    await bot.send_message(
        chat_id,
        fart_post,
        parse_mode="Markdown"
    )
    
    # Отправляем подтверждение в личку
    await message.answer("✅ Пост отправлен в чат!")
    
    await state.clear()
    
# ============ ОСНОВНЫЕ КОМАНДЫ ============

@dp.message(Command("start"))
async def start_command(message: types.Message):
    """Команда /start"""
    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        f"Я бот для дегродских развлечений в этом сраном чате. Выбери функцию:",
        reply_markup=get_main_keyboard()
    )

@dp.message(Command("help"))
async def help_command(message: types.Message):
    """Команда /help"""
    help_text = (
        "📖 **Доступные функции:**\n\n"
        "👹 **Найди крайнего, ёпт** - создай сеанс и выбери крайнего\n"
        "💩 **Порча на понос** - напиши смешной пост о ком-то\n"
        "💨 **Дать в облака** - смешной пост о пуке\n"
        "🎵 **Скачай трек** - скачай трек с rus.hitmotop.com\n\n"
        "Используй /start для начала"
    )
    await message.answer(help_text, parse_mode="Markdown")

@dp.message()

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

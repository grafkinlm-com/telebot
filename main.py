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
        'chat_id': message.chat.id
    }
    
    await state.set_state(ScapegoatStates.waiting_options)
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
    
    # Отправляем в личку счётчик
    spinning_message = await bot.send_message(
        user_id,
        "👹 Ищем крайнего...\n\n" + "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(options)])
    )
    
    # Имитируем прокрутку
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
    
    # Отправляем результат в личку
    await bot.edit_message_text(
        f"✅ Крайний найден!\n\n**Сегодня в {name} побеждает {scapegoat}**",
        user_id,
        spinning_message.message_id,
        parse_mode="Markdown"
    )
    
    # Отправляем результат в чат (видят все)
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
# ============ СКАЧАЙ ТРЕК ============

async def search_track_on_hitmotop(artist: str, title: str) -> str:
    """Поиск трека на rus.hitmotop.com"""
    try:
        # Формируем поисковый запрос
        search_query = f"{artist} {title}".strip()
        search_url = f"https://rus.hitmotop.com/search?q={quote(search_query)}"
        
        logger.info(f"Ищу трек: {search_query}")
        
        # Делаем запрос
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(search_url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            logger.error(f"Ошибка при поиске: {response.status_code}")
            return None
        
        # Парсим HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Ищем ссылку на трек
        track_links = soup.find_all('a', href=True)
        
        for link in track_links:
            href = link.get('href', '')
            if href.endswith('.mp3') or '/download/' in href:
                # Если это относительная ссылка, добавляем домен
                if href.startswith('/'):
                    download_url = f"https://rus.hitmotop.com{href}"
                elif not href.startswith('http'):
                    download_url = f"https://rus.hitmotop.com/{href}"
                else:
                    download_url = href
                
                logger.info(f"Найдена ссылка: {download_url}")
                return download_url
        
        logger.warning("Трек не найден на сайте")
        return None
        
    except Exception as e:
        logger.error(f"Ошибка при поиске трека: {e}")
        return None

def download_track(download_url: str, artist: str, title: str) -> str:
    """Скачивание трека"""
    try:
        logger.info(f"Скачиваю трек с {download_url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(download_url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"Ошибка при загрузке: {response.status_code}")
            return None
        
        # Формируем имя файла
        filename = f"{artist} - {title}.mp3"
        # Очищаем имя файла от недопустимых символов
        filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.'))
        
        filepath = DOWNLOADS_FOLDER / filename
        
        # Сохраняем файл
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"Трек скачан: {filepath}")
        return str(filepath)
        
    except Exception as e:
        logger.error(f"Ошибка при скачивании: {e}")
        return None

@dp.callback_query(F.data == "download_track")
async def download_track_start(query: types.CallbackQuery, state: FSMContext):
    """Начало скачивания трека"""
    user_id = query.from_user.id
    await state.set_state(TrackStates.waiting_artist)
    
    await query.message.edit_text(
        "Введи имя исполнителя:",
        reply_markup=None
    )
    await query.answer()

@dp.message(TrackStates.waiting_artist)
async def track_artist_received(message: types.Message, state: FSMContext):
    """Получение исполнителя"""
    user_id = message.from_user.id
    
    if user_id not in user_data:
        user_data[user_id] = {}
    
    user_data[user_id]['track'] = {
        'artist': message.text,
        'chat_id': message.chat.id
    }
    
    await state.set_state(TrackStates.waiting_title)
    await message.answer("Введи название трека:")

@dp.message(TrackStates.waiting_title)
async def track_title_received(message: types.Message, state: FSMContext):
    """Получение названия трека и скачивание"""
    user_id = message.from_user.id
    
    user_data[user_id]['track']['title'] = message.text
    
    track_data = user_data[user_id]['track']
    artist = track_data['artist']
    title = track_data['title']
    chat_id = track_data['chat_id']
    
    # Отправляем сообщение о начале поиска
    status_msg = await message.answer(f"🔍 Ищу трек '{artist} - {title}'...")
    
    try:
        # Ищем трек
        download_url = search_track_on_hitmotop(artist, title)
        
        if not download_url:
            await bot.edit_message_text(
                f"❌ Трек '{artist} - {title}' не найден на сайте",
                user_id,
                status_msg.message_id
            )
            await state.clear()
            return
        
        # Обновляем статус
        await bot.edit_message_text(
            f"⬇️ Скачиваю трек '{artist} - {title}'...",
            user_id,
            status_msg.message_id
        )
        
        # Скачиваем трек
        filepath = download_track(download_url, artist, title)
        
        if not filepath or not os.path.exists(filepath):
            await bot.edit_message_text(
                f"❌ Ошибка при скачивании трека",
                user_id,
                status_msg.message_id
            )
            await state.clear()
            return
        
        # Отправляем трек в чат
        with open(filepath, 'rb') as audio:
            await bot.send_audio(
                chat_id,
                audio,
                title=title,
                performer=artist,
                caption=f"🎵 {artist} - {title}"
            )
        
        # Обновляем статус
        await bot.edit_message_text(
            f"✅ Трек '{artist} - {title}' успешно загружен!",
            user_id,
            status_msg.message_id
        )
        
        # Удаляем файл после отправки
        try:
            os.remove(filepath)
        except:
            pass
        
    except Exception as e:
        logger.error(f"Ошибка при скачивании трека: {e}")
        await bot.edit_message_text(
            f"❌ Ошибка: {str(e)}",
            user_id,
            status_msg.message_id
        )
    
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

import asyncio
import logging
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime, timedelta
import requests

API_TOKEN = 'your token'
HOROSCOPE_API_URL = 'https://horoscopes.rambler.ru/'  # Замените на реальный URL вашего API гороскопа
zodiac_signs = {
    "♈️": "aries",
    "♉️": "taurus",
    "♊️": "gemini",
    "♋️": "cancer",
    "♌️": "leo",
    "♍️": "virgo",
    "♎️": "libra",
    "♏️": "scorpio",
    "♐️": "sagittarius",
    "♑️": "capricorn",
    "♒️": "aquarius",
    "♓️": "pisces"
}

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Состояния
class Form:
    zodiac = 'zodiac'
    horoscope = 'horoscope'

# Клавиатура для выбора знака зодиака
zodiac_buttons = [
    [KeyboardButton(text="♈️"), KeyboardButton(text="♉️"), KeyboardButton(text="♊️"), KeyboardButton(text="♋️")],
    [KeyboardButton(text="♌️"), KeyboardButton(text="♍️"), KeyboardButton(text="♎️"), KeyboardButton(text="♏️")],
    [KeyboardButton(text="♐️"), KeyboardButton(text="♑️"), KeyboardButton(text="♒️"), KeyboardButton(text="♓️")]
]

zodiac_keyboard = ReplyKeyboardMarkup(keyboard=zodiac_buttons, resize_keyboard=True, one_time_keyboard=True, input_field_placeholder="Воспользуйтесь меню:")

# Хранение гороскопов
user_horoscopes = {}

# Функция для получения гороскопа
def get_horoscope(zodiac):
    # Замените на ваш метод получения гороскопа
    response = requests.get(f"https://horoscopes.rambler.ru/{zodiac}/")
    if response.status_code == 200:
        # Парсим HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup
    else:
        return f"Ошибка при получении страницы: {response.status_code}"

def format_horoscope(soup):
    # Инициализируем словарь для хранения данных
    horoscope_data = {}

    # Извлекаем заголовок (знак зодиака)
    title = soup.find('h1', class_='axVQ8 ky3yC jNRwu b1dta')
    if title:
        horoscope_data['zodiac_sign'] = title.text.strip()

    # Извлекаем дату
    date = soup.find('span', class_='s5XIp fd56h eTVjl')
    if date:
        horoscope_data['date'] = date.text.strip()

    # Извлекаем текст гороскопа
    description = soup.find('div', class_='dGWT9 cidDQ').find('p')
    if description:
        horoscope_data['description'] = description.text.strip()

    return horoscope_data   

# Функция для отправки гороскопа
async def send_horoscope(user_id, zodiac_name, horoscope):
    text = f"Ваш знак зодиака: {zodiac_name}\nГороскоп на сегодня: {horoscope}"
    # Отправка изображения, если оно есть
    if 'image_url' in horoscope:
        await bot.send_photo(user_id, horoscope['image_url'], caption=text)
    else:
        await bot.send_message(user_id, text)

# Команда /start
@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("Привет! Выберите свой знак зодиака:", reply_markup=zodiac_keyboard)

# Обработка выбора знака зодиака
@dp.message(lambda message: message.text in zodiac_signs)
async def process_zodiac(message: types.Message):
    zodiac_name = zodiac_signs[message.text]
    await message.reply(f"Ваш знак зодиака: {zodiac_name}")
    logging.info(f"Получен знак зодиака: {zodiac_name}")

    # Получаем гороскоп
    data = get_horoscope(zodiac_name)
    horoscope =  format_horoscope(data)

    if horoscope:
        await send_horoscope(message.from_user.id, horoscope['zodiac_sign'], horoscope['description'])
    else:
        await message.answer("Не удалось получить гороскоп.")

# Команда /change_zodiac
@dp.message(Command('change_zodiac'))
async def cmd_change_zodiac(message: types.Message):
    await message.answer("Выберите новый знак зодиака:", reply_markup=zodiac_keyboard)

# Команда /clear_history
@dp.message(Command('clear_history'))
async def cmd_clear_history(message: types.Message):
    if message.from_user.id in user_horoscopes:
        zodiac_sign = user_horoscopes[message.from_user.id][0]
        user_horoscopes[message.from_user.id] = (zodiac_sign, None)
        zodiac_sign = user_horoscopes[message.from_user.id][0]
        user_horoscopes[message.from_user.id] = (zodiac_sign, None)
        await message.answer("История очищена. Вы можете выбрать новый знак зодиака с помощью /change_zodiac.")
    else:
        await message.answer("История сообщений пуста.")

# Обработка всех других сообщений
@dp.message()
async def handle_unknown(message: types.Message):
    await message.answer("Извините, я не понял.")

# Функция для отправки гороскопа каждый день в 10 утра
async def scheduler():
    while True:
        now = datetime.now()
        # Устанавливаем время на 10:00 следующего дня
        target_time = now.replace(hour=10, minute=0, second=0, microsecond=0)
        if now > target_time:
            target_time += timedelta(days=1)

        wait_time = (target_time - now).total_seconds()
        await asyncio.sleep(wait_time)

        # Отправка гороскопа всем пользователям
        for user_id, (zodiac_sign, _) in user_horoscopes.items():
            horoscope = get_horoscope(zodiac_sign)
            if horoscope:
                user_horoscopes[user_id] = (zodiac_sign, horoscope)
                await send_horoscope(user_id, zodiac_sign, horoscope)

async def main():
    loop = asyncio.get_event_loop()
    loop.create_task(scheduler())  # Запускаем планировщик
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

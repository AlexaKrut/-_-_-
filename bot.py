import asyncio
import logging
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from datetime import datetime, timedelta
import requests


API_TOKEN = 'your bot token'
HOROSCOPE_API_URL = 'https://horoscopes.rambler.ru'
SECOND_HOROSCOPE_API_URL = 'https://goroskop365.ru'

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

zodiac_images = {
    "aries": "https://i.pinimg.com/564x/a9/5c/73/a95c734313804ed2ede38483868a08d1.jpg",
    "taurus": "https://i.pinimg.com/564x/d3/fd/16/d3fd16c46ee0c5ff04a4dbdad77aacbf.jpg",
    "gemini": "https://i.pinimg.com/564x/3a/7a/6c/3a7a6c6cefd8aace2af6ffaa71399ad2.jpg",
    "cancer": "https://i.pinimg.com/564x/bd/c7/27/bdc72707bb0d5049d30a796f8db7c67c.jpg",
    "leo": "https://i.pinimg.com/564x/b3/e0/6e/b3e06e00efb76e3c64b4e078879aa1b0.jpg",
    "virgo": "https://i.pinimg.com/564x/f6/c6/fe/f6c6fe21303d7f67c2d99536ffdcac19.jpg",
    "libra": "https://i.pinimg.com/564x/a7/43/59/a74359ca1d211996bffe291ffd51bc40.jpg",
    "scorpio": "https://i.pinimg.com/564x/fb/52/06/fb5206ad15d5600507ef315b42e06113.jpg",
    "sagittarius": "https://i.pinimg.com/564x/fd/87/00/fd8700b592e99e76641aaaea320bfe45.jpg",
    "capricorn": "https://i.pinimg.com/564x/95/ea/d1/95ead1538d3ecfae9b27143b0ea66b73.jpg",
    "aquarius": "https://i.pinimg.com/564x/8b/cd/a4/8bcda40cc833c6e2bcbcce714bee1ea7.jpg",
    "pisces": "https://i.pinimg.com/564x/1d/2b/df/1d2bdf0b6bf64d33204d12f48e28ad0f.jpg"
}

# Хранение информации о пользователях
user_data = {}

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Клавиатура для выбора знака зодиака
zodiac_buttons = [
  [KeyboardButton(text="♈️"), KeyboardButton(text="♉️"), KeyboardButton(text="♊️"), KeyboardButton(text="♋️")],
  [KeyboardButton(text="♌️"), KeyboardButton(text="♍️"), KeyboardButton(text="♎️"), KeyboardButton(text="♏️")],
  [KeyboardButton(text="♐️"), KeyboardButton(text="♑️"), KeyboardButton(text="♒️"), KeyboardButton(text="♓️")]
]

zodiac_keyboard = ReplyKeyboardMarkup(keyboard=zodiac_buttons, resize_keyboard=True, one_time_keyboard=True)

# Функция для получения гороскопа
def get_horoscope(zodiac, source='first'):
    if source == 'first':
        response = requests.get(f"{HOROSCOPE_API_URL}/{zodiac}/")
    else:
        response = requests.get(f"{SECOND_HOROSCOPE_API_URL}/{zodiac}/")
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup
    else:
        logging.error(f"Failed to get horoscope from {source}. Status code: {response.status_code}")
        return None

def format_horoscope_first_site(soup):
    # Форматирование для первого сайта
    horoscope_data = {}
    title = soup.find('h1', class_='axVQ8 ky3yC jNRwu b1dta')
    if title:
        horoscope_data['zodiac_sign'] = title.text.strip()
    date = soup.find('span', class_='s5XIp fd56h eTVjl')
    if date:
        horoscope_data['date'] = date.text.strip()
    description = soup.find('div', class_='dGWT9 cidDQ').find('p')
    if description:
        horoscope_data['description'] = description.text.strip()
    return horoscope_data

def format_horoscope_second_site(soup):
    # Форматирование для второго сайта
    horoscope_data = {}
    title = soup.find('h1', itemprop='name')  # Пример селектора для второго сайта
    if title:
        horoscope_data['zodiac_sign'] = title.text.strip()
    date = soup.find('div', class_='date')  # Пример селектора для даты
    if date:
        horoscope_data['date'] = date.text.strip()
    description = soup.find('div', class_='content_wrapper horoborder')  # Пример селектора для описания
    if description:
        paragraphs = description.find_all('p')
        horoscope_data['description'] = ' '.join([p.text.strip() for p in paragraphs])
    return horoscope_data

# Функция для отправки гороскопа
async def send_horoscope(user_id, zodiac_sign, horoscope):
    text = f"Гороскоп на <b>{horoscope['date']}</b>:\n{horoscope['description']}"
    
    # Получаем URL изображения из словаря
    image_url = zodiac_images.get(zodiac_sign)
    
    # Если URL изображения существует, отправляем его
    if image_url:
        await bot.send_photo(user_id, image_url, caption=text, reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Обновить", callback_data="refresh_horoscope")]
            ]
        ), parse_mode="html")
    else:
        await bot.send_message(user_id, text, reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Обновить", callback_data="refresh_horoscope")]
            ]
        ), parse_mode="html")

# Команда /start
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer("Привет! Выберите свой знак зодиака:", reply_markup=zodiac_keyboard)

# Обработка выбора знака зодиака
@dp.message(lambda message: message.text in zodiac_signs)
async def process_zodiac(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    zodiac_sign = zodiac_signs[message.text]
    user_data[user_id] = {'zodiac_sign': zodiac_sign}

    await message.answer(f"Ваш знак зодиака: {zodiac_sign}")

    # Получение и отправка гороскопа
    horoscope = get_horoscope(zodiac_sign)
    if horoscope:
        horoscope_data = format_horoscope_first_site(horoscope)
        user_data[user_id]['horoscope'] = horoscope_data
        await send_horoscope(user_id, zodiac_sign, horoscope_data)

# Обработка нажатия на кнопку "Обновить"
@dp.callback_query(lambda c: c.data == 'refresh_horoscope')
async def refresh_horoscope(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    zodiac_sign = user_data[user_id]['zodiac_sign']
    
    last_source = user_data[user_id].get('last_source', 'first')
    new_source = 'second' if last_source == 'first' else 'first'
    
    horoscope = get_horoscope(zodiac_sign, source=new_source)
    horoscope_data = None

    if new_source == 'first':
        horoscope_data = format_horoscope_first_site(horoscope)
    else:
        horoscope_data = format_horoscope_second_site(horoscope)

    if horoscope_data:
        user_data[user_id]['horoscope'] = horoscope_data
        user_data[user_id]['last_source'] = new_source
        
        await send_horoscope(user_id, zodiac_sign, horoscope_data)
    else:
        await callback_query.answer("Не удалось получить новый гороскоп.")

# Команда /update
@dp.message(Command('update'))
async def update_horoscope(message: types.Message):
    user_id = message.from_user.id
    zodiac_sign = user_data[user_id].get('zodiac_sign')

    if not zodiac_sign:
        await message.answer("Сначала выберите знак зодиака.")
        return

    last_source = user_data[user_id].get('last_source', 'first')
    new_source = 'second' if last_source == 'first' else 'first'

    horoscope = get_horoscope(zodiac_sign, source=new_source)
    if horoscope:
        if new_source == 'first':
            horoscope_data = format_horoscope_first_site(horoscope)
        else:
            horoscope_data = format_horoscope_second_site(horoscope)

        user_data[user_id]['horoscope'] = horoscope_data
        user_data[user_id]['last_source'] = new_source
        await send_horoscope(user_id, zodiac_sign, horoscope_data)
    else:
        await message.answer("Не удалось обновить гороскоп. Попробуйте позже.")

# Команда /change_zodiac
@dp.message(Command('change_zodiac'))
async def cmd_change_zodiac(message: types.Message):
    await message.answer("Выберите новый знак зодиака:", reply_markup=zodiac_keyboard)

# Команда /clear_history
@dp.message(Command('clear_history'))
async def cmd_clear_history(message: types.Message):
    user_id = message.from_user.id
    if user_id in user_data:
        zodiac_sign = user_data[user_id]['zodiac_sign']
        await message.answer(f"Ваш знак зодиака: {zodiac_sign}")
        await message.delete()
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
        target_time = now.replace(hour=10, minute=0, second=0, microsecond=0)
        
        if now > target_time:
            target_time += timedelta(days=1)

        wait_time = (target_time - now).total_seconds()
        await asyncio.sleep(wait_time)

        # Отправка гороскопа всем пользователям
        for user_id, data in user_data.items():
            zodiac_sign = data['zodiac_sign']
            last_horoscope_date = data.get('horoscope', {}).get('date')

            # Проверяем, есть ли гороскоп на сегодня
            if last_horoscope_date != datetime.now().strftime('%Y-%m-%d'):
                horoscope = get_horoscope(zodiac_sign, source='first')  # Получаем гороскоп только с первого сайта
                if horoscope:
                    horoscope_data = format_horoscope_first_site(horoscope)  # Форматируем данные с первого сайта
                    user_data[user_id]['horoscope'] = horoscope_data
                    await send_horoscope(user_id, zodiac_sign, horoscope_data)  # Отправляем гороскоп
                else:
                    # Можно добавить логику для уведомления пользователя об ошибке
                    await send_horoscope(user_id, zodiac_sign, "Не удалось получить гороскоп. Попробуйте позже.")

# Запуск бота и планировщика
async def main():
    loop = asyncio.get_event_loop()
    loop.create_task(scheduler())
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())   

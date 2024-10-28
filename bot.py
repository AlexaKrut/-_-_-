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
import random

API_TOKEN = 'yours'
HOROSCOPE_API_URL = 'https://horoscopes.rambler.ru/'  # Замените на реальный URL вашего API гороскопа
UNSPLASH_API_KEY = 'yours'
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

# Клавиатура для выбора знака зодиака
zodiac_buttons = [
  [KeyboardButton(text="♈️"), KeyboardButton(text="♉️"), KeyboardButton(text="♊️"), KeyboardButton(text="♋️")],
  [KeyboardButton(text="♌️"), KeyboardButton(text="♍️"), KeyboardButton(text="♎️"), KeyboardButton(text="♏️")],
  [KeyboardButton(text="♐️"), KeyboardButton(text="♑️"), KeyboardButton(text="♒️"), KeyboardButton(text="♓️")]
]

zodiac_keyboard = ReplyKeyboardMarkup(keyboard=zodiac_buttons, resize_keyboard=True, one_time_keyboard=True)

main_menu_buttons = [
  [KeyboardButton(text="/start"), KeyboardButton(text="/change_zodiac")],
  [KeyboardButton(text="/update"), KeyboardButton(text="/clear_history")]
]

main_menu_keyboard = ReplyKeyboardMarkup(keyboard=main_menu_buttons, resize_keyboard=True)

# Хранение информации о пользователях
user_data = {}

# Функция для получения гороскопа
def get_horoscope(zodiac):
  response = requests.get(f"{HOROSCOPE_API_URL}/{zodiac}/")
  if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup
  else:
    return None

def format_horoscope(soup):
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

# Функция для отправки гороскопа
async def send_horoscope(user_id, zodiac_sign, horoscope):
    text = f"Ваш знак зодиака: {zodiac_sign}\nГороскоп на {horoscope['date']}: {horoscope['description']}"
    
    image_url = await get_unsplash_image(zodiac_sign)
    if image_url:
        await bot.send_photo(
            chat_id=user_id,
            photo=image_url, 
            caption=text,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="Обновить", callback_data="refresh_horoscope")]
                ]
            )
        )
    else:
        await bot.send_message(chat_id=user_id, text=text, reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="Обновить", callback_data="refresh_horoscope")]
                ]
            )
        )


async def get_unsplash_image(query):
  url = 'https://api.unsplash.com/search/photos'
  query = query
  params = {
    'query': query,
    'client_id': UNSPLASH_API_KEY,
    'per_page': 1,
    'include' : 'zodiac sign',
    'exclude' : 'illness and doctors',
    'page': random.randint(1, 10) # Добавляем случайную страницу
  }
  response = requests.get(url, params=params)
  if response.status_code == 200:
    data = response.json()
    if data['results']:
      return data['results'][0]['urls']['regular']
  return None

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
        horoscope_data = format_horoscope(horoscope)
        user_data[user_id]['horoscope'] = horoscope_data
        await send_horoscope(user_id, zodiac_sign, horoscope_data)
    
    await message.answer("Что вы хотите сделать?", reply_markup=main_menu_keyboard)

# Обработка нажатия на кнопку "Обновить"
@dp.callback_query(lambda c: c.data == 'refresh_horoscope')
async def refresh_horoscope(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    zodiac_sign = user_data[user_id]['zodiac_sign']

    # Получение и отправка обновленного гороскопа
    horoscope = get_horoscope(zodiac_sign)
    if horoscope:
        horoscope_data = format_horoscope(horoscope)
        user_data[user_id]['horoscope'] = horoscope_data
        await send_horoscope(user_id, zodiac_sign, horoscope_data)
    await callback_query.message.edit_text(
        f"Ваш знак зодиака: {zodiac_sign}\nГороскоп на {horoscope_data['date']}: {horoscope_data['description']}",
        reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Обновить", callback_data="refresh_horoscope")]
        ]
        )
    )

# Команда /update
@dp.message(Command('update'))
async def cmd_update(message: types.Message):
    user_id = message.from_user.id
    if user_id in user_data: 
        zodiac_sign = user_data[user_id]['zodiac_sign']
        horoscope = get_horoscope(zodiac_sign)
        if horoscope:
            horoscope_data = format_horoscope(horoscope)
            user_data[user_id]['horoscope'] = horoscope_data
            await send_horoscope(user_id, zodiac_sign, horoscope_data)
        else:
            await message.answer("Извините, гороскоп на сегодня недоступен.")

    await message.answer("Что вы хотите сделать?", reply_markup=main_menu_keyboard)

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
    await message.answer("Что вы хотите сделать?", reply_markup=main_menu_keyboard)


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

        wait_time = (target_time- now).total_seconds()
        await asyncio.sleep(wait_time)

        # Отправка гороскопа всем пользователям
        for user_id, data in user_data.items():
            zodiac_sign = data['zodiac_sign']
            last_horoscope_date = data.get('horoscope', {}).get('date')
            if last_horoscope_date != datetime.now().strftime('%Y-%m-%d'):
                horoscope = get_horoscope(zodiac_sign)
                if horoscope:
                    horoscope_data = format_horoscope(horoscope)
                    user_data[user_id]['horoscope'] = horoscope_data
                    await send_horoscope(user_id, zodiac_sign, horoscope_data)

# Запуск бота и планировщика
async def main():
    loop = asyncio.get_event_loop()
    loop.create_task(scheduler())
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())   

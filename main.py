import json
import aiohttp
import asyncio
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, ReplyKeyboardRemove
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

# Initialize bot and dispatcher with memory storage
bot = Bot('6963877013:AAFUrMcy-J8K6syj4_KLoEZVuMbCZ2hFpt0')
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Define states
class Form(StatesGroup):
    name = State()
    location = State()
    manual_location = State()
    phone_number = State()
    manual_phone_number = State()

# Temporary storage for user data
user_data = {}

# Function for sending data to Telegram
async def send_data_to_telegram(data):
    await bot.send_message(chat_id="-4259361566", text=data)

# Function for fetching data from a website
async def fetch_data_from_website():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('https://shukuril.github.io/html-css-js-py/') as response:
                data = await response.json()
                return data
    except Exception as e:
        print("Veb-saytdan maʼlumotlarni olishda xatolik yuz berdi:", e)
        return None

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await Form.name.set()
    await message.answer('Salom! Ismingiz nima?', reply_markup=ReplyKeyboardRemove())

@dp.message_handler(state=Form.name)
async def ask_name(message: types.Message, state: FSMContext):
    user_data['name'] = message.text
    location_markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    location_markup.add(KeyboardButton('Geografik joylashuvni yuborish', request_location=True))
    location_markup.add(KeyboardButton('Qo\'lda kiriting'))
    await Form.next()
    await message.answer('Etkazib berish joyini ko\'rsating:', reply_markup=location_markup)

@dp.message_handler(lambda message: message.text == 'Qo\'lda kiriting', state=Form.location)
async def manual_location(message: types.Message):
    await Form.manual_location.set()
    await message.answer('Yetkazib berish manzilini kiriting:')

@dp.message_handler(state=Form.manual_location)
async def receive_manual_location(message: types.Message, state: FSMContext):
    user_data['location'] = message.text
    await ask_phone_number(message)

@dp.message_handler(content_types=['location'], state=Form.location)
async def receive_location(message: types.Message, state: FSMContext):
    latitude = message.location.latitude
    longitude = message.location.longitude
    user_data['location'] = f"https://www.google.com/maps/search/?api=1&query={latitude},{longitude}"
    await ask_phone_number(message)

async def ask_phone_number(message: types.Message):
    phone_markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    phone_markup.add(KeyboardButton('Telefon raqamini yuboring', request_contact=True))
    phone_markup.add(KeyboardButton('Qo\'lda kiriting'))
    await Form.phone_number.set()
    await message.answer('Iltimos, telefon raqamingizni yuboring:', reply_markup=phone_markup)

@dp.message_handler(lambda message: message.text == 'Qo\'lda kiriting', state=Form.phone_number)
async def manual_phone_number(message: types.Message):
    await Form.manual_phone_number.set()
    await message.answer('Iltimos, telefon raqamingizni kiriting:')

@dp.message_handler(state=Form.manual_phone_number)
async def receive_manual_phone_number(message: types.Message, state: FSMContext):
    user_data['phone_number'] = message.text
    await send_summary(message, state)

@dp.message_handler(content_types=['contact'], state=Form.phone_number)
async def receive_phone_number(message: types.Message, state: FSMContext):
    user_data['phone_number'] = message.contact.phone_number
    await send_summary(message, state)

async def send_summary(message: types.Message, state: FSMContext):
    summary = f"Buyurtmachini ismi: {user_data['name']}\n\nYetkazib berish joyi: {user_data['location']}\n\nTelefon raqami: {user_data['phone_number']}"
    await send_data_to_telegram(summary)
    inline_markup = ReplyKeyboardMarkup(resize_keyboard=True)
    inline_markup.add(KeyboardButton('Veb-sahifani oching', web_app=WebAppInfo(url='https://shukuril.github.io/html-css-js-py/')))
    await message.answer('Rahmat! Bu yerda sizning buyurtma ma\'lumotlaringiz:\n' + summary, reply_markup=inline_markup)
    await state.finish()

@dp.message_handler(content_types=['web_app_data'])
async def web_app(message: types.Message):
    res = json.loads(message.web_app_data.data)
    formatted_message = ""
    
    for item in res:
        summary = (
            f"======== BUYURTMACHI ========\n\n"
            f"Buyurtmachini ismi: {user_data['name']}\n"
            f"Yetkazib berish joyi: {user_data['location']}\n"
            f"Telefon raqami: {user_data['phone_number']}\n\n"
            f"==============================\n"
            f"               BUYURTMALAR    \n"
            f"==============================\n\n"
        )

    formatted_items = ""
    for item in res:
        formatted_items += (
            f"Rasm: {item['imgSrc']}\n"
            f"Ismi: {item['title']}\n"
            f"Narxi: {item['price']}\n"
            f"Soni: {item['quantity']}\n"
            f"Hajmi: {item['size']}\n"
            f"Rangi: {item['color']}\n"
            f"==============================\n"
        )

    await send_data_to_telegram(summary + formatted_items)
    await message.answer("Savatdan ma’lumotlar qabul qilinadi va Telegram’ga jo‘natiladi.")

@dp.message_handler(commands=['fetch_data'])
async def fetch_and_send_data(message: types.Message):
    website_data = await fetch_data_from_website()
    if website_data:
        await send_data_to_telegram(json.dumps(website_data, indent=4))
        await message.answer("Telegramga yuborilgan veb-saytdan olingan ma'lumotlar.")
    else:
        await message.answer("Veb-saytdan maʼlumotlarni olib boʻlmadi.")

# Start polling
executor.start_polling(dp, skip_updates=True)

import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# Танзимоти логгинг
logging.basicConfig(level=logging.INFO)

# ТОКЕНИ ТУ
API_TOKEN = '8560757080:AAFXJLy71LZTPKMmCiscpe1mWKmj3lC-hDE'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Гурӯҳи ҳолатҳо барои бақайдгирӣ
class Registration(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()

# Клавиатураи асосӣ
def get_main_keyboard():
    buttons = [
        [types.KeyboardButton(text="💎 Актуальные кейсы")],
        [types.KeyboardButton(text="📝 Регистрация в клубе")],
        [types.KeyboardButton(text="📞 Связь с админом")]
    ]
    return types.ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# Фармони /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        f"Здравствуйте, {message.from_user.first_name}! 👋\n"
        "Добро пожаловать в официальный бот Кейс-клуба.\n"
        "Выберите интересующий вас раздел:",
        reply_markup=get_main_keyboard()
    )

# 1. Тугмаи "Актуальные кейсы"
@dp.message(F.text == "💎 Актуальные кейсы")
async def show_cases(message: types.Message):
    text = (
        "📊 **Доступные кейсы на сегодня:**\n\n"
        "1️⃣ **Маркетинг:** Как привлечь первых 100 клиентов?\n"
        "2️⃣ **IT:** Автоматизация малого бизнеса через Telegram.\n"
        "3️⃣ **Финансы:** Как управлять капиталом в кризис.\n\n"
        "Выберите кейс для изучения в меню админ-панели."
    )
    await message.answer(text, parse_mode="Markdown")

# 2. Тугмаи "Связь с админом"
@dp.message(F.text == "📞 Связь с админом")
async def contact_admin(message: types.Message):
    await message.answer(
        "Наш менеджер ответит на все ваши вопросы.\n"
        "Пишите сюда: @your_admin_username"
    )

# 3. Раванди бақайдгирӣ
@dp.message(F.text == "📝 Регистрация в клубе")
async def start_registration(message: types.Message, state: FSMContext):
    await state.set_state(Registration.waiting_for_name)
    await message.answer("Для регистрации, пожалуйста, введите ваше Имя и Фамилию:")

@dp.message(Registration.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await state.set_state(Registration.waiting_for_phone)
    
    # Тугма барои фиристодани номер
    kb = [[types.KeyboardButton(text="📱 Отправить мой номер телефона", request_contact=True)]]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)
    
    await message.answer(f"Приятно познакомится, {message.text}! Теперь нажмите кнопку ниже, чтобы поделиться контактом:", reply_markup=keyboard)

@dp.message(Registration.waiting_for_phone, F.contact)
async def process_phone(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    phone_number = message.contact.phone_number
    
    await state.clear()
    
    # Ин ҷо мо маълумотро ба корбар нишон медиҳем
    await message.answer(
        f"✅ **Регистрация успешно завершена!**\n\n"
        f"👤 Имя: {user_data['full_name']}\n"
        f"📞 Телефон: {phone_number}\n\n"
        "Добро пожаловать в наше сообщество!",
        reply_markup=get_main_keyboard()
    )

# Оғози бот
async def main():
    print("Бот запущен. Проверьте Telegram!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Ошибка: {e}")

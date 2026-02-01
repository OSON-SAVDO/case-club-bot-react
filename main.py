import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from deep_translator import GoogleTranslator
from gtts import gTTS
import speech_recognition as sr
from pydub import AudioSegment

# ТОКЕНИ ШУМО
TOKEN = '8560757080:AAFXJLy71LZTPKMmCiscpe1mWKmj3lC-hDE'

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()
recognizer = sr.Recognizer()

user_modes = {}

def get_keyboard():
    buttons = [
        [InlineKeyboardButton(text="🇹🇯 Тоҷикӣ -> 🇬🇧 English", callback_data="tg_en")],
        [InlineKeyboardButton(text="🇷🇺 Русский -> 🇬🇧 English", callback_data="ru_en")],
        [InlineKeyboardButton(text="🇬🇧 English -> 🇹🇯 Тоҷикӣ", callback_data="en_tg")],
        [InlineKeyboardButton(text="🇹🇯 Тоҷикӣ -> 🇷🇺 Русский", callback_data="tg_ru")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.message(Command("start"))
async def start(message: types.Message):
    user_modes[message.from_user.id] = 'tg_en'
    await message.answer("Салом! Забонро интихоб кунед ва ба ман матн ё овоз (голос) фиристед:", reply_markup=get_keyboard())

@dp.callback_query(F.data.contains("_"))
async def set_mode(callback: types.CallbackQuery):
    user_modes[callback.from_user.id] = callback.data
    await callback.answer("Забон иваз шуд!")
    await callback.message.answer(f"✅ Ҳолати нав фаъол шуд. Фиристед!")

# КОРКАРДИ МАТН
@dp.message(F.text)
async def handle_text(message: types.Message):
    mode = user_modes.get(message.from_user.id, 'tg_en')
    src, dest = mode.split('_')
    try:
        translated = GoogleTranslator(source=src, target=dest).translate(message.text)
        tts = gTTS(text=translated, lang=dest)
        audio_path = f"res_{message.from_user.id}.mp3"
        tts.save(audio_path)
        
        await message.answer(f"📝 {translated}")
        await message.answer_voice(FSInputFile(audio_path))
        os.remove(audio_path)
    except Exception as e:
        await message.answer(f"Хатогӣ: {e}")

# КОРКАРДИ ОВОЗ (VOICE TO TEXT + TRANSLATE)
@dp.message(F.voice)
async def handle_voice(message: types.Message):
    mode = user_modes.get(message.from_user.id, 'tg_en')
    src, dest = mode.split('_')
    
    msg = await message.answer("Овозро шунида истодаам... ⏳")
    
    file_id = message.voice.file_id
    file = await bot.get_file(file_id)
    ogg_path = f"v_{message.from_user.id}.ogg"
    wav_path = f"v_{message.from_user.id}.wav"
    
    await bot.download_file(file.file_path, ogg_path)

    try:
        # Табдили формат (Дар GitHub/Сервер ин кор мекунад)
        audio = AudioSegment.from_file(ogg_path)
        audio.export(wav_path, format="wav")

        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            # Google Speech Recognition забонро вобаста ба интихоб мегирад
            stt_lang = 'tg-TJ' if src == 'tg' else 'ru-RU' if src == 'ru' else 'en-US'
            text = recognizer.recognize_google(audio_data, language=stt_lang)
            
            # Тарҷума
            translated = GoogleTranslator(source=src, target=dest).translate(text)
            
            # Табдил ба овоз (TTS)
            tts = gTTS(text=translated, lang=dest)
            res_path = f"fin_{message.from_user.id}.mp3"
            tts.save(res_path)
            
            await message.answer(f"🎤 Шумо гуфтед: {text}\n📝 Тарҷума: {translated}")
            await message.answer_voice(FSInputFile(res_path))
            os.remove(res_path)
            
    except Exception as e:
        await message.answer(f"Мутаассифона, овозро шинохта натавонистам: {e}")
    finally:
        if os.path.exists(ogg_path): os.remove(ogg_path)
        if os.path.exists(wav_path): os.remove(wav_path)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

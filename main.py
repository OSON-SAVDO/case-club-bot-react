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

# --- ТОКЕН ---
TOKEN = '8560757080:AAFXJLy71LZTPKMmCiscpe1mWKmj3lC-hDE'

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()
recognizer = sr.Recognizer()

user_modes = {}

def get_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇹🇯 Тоҷикӣ -> 🇬🇧 English", callback_data="tg_en")],
        [InlineKeyboardButton(text="🇹🇯 Тоҷикӣ -> 🇷🇺 Русский", callback_data="tg_ru")],
        [InlineKeyboardButton(text="🇷🇺 Русский -> 🇬🇧 English", callback_data="ru_en")]
    ])

@dp.message(Command("start"))
async def start(message: types.Message):
    user_modes[message.from_user.id] = 'tg_en'
    await message.answer("Салом! Забонро интихоб кунед. Ман маҳз ҳамон забонро гӯш мекунам:", reply_markup=get_keyboard())

@dp.callback_query(F.data.contains("_"))
async def set_mode(callback: types.CallbackQuery):
    user_modes[callback.from_user.id] = callback.data
    await callback.message.answer(f"✅ Ҳолати фаъол: {callback.data}")
    await callback.answer()

@dp.message(F.voice)
async def handle_voice(message: types.Message):
    mode = user_modes.get(message.from_user.id, 'tg_en')
    src, dest = mode.split('_') # Масалан: src='tg', dest='en'
    
    # Муайян кардани коди забон барои Google Speech
    # Агар 'tg' бошад, ҳатман 'tg-TJ'-ро истифода мебарем
    stt_lang = 'tg-TJ' if src == 'tg' else 'ru-RU' if src == 'ru' else 'en-US'
    
    ogg_path = f"v_{message.from_user.id}.ogg"
    wav_path = f"v_{message.from_user.id}.wav"
    
    await bot.download_file((await bot.get_file(message.voice.file_id)).file_path, ogg_path)

    try:
        # Табдил ба WAV
        AudioSegment.from_file(ogg_path).export(wav_path, format="wav")

        with sr.AudioFile(wav_path) as source:
            # Танзими овоз барои кам кардани садоҳои зиёдатӣ
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio_data = recognizer.record(source)
            
            # ШУНАВОИИ МАҲЗ БО ЗАБОНИ ИНТИХОБШУДА
            text = recognizer.recognize_google(audio_data, language=stt_lang)
            
            # Тарҷума
            translated = GoogleTranslator(source=src, target=dest).translate(text)
            
            # Табдил ба овоз (MP3)
            res_path = f"f_{message.from_user.id}.mp3"
            tts = gTTS(text=translated, lang=dest)
            tts.save(res_path)
            
            await message.answer(f"🎤 Шумо гуфтед (Тайёр): {text}\n📝 Тарҷума: {translated}")
            await message.answer_voice(FSInputFile(res_path))
            os.remove(res_path)
            
    except sr.UnknownValueError:
        await message.answer("Бубахшед, калимаҳои тоҷикиро нафаҳмидам. Лутфан равшантар гӯед.")
    except Exception as e:
        await message.answer(f"Хатогӣ: {e}")
    finally:
        for p in [ogg_path, wav_path]:
            if os.path.exists(p): os.remove(p)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

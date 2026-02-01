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

TOKEN = '8560757080:AAFXJLy71LZTPKMmCiscpe1mWKmj3lC-hDE'

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()
recognizer = sr.Recognizer()

user_modes = {}

def get_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇹🇯 Тоҷикӣ ➡️ 🇬🇧 English", callback_data="tg_en"),
         InlineKeyboardButton(text="🇬🇧 English ➡️ 🇹🇯 Тоҷикӣ", callback_data="en_tg")],
        [InlineKeyboardButton(text="🇷🇺 Русский ➡️ 🇬🇧 English", callback_data="ru_en"),
         InlineKeyboardButton(text="🇬🇧 English ➡️ 🇷🇺 Русский", callback_data="en_ru")],
        [InlineKeyboardButton(text="🇹🇯 Тоҷикӣ ➡️ 🇷🇺 Русский", callback_data="tg_ru"),
         InlineKeyboardButton(text="🇷🇺 Русский ➡️ 🇹🇯 Тоҷикӣ", callback_data="ru_tg")]
    ])

@dp.message(Command("start"))
async def start(message: types.Message):
    user_modes[message.from_user.id] = 'tg_en'
    await message.answer("Хуш омадед! Самти тарҷумаро интихоб кунед:", reply_markup=get_keyboard())

@dp.callback_query(F.data.contains("_"))
async def set_mode(callback: types.CallbackQuery):
    user_modes[callback.from_user.id] = callback.data
    m = callback.data.replace('_', ' to ')
    await callback.message.answer(f"✅ Ҳолати нав: {m.upper()}")
    await callback.answer()

@dp.message(F.voice)
async def handle_voice(message: types.Message):
    mode = user_modes.get(message.from_user.id, 'tg_en')
    src, dest = mode.split('_')
    
    # Танзими забони шунавоӣ (STT)
    stt_langs = {'tg': 'tg-TJ', 'en': 'en-US', 'ru': 'ru-RU'}
    stt_lang = stt_langs.get(src, 'en-US')
    
    ogg_path = f"v_{message.from_user.id}.ogg"
    wav_path = f"v_{message.from_user.id}.wav"
    await bot.download_file((await bot.get_file(message.voice.file_id)).file_path, ogg_path)

    try:
        # Табдил ба WAV барои шинохтан
        AudioSegment.from_file(ogg_path).export(wav_path, format="wav")
        

        with sr.AudioFile(wav_path) as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio_data = recognizer.record(source)
            # Шинохтани матни аслӣ
            original_text = recognizer.recognize_google(audio_data, language=stt_lang)
            
            # Тарҷума
            translated_text = GoogleTranslator(source=src, target=dest).translate(original_text)
            
            # Сохтани овоз (TTS)
            # gTTS барои тоҷикӣ ('tg') овоз надорад, бинобар ин 'ru'-ро барои талаффузи матни тоҷикӣ истифода мебарем
            tts_lang = dest if dest in ['en', 'ru'] else 'ru'
            res_path = f"ans_{message.from_user.id}.mp3"
            gTTS(text=translated_text, lang=tts_lang).save(res_path)
            
            # Ҷавоби дутарафа: Матни аслӣ + Тарҷума
            response_msg = (
                f"🎤 **Шумо гуфтед ({src}):**\n_{original_text}_\n\n"
                f"📝 **Тарҷума ({dest}):**\n**{translated_text}**"
            )
            
            await message.answer(response_msg, parse_mode="Markdown")
            await message.answer_voice(FSInputFile(res_path))
            
            if os.path.exists(res_path): os.remove(res_path)
            
    except Exception as e:
        await message.answer("❌ Мутаассифона, овозро фаҳмида натавонистам. Лутфан равшантар гӯед.")
    finally:
        for p in [ogg_path, wav_path]:
            if os.path.exists(p): os.remove(p)

@dp.message(F.text)
async def handle_text(message: types.Message):
    mode = user_modes.get(message.from_user.id, 'tg_en')
    src, dest = mode.split('_')
    try:
        translated = GoogleTranslator(source=src, target=dest).translate(message.text)
        tts_lang = dest if dest in ['en', 'ru'] else 'ru'
        res_path = f"t_{message.from_user.id}.mp3"
        gTTS(text=translated, lang=tts_lang).save(res_path)
        
        await message.answer(f"📝 **Тарҷума:** {translated}", parse_mode="Markdown")
        await message.answer_voice(FSInputFile(res_path))
        os.remove(res_path)
    except Exception as e:
        await message.answer(f"Хато: {e}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

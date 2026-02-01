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

# --- ТАНЗИМОТ ---
TOKEN = '8560757080:AAFXJLy71LZTPKMmCiscpe1mWKmj3lC-hDE'

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()
recognizer = sr.Recognizer()

# Нигоҳ доштани ҳолати корбар (бо нобаёнӣ Chain Translation)
user_modes = {}

def get_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 TG ➡️ RU ➡️ EN (Занҷиравӣ)", callback_data="chain_tg_ru_en")],
        [InlineKeyboardButton(text="🇹🇯 Тоҷикӣ ➡️ 🇬🇧 English", callback_data="tg_en")],
        [InlineKeyboardButton(text="🇷🇺 Русский ➡️ 🇬🇧 English", callback_data="ru_en")],
        [InlineKeyboardButton(text="🇬🇧 English ➡️ 🇷🇺 Русский", callback_data="en_ru")]
    ])

@dp.message(Command("start"))
async def start(message: types.Message):
    user_modes[message.from_user.id] = 'chain_tg_ru_en'
    await message.answer(
        "Салом! Ман боти тарҷумони ақлнок. \n"
        "Ҳолати **Занҷиравӣ (TG->RU->EN)** фаъол аст. Овоз фиристед!", 
        reply_markup=get_keyboard()
    )

@dp.callback_query(F.data.contains("_"))
async def set_mode(callback: types.CallbackQuery):
    user_modes[callback.from_user.id] = callback.data
    await callback.message.answer(f"✅ Ҳолати нав интихоб шуд: {callback.data}")
    await callback.answer()

@dp.message(F.voice)
async def handle_voice(message: types.Message):
    mode = user_modes.get(message.from_user.id, 'chain_tg_ru_en')
    
    sent_msg = await message.answer("Дар ҳоли коркард... 🔄")
    
    ogg_path = f"v_{message.from_user.id}.ogg"
    wav_path = f"v_{message.from_user.id}.wav"
    
    await bot.download_file((await bot.get_file(message.voice.file_id)).file_path, ogg_path)

    try:
        # 1. Табдил ба WAV (FFmpeg дар сервер лозим аст)
        AudioSegment.from_file(ogg_path).export(wav_path, format="wav")
        

        with sr.AudioFile(wav_path) as source:
            recognizer.adjust_for_ambient_noise(source)
            audio_data = recognizer.record(source)
            
            # Агар ҳолат занҷиравӣ бошад
            if mode == 'chain_tg_ru_en':
                # Шинохтани овоз (Тоҷикӣ)
                original_text = recognizer.recognize_google(audio_data, language='tg-TJ')
                
                # Қадами 1: TG -> RU
                russian_text = GoogleTranslator(source='tg', target='ru').translate(original_text)
                
                # Қадами 2: RU -> EN
                english_text = GoogleTranslator(source='ru', target='en').translate(russian_text)
                
                # Сохтани овоз (Англисӣ)
                res_path = f"res_{message.from_user.id}.mp3"
                gTTS(text=english_text, lang='en').save(res_path)
                
                result = (
                    f"🇹🇯 **Шумо гуфтед:** {original_text}\n"
                    f"🇷🇺 **Тарҷумаи русӣ:** {russian_text}\n"
                    f"🇬🇧 **Тарҷумаи англисӣ:** {english_text}"
                )
                await message.answer(result, parse_mode="Markdown")
                await message.answer_voice(FSInputFile(res_path))
                os.remove(res_path)
            
            else:
                # Тарҷумаи муқаррарӣ (агар тугмаҳои дигарро пахш кунед)
                src, dest = mode.split('_')
                stt_lang = 'tg-TJ' if src == 'tg' else 'ru-RU' if src == 'ru' else 'en-US'
                text = recognizer.recognize_google(audio_data, language=stt_lang)
                translated = GoogleTranslator(source=src, target=dest).translate(text)
                
                res_path = f"simple_{message.from_user.id}.mp3"
                gTTS(text=translated, lang=dest if dest in ['en', 'ru'] else 'ru').save(res_path)
                
                await message.answer(f"🎤 {text}\n📝 {translated}")
                await message.answer_voice(FSInputFile(res_path))
                os.remove(res_path)

    except Exception as e:
        await message.answer(f"❌ Хатогӣ: {e}")
    finally:
        for p in [ogg_path, wav_path]:
            if os.path.exists(p): os.remove(p)
        await sent_msg.delete()

@dp.message(F.text)
async def handle_text(message: types.Message):
    # Тарҷумаи матн низ бо мантиқи занҷиравӣ (агар фаъол бошад)
    mode = user_modes.get(message.from_user.id, 'chain_tg_ru_en')
    try:
        if mode == 'chain_tg_ru_en':
            ru = GoogleTranslator(source='tg', target='ru').translate(message.text)
            en = GoogleTranslator(source='ru', target='en').translate(ru)
            await message.answer(f"🇷🇺 Русӣ: {ru}\n🇬🇧 Англисӣ: {en}")
        else:
            src, dest = mode.split('_')
            res = GoogleTranslator(source=src, target=dest).translate(message.text)
            await message.answer(f"📝 Тарҷума: {res}")
    except Exception as e:
        await message.answer(f"Хато: {e}")

async main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

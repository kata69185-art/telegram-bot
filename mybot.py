import os, asyncio, aiohttp
from aiogram import Bot, Dispatcher, types
from aiohttp import web

BOT_TOKEN = os.environ.get("BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_VOICE_KEY = os.environ.get("GROQ_VOICE_KEY") 

SYSTEM = "Ты — дружелюбный помощник. Отвечай кратко и по делу. Пиши не более 2-3 предложений за раз."

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_histories = {}

@dp.message()
async def handle(msg: types.Message):
    user_id = msg.from_user.id
    if user_id not in user_histories:
        user_histories[user_id] = [{"role": "system", "content": SYSTEM}]
    
    user_text = "" # Создаем переменную для текста

    # Если пришло голосовое сообщение
    if msg.voice:
        file_id = msg.voice.file_id
        file = await bot.get_file(file_id)
        file_path = f"voice_{user_id}.ogg"
        await bot.download_file(file.file_path, file_path)
        
        async with aiohttp.ClientSession() as s:
            with open(file_path, "rb") as f:
                form = aiohttp.FormData()
                form.add_field('file', f, filename='voice.ogg')
                form.add_field('model', 'whisper-large-v3')
                
                async with s.post(
                    "https://api.groq.com/openai/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {GROQ_VOICE_KEY}"},
                    data=form
                ) as r:
                    result = await r.json()
                    if 'text' in result:
                        user_text = result['text'] # Записываем текст в переменную
                        await msg.answer(f"🎤 Я услышал: {user_text}")
                    else:
                        await msg.answer("Не удалось распознать голос.")
                        return

    # Если это текстовое сообщение
    elif msg.text:
        user_text = msg.text

    if not user_text:
        return

    user_histories[user_id].append({"role": "user", "content": user_text})
    if len(user_histories[user_id]) > 11:
        user_histories[user_id] = [user_histories[user_id][0]] + user_histories[user_id][-10:]

    async with aiohttp.ClientSession() as s:
        async with s.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            json={
                "model": "openai/gpt-oss-20b",
                "messages": user_histories[user_id]
            }
        ) as r:
            data = await r.json()
            try:
                answer = data["choices"][0]["message"]["content"]
                await msg.answer(answer)
                user_histories[user_id].append({"role": "assistant", "content": answer})
            except Exception as e:
                await msg.answer(f"Ошибка: {e}")

async def web_server():
    app = web.Application()
    app.router.add_get('/', lambda r: web.Response(text="Bot is running!"))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 8080)))
    await site.start()

async def main():
    await web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

import os, asyncio, aiohttp
from aiogram import Bot, Dispatcher, types
from aiohttp import web

# Берем ключи из переменных окружения (настроим их на Render)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

SYSTEM = "Ты — дружелюбный помощник. Отвечай кратко и по делу. Пиши не более 2-3 предложений за раз."

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_histories = {}

@dp.message()
async def handle(msg: types.Message):
    user_id = msg.from_user.id
    if user_id not in user_histories:
        user_histories[user_id] = [{"role": "system", "content": SYSTEM}]
    
    user_histories[user_id].append({"role": "user", "content": msg.text})
    
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

# Этот блок нужен, чтобы Render видел, что бот работает
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

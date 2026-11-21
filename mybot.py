import telebot
import requests

BOT_TOKEN = "9243735822:AAG4LekVYNySO6EvAs8TROTFjooijkVnCyU"
GROQ_KEY = "gsk_u99U0DN0UFtkqMns8TR0TFjooijkVnCyU"

bot = telebot.TeleBot(BOT_TOKEN)
chat_history = {}

SYSTEM_PROMPT = "Ты — дружелюбный помощник. Помогаешь с бытовыми вопросами, домашкой, можешь ролить в ролевых играх. Отвечай живо и по делу. ВАЖНО: не используй таблицы, решетки (#), дефисы (---) и сложное форматирование. Пиши простым и понятным текстом."

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        
        response = requests.post(
            url="https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "openai/gpt-oss-20b",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT}
                ] + chat_history.get(message.chat.id, []) + [
                    {"role": "user", "content": message.text}
                ]
            }
        )
        
        data = response.json()
        if "choices" in data:
            answer = data["choices"][0]["message"]["content"]
            bot.reply_to(message, answer)
            
            chat_history.setdefault(message.chat.id, []).append({"role": "user", "content": message.text})
            chat_history[message.chat.id].append({"role": "assistant", "content": answer})
            
            if len(chat_history[message.chat.id]) > 10:
                chat_history[message.chat.id] = chat_history[message.chat.id][-10:]
                
        else:
            error_msg = data.get("error", {}).get("message", "Неизвестная ошибка")
            bot.reply_to(message, f"Ошибка API: {error_msg}")
            
    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка: {e}")

print("Бот запущен!")
bot.remove_webhook()
bot.polling(non_stop=True)

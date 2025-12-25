import json
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import google.generativeai as genai

# Загрузка ключей
with open('keys.json', 'r') as f:
    CONFIG = json.load(f)

class ChatOnlyBot:
    def __init__(self):
        self.keys = CONFIG['gemini_keys']
        self.current_key = 0
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start"""
        await update.message.reply_text(
            "🤖 Чат-бот с Gemini AI\n"
            "Просто напиши /q [ваше сообщение]\n\n"
            "Например: /q расскажи анекдот\n\n"
            "🔑 Автоматически переключаю ключи при лимитах"
        )
    
    async def chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Единственная команда /q"""
        if not context.args:
            await update.message.reply_text("Напиши: /q [твой вопрос]")
            return
        
        user_text = " ".join(context.args)
        await update.message.chat.send_action(action="typing")
        
        # Пробуем получить ответ
        response = await self.get_gemini_response(user_text + ". Дай сжатый и конкретный ответ.")
        
        if response:
            await update.message.reply_text(response[:4000])
        else:
            await update.message.reply_text("❌ Все ключи исчерпали лимиты")

    async def get_gemini_response(self, question: str):
        """Получить ответ, перебирая ключи"""
        
        # Пробуем каждый ключ
        for _ in range(len(self.keys)):
            key = self.keys[self.current_key]
            
            try:
                # Настраиваем Gemini
                genai.configure(api_key=key)
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                # Отправляем запрос
                response = model.generate_content(question)
                
                # Успех! Возвращаем ответ
                return response.text
                
            except Exception as e:
                error_msg = str(e)
                
                # Если лимиты - пробуем следующий ключ
                if "429" in error_msg or "quota" in error_msg.lower():
                    print(f"🔑 Ключ {self.current_key} исчерпан, пробую следующий...")
                    self.current_key = (self.current_key + 1) % len(self.keys)
                    continue
                
                # Другая ошибка
                return f"Ошибка: {error_msg[:100]}"
        
        # Все ключи исчерпаны
        return None

def main():
    bot = ChatOnlyBot()
    
    # Создаем приложение
    app = Application.builder().token(CONFIG['telegram_token']).build()
    
    # Только 2 команды
    app.add_handler(CommandHandler("start", bot.start))
    app.add_handler(CommandHandler("q", bot.chat))
    
    # Запускаем
    print("🤖 Чат-бот запущен! Только /q команда")
    app.run_polling()

if __name__ == "__main__":
    main()
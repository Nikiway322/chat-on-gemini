import json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import google.generativeai as genai
import html

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
            "Просто напиши Бот [ваше сообщение]\n\n"
            "Например: Бот расскажи анекдот\n\n"
            "🔑 Автоматически переключаю ключи при лимитах"
        )
    
    async def chat_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /q"""
        if not context.args:
            await update.message.reply_text("Напиши: Бот [твой вопрос]")
            return
        
        user_text = " ".join(context.args)
        await self.process_message(update, user_text)
    
    async def chat_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик обычных сообщений"""
        user_text = update.message.text
        
        # Проверяем, начинается ли сообщение с "Бот" (регистр не важен)
        if user_text.lower().startswith('бот'):
            # Убираем "бот" из начала сообщения
            query = user_text[3:].strip()
            
            # Если после "бот" есть текст
            if query:
                await self.process_message(update, query)
            else:
                await update.message.reply_text("Что хочешь узнать? Напиши: Бот [твой вопрос]")
    
    async def process_message(self, update: Update, user_text: str):
        """Обработка запроса пользователя"""
        await update.message.chat.send_action(action="typing")
        
        # Добавляем инструкцию к запросу
        full_query = f"{user_text}. Дай сжатый и конкретный ответ. Так же твоя речь должна быть грубая, как будто общаюсь с гопником. Если можно, то используй нецензурную лексику."
        
        # Пробуем получить ответ
        response = await self.get_gemini_response(full_query)
        
        if response:
            # Убираем форматирование - экранируем HTML символы
            escaped_response = html.escape(response)
            
            # Отправляем без форматирования
            await update.message.reply_text(
                escaped_response[:4000],
                parse_mode=None  # Отключаем форматирование
            )
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
    
    # Команды
    app.add_handler(CommandHandler("start", bot.start))
    app.add_handler(CommandHandler("q", bot.chat_command))
    
    # Обработчик обычных сообщений, начинающихся с "бот"
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,  # Только текст, не команды
        bot.chat_message
    ))
    
    # Запускаем
    print("🤖 Чат-бот запущен!")
    print("Теперь бот реагирует на:")
    print("1. /start")
    print("2. /q [вопрос]")
    print("3. Бот [вопрос] (без слеша)")
    app.run_polling()

if __name__ == "__main__":
    main()
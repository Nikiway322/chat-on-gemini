import json
import html
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
import google.generativeai as genai


# ─────── загрузка ключей ───────
with open("keys.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)


class ChatOnlyBot:
    def __init__(self):
        self.keys = CONFIG["gemini_keys"]
        self.current_key = 0
        self.bot_username = None  # узнаем при старте

    # ─────── /start ───────
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🤖 Я чат-бот\n\n"
            "Пиши:\n"
            "• Бот расскажи анекдот\n"
            "• @ИмяБота расскажи анекдот\n\n"
            "В группе тоже работаю, епта."
        )

    # ─────── обработчик текста ───────
    async def chat_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message or not update.message.text:
            return

        text = update.message.text.strip()
        text_lower = text.lower()

        query = None

        # Вариант 1: "бот ..."
        if text_lower.startswith("бот"):
            query = text[3:].strip()

        # Вариант 2: "@BotName ..."
        elif self.bot_username and text_lower.startswith(f"@{self.bot_username.lower()}"):
            query = text[len(self.bot_username) + 1:].strip()

        # Если не обращались к боту — идем нахуй
        if not query:
            return

        if not query:
            await update.message.reply_text(
                "Ты чё хотел, бля? Напиши нормально: Бот [вопрос]"
            )
            return

        await self.process_message(update, query)

    # ─────── обработка запроса ───────
    async def process_message(self, update: Update, user_text: str):
        await update.message.chat.send_action("typing")

        full_query = (
            f"{user_text}. "
            "Отвечай коротко и по делу. "
            "Говори грубо, как гопник. "
            "Можно материться."
        )

        response = await self.get_gemini_response(full_query)

        if not response:
            await update.message.reply_text("Все ключи сдохли, брат.")
            return

        formatted = self.format_response(response)

        await update.message.reply_text(
            formatted[:4000],
            parse_mode="HTML"
        )

    # ─────── форматирование ───────
    def format_response(self, text: str) -> str:
        text = html.escape(text)

        if "```" in text:
            parts = text.split("```")
            result = []

            for i, part in enumerate(parts):
                if i % 2 == 0:
                    result.append(part)
                else:
                    result.append(f"<pre><code>{part}</code></pre>")

            return "".join(result)

        return text

    # ─────── Gemini ───────
    async def get_gemini_response(self, question: str):
        for _ in range(len(self.keys)):
            key = self.keys[self.current_key]

            try:
                genai.configure(api_key=key)
                model = genai.GenerativeModel("gemini-2.5-flash")
                response = model.generate_content(question)
                return response.text

            except Exception as e:
                msg = str(e).lower()

                if "429" in msg or "quota" in msg:
                    self.current_key = (self.current_key + 1) % len(self.keys)
                    continue

                return f"Ошибка: {str(e)[:100]}"

        return None


# ─────── запуск ───────
def main():
    bot = ChatOnlyBot()

    app = Application.builder().token(CONFIG["telegram_token"]).build()

    # узнаем username бота
    async def post_init(application):
        me = await application.bot.get_me()
        bot.bot_username = me.username
        print(f"🤖 Запущен как @{bot.bot_username}")

    app.post_init = post_init

    app.add_handler(CommandHandler("start", bot.start))

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            bot.chat_message
        )
    )

    print("🤖 Бот запущен и готов хуярить")
    app.run_polling()


if __name__ == "__main__":
    main()

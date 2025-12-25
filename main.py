import google.generativeai as genai
import os

class GeminiChat:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Установите GEMINI_API_KEY или передайте ключ")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    def ask(self, question):
        try:
            response = self.model.generate_content(question)
            return response.text
        except Exception as e:
            return f"Ошибка: {e}"

# Использование
if __name__ == "__main__":
    # Способ 1: Через переменную окружения
    # export GEMINI_API_KEY="ваш_ключ"
    
    # Способ 2: Прямо в коде
    chat = GeminiChat()
    
    while True:
        user_input = input("\nВы: ")
        if user_input.lower() in ['выход', 'exit']:
            break
        print("Gemini:", chat.ask(user_input))
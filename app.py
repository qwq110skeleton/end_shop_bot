import os
import threading
import time
from flask import Flask
from end_shop_bot import bot, TOKEN  # Импортируем вашего бота
# Создаем веб-сервер Flask
app = Flask(__name__)
# Простая страница, чтобы проверить, что бот жив
@app.route('/')
def home():
    return "Бот End_Shop работает!"
# Страница для "здоровья" бота, которую будет проверять Render
@app.route('/health')
def health():
    return "OK", 200
# Функция, которая запускает вашего бота в фоновом режиме
def run_bot():
    try:
        print("Запуск бота End_Shop...")
        bot.polling(none_stop=True, interval=0)
    except Exception as e:
        print(f"Ошибка в боте: {e}")
        time.sleep(5)
if __name__ == '__main__':
    # Запускаем бота в отдельном потоке, чтобы он не блокировал веб-сервер
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    # Запускаем веб-сервер, чтобы Render не ругался
    # Порт берется из переменной окружения PORT, которую дает Render
    port = int(os.environ.get('PORT', 5000))
    print(f"Запуск веб-сервера на порту {port}...")
    app.run(host='0.0.0.0', port=port)

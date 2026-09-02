import os
import threading
import time
from flask import Flask
from end_shop_bot import bot

app = Flask(__name__)

@app.route('/')
def home():
    return "Бот End_Shop работает!"

@app.route('/health')
def health():
    return "OK", 200

def run_bot():
    time.sleep(5)  # Даём время на инициализацию веб-сервера и сети
    try:
        print("Запуск бота End_Shop...")
        bot.polling(none_stop=True, interval=0)
    except Exception as e:
        print(f"Ошибка в боте: {e}")
        time.sleep(5)

if __name__ == '__main__':
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    # Запускаем веб-сервер Flask
    port = int(os.environ.get('PORT', 5000))
    print(f"Запуск веб-сервера на порту {port}...")
    app.run(host='0.0.0.0', port=port)

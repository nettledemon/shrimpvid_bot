from config import get_bot_token
from bot import get_application

# точка входа
def main():
    token = get_bot_token()
    app = get_application(token)
    print("Бот запущен. Жми Ctrl+C для остановки.")
    app.run_polling()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nБот остановлен")
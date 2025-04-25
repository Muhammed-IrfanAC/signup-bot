import threading
import os

# Run Flask app
def run_api():
    os.system("python app.py")

# Run Discord bot
def run_bot():
    os.system("python bot.py")

if __name__ == "__main__":
    t1 = threading.Thread(target=run_api)
    t2 = threading.Thread(target=run_bot)

    t1.start()
    t2.start()

    t1.join()
    t2.join()

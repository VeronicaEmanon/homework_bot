import logging
import os
import time
from http import HTTPStatus

import telegram
import requests
from dotenv import load_dotenv
# from telegram import Bot

load_dotenv()
PRACTICUM_TOKEN = os.getenv("PRACTICUM_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    level=logging.INFO,
    filename='program.log',
    # filemode='w',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())


def send_message(bot, message):
    """Отправка сообщения в чат."""
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message
        )
        logger.info(f"Сообщение удачно отправлено:'{message}'")
    except telegram.TelegramError as message:
        logger.error(
            f"Ошибка при отправке сообщения '{message}'."
        )


def get_api_answer(current_timestamp):
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    api_answer = {
        'url': ENDPOINT,
        'headers': HEADERS,
        'params': params
    }
    logger.info
    try:
        response = requests.get(**api_answer)
    except Exception as error:
        logger.error(
            f"Ошибка отправки эндпоинта {error}"
        )
    if response.status_code != HTTPStatus.OK:
        st_code_message = (f"Ошибка статус кода {response.status_code}")
        raise KeyError(st_code_message)
    return response.json()


def check_response(response):
    logger.info
    if not isinstance(response, dict):
        logger.error("Это не словарь")
        raise TypeError("Это не словарь")
    if not isinstance(response["homeworks"], list):
        logger.error("Это не список")
        raise TypeError("Это не список")
    try:
        homework = response['homeworks']
    except Exception:
        logger.error('Ошибка')
    return homework


def parse_status(homework):
    logger.info
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    try:
        verdict = HOMEWORK_STATUSES[homework_status]
    except Exception as error:
        logger.error(
            f'Нет соответствия по ключевым словам {error}.'
        )
        raise KeyError(
            f"Нет соответствия по ключевым словам {error}."
        )
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    if all([
        PRACTICUM_TOKEN,
        TELEGRAM_TOKEN,
        TELEGRAM_CHAT_ID
    ]):
        return True
    else:
        return False


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        raise ValueError('Несоответсвие по токенам')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(current_timestamp)
            current_timestamp = response['current_date']
            homeworks = check_response(response)
            for homework in homeworks:
                homework_status = parse_status(homework)
                send_message(bot, homework_status)
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            time.sleep(RETRY_TIME)
        else:
            message = parse_status(homework)
            send_message(bot, message)


if __name__ == '__main__':
    main()

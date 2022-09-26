import logging
import os
import time
from http import HTTPStatus
import telegram
import requests
from dotenv import load_dotenv

load_dotenv()
PRACTICUM_TOKEN = os.getenv("PRACTICUM_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

RETRY_TIME: int = 60 * 60 * 10
ENDPOINT = "https://practicum.yandex.ru/api/user_api/homework_statuses/"
HEADERS = {"Authorization": f"OAuth {PRACTICUM_TOKEN}"}


HOMEWORK_VERDICTS = {
    "approved": "Работа проверена: ревьюеру всё понравилось. Ура!",
    "reviewing": "Работа взята на проверку ревьюером.",
    "rejected": "Работа проверена: у ревьюера есть замечания."
}


class StatusCodeError(Exception):
    """Ошибка статус кода страницы."""


logging.basicConfig(
    level=logging.DEBUG,
    filename="program.log",
    filemode="w",
    format="%(asctime)s, %(levelname)s, %(message)s, %(name)s"
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
        logger.info(
            f"Сообщение удачно отправлено:'{message}'."
        )
    except telegram.TelegramError as message:
        raise KeyError(
            f"Ошибка при отправке сообщения '{message}'."
        )


def get_api_answer(current_timestamp):
    """Ответ от API Практикум.Домашка."""
    timestamp = current_timestamp or int(time.time())
    params = {"from_date": timestamp}
    hw_statuses = {
        "url": ENDPOINT,
        "headers": HEADERS,
        "params": params
    }
    logger.info("Проверям получен ли ответ от API Практикум.Домашка")
    try:
        response = requests.get(**hw_statuses)
        if response.status_code != HTTPStatus.OK:
            st_code_message = (
                f"Ошибка статус кода страницы {response.status_code}."
            )
            raise StatusCodeError(st_code_message)
    except Exception as error:
        raise KeyError(
            f"Ошибка при запросе к эндпоинту {error}."
        )
    return response.json()


def check_response(response):
    """Корректность ответа от API."""
    logger.info("Проверяем корректность ответа от API.")
    if not isinstance(response, dict):
        raise TypeError("Ответ API не словарь.")
    if "homeworks" not in response:
        raise KeyError("Нет ключа 'homeworks' в ответе от API")
    homework = response["homeworks"]
    if not isinstance(homework, list):
        raise TypeError("Ответ API 'homeworks' ожидает список")
    return homework


def parse_status(homework):
    """Извлекаем информацию о конкретной домашней работе."""
    logger.info("Извлекаем информацию о конкретной домашней работе.")
    if "homework_name" not in homework:
        raise KeyError(
            f"В {homework} нет ключа 'homework_name'в ответе API."
        )
    if "status" not in homework:
        raise KeyError(
            f"В {homework} нет ключа 'status' в ответе API."
        )
    homework_name = homework.get("homework_name")
    homework_status = homework.get("status")
    try:
        verdict = HOMEWORK_VERDICTS[homework_status]
    except Exception:
        raise KeyError(
            f"Статуса {homework_status} нет в 'HOMEWORK_VERDICTS'."
        )
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка наличия токенов."""
    if all([
        PRACTICUM_TOKEN,
        TELEGRAM_TOKEN,
        TELEGRAM_CHAT_ID
    ]):
        return True


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        tokenErrMSG = ("Ошибка в переменных окружения")
        logger.critical(tokenErrMSG)
        raise KeyError(tokenErrMSG)
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    status = ''
    while True:
        try:
            response = get_api_answer(current_timestamp)
            current_timestamp = response['current_date']
            homeworks = check_response(response)
            for homework in homeworks:
                message = parse_status(homework)
                if message != status:
                    send_message(bot, message)
                    status = message
        except Exception as error:
            message = (
                f"Сбой в работе программы: {error}"
            )
            logger.error(message)
            send_message(bot, message)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()

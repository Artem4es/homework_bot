from json import JSONDecodeError
from logging import StreamHandler
import logging
import os
import sys
import time

from dotenv import load_dotenv
from telegram.error import TelegramError
import requests
import telegram

from exсeptions import (
    ConnectionError,
    HomeworkStatusError,
    MessageError,
    ResponseFormatError,
)

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s, %(levelname)s, %(name)s, %(message)s, Строка: %(lineno)s,'
)
terminal_handler = StreamHandler(sys.stdout)
terminal_handler.setFormatter(formatter)
file_handler = logging.FileHandler('homework.log', encoding='UTF-8')
file_handler.setFormatter(formatter)
logger.addHandler(terminal_handler)
logger.addHandler(file_handler)


last_parse_status = None
api_errors = []


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = int(os.getenv('RETRY_PERIOD'))
ENDPOINT = os.getenv('ENDPOINT')

HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.',
}


def check_tokens():
    """Проверяет наличие необходимых переменных окружения."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def send_message(bot, message):
    """Отправка сообщения в телеграм."""
    logger.debug('Начата отправка сообщения в Telegram')
    try:
        bot.send_message(text=message, chat_id=TELEGRAM_CHAT_ID)
        logger.debug(f'Сообщение успешно отправлено: {message}')
    except TelegramError as error:
        message = f'Ошибка при отправке сообщения {error}'
        logger.error(message)
        # без логирования до raise не проходит тест не понятно почему)
        raise MessageError(message)


def get_api_answer(timestamp):
    """Получение ответа от API домашки."""
    date = {'from_date': timestamp}
    logger.debug(
        f'Начат запрос к серверу. Эндпоинт: {ENDPOINT}, headers: {HEADERS},'
        f' params: {date}'
    )
    try:
        response = requests.get(url=ENDPOINT, headers=HEADERS, params=date)
    except Exception as error:
        raise ConnectionError(f'Ошибка при запросе к API: {error}')
    response = response.json()
    check_response(response)
    homeworks = response.get('homeworks')
    return (
        homeworks[0] if homeworks else {'status': None, 'homework_name': None}
    )


def check_response(response):
    """Проверка формата ответа API."""
    logger.debug(f'Начата проверка ответа сервера: {response}')
    try:
        actual = response['homeworks']
        if not isinstance(actual, list):
            raise TypeError
    except KeyError:
        raise ResponseFormatError(response)


def parse_status(homework):
    """
    Извлекает статус последней домашки и в случае обновления статуса.
    Возвращает новый статус в виде строки.
    """
    global last_parse_status
    try:
        new_status = homework['status']
        homework_name = homework['homework_name']
    except KeyError:
        raise HomeworkStatusError(homework)  # детали хендлятся exceptions.py
    if new_status not in HOMEWORK_VERDICTS and new_status is not None:
        raise HomeworkStatusError(f'Неизвестный статус домашки: {new_status}')
    if last_parse_status != new_status:
        homework_name = homework.get('homework_name')
        verdict = HOMEWORK_VERDICTS.get(new_status)
        last_parse_status = new_status
        logger.debug(f'Новый статус домашки: {new_status}')
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    logger.debug('Статус домашки не изменился')


def main():
    """Основная логика работы бота."""
    if check_tokens():
        try:
            bot = telegram.Bot(token=TELEGRAM_TOKEN)
        except TelegramError as error:
            raise TelegramError(f'Ошибка при инциализации бота: {error}')
        timestamp = int(time.time())

        while True:
            try:
                homework = get_api_answer(timestamp)
                status = parse_status(homework)
                if status:
                    send_message(bot, status)
                time.sleep(RETRY_PERIOD)

            except JSONDecodeError as error:
                message = f'Формат ответа API не JSON: {error}'
                logger.error(message)
                if message not in api_errors:
                    send_message(bot, message)
                    api_errors.append(message)

            except MessageError as error:
                logger.error(error)

            except Exception as error:
                message = f'Сбой в работе программы: {error}'
                logger.error(message)
                if message not in api_errors:
                    send_message(bot, message)
                    api_errors.append(message)

            finally:
                time.sleep(RETRY_PERIOD)

    logger.critical('Не найдены токены! Завершение программы')
    sys.exit()


if __name__ == '__main__':
    main()

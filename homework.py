from json import JSONDecodeError
from logging import StreamHandler
import logging
import os
import sys
import time

from dotenv import load_dotenv
from telegram.error import Unauthorized
import requests
import telegram

from exсeptions import (
    BadRequestError,
    HomeworkStatusError,
    ResponseFormatError,
    SendMessageError,
)

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    filename='flashbot.log',
    format='%(asctime)s, %(levelname)s, %(name)s, %(message)s',
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = StreamHandler(sys.stdout)
logger.addHandler(handler)

last_parse_status = None
api_errors = {
    BadRequestError: False,
    JSONDecodeError: False,
    ResponseFormatError: False,
    HomeworkStatusError: False,
}

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'

HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.',
}


def check_tokens():
    """Проверяет наличие необходимых переменных окружения"""

    tokens = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID,
    }
    for token, value in tokens.items():
        if value is None:
            logger.critical(f'Недоступен токен {token}.Программа остановлена')
            exit(f'Не найден токен {token}. Программа остановлена')


def send_message(bot, message):
    """Отправка сообщения в телеграм"""

    try:
        # TypeError в тексте Unauthorized если токен
        bot.send_message(text=message, chat_id=TELEGRAM_CHAT_ID)
        logger.debug(f'Сообщение успешно отправлено: {message}')
    except Unauthorized:
        logger.error('Cообщение не отправлено. Ошибка авторизации телеграм')
        raise SendMessageError(
            f'Ошибка при отправке сообщения. Бот токен: {bot.token}, '
            f'сообщение: {message}, chat_id: {TELEGRAM_CHAT_ID}'
        )
    except Exception:
        logger.error('Что-то пошло не по плану при отправке сообщения')
        raise SendMessageError(
            f'Ошибка при отправке сообщения. Бот токен: {bot.token}, '
            f'сообщение: {message}, chat_id: {TELEGRAM_CHAT_ID}'
        )


def get_api_answer(timestamp):
    """Получение ответа от API домашки"""
    date = {'from_date': timestamp}
    try:
        response = requests.get(url=ENDPOINT, headers=HEADERS, params=date)
    except:
        raise BadRequestError(f'Неудачный запрос к эндпоинту: {ENDPOINT}')
    response = response.json()
    check_response(response)
    homeworks = response.get('homeworks')
    return (
        homeworks[0] if homeworks else {'status': None, 'homework_name': None}
    )


def check_response(response):
    """Проверка формата ответа API"""
    try:
        actual = response['homeworks']
        if not isinstance(actual, list):
            raise TypeError
    except:
        raise TypeError


def parse_status(homework):
    """
    Извлекает статус последней домашки и в случае обновления статуса
    возвращает новый статус в виде строки
    """
    global last_parse_status
    try:
        new_status = homework['status']
        homework_name = homework['homework_name']
    except:
        raise HomeworkStatusError(homework)
    if new_status not in HOMEWORK_VERDICTS and new_status != None:
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
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
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
            logger.error(error)
            if api_errors[JSONDecodeError] == False:
                send_message(bot, message)
                api_errors[JSONDecodeError] = True

        except ResponseFormatError as error:
            logger.error(error)
            message = str(error)
            if api_errors[ResponseFormatError] == False:
                send_message(bot, message)
                api_errors[ResponseFormatError] = True

        except HomeworkStatusError as error:
            logger.error(error)
            message = str(error)
            if api_errors[HomeworkStatusError] == False:
                send_message(bot, message)
                api_errors[HomeworkStatusError] = True

        except BadRequestError as error:
            logger.error(error)
            message = str(error)
            if api_errors[BadRequestError] == False:
                send_message(bot, message)
                api_errors[BadRequestError] = True

        except SendMessageError as error:
            logger.error(error)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)


if __name__ == '__main__':
    main()

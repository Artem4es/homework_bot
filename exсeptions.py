class BadRequestError(Exception):
    """Ошибка при запросе к эндпоинту."""


class ResponseFormatError(Exception):
    """Определяет тип ошибки в ответе API."""

    def __init__(self, response):
        self.response = response
        if response.get('code') == 'not_authenticated':
            self.message = response['message']
        elif response.get('code') == 'UnknownError':
            self.message = f'{response.get("error")}'
        elif 'homeworks' not in response:
            self.message = (
                f'Не найден ключ homeworks. Проверьте ответ API: {response}'
            )
        elif not isinstance(response.get('homeworks'), list):
            self.message = (
                f'Тип значения ключа homeworks не лист. '
                f'Проверьте ответ API: {response}'
            )
        else:
            self.message = (
                f'Неожиданный ответ API. Проверьте ответ API: {response}'
            )

    def __str__(self):
        return f'Ошибка следующая: {self.message}'


class HomeworkStatusError(Exception):
    """Ошибка в статусе домашней работы."""

    def __init__(self, homework):
        self.homework = homework
        status = homework.get('status', True)
        homework_name = homework.get('homework_name', True)
        if status:
            self.message = f'В ответе API нет ключа status: {homework}'
        elif homework_name:
            self.message = f'В ответе API нет ключа homework_name {homework}'

    def __str__(self):
        return self.message


class SendMessageError(Exception):
    """Ошибка при отправке сообщения."""

    ...

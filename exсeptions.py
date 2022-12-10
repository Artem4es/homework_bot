class HomeworkStatusError(Exception):
    """Ошибка в статусе домашней работы."""  # +

    def __init__(self, homework):
        self.homework = homework
        status = homework.get('status', True)
        homework_name = homework.get('homework_name', True)
        if status and homework_name:
            self.message = f'В homework нет ключей status и homework_name'
        elif status:
            self.message = f'В homework нет ключа status.'
        elif homework_name:
            self.message = f'В homework нет ключа homework_name.'

    def __str__(self):
        return f'{self.message} homework: {self.homework}'


class ResponseFormatError(Exception):
    """Определяет тип ошибки в ответе API."""

    def __init__(self, response):
        self.response = response
        if response.get('code') == 'not_authenticated':
            self.message = response['message']
        elif response.get('code') == 'UnknownError':
            self.message = f'{response.get("error")}'
        elif 'homeworks' not in response:
            self.message = f'Не найден ключ homeworks.'
        else:
            self.message = f'Неожиданный ответ API.'

    def __str__(self):
        return f'{self.message}. Проверьте ответ API: {self.response}'

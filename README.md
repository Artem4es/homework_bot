### Что это за Homework bot? :space_invader:
Это бот для автоматической проверки статуса проверки домашней работы в Яндекс Практикуме. Он осуществляет взаимодействие с API Яндекс Практикума путем отправки JSON GET запросов для получения информации о текущем статусе проверки домашней работы. После получения ответа от API Яндекс Практикума, модуль бота сверяет текущий статус с полученным через API и при его изменении отправляет уведомление в телеграм-бот пользователя. Это позволяет пользователю получать уведомления о статусе проверки домашней работы в режиме реального времени. В проекте также реализована запись логов и обработка ошибок, что позволяет отслеживать работу бота и быстро реагировать на возможные проблемы.

### Как развернуть проект: :question:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone git@github.com:Artem4es/homework_bot.git
```

```
cd homework_bot
```

Cоздать и активировать виртуальное окружение:

```
python3.9 -m venv venv
```

```
source venv/Scripts/activate (venv/Scripts/activate для Windows)
```

```
python3 -m pip install --upgrade pip (python далее везде для Windows)
```

Установить зависимости из requirements.txt:

```
pip install -r requirements.txt
```
Необходимо создать файл .env с данными для телеграм бота:
```
PRACTICUM_TOKEN = Необходимо получить токен от Я.Практикума
TELEGRAM_TOKEN = Токен вашего бота в ТГ
TELEGRAM_CHAT_ID = Ваш ID в Телеграм

```

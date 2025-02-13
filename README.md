# GoogleSheets2Ekis DO

Бот для переноса данных из Гугл таблиц в форму ЕКИС <https://st.educom.ru/>.

Доступный три операции:
- "Заполнить" - перенести данные из гугл в екис.
- "Проверить" - прислать данные из гугл.
- "Очистить" - очистить гугл таблицу.

## Требования
  1. Логин и пароль от ЕКИС <https://st.educom.ru/>.
  1. Данные для доступа к API Google `credentials.json`, можно получить тут - `https://console.cloud.google.com/apis/credentials`.
  1. Токен бота, полученный от [@BotFather](https://t.me/botfather).
  1. Идентификатор чата, так как бот будет доступен только указаному айди.
     Можно получить от [@userinfobot](https://telegram.me/userinfobot) или самого этого бота командой `/start`.

## Настройки
  1. Установить Python 3.9 (с другими версиями бот не проверялся)
  1. Клонировать и открыть каталог репозитория
  1. Установить зависимости `pip install -r requirements.txt`
  1. Переименовать файл `.env.example` в `.env`
  1. Отредактировать файл `.env`, заменив переменные на свои
    - `CREDENTIALS_FILE` = 'credentials.json' - путь к учетным данным для гугл.
    - `MYID` = '123456789' - айди пользователя Telegram
    - `BOT_TOKEN` = '87654321:Abcdefghijklmnopqo' - токен бота Telegram
    - `EKIS_LOGIN` = 'login' - логин ЕКИС
    - `EKIS_PASSWORD` = 'passwd' - пароль ЕКИС
    - `SPREADSHEETS_ID` = 'Fg2bsmNdy14saSJmau3Xdw' - айди гугл таблицы, можно посмотреть в адресной строке.
  1. В фале `bot.py` отредактировать словарь `DO_RANGES_ADDRESSES` с диапазонами адресов таблицы и адресами зданий из ЕКИС.

## Запуск
Из командной строки `python3 bot/bot.py`
Или через Docker:
  1. `sudo docker build -t gs2ekis_do .`
  1. `sudo docker run -d  -v путь_к_файлу_.env:/bot --name gs2ekis_do --restart=always gs2ekis_do`
Или через Docker compose, доступ к `credentials.json` через общий том, смотри файл `docker-compose.yml`:
  1. `docker compose up --build`

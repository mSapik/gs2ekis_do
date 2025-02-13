import logging
import os

import apiclient
import httplib2
import requests
import telebot
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials
from requests.auth import HTTPBasicAuth
from telebot import types

load_dotenv()

CREDENTIALS = ServiceAccountCredentials.from_json_keyfile_name(
    os.getenv('CREDENTIALS_FILE'),
    ['https://www.googleapis.com/auth/spreadsheets',
     'https://www.googleapis.com/auth/drive']
)
MYID = os.getenv('MYID')
BOT_TOKEN = os.getenv('BOT_TOKEN')
EKIS_LOGIN = os.getenv('EKIS_LOGIN')
EKIS_PASSWORD = os.getenv('EKIS_PASSWORD')
SPREADSHEETS_ID = os.getenv('SPREADSHEETS_ID')
URL = os.getenv('URL')
SCH_ID = '12345'  # id школы
FORM_ID = '7156'  # id формы (тут ежедневная ДО)

# Ниже словарь, диапазон в гугл таблицах: адрес из системы
DO_RANGES_ADDRESSES = {
    'Адрес1!A4:C20': (
        '<bti_buildings AOK="100" MR="001" '
        'addressText="город Москва, улица Улица, дом 1, корпус 2" '
        'unom="12345678" unad="1"/>'
    ),
    'Адрес2!A4:C20': (
        '<bti_buildings AOK="100" MR="001" '
        'addressText="город Москва, улица Улица, дом 1, корпус 3" '
        'unom="12345678" unad="1"/>'
    ),
    'Адрес3!A4:C20': (
        '<bti_buildings AOK="100" MR="001" '
        'addressText="город Москва, улица Улица, дом 1, корпус 4" '
        'unom="12345678" unad="1"/>'
    )
}


ekis_auth = HTTPBasicAuth(EKIS_LOGIN, EKIS_PASSWORD)

bot = telebot.TeleBot(BOT_TOKEN, parse_mode='MARKDOWN')
bot.remove_webhook()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("Ekis_DO_Bot")


headers = {
    'authority': 'st.educom.ru',
    'accept': '*/*',
    'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'origin': 'https://st.educom.ru',
    'referer': 'https://st.educom.ru/eduoffices/index.php',
    'user-agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) '
                   'Chrome/118.0.0.0 Safari/537.36'
                   ),
    'x-requested-with': 'XMLHttpRequest',
}

params = {
    'do': 'xf_set_form_filling_state_for_eo'
}

data = {
    'eo': SCH_ID,  # id школы
    'f': FORM_ID,  # id формы
    'responsible': 'Имя Фамилия Отчество',  # ФИО ответственного
    'phone': '(495) 123-45-56',
    'email': 'school@mail.ru'
}

paramsCLOSE1 = {
    'do': 'xf_get_form_filling_responsible',
}

dataCLOSE1 = {
    'eo': SCH_ID,
    'f': FORM_ID,
}

paramsCLOSE2 = {
    'do': 'xf_update_ts',
}

dataCLOSE2 = {
    'eo': SCH_ID,
    'f': FORM_ID,
    'd': '1',
}

paramsCLOSE3 = {
    'do': 'xf_get_form_last_change_ts',
}


def google_auth():
    """Авторизация в гугл."""
    try:
        httpAuth = CREDENTIALS.authorize(httplib2.Http())
        service = apiclient.discovery.build('sheets', 'v4', http=httpAuth)

        return service
    except Exception as e:
        logger.info(f"!!! ОШИБКА !!! {e}")


def google_get(g_range, g_service):
    """"Получение данных из гугл таблицы."""
    try:
        spreadsheet_id = SPREADSHEETS_ID
        values = g_service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=g_range
        ).execute()
        g_values = values['values']
        for row in g_values:
            if '0' in row:
                row.clear()
            for digit in row:
                if not digit.isnumeric():
                    row.clear()

        g_values = list(filter(None, g_values))
        g_values_hr = ''
        for row in g_values:
            string = ''
            for digit in row:
                string += digit + ","
            g_values_hr += "\n" + string
        logger.info(g_range + " " + g_values_hr)
        bot.send_message(MYID, g_range + g_values_hr)
        return (g_values)

    except Exception as e:
        logger.info(f"!!! ОШИБКА !!! {e}")


def google_delete(service):
    """Очистка гугл таблицы."""

    try:
        for do_range in DO_RANGES_ADDRESSES:
            request = service.spreadsheets().values().clear(
                spreadsheetId=SPREADSHEETS_ID,
                range=do_range.replace('A', 'C')
            )
            response = request.execute()
            logger.info(f"Очищаю {response}")

    except Exception as e:
        logger.info(f"!!! ОШИБКА !!! {e}")


def ekis(e_param, e_data, e_header):
    """"Отправка данных в форму ЕКИС."""
    try:
        r = requests.post(
            url=URL,
            auth=ekis_auth,
            params=e_param,
            data=e_data,
            headers=e_header
        )
        if r.status_code != 200:
            logger.info("Ошибка запроса! (" + str(r.status_code) + ")")
        results = r.json()['success']
        if results:
            logger.info("!!! УСПЕШНО !!!")
        return results
    except Exception as e:
        logger.info(f"!!! ОШИБКА !!! {e}")


def ekis_get():
    """Получение предыдущих данных из формы ЕКИС."""

    paramsGET = {
        'do': 'xf_get_table_data'
    }

    dataGET = {
        'start': '0',
        'limit': '100',
        'col_id': '0',
        'eo': SCH_ID,
        'g': '8861',
        't': '9361',
        'search': '',
        'attribute_id_searh': '52818',
        'page': '1',
    }

    rownums = []

    try:
        get = requests.post(url=URL, auth=ekis_auth,
                            params=paramsGET, headers=headers,
                            data=dataGET)
        if get.status_code != 200:
            logger.info("Ошибка запроса! (" + str(get.status_code) + ")")
        results = get.json()['success']
        if results:
            logger.info("!!! УСПЕШНО !!!")
        for row in get.json().get('vtable_body'):
            rownum = row.get('rownum')
            rownums.append(str(rownum))

        return rownums

    except Exception as e:
        logger.info(f"!!! ОШИБКА !!! {e}")


def ekis_del(rownums):
    """Очистка формы ЕКИС."""

    paramsDEL = {
        'do': 'xf_del_table_rows',
    }

    dataDEL = {
        'eo': SCH_ID,
        't': '9361',
        'f': FORM_ID,
        'rows': '[' + ','.join(rownums) + ']',
        'col_id': '0',
    }

    try:

        delete = requests.post(url=URL, auth=ekis_auth,
                               params=paramsDEL, headers=headers,
                               data=dataDEL)
        if delete.status_code != 200:
            logger.info("Ошибка запроса! (" + str(delete.status_code) + ")")
        results = delete.json()['success']
        if results:
            logger.info("!!! УСПЕШНО !!!")

        return results

    except Exception as e:
        logger.info(f"!!! ОШИБКА !!! {e}")


def ekis_add(do_lst, addr, e_header):
    """"Добавление данных в форму ЕКИС."""

    params = {
        'do': 'xf_update_values',
    }
    try:
        for values in do_lst:
            if len(values) == 3:

                data = {
                    'f': FORM_ID,
                    'eo': SCH_ID,
                    'new_attrs': '[{\
                        "52818": "' + addr + '",\
                        "52819": "' + values[0] + '",\
                        "52820": "' + values[2] + '"\
                    }]',
                    'upd_attrs': '{}',
                    'col_id': '0',
                    't': '9361',
                }

                add = requests.post(
                    url=URL,
                    auth=ekis_auth,
                    params=params,
                    data=data,
                    headers=e_header
                )
                if add.status_code != 200:
                    logger.info(
                        "Ошибка запроса! (" + str(add.status_code) + ")")
                    bot.send_message(
                        MYID, "Ошибка запроса! (" + str(add.status_code) + ")")

                results = add.json()['success']
                if results:
                    logger.info(
                        f'{values[0]}: {values[2]} УСПЕШНО!'
                    )
                    bot.send_message(
                        MYID,
                        f'{values[0]}: {values[2]} УСПЕШНО!'
                    )
                else:
                    logger.info("!!! ОШИБКА !!!")
                    bot.send_message(MYID, "!!! ОШИБКА !!!")

    except Exception as e:
        logger.info(f"!!! ОШИБКА !!! {e}")


@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    if message.from_user.id == 201732582:
        if message.text == "Запуск":
            bot.send_message(MYID, "Запущен")

        elif message.text == "Проверить":

            for do_range in DO_RANGES_ADDRESSES:
                response = google_get(str(do_range), google_auth())
                print(str(do_range) + str(response))
                logger.info(str(do_range) + str(response))

        elif message.text == "Заполнить":

            logger.info("Открываю...")
            bot.send_message(MYID, "Открываю...")
            data['state'] = '1'
            ekis(params, data, headers)

            logger.info("Удаляю...")
            bot.send_message(MYID, "Удаляю...")
            ekis_del(ekis_get())

            for do_range in DO_RANGES_ADDRESSES:
                response = google_get(str(do_range), google_auth())
                logger.info(f"ЗАПОЛНЯЮ {str(do_range)}")
                bot.send_message(MYID, f"ЗАПОЛНЯЮ {str(do_range)}")
                ekis_add(response, DO_RANGES_ADDRESSES[do_range], headers)

            logger.info("Завершаю...")
            bot.send_message(MYID, "Завершаю...")
            ekis(paramsCLOSE1, dataCLOSE1, headers)

            logger.info("Обновляю...")
            bot.send_message(MYID, "Обновляю...")
            ekis(paramsCLOSE2, dataCLOSE2, headers)

            logger.info("Подтверждаю...")
            bot.send_message(MYID, "Подтверждаю...")
            ekis(paramsCLOSE3, dataCLOSE1, headers)

            logger.info("Закрываю...")
            bot.send_message(MYID, "Закрываю...")
            data['state'] = '0'
            ekis(params, data, headers)

        elif message.text == "Помощь":
            bot.send_message(
                MYID,
                """`Старт` для запуска автоотправки,
                `Проверить` для проверки вручную.""")

        elif message.text == "Очистить":
            bot.send_message(MYID, "Очищаю гугл таблицу")
            google_delete(google_auth())

        else:
            bot.send_message(
                MYID, "Введи `Помощь`, если не знаешь, что делать.")

        markup = types.ReplyKeyboardMarkup()
        itembtn1a = types.KeyboardButton('Заполнить')
        itembtn1b = types.KeyboardButton('Проверить')
        itembtn1с = types.KeyboardButton('Очистить')
        markup.row(itembtn1a, itembtn1b, itembtn1с)
        bot.send_message(MYID, "Введи команду:", reply_markup=markup)
    else:
        bot.send_message(MYID, "Кто-то балуется ботом")
        bot.send_message(message.from_user.id, "Это приватный бот")


def main():
    bot.polling(none_stop=True)


if __name__ == '__main__':
    main()

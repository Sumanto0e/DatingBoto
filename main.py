#   состояния (state):
#   0 - регистрация юзера        1 - готовый акаунт         2 - изменение описания
#   3 - удаление акаунта         4 - блокировка акаунта     5 - сообщение пользователю
#   6 -                          7 - ввод реф. кода         8 - смена города
#   9 - смена возраста           10 - выбор пола            11 -

# гайд по импортам;

import datetime  # модуль для работы с датами
import random  # модуль для работы со случайными числами
import requests  # модуль для запросов (в моём случае к QIWI api)
import keys  # ..
import pyqiwi # .
from vk_api import VkApi  # модуль для работы с api
from vk_api.longpoll import VkLongPoll, VkEventType  # модуль для работы с longpoll
from vk_api.keyboard import VkKeyboard, VkKeyboardColor  # модуль для работы с клавиатурами
from random import choice  # ...
from sqlite3 import connect  # модуль для работы с базами данных

# ...


# подключаюсь к базе данных ( Далее - БД) и создаю таблицу с пользователями
database = connect('database.db')
try:
    database.execute(f'CREATE TABLE users ('
                     f'user_id UNIQUE,'
                     f'name TEXT,'
                     f'surname TEXT,'
                     f'about TEXT,'
                     f'likes INT,'
                     f'dislikes INT,'
                     f'state INT,'
                     f'viewed_user INT,'
                     f'photo TEXT,'
                     f'pro INT,'
                     f'views INT,'
                     f'city TEXT,'
                     f'views_count INT,'
                     f'pro_update_date TEXT,'
                     f'referral_code TEXT,'
                     f'payment_code INT,'
                     f'age INT,'
                     f'sex INT,'
                     f'select_sex INT,'
                     f'active INT,'
                     f'all_views INT);')
    database.commit()
except:
    pass
# ...

# подключаюсь к vk api и QIWI api
bot = VkApi(token=keys.VK_API_ACCESS_TOKEN)
longpoll = VkLongPoll(bot)
wallet = pyqiwi.Wallet(token=keys.QIWI_API_ACCESS_TOKEN, number=keys.QIWI_API_TELEPHONE_NUMBER)
qiwi_count = 1
# ...


# создаю основные клавиатуры
mainmenu = VkKeyboard()
mainmenu.add_button('❤', VkKeyboardColor.POSITIVE)
mainmenu.add_button('✉', VkKeyboardColor.PRIMARY)
mainmenu.add_button('💔', VkKeyboardColor.NEGATIVE)
mainmenu.add_button('🙍‍♂', VkKeyboardColor.SECONDARY)
mainmenu.add_line()
mainmenu.add_button('Продолжить просмотр 👀', VkKeyboardColor.POSITIVE)
mainmenu.add_line()
mainmenu.add_button('Купить pro 👑', VkKeyboardColor.SECONDARY)

promainmenu = VkKeyboard()
promainmenu.add_button('❤', VkKeyboardColor.POSITIVE)
promainmenu.add_button('✉', VkKeyboardColor.PRIMARY)
promainmenu.add_button('💔', VkKeyboardColor.NEGATIVE)
promainmenu.add_button('🙍‍♂', VkKeyboardColor.SECONDARY)
promainmenu.add_line()
promainmenu.add_button('Продолжить просмотр 👀', VkKeyboardColor.POSITIVE)

geolocation_keyboard = VkKeyboard()
geolocation_keyboard.add_location_button()
geolocation_keyboard.add_button('❌ Отмена')

createprofile = VkKeyboard(inline=True)
createprofile.add_button(f'Создать анкету {choice(["🎅", "🎁", "😉", "👑"])}')

main_profile_keyboard = VkKeyboard(inline=True)
main_profile_keyboard.add_button('Мой реф. код 🔑', VkKeyboardColor.SECONDARY)
main_profile_keyboard.add_line()
main_profile_keyboard.add_button('Ввести реф. код 🔑', VkKeyboardColor.SECONDARY)
main_profile_keyboard.add_line()
main_profile_keyboard.add_button('Отключить/включить акаунт 😴', VkKeyboardColor.NEGATIVE)
main_profile_keyboard.add_line()
main_profile_keyboard.add_button('Меню редактирования ✏', VkKeyboardColor.PRIMARY)

edit_profile_keyboard = VkKeyboard(inline=True)
edit_profile_keyboard.add_button('Изменить выборку 👩/👨', VkKeyboardColor.POSITIVE)
edit_profile_keyboard.add_line()
edit_profile_keyboard.add_button('Обновить фото 📷🔁', VkKeyboardColor.POSITIVE)
edit_profile_keyboard.add_line()
edit_profile_keyboard.add_button('Изменить возраст 🗓', VkKeyboardColor.POSITIVE)
edit_profile_keyboard.add_line()
edit_profile_keyboard.add_button('Изменить описание ✏', VkKeyboardColor.PRIMARY)
edit_profile_keyboard.add_line()
edit_profile_keyboard.add_button('Cменить город 🏙', VkKeyboardColor.PRIMARY)
edit_profile_keyboard.add_line()
edit_profile_keyboard.add_button('Удалить акаунт 🗑', VkKeyboardColor.NEGATIVE)

sex_keyboard = VkKeyboard(inline=True)
sex_keyboard.add_button('Девушек', VkKeyboardColor.PRIMARY)
sex_keyboard.add_line()
sex_keyboard.add_button('Парней', VkKeyboardColor.PRIMARY)
sex_keyboard.add_line()
sex_keyboard.add_button('Всех', VkKeyboardColor.SECONDARY)

back_payment_keyboard = VkKeyboard()
back_payment_keyboard.add_button('Отменить платёж', VkKeyboardColor.SECONDARY)

end_registration_keyboard = VkKeyboard()
end_registration_keyboard.add_button('Завершить регистрацию ✅', VkKeyboardColor.POSITIVE)

# ...


def generate_random_string(user_id):
    """ функция генерирует реферальный код для участника """
    letters = '1234567890'
    rand_string = str(user_id) + '-' + ''.join(random.choice(letters) for i in range(8))
    return rand_string


def database_query(query):
    """ функция запросов к БД """
    database.execute(query)
    database.commit()


#   это часть с оплатой премиума

def generate_payment_code():  # тут я генерирую платёжный код
    code = []

    def generate():
        return str(choice(range(10)))

    for _ in range(6):
        code.append(generate())
    return int(str(i.user_id) + ''.join(code))


def get_payments_history():  # получаю последние 3 транзакции
    """ функция получает последние транзакции владельца кошелька """
    count = len(database.execute(f'SELECT user_id FROM users WHERE payment_code!=0').fetchall())
    try:  # если их возможно получить - беру
        history = wallet.history(rows=count).get('transactions')
    except ValueError:  # если нет - то нет
        history = [0]

    payment_code = database.execute(f'SELECT payment_code FROM users WHERE user_id={user_id}').fetchone()[0]

    for i in history:
        try:
            comm = int(i.raw['comment'])
        except:
            comm = 0
        if payment_code == comm:
            return (True, i)
    return False


def get_qiwi_payment_url():
    """ функция генерирует платёжную форму для пользователя """
    url = f"https://qiwi.com/payment/form/99999?extra%5B%27account%27%5D=SAINA682&extra%5B%27comment%27%5D=42345&amountInteger={qiwi_count}" \
          "&amountFraction=0&currency=643&blocked[0]=sum&blocked[1]=account&blocked[2]=comment&extra%5B%27accountType%27%5D=nickname"
    return url


for i in longpoll.listen():
    if i.type == VkEventType.MESSAGE_NEW and i.to_me:
        now = datetime.datetime.now().date()
        text = i.text.lower()  # текст сообщения пользователя
        normaltext = i.text  # текст без lower()
        user_id = i.user_id  # id пользователя вк
        state = database.execute(f'SELECT state FROM users WHERE user_id={user_id}').fetchone()  # получение состояния

        if not state is None:  # проверка, есть ли юзер в базе
            state = state[0]


        def send(text, keyboard=None, id=user_id, attachments=0):

            """ функция отправки сообщения """
            if keyboard:
                bot.method(f'messages.send', {'message': text,
                                              'user_id': id,
                                              'random_id': 0,
                                              'keyboard': keyboard,
                                              'attachment': attachments})
            else:
                try:
                    pro = database.execute(f'SELECT pro FROM users WHERE user_id={user_id}').fetchone()[0]
                except:
                    pro = 0

                if pro == 1:
                    keyboard = promainmenu
                else:
                    keyboard = mainmenu

                bot.method(f'messages.send', {'message': text,
                                              'user_id': id,
                                              'random_id': 0,
                                              'attachment': attachments,
                                              'keyboard': keyboard.get_keyboard()})


        def check_pro_update():
            """ функция обновляет премиум  """
            try:
                pro_update_date = database.execute(f'SELECT pro_update_date FROM '
                                                   f'users WHERE user_id={user_id}').fetchone()[0]
                pro_update_date = '0-0-0' if not pro_update_date else pro_update_date

                pro_update_date = list(map(lambda x: int(x), pro_update_date.split('-')))
                pro_update_date = datetime.date(day=pro_update_date[2],
                                                month=pro_update_date[1],
                                                year=pro_update_date[0])
                if now > pro_update_date:
                    return True
                return False
            except:
                return False


        def view():
            """ функция нужна, чтобы после каждого действия отправлять новую анкету """

            if check_pro_update():
                send('✅ Ура!\n'
                     'Тебе снова доступен пакет из 10 анкет в день!')
                database_query(f'UPDATE users SET pro_update_date="{now}", views_count=0 WHERE user_id={user_id}')

            views_count = database.execute(f'SELECT views_count FROM users WHERE user_id={user_id}').fetchone()[0]
            views_count = 0 if not views_count else views_count
            pro = database.execute(f'SELECT pro FROM users WHERE user_id={user_id}').fetchone()[0]

            if pro == 1 or views_count < 10:
                all_views = database.execute(f'SELECT all_views FROM users WHERE user_id={user_id}').fetchone()[0]
                print(all_views)
                database_query(f'UPDATE users SET all_views={all_views + 1} WHERE user_id={user_id} ')
                sex = database.execute(f'SELECT select_sex FROM users WHERE user_id={user_id}').fetchone()[0]
                city = database.execute(f'SELECT city FROM users WHERE user_id={user_id}').fetchone()[0]
                if city != 'all':
                    if sex == 0:
                        usersdata = database.execute(f'SELECT * FROM '
                                                     f'users WHERE city="{city}" AND active=1').fetchall()  # Все пользователи бота с опред. городом
                    else:
                        usersdata = database.execute(f'SELECT * FROM '
                                                     f'users WHERE city="{city}" AND sex={sex} AND active=1').fetchall()
                else:
                    if sex == 0:
                        usersdata = database.execute(f'SELECT * FROM users WHERE active=1').fetchall()  # Все пользователи бота
                    else:
                        usersdata = database.execute(f'SELECT * FROM '
                                                     f'users WHERE sex={sex} AND active=1').fetchall()

                if len(usersdata) > 1:
                    for i in range(len(usersdata)):  # убираем id текущего юзера
                        if usersdata[i][0] == user_id:
                            del usersdata[i]
                            break

                    user = choice(usersdata)  # Случайный пользователь бота pro - 9
                    pro = user[9]
                    if pro == 1:
                        pro = '👑 (pro)'
                    else:
                        pro = '💞'
                    database_query(f'UPDATE users SET viewed_user={user[0]} WHERE user_id={user_id}')
                    city = database.execute(f'SELECT city FROM users WHERE user_id={user[0]}').fetchone()[0]
                    city = 'не указан' if city is None or city == 'none' else city
                    photo = database.execute(f'SELECT photo FROM users WHERE user_id={user[0]}').fetchone()[0]

                    if photo == '0':
                        photo = 'photo-204338719_457239214'

                    if city == 'all':
                        city = 'все города'

                    keyboard = mainmenu if pro == 0 else promainmenu

                    age = user[16] if user[16] else 'не указан'
                    send('✅ Подходящая анкета:\n\n'
                         f'{pro} {user[1]} {user[2]} | {age} | {city}\n\n'
                         f'{user[3]}\n\nФото:', keyboard.get_keyboard(),
                         user_id,
                         photo)

                    user_views = database.execute(f'SELECT views FROM users WHERE user_id={user[0]}').fetchone()[0]
                    database_query(
                        f'UPDATE users SET views={user_views + 1}'
                        f' WHERE user_id={user[0]}')  # увеличиваю просмотр на 1
                    database_query(f'UPDATE users SET views_count={views_count + 1} WHERE user_id={user_id}')

                else:
                    send('Похоже, из вашего города есть только вы:)\n'
                         'Но вы можете пригласить друзей по ссылке:\n'
                         'https://vk.com/write-204338719')

            else:
                send('❌ Вы не можете смотреть больше 10 анкет в день без подписки pro!')


        if state == 0:  # проверяем состояние
            send('✅ Вы успешно зарегистрированы!\n'
                 'Будьте вежливы, и тогда вы найдёте друзей!\n\n'
                 'Короткий гайд по функциям бота:\n'
                 'https://vk.com/@datingbotvk-gaid-po-funkciyam-bota', mainmenu.get_keyboard())
            send('Так-же вы можете сменить город, чтобы вы знакомились с людьми из вашего города.'
                 '\nПока вы не сменили город, вам показываются люди из всех городов.\n'
                 'Читайте тут: https://vk.com/@datingbotvk-smena-goroda-i-s-chem-ee-edyat.')
            database_query(f'UPDATE users SET state=1, active=1, all_views=1 WHERE user_id={user_id}')

        elif state == 2:  # состояние смены описания при регистрации
            send(f'✅ Добавлено описание: {normaltext}')
            send(f'Теперь выбери, кого ты хочешь видеть в рекомендациях?', sex_keyboard.get_keyboard())
            database_query(f'UPDATE users SET about="{normaltext}", state=10 WHERE user_id={user_id}')

        elif state == 21:  # состояние смены описания
            send(f'✅ Описание изменено: {normaltext}')
            database_query(f'UPDATE users SET about="{normaltext}", state=1 WHERE user_id={user_id}')

        elif state == 3:  # состояние удаления акаунта
            if text == 'да, я подтверждаю удаление акаунта.':
                send('Удаляем ваш акаунт 🔃')
                database_query(f'DELETE FROM users WHERE user_id={user_id}')
                send('✅ Мы удалили ваш акаунт;')

            else:
                send('Неверно. Попытка удаления акаунта была заблокирована.')
                database_query(f'UPDATE users SET state=1 WHERE user_id={user_id}')

        elif state == 4:  # состояние блокировки
            send('❌ Ваш акаунт был заблокирован.')

        elif state == 5:  # состояние отправки сообщения
            try:
                send('✅ Отправлено;')

                recipient = database.execute(f'SELECT viewed_user FROM users WHERE user_id={user_id}').fetchone()
                recipient = database.execute(
                    f'SELECT name, surname, user_id FROM users WHERE user_id={recipient[0]}').fetchone()
                sender = database.execute(f'SELECT name, surname FROM users WHERE user_id={user_id}').fetchone()
                user = bot.method(f'users.get', {'user_ids': [user_id], 'fields': 'screen_name'})[0]
                try:
                    send(f'@{user["screen_name"]} ({sender[0]} {sender[1]}) оставил тебе сообщение:\n'
                         f'{text}', None, recipient[2])

                except:
                    send('Пользователь заблокировал бота.')

                database_query(f'UPDATE users SET state=1 WHERE user_id={user_id}')
                view()
            except:
                send('❌ Ошибка отправки. \nПохоже, пользователь не зарегистрирован!')

        elif state == 7:  # состояние отправки реф. кода
            code = database.execute(f'SELECT user_id, name, surname FROM users WHERE referral_code="{text}"').fetchone()
            if code:
                if code[0] != user_id:
                    send(f'Реферальный код пользователя {code[1]} {code[2]} принят ✅\n')
                    send('Привет 👋\n'
                         f'Твой реферальный код ({text}) кто-то активировал, тебе'
                         ' полагается премиум, и он уже активен 😎\n\n'
                         'Теперь у тебя нет реферального кода.', None, code[0])
                    send('Вы активировали премиум по реферальному коду ✅\n'
                         'Приятного использования!')
                    database_query(f'UPDATE users SET referral_code="" WHERE user_id={code[0]}')  # пустой реф. код
                    database_query(f'UPDATE users SET pro=1 WHERE user_id={user_id}')  # даю прем
                    database_query(f'UPDATE users SET pro=1 WHERE user_id={user_id}')  # даю прем
                else:
                    send('🦐 Нельзя ввести свой же код:)')
            else:
                send('❌ Реферальный код не найден, или уже использован.')
            database_query(f'UPDATE users SET state=1 WHERE user_id={user_id}')  # возвращаю состояние.

        elif state == 8:  # состояние смены города
            result = bot.method("messages.getById", {"message_ids": [i.message_id],
                                                     "group_id": 189072320})

            if text == 'все':
                database_query(f'UPDATE users SET city="all" WHERE user_id={user_id}')
                send('Теперь вы просматриваете все города.')
            else:
                try:
                    if result['items'][0].get('geo', False):
                        result = result['items'][0]['geo']['place']['city']
                        send(f'Ваш город - {result}.'
                             f'Мы заполнили эту информация, и теперь будем показывать вам людей из вашего города ✅')
                        database_query(f'UPDATE users SET city="{result}" WHERE user_id={user_id}')
                    else:
                        send('Это не местоположение  📍')
                except:
                    send('❌ Ошибка')

            database_query(f'UPDATE users SET state=1 WHERE user_id={user_id}')

        elif state == 9:  # cостояние смены возраста при регистрации
            if text.isdigit():
                if int(text) >= 18:
                    send('✅ Принято;')
                    database_query(f'UPDATE users SET state=2, age={int(text)} WHERE user_id={user_id}')
                    send('Отправь мне информацию о тебе в одном сообщении (чем ты хочешь заняться, или что ищешь тут);')
                else:
                    send('❌ Обязательное условие регистрации: вам больше 18 лет.')
            else:
                send('❌ Укажи корректный возраст;')

        elif state == 91:  # cостояние смены возраста
            if text.isdigit():
                if int(text) >= 18:
                    send('✅ Принято;')
                    database_query(f'UPDATE users SET state=1, age={int(text)} WHERE user_id={user_id}')
                else:
                    send('❌ Обязательное условие регистрации: вам больше 18 лет.')
                    database_query(f'UPDATE users SET state=1 WHERE user_id={user_id}')
            else:
                send('❌ Укажи корректный возраст;')

        elif state == 10:  # состояние выбора выборки при регистрации
            send('✅ Принято')
            end = False
            if text == 'парней':
                database_query(f'UPDATE users SET select_sex=2, state=11 WHERE user_id={user_id}')
                end = True
            elif text == 'девушек':
                database_query(f'UPDATE users SET select_sex=1, state=11 WHERE user_id={user_id}')
                end = True
            elif text == 'всех':
                database_query(f'UPDATE users SET select_sex=0, state=11 WHERE user_id={user_id}')
                end = True
            else:
                send('❌ Введите корректные значения;')

            if end:
                send('Отлично ✅', end_registration_keyboard.get_keyboard())
                photo_url = bot.method(f'users.get', {'fields': ['photo_max_orig'], 'user_id': user_id})[0][
                    'photo_max_orig']

                with open(f'users_photos/{user_id}.png', 'wb') as f:
                    f.write(requests.get(photo_url).content)

                upload_url = bot.method(f'photos.getMessagesUploadServer', {})['upload_url']
                upload = requests.post(upload_url, files={'photo': open(f'users_photos/{user_id}.png', 'rb')}).json()
                result = bot.method('photos.saveMessagesPhoto', {'photo': upload['photo'],
                                                                 'server': upload['server'],
                                                                 'hash': upload['hash']})[0]

                photo = 'photo' + str(result['owner_id']) + '_' + str(result['id'])

                database_query(f'UPDATE users SET photo="{photo}", state=0 WHERE user_id={user_id}')


        elif state == 101:  # состояние выбора выборки
            send('✅ Принято')
            if text == 'парней':
                database_query(f'UPDATE users SET select_sex=2, state=1 WHERE user_id={user_id}')
            elif text == 'девушек':
                database_query(f'UPDATE users SET select_sex=1, state=1 WHERE user_id={user_id}')
            elif text == 'всех':
                database_query(f'UPDATE users SET select_sex=0, state=1 WHERE user_id={user_id}')
            else:
                send('❌ Введите корректные значения;')


        elif state is None:

            if 'создать анкету' in text:  # старт нового пользователя
                send('Привет!\nЯ - бот для знакомств, и сейчас мы с тобой создадим тебе анкету!')
                send('Здесь тебе нужна лишь информация о тебе и твой возраст: это обязательно;\n'
                     'Имя, фамилию и пол мы возьмём из твоего акаунта ВКонтакте.')
                send('Отправь мне твой возраст;')
                usersex = bot.method(f'users.get', {'user_ids': [user_id], 'fields': ['sex']})[0][
                    'sex']  # 1 - жен. 2 - муж.
                userdata = bot.method('users.get', {'user_ids': user_id})[0]  # имя/фамилия юзера по его id
                code = generate_random_string(user_id)
                database_query(
                    f'INSERT OR IGNORE INTO users (user_id, name, surname, about, '
                    f'likes, dislikes, state, viewed_user, photo, views, pro, city, views_count, pro_update_date, '
                    f'referral_code, payment_code, age, sex)'
                    f' VALUES ({user_id}, "{userdata["first_name"]}", "{userdata["last_name"]}",'
                    f'"Нет информации;", 0, 0, 9, "{user_id}", 0, 0, 0, "all", 0, "{now}", "{code}",'
                    f'0, 0, {usersex});')  # добавляем анкету в базу
            else:
                send('Для начала создайте анкету 👼', createprofile.get_keyboard())

        else:
            if '🙍‍♂' in text:
                userdata = database.execute(
                    f'SELECT name, surname, about, views, likes, dislikes, age FROM users WHERE '
                    f'user_id={user_id}').fetchone()  # получение акаунта юзера
                city = database.execute(f'SELECT city FROM users WHERE user_id={user_id}').fetchone()[0]
                photo = database.execute(f'SELECT photo FROM users WHERE user_id={user_id}').fetchone()[0]

                if city == 'all':
                    city = 'Все города;'
                pro = database.execute(f'SELECT pro FROM users WHERE user_id={user_id}').fetchone()[0]
                pro = '👑 Подписка pro активна\n' if pro == 1 else '❌ Подписки pro нет\n'
                send('👀 Вот ваша анкета:\n\n'
                     f'🛀 {userdata[0]} {userdata[1]} | {city}\n'
                     f'{pro}'
                     f'🗓 Возраст: {userdata[6]}\n\n'
                     f'{userdata[2]}\n\n'
                     f'📊 Ваша статистика\n\n'
                     f'👀 Просмотров: {userdata[3]}\n'
                     f'❤ Лайков: {userdata[4]}\n'
                     f'💔 Дизлайков: {userdata[5]}\n'
                     f'Твое фото (фото из твоего профиля ВКонтакте):',
                     main_profile_keyboard.get_keyboard(),
                     user_id,
                     photo)

            elif 'меню редактирования' in text:
                send('Здесь вы сможете отредактировать вашу анкету ✏', edit_profile_keyboard.get_keyboard())

            elif 'проверить платёж' in text:
                phis = get_payments_history()
                payment_code = database.execute(f'SELECT payment_code FROM users WHERE user_id={user_id}').fetchone()[0]
                if payment_code != 0:
                    if phis:
                        if phis and phis[1].raw['errorCode'] == 0 and phis[1].raw['status'] != 'WAITING':
                            userdata = phis[1].raw
                            database_query(f'UPDATE users SET payment_code=0, pro=1 WHERE user_id={user_id}')
                            send('🎈 Статус: оплачено ✅\n\n'
                                 '❗ Подробная информация о платеже:\n'
                                 f'📆 Дата: {userdata["date"]}\n'
                                 f'💸 Сумма: @datingbotvk ({userdata["total"]["amount"]} рублей)\n'
                                 f'💬 Комментарий: {userdata["comment"]}'
                                 '\n\nПремиум активирован 👑', promainmenu.get_keyboard())
                            database_query(f'UPDATE users SET payment_code=0, pro=1 WHERE user_id={user_id}')

                        elif phis[1].raw['errorCode'] != 0:
                            send('❌ Ошибка платежа. Повторите платёж и введите верный код.',
                                 back_payment_keyboard.get_keyboard())
                        else:
                            send('❌ Что-то пошло не так;\n'
                                 'Возможные причины:\n'
                                 '1) Вы не оплатили товар\n'
                                 '2) Вы оплатили товар, но не ввели в комментарий код\n'
                                 '3) Технические неполадки\n\n'
                                 'Тщательно проверьте ваш платёж.\n'
                                 'Если ошибка в переводе, обратитесь в техподдержку QIWI.',
                                 back_payment_keyboard.get_keyboard())
                    else:
                        send('❌ Вы не оплатили товар.', back_payment_keyboard.get_keyboard())
                else:
                    send('Никаких транзакций не производиться ⚙✅')

            elif 'нетпро' in text:
                send('ок', mainmenu.get_keyboard())
                database_query(f'UPDATE users SET pro=0 WHERE user_id={user_id}')

            elif 'дапро' in text:
                send('ок', mainmenu.get_keyboard())
                database_query(f'UPDATE users SET pro=1 WHERE user_id={user_id}')

            elif 'купить pro' in text:
                url = get_qiwi_payment_url()
                code = generate_payment_code()
                check_payment_keyboard = VkKeyboard(inline=True)
                check_payment_keyboard.add_openlink_button('Оплатить ▶', url)
                check_payment_keyboard.add_button('Проверить платёж 💲', VkKeyboardColor.PRIMARY)
                send(f'💳 Чек на сумму @datingbotvk ({qiwi_count} рублей)\n'
                     '🎈 Статус: не оплачено ❌\n\nВаша платёжная форма готова.\n'
                     f'\n ❗ ВАЖНО: в комментарий к платежу оставьте код: {code}\n'
                     f'После совершения платежа нажмите "Проверить платёж".\n\n'
                     f'⬇ Чтобы оплатить нажмите кнопку ниже.', check_payment_keyboard.get_keyboard())
                send('Если вы передумали, можно отменить покупку кнопкой "отменить платёж".',
                     back_payment_keyboard.get_keyboard())
                database_query(f'UPDATE users SET payment_code={int(code)} WHERE user_id={user_id}')

            elif 'изменить выборку' in text:
                send('Выбери, кого ты хочешь видеть в рекомендациях?', sex_keyboard.get_keyboard())
                database_query(f'UPDATE users SET state=101 WHERE user_id={user_id}')

            elif 'обновить фото' in text:
                send('Скачиваю фото с твоей страницы вконтакте ⚙')
                photo_url = bot.method(f'users.get', {'fields': ['photo_max_orig'], 'user_id': user_id})[0][
                    'photo_max_orig']
                database_query(f'UPDATE users SET photo="{photo_url}" WHERE user_id={user_id}')

                with open(f'users_photos/{user_id}.png', 'wb') as f:
                    f.write(requests.get(photo_url).content)
                send('Загружаю фото на сервер ВКонтакте ⚙')
                upload_url = bot.method(f'photos.getMessagesUploadServer', {})['upload_url']
                upload = requests.post(upload_url, files={'photo': open(f'users_photos/{user_id}.png', 'rb')}).json()
                result = bot.method('photos.saveMessagesPhoto', {'photo': upload['photo'],
                                                                 'server': upload['server'],
                                                                 'hash': upload['hash']})[0]
                send('Составляю адрес доставки фото ⚙')
                photo = 'photo' + str(result['owner_id']) + '_' + str(result['id'])
                send('Сохраняю фото тебе в профиль ⚙')
                database_query(f'UPDATE users SET photo="{photo}" WHERE user_id={user_id}')
                send('✅ Твоё фото обновлено;')


            elif 'мой реф. код' in text:
                code = database.execute(f'SELECT referral_code FROM users WHERE user_id={user_id}').fetchone()[0]
                code = [0, 0] if not code else code

                if len(code) != 0:
                    if code is None or code == [0, 0]:
                        database_query(f'UPDATE users SET referral_code="{generate_random_string(user_id)}" '
                                       f'WHERE user_id={user_id}')
                    code = database.execute(f'SELECT referral_code FROM users WHERE user_id={user_id}').fetchone()[0]
                    send(f'Ваш реферальный код: {code}\n\n'
                         f'Как им воспользоваться читайте тут:\n'
                         f'https://vk.com/@datingbotvk-kak-vospolzovatsya-ref-kodom')
                else:
                    send('Ваш реферальный код уже неактивен 👴')


            elif 'рассылка' in text:
                text = text.split('рассылка')[1]
                users = database.execute(f'SELECT user_id FROM users').fetchall()
                for i in users:
                    try:
                        send(text, None, i[0])
                    except:
                        send('Заблокированный юзер!')


            elif 'ввести реф. код' in text:
                send('Введите реф. код: ')
                database_query(f'UPDATE users SET state=7 WHERE user_id={user_id}')  # меняю состояние

            elif 'город' in text:
                send('Отправь мне геолокацию (где ты находишься) и я буду отправлять тебе людей из твоего города ✅',
                     geolocation_keyboard.get_keyboard())
                database_query(f'UPDATE users SET state=8 WHERE user_id={user_id}')  # меняю состояние

            elif '✉' in text:
                send('Напишите своё сообщение: ')
                database_query(f'UPDATE users SET state=5 WHERE user_id={user_id}')  # меняю состояние

            elif 'изменить возраст' in text:
                send('Отправь мне твой возраст;')
                database_query(f'UPDATE users SET state=91 WHERE user_id={user_id}')

            elif 'изменить описание' in text:
                send('✏ Введи новое описание: ')
                database_query(f'UPDATE users SET state=21 WHERE user_id={user_id}')  # меняю состояние

            elif 'удалить акаунт' in text:
                send('Для удаления акаунта вы должны ввести следующее:\n'
                     '"да, я подтверждаю удаление акаунта.", и мы удалим ваш акаунт.\n\n'
                     'Подробнее про удалённые акаунты вы можете прочитать тут:\n'
                     'https://vk.com/@datingbotvk-udalenie-akauntov')
                database_query(f'UPDATE users SET state=3 WHERE user_id={user_id}')  # меняю состояние

            elif 'отключить/включить акаунт' in text:
                active = database.execute(f'SELECT active FROM users WHERE user_id={user_id}').fetchone()[0]
                if active == 1:
                    send('Ваш аккаунт отключён ✅')
                    database_query(f'UPDATE users SET active=0 WHERE user_id={user_id}')  # меняю состояние
                else:
                    send('Ваш аккаунт включён ✅')
                    database_query(f'UPDATE users SET active=1 WHERE user_id={user_id}')  # меняю состояние

            elif 'смотреть' in text or 'продолжить просмотр' in text:
                view()  # отправляю новую анкету

            elif 'отменить платёж' in text:
                pro = database.execute(f'SELECT pro FROM users WHERE user_id={user_id}').fetchone()[0]
                keyboard = mainmenu
                if pro == 1:
                    keyboard = promainmenu
                database_query(f'UPDATE users SET payment_code=0 WHERE user_id={user_id}')
                send('✅ Покупка подписки pro отменена.', keyboard.get_keyboard())
                view()


            elif '❤' in text:  # лайк
                try:
                    recipient = database.execute(f'SELECT viewed_user FROM users WHERE user_id={user_id}').fetchone()
                    recipient = database.execute(
                        f'SELECT name, surname, user_id FROM users WHERE user_id={recipient[0]}').fetchone()
                    recipient_likes = \
                        database.execute(f'SELECT likes FROM users WHERE user_id={recipient[2]}').fetchone()[0]
                    database_query(f'UPDATE users SET likes={recipient_likes + 1} WHERE user_id={recipient[2]}')
                    sender = database.execute(f'SELECT name, surname FROM users WHERE user_id={user_id}').fetchone()
                    user = bot.method(f'users.get', {'user_ids': [user_id], 'fields': 'screen_name'})[0]

                    userdata = database.execute(
                        f'SELECT photo, age, city, name, surname, about FROM users WHERE user_id={user_id}').fetchone()
                    city = 'не указан' if userdata[2] is None or userdata[2] == 'none' else userdata[2]
                    photo = userdata[0]

                    if photo == '0':
                        photo = 'photo-204338719_457239214'

                    if city == 'all':
                        city = 'все города'

                    write_a_message_keyboard = VkKeyboard(inline=True)
                    write_a_message_keyboard.add_openlink_button('Написать 📧', f'https://vk.me/{user["screen_name"]}')

                    age = userdata[1] if userdata[1] else 'не указан'

                    send(f'{recipient[0]}, привет!👋\n'
                         f'{sender[0]} {sender[1]} поставил тебе лайк!\n\n'
                         '✅ Вот его анкета:\n\n'
                         f'💞 {userdata[3]} {userdata[4]} | {age} | {city}\n\n'
                         f'{userdata[5]}\n\nФото:', write_a_message_keyboard.get_keyboard(),
                         recipient[2],
                         photo)
                except:
                    send('Вы никого не просматриваете.')

                view()  # отправляю новую анкету

            elif '💔' in text:  # дизлайк
                recipient = database.execute(f'SELECT viewed_user FROM users WHERE user_id={user_id}').fetchone()
                recipient = database.execute(
                    f'SELECT name, surname, user_id FROM users WHERE user_id={recipient[0]}').fetchone()
                recipient_likes = \
                    database.execute(f'SELECT dislikes FROM users WHERE user_id={recipient[2]}').fetchone()[
                        0]
                database_query(f'UPDATE users SET dislikes={recipient_likes + 1} WHERE user_id={recipient[2]}')

                view()  # отправляю новую анкету

            elif '❌ отмена' in text:
                database_query(f'UPDATE users SET state=0 WHERE user_id={user_id}')
                send('Действие отменено ✅', mainmenu.get_keyboard())

            if database.execute(f'SELECT all_views FROM users WHERE user_id={user_id}').fetchone()[0] % 40 == 0:
                send('👋 Привет\n Чтобы просматривать больше анкет, подпишись!')

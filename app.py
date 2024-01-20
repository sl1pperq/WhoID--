import smtplib
from email.mime.text import MIMEText

from flask import Flask, render_template, request, jsonify, send_file
import json
import random
import uuid

app = Flask(__name__)
users = []
tokens = []
auth = []
cards = []
app.config['JSON_AS_ASCII'] = False

try:
    with open('data/users.json', 'r') as file:
        users = json.loads(file.read())
    with open('data/tokens.json', 'r') as file:
        tokens = json.loads(file.read())
    with open('data/auth.json', 'r') as file:
        auth = json.loads(file.read())
    with open('data/cards.json', 'r') as file:
        cards = json.loads(file.read())
except:
    pass


def save_data():
    with open('data/users.json', 'w') as file:
        file.write(json.dumps(users, ensure_ascii=False))
    with open('data/tokens.json', 'w') as file:
        file.write(json.dumps(tokens, ensure_ascii=False))
    with open('data/auth.json', 'w') as file:
        file.write(json.dumps(auth, ensure_ascii=False))
    with open('data/cards.json', 'w') as file:
        file.write(json.dumps(cards, ensure_ascii=False))


@app.route('/')
def hello_world():
    return render_template('main.html')


@app.route('/api-welcome.html')
def welcome_docs():
    return send_file('templates/docs/api-welcome.html')


@app.route('/api-python.html')
def python_docs():
    return send_file('templates/docs/api-python.html')


@app.route('/api-link.html')
def link_docs():
    return send_file('templates/docs/api-link.html')


@app.route('/api-oauth.html')
def oauth_docs():
    return send_file('templates/docs/api-oauth.html')

@app.route('/api-oauth-tg.html')
def oauth_tg_docs():
    return send_file('templates/docs/api-oauth-tg.html')


@app.route('/HelpTOC.json')
def help_toc():
    return send_file('HelpTOC.json')


@app.route('/config.json')
def config():
    return send_file('config.json')


@app.route('/login')
def login():
    go_type = request.args.get('create')
    return render_template('signin.html', create=go_type)


@app.route('/login', methods=['POST'])
def post_login():
    name = request.form.get('name')
    clas = request.form.get('class')
    tele = request.form.get('phone')
    mail = request.form.get('email')
    pasw = request.form.get('password')
    en_pasw = encrypt(pasw)
    user_id = str(random.randint(1000000, 9999999))
    if not check_if(mail):
        users.append({
            'id': user_id,
            'mail': mail,
            'password': pasw,
            'en_password': en_pasw,
            'name': name,
            'class': clas,
            'phone': tele,
            'authorized': False
        })
        save_data()
        text = f'Для активации аккаунта - перейдите по ссылке - https://whoid.ru/login/confirm/{user_id}'
        send_email_message(mail, text, 'WhoID: Активация')
        return render_template('message.html', msg='MailSend')
    else:
        return render_template('message.html', msg='HaveAccountError')


@app.route('/login/confirm/<id>')
def login_confirm(id):
    authorize_user(id)
    mail = get_user_id(id)['mail']
    text = f'Добро пожаловать! Теперь у вас есть аккаунт WhoID - это означает, что вы сможете быстро входить на многие школьные сайты.<p>Если у Вас возник вопрос - задайте его на почту admin@banjosurf.ru</p>С уважением,<br>администратор WhoID!'
    send_email_message(mail, text, 'WhoID: Регистрация')
    return render_template('message.html', msg='MailConfirm')


@app.route('/get_token', methods=['POST'])
def post_get_login():
    name = request.form.get('name')
    tele = request.form.get('phone')
    mail = request.form.get('email')
    target = request.form.get('target')
    token = str(uuid.uuid4())
    tokens.append({
        'token': token,
        'mail': mail,
        'target': target,
        'name': name,
        'phone': tele,
        'authorized': False
    })
    save_data()
    text = f'Для активации токена - перейдите по ссылке - http://whoid.ru/get_token/authorize/{token}'
    send_email_message(mail, text, 'WhoID: Токен')
    return render_template('message.html', msg='TokenSend')


@app.route('/get_token/authorize/<token>')
def get_token_autorize(token):
    authorize_token(token)
    mail = find_token_info(token)['mail']
    text = f'Вы успешно получили токен и теперь можете использовать WhoID API. Ваш токен - {token}.<p>Храните его в секрете и не передавайте третьим лицам. Если вы заподозрили, что его украли - незамедлительно сообщите об этом на почту admin@banjosurf.ru</p>С уважением,<br>администратор WhoID'
    send_email_message(mail, text, 'WhoID: Получение токена')
    return render_template('message.html', msg='TokenConfirm')


@app.route('/api/get')
def api_get():
    token = request.args.get('token')
    mail = request.args.get('mail')
    password = request.args.get('password')
    result = check_user(mail, password)
    if find_token(token):
        if result == "Incorrect password" or result == "Not found" or result == "Not authorized":
            response = {"error": result}
            return jsonify(response)
        else:
            response = {
                "name": result['name'],
                "class": result['class'],
                "phone": result['phone']
            }
            return jsonify(response)
    else:
        response = {
            "error": "Token not found"
        }
        return jsonify(response)


@app.route('/api/fio')
def api_fio():
    token = request.args.get('token')
    name = request.args.get('name')
    result = find_fio(name)
    if find_token(token):
        if result == 'Not found' or result == 'Not authorized':
            response = {"error": result}
            return jsonify(response)
        else:
            response = {
                "class": result['class'],
                "phone": result['phone'],
                "mail": result['mail']
            }
            return jsonify(response)
    else:
        response = {
            "error": "Token not found"
        }
        return jsonify(response)


@app.route('/api/mail')
def api_mail():
    token = request.args.get('token')
    mail = request.args.get('mail')
    result = get_user(mail)
    if find_token(token):
        if result == "Not found":
            return jsonify({"error": "User not found"})
        elif result == "Not authorized":
            return jsonify({"error": "Not authorized"})
        else:
            return jsonify(
                {"name": result['name'], "class": result['class'], 'phone': result['phone']}
            )
    else:
        response = {
            "error": "Token not found"
        }
        return jsonify(response)

@app.route('/api/auth/find')
def api_auth_find():
    token = request.args.get('token')
    id = request.args.get('id')
    result = find_auth(id)
    print(result)
    if find_token(token):
        if result != False:
            return jsonify(result)
        else:
            return jsonify({"error": "Error"})
    else:
        return jsonify({"error": "Token not found"})


@app.route('/api/token')
def api_token():
    token = request.args.get('token')
    result = find_token(token)
    if result == "Not found":
        return jsonify({"error": "Token not found", "recommendation": "Try again in a few seconds"})
    else:
        return jsonify(result)

@app.route('/auth/login')
def auth_login():
    token = request.args.get('token')
    link = request.args.get('link')
    bot = request.args.get('bot')
    if bot == "true":
        tg_bot = True
    else:
        tg_bot = False
    if find_free_auth(token):
        auth.append({
            'id': token,
            'status': "Logging",
            'link': link,
            'mail': None,
            'bot': tg_bot
        })
        save_data()
        return render_template('auth.html', token=token)
    else:
        return jsonify({"error": "Token already exists"})


@app.route('/auth/login', methods=['POST'])
def post_auth_login():
    token = request.args.get('token')
    mail = request.form.get('email')
    password = request.form.get('password')
    user = find_this_auth(token)
    if check_user_tf(mail, password):
        status_success_auth(token)
        change_auth_mail(token, mail)
        s = 'Вход был выполнен успешно! Вы можете вернуться на сайт!'
        text = 'Сейчас был выполнен вход в ваш аккаунт при помощи WhoID OAuth. Если это были не вы - срочно напишите на почту admin@banjosurf.ru'
        send_email_message(mail, text, 'WhoID: Вход в аккаунт')
        return render_template('auth.html', final=True, user=user, success=s)
    else:
        status_error_auth(token)
        return render_template('auth.html', final=False, user=user)


@app.route('/card/api/check')
def card_api_check():
    num = str(request.args.get('card'))
    check = find_card_id(num)
    if not check:
        return jsonify({"error": "Card ID not found"})
    else:
        return jsonify(check)

@app.route('/card/reg')
def card_api_register():
    num = request.args.get('card')
    if not find_card_id(num):
        return render_template('signin.html', create='card', num=num)
    else:
        return render_template('message.html', msg='AlreadyReg')

@app.route('/card/reg', methods=['POST'])
def card_reg():
    num = request.args.get('card')
    cards.append({
        'id': num,
        'student': request.form.get('mail')
    })
    save_data()
    return render_template('message.html', msg='AlreadyReg')


def find_card_id(id):
    for card in cards:
        if card['id'] == id:
            return card
    return False


def authorize_token(token):
    for t in tokens:
        if t['token'] == token:
            t['authorized'] = True
            save_data()


def authorize_user(id):
    for user in users:
        if user['id'] == id:
            user['authorized'] = True
            save_data()


def change_auth_mail(token, mail):
    for a in auth:
        if a['id'] == token:
            a['mail'] = mail
            save_data()
    return False


def status_success_auth(token):
    for a in auth:
        if a['id'] == token:
            a['status'] = 'Success'
            save_data()
    return False


def status_error_auth(token):
    for a in auth:
        if a['id'] == token:
            a['status'] = 'Error'
            save_data()
    return False


def find_this_auth(token):
    for a in auth:
        if a['id'] == token:
            return a
    return False


def find_free_auth(token):
    for a in auth:
        if a['id'] == token:
            return False
    return True

def find_auth(token):
    for a in auth:
        if a['id'] == token:
            return a
    return False

def find_token(token):
    for t in tokens:
        if t['token'] == token:
            if t['authorized']:
                return True
            else:
                return False
    return False


def find_token_info(token):
    for t in tokens:
        if t['token'] == token:
            return t
    return False


def check_if(mail):
    for user in users:
        if user['mail'] == mail:
            return True
    return False


def check_user(mail, password):
    for user in users:
        if user['mail'] == mail:
            if user['password'] == password:
                if user['authorized']:
                    return user
                else:
                    return "User not authorized"
            else:
                return "Incorrect password"
    return "Not found"


def check_user_tf(mail, password):
    for user in users:
        if user['mail'] == mail:
            if user['password'] == password:
                if user['authorized'] == True:
                    return True
                else:
                    return False
            else:
                return False
    return False


def find_fio(name):
    for user in users:
        if user['name'] == name:
            if user['authorized'] == True:
                return user
            else:
                return 'Not authorized'
    return "Not found"


def get_user(mail):
    for user in users:
        if user['mail'] == mail:
            if user['authorized'] == True:
                return user
            else:
                return "Not authorized"
    return "Not found"


def get_user_id(id):
    for user in users:
        if user['id'] == id:
            return user
    return "Not found"


def send_email_message(receiver_mail, text, title):
    port = 465
    password = 'TOKEN'
    sender_mail = 'banjobot@mail.ru'
    smtp_server = 'smtp.mail.ru'
    try:
        with smtplib.SMTP_SSL(smtp_server, port) as server:
            server.login(sender_mail, password)
            msg = MIMEText(f'{text}', 'html')
            msg['Subject'] = title
            msg['From'] = sender_mail
            msg['To'] = receiver_mail
            server.sendmail(sender_mail, receiver_mail, msg.as_string())
    except Exception as e:
        print(e)


def encrypt(text):
    result = ""
    for char in text:
        if char.isalpha():
            shift_amount = 10 % 26
            if char.islower():
                shifted_char = chr(((ord(char) - ord('a') + shift_amount) % 26) + ord('a'))
            else:
                shifted_char = chr(((ord(char) - ord('A') + shift_amount) % 26) + ord('A'))
            result += shifted_char
        else:
            result += char
    return result


def decrypt(text):
    result = ""
    for char in text:
        if char.isalpha():
            shift_amount = -10 % 26
            if char.islower():
                shifted_char = chr(((ord(char) - ord('a') + shift_amount) % 26) + ord('a'))
            else:
                shifted_char = chr(((ord(char) - ord('A') + shift_amount) % 26) + ord('A'))
            result += shifted_char
        else:
            result += char
    return result


app.run(port=5008)

from configparser import ConfigParser
from twocaptcha import TwoCaptcha
import random
import requests

config = ConfigParser()
ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"


def main():
    try:
        with open(f'{__file__}.cookie', 'r') as f:
            cookie = f.read()
    except FileNotFoundError:
        cookie = ''
        pass
    if cookie_valid(cookie):
        print('cookie 有效, 已跳过登录')
        return
    cookie = get_new_cookie()
    if cookie == '':
        print('登录失败')
        return
    if cookie_valid(cookie):
        print('登录成功')
        with open(f'{__file__}.cookie', 'w') as f:
            f.write(cookie)


def cookie_valid(cookie: str) -> bool:
    headers = {
        'cookie': cookie,
        'User-Agent': ua,
    }
    response = requests.get('https://u2.dmhy.org/index.php', headers=headers, allow_redirects=False)
    if response.status_code == 200:
        return True
    else:
        return False


def get_new_cookie() -> str:
    cookie = ''
    try:
        email = config['email']
        password = config['password']
        api_key = config['2captcha_key']
    except KeyError as e:
        print(f'未找到 {e.args}, 请检查 config.ini 文件')
        return ''

    solver = TwoCaptcha(api_key)
    if solver.balance() < 0.1:
        print('2captcha 余额不足')
        return ''
    base_url = 'https://u2.dmhy.org/'
    captcha_image_url = base_url + '/captcha.php?sid='
    login_url = base_url + '/takelogin.php'
    headers = {
        'User-Agent': ua,
    }

    failed_count = 0

    while failed_count < 5:
        print('进行第 %d 次登录尝试' % (failed_count + 1))
        response = requests.get(captcha_image_url + str(random.random()), headers=headers)
        if response.status_code != 200:
            print('获取验证码失败')
            return ''
        if cookie == '':
            cookie = response.headers['set-cookie'].split(';')[0]
            headers['cookie'] = cookie
        with open(f'{__file__}.captcha.png', 'wb') as f:
            f.write(response.content)
        try:
            result = solver.normal(f'{__file__}.captcha.png', min_len=4, max_len=4)
            code = result['code']
            print(f'验证码识别结果: {code}')
        except Exception as e:
            print(e)
            failed_count += 1
            continue
        # try login
        parmas = {
            'login_type': 'email',
            'login_ajax': '1',
            'username': email,
            'password': password,
            'captcha': code,
            'ssl': 'yes',
        }
        response = requests.post(login_url, headers=headers, data=parmas)
        print(response.text)
        status = response.json()['status']
        if status == 'redirect':
            cookie = response.headers['set-cookie'].split(';')[0]
            solver.report(result['captchaId'], True)
            print('cookie 获取成功')
            return cookie
        elif status == 'error':
            print('登录失败，验证码错误')
            failed_count += 1
            solver.report(result['captchaId'], False)
            continue
        else:
            return ''


def read_config():
    global config
    section = 'u2.dmhy.org'
    try:
        config.read('config.ini')
        config = config[section]
    except KeyError:
        print(f'未找到 section [{section}], 请检查 config.ini 文件')
        exit(1)


if __name__ == '__main__':
    read_config()
    main()

from celery import Celery
from django.core.mail import send_mail
from dailyfresh import settings

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dailyfresh.settings")

application = get_wsgi_application()

app = Celery('celery_tasks.tasks', broker='redis://localhost:6379/5')

@app.task
def send_rigister_active_email(to_mail, username, token):
    # 设置邮件的发送内容,参数如下
    # 邮件标题
    title = '欢迎注册天天生鲜'
    # 邮件正文
    # 发件人
    # 收件人列表
    # 网页信息
    msg_html = '''<h1>Dear %s:</h1>
                        请点击以下链接激活账户：<br>
                        <a href= 'http://192.168.138.131:8000/user/active/%s'>http://192.168.138.131:8000/user/active/%s</a>''' % (
    username, token, token)

    send_mail(title, '', settings.EMAIL_FROM, [to_mail ], html_message=msg_html)

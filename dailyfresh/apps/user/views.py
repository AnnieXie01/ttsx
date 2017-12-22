# 导入正则表达式
import re
# 导入django自带的验证用户名及密码是否匹配、保存用户登录状态、删除用户登录状态函数
from django.contrib.auth import authenticate, login, logout
# 导入views反向解析函数reverse
from django.core.urlresolvers import reverse
# 导入应答渲染函数render和跳转函数redirect
from django.shortcuts import render, redirect
# 导入views中的View类，使类视图继承该类
from django.views.generic import View
# 导入创建redis链接对象函数
from django_redis import get_redis_connection
# 导入数据加密类，并重命名类名称
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
# 导入应用goods中的商品SKU模型类
from apps.goods.models import GoodsSKU
# 导入应用user中的用户模型类和地址模型类
from apps.user.models import User, Address
# 导入celery异步文件中的发送邮件函数
from celery_tasks.tasks import send_rigister_active_email
# 导入项目中的settings文件中的加密秘钥
from dailyfresh.settings import SECRET_KEY


# Create your views here.

# /user/rigister
class Register(View):
    '''注册界面处理'''

    def get(self, request):
        # get请求处理，返回注册界面
        return render(request, 'register.html')

    def post(self, request):
        # 当请求为post，处理用户提交的注册信息

        # 使用request.POST获取用户提交的注册信息
        # 用户名
        username = request.POST.get('user_name')
        # 密码
        pwd = request.POST.get('pwd')
        # 确认密码
        cpwd = request.POST.get('cpwd')
        # 邮箱
        email = request.POST.get('email')
        # 是否同意用户协议
        allow = request.POST.get('allow')

        # 使用all方法判断数据的完整性，all()中用列表放入需要判断的数据内容
        # 只要有一个内容为空，则返回False
        if not all([username, pwd, email]):
            # 如果数据不完整，返回注册页面，并显示提示信息
            return render(request, 'register.html', {'error_msg': '数据不完整'})

        # 使用正则表达式判断邮箱是否有效
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            # 如果不匹配，返回注册界面，并显示提示信息
            return render(request, 'register.html', {'error_msg': '邮箱不合法'})

        # 判断两次输入的密码是否相同
        if pwd != cpwd:
            # 如不相同，返回注册界面及提示信息
            return render(request, 'register.html', {'error_msg': '两次输入的密码不相同'})

        # 判断是否勾选使用协议，
        # checkbox类型的input标签，当勾选时，值为on，不勾选，则为空
        if allow != 'on':
            # 如果值不为on，返回注册页面及提示信息
            return render(request, 'register.html', {'error_msg': '请同意用户协议'})

        # 判断用户名是否存在,判断邮箱是否已经注册
        try:
            user = User.objects.get(username=username)
            # user = User.objects.filter(Q(username=username) |Q(email=email))
        # 如果出现User.DoesNotExist错误，则说明未被注册，user为空
        except User.DoesNotExist:
            user = None
        # 判断user，确认用户是否注册，如果注册
        if user:
            # 返回注册页，并提示用户名已注册
            return render(request, 'register.html', {'error_msg': '用户名已存在'})
        # 代码到这里，说明验证都没有问题，执行create_user方法，在数据库中创建一个用户
        user = User.objects.create_user(username, email, pwd)
        # 默认用户的激活状态是True，改为False，0代表False
        user.is_active = 0
        # 保存修改内容
        user.save()

        # 创建数据加密器对象
        serializer = Serializer(SECRET_KEY, 3600)
        # 设置加密信息，加密的时候为字典，解密时候也为字典
        info = {'confirm': user.id}
        # 数据加密
        token = serializer.dumps(info)
        # 将加密后的数据进行解码为字符串
        token = token.decode()
        # 使用celery异步方式发送邮件，提高用户体验；
        # 使发送邮件的操作不因其他原因造成阻塞；
        # 影响到用户的下一步操作
        send_rigister_active_email.delay(email, username, token)
        # 操作完成，返回首页
        return redirect(reverse('goods:index'))

# /user/active/(\d)
class ActiveView(View):
    '''激活账户'''
    def get(self, request, token):
        # 激活账户时， 需要接收token参数，以确认用户id
        # 创建加密器对象
        serializer = Serializer(SECRET_KEY, 3600)
        # 调用加密器对象的ｌｏａｄｓ方法进行解密
        info = serializer.loads(token)
        # 通过字典的键取出用户ｉｄ，加密的数据是{'confirm'：user.id}
        user_id = info['confirm']
        # 查找对应id的用户，浏览器传输的数据都是str类型，需要进行类型转换
        user = User.objects.get(id=int(user_id))
        # 将查找到的对象的激活值改为１，1为True
        user.is_active = 1
        # 保存修改到数据库
        user.save()
        # 跳转到用户登录页
        return redirect(reverse('user:login'))

# /user/login
class LoginView(View):
    '''用户登录处理'''
    # 当用户请求为get类型
    def get(self, request):
        #　获取ｃｏｏｋｉｅｓ中是否存在用户名
        # 如果用户在上一次登录时，保存过用户名，则cookies中会有对应的cookie
        # 如果username在cookies中
        if 'username' in request.COOKIES:
            # 则用户名为cookies中的username
            username = request.COOKIES['username']
            # 是否记住用户为勾选
            checked = 'checked'
        # 如果没有
        else:
            # 则用户名默认为空
            username = ''
            # 记住用户不勾选
            checked = ''
        # 返回登录页面及前端需要使用的参数
        return render(request, 'login.html', {'username':username, 'checked':checked})

    # 如果请求为post类型
    def post(self, request):
        '''处理post的登录请求'''
        # 获取用户名，密码，是否记住用户
        username = request.POST.get('username')
        pwd = request.POST.get('pwd')
        remember = request.POST.get('remember')

        # 判断数据是否完整
        if not all([username, pwd]):
            return render(request, 'login.html', {'error_msg':'数据不完整'})
        # 判断用户名及密码是否匹配，使用django自带的验证函数authenticate，传入用户名及密码
        user = authenticate(username=username,password=pwd)
        # 当密码不匹配，返回值为一个user对象，如为空，则代表用户名密码不匹配
        # 如果不为空，代表用户名密码正确
        if user is not None:
            # 判断账户是否激活
            if user.is_active:
                # 如果账户激活，记录用户的登录状态，使用django自带的login函数进行记录，会将状态记录到redis中
                login(request, user)
                # 获取get请求中的ｎｅｘｔ，如果有，返回跳转到ｎｅｘｔ中的链接，如果没有，设置默认跳转到首页
                next = request.GET.get('next', reverse('goods:index'))
                response = redirect(next)
                # 如果用户名及密码正确，且账户已激活，判断是否勾选记住用户名
                if remember == 'on':
                    # 如勾选，则设置cookie记住用户名，设置cookies的保存时长为7天
                    response.set_cookie('username', username, max_age=7*24*3600)

                else:
                    # 如果没有勾选，则删除cookie里面的username的cookie
                    response.delete_cookie('username')
                # 返回应答
                return response
            # 如果账户未被激活，返回登录页面及错误提示信息
            else:
                return render(request, 'login.html', {'error_msg':'用户未激活'})
        # 如果user为空，则用户名密码不匹配，返回登录页及错误提示信息
        else:
            return render(request, 'login.html', {'error_msg':'用户名或密码错误'})

# /user/logout
class LogoutView(View):
    '''退出登录处理'''
    def get(self, request):
        # 如果用户选择退出登录，清除用户的登录状态
        logout(request)
        # 返回首页
        return redirect(reverse('goods:index'))

# /user/user_center_info
class CenterInfoView(View):
    '''用户中心个人信息页'''
    # 用户申请用户中心个人信息页
    def get(self, request):
        '''处理get页面请求'''
        # 获取request中记录的user对象
        user = request.user
        # 使用用户的user对象，获取用户的默认地址信息
        try:
            addr= Address.objects.get(user=user, is_default=True)
        # 如果无法获取，则代表没有地址信息
        except Address.DoesNotExist:
            # 设置addr为空
            addr=None

        # 使用django_redis的get_redis_connection函数创建redis的链接对象，查询用户的浏览记录，
        # 浏览记录保存在redis中
        conn = get_redis_connection('default')
        # 根据键及用户id查询浏览记录
        history = 'history_%d' % user.id
        # 获取用户浏览的5条数据，保存的数据为商品SKUid
        sku_ids = conn.lrange(history, 0, 4) # 查询5个值得到的是列表[]
        # 根据id，获取商品的数据对象
        skus = GoodsSKU.objects.filter(id__in=sku_ids)
        # 默认获取的数据都按照ｉｄ排序，需要按照浏览顺序排序，需重新定义一个列表
        sku_list = []
        # 遍历id列表，获取id
        for i in sku_ids:
            # 遍历商品对象列表，获取商品对象
            for j in skus:
                # 如果商品对象的id等于id列表中的id，将商品对象放入新列表中
                # 浏览器传入的数据默认为str类型，需要对比需转换为整数类型
                if j.id == int(i):
                    sku_list.append(j)

        # 返回用户中心的个人信息页面，并返回地址信息对象和浏览记录对象的列表
        return render(request, 'user_center_info.html', {'addr':addr, 'sku_list':sku_list})

# /user/user_center_order
class CenterOrderView(View):
    '''处理用户中心，订单页面请求'''
    def get(self, request):
        # 返回订单页面
        return render(request, 'user_center_order.html')

# /user/user_center_site
class CenterSiteView(View):
    '''处理用户中心，地址页面请求'''
    def get(self, request):
        '''处理get请求'''
        # 获取request中的用户对象
        user = request.user
        # 获取用户对象的默认地址数据
        try:
            addr = Address.objects.get(user=user, is_default=True)
        # 如果没有，则代表用户没有设置过地址，则对象为空
        except Address.DoesNotExist:
            addr = None
        # 返回需求页面，及对应的地址对象参数
        return render(request, 'user_center_site.html', {'addr': addr})

    def post(self, request):
        '''处理增加地址的post请求'''
        # 获取post中的收件人，地址，邮编，联系电话参数
        receiver = request.POST.get('receiver')
        addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get('phone')

        # 使用all函数判断数据的完整性，邮编可以为空，不需要判断
        if not all([receiver, addr, phone]):
            # 如果数据不完整，返回页面，并返回错误提示信息
            return render(request, 'user_center_site.html', {'error_msg': '数据不完整'})
        # 判断手机号码是否合法，如不合法
        if not re.match(r'1[3457]\d{9}', phone):
            # 返回页面，并返回错误提示信息
            return render(request, 'user_center_site.html', {'error_msg': '手机号码不合法'})

        # 判断是否存在默认地址：
        # 获取request中的user对象
        user = request.user
        # 使用对象，获取对象是否有默认地址
        try:
            address = Address.objects.get(user=user, is_default=True)
        # 如果没有，则代表未设置过地址
        except Address.DoesNotExist:
            address = None
        # 设置新增的地址为默认地址
        is_default = True
        # 如果有查询到的地址对象，则设置为非默认地址
        if address:
            is_default = False
        # 在数据库中新增地址数据
        Address.objects.create(user=user, receiver=receiver, addr=addr, zip_code=zip_code, phone=phone, is_default=is_default)

        # 返回到地址页
        return redirect(reverse('user:center_site'))

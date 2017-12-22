from django.conf import settings
from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client


class FDFSStorage(Storage):
    '''fastdfs文件存储类'''
    def __init__(self, client_conf=None, base_url=None):
        '''初始化
            初始化storage类时，不能设置没有值的参数，
            所以需要使用命名参数的形式，接收客户端传入的参数
        '''
        if client_conf is None:
            # 如果客户端没有传入配置文件，默认使用settings中设置好的配置文件
            client_conf = settings.FDFS_CLIENT_CONF
        # 设置client_conf的类属性
        self.client_conf = client_conf
        if base_url is None:
            # 如果客户端没有传入fdfs服务器的url地址，默认使用settings中设置好的服务器地址
            base_url = settings.FDFS_SERVER_URL
        # 设置fdfs服务器地址的类属性
        self.base_url = base_url

    def _open(self, name, mode='rb'):
        '''获取文件'''
        # 使用自Storage类中继承的open方法，将文件获取方式设置为‘rb’
        pass

    def _save(self, name, content):
        '''存储文件方法'''
        # 重点内容
        # 创建客户端,使用客户端配置文件，创建客户端对象
        client = Fdfs_client(self.client_conf)
        # 上传文件到fdfs文件存储系统,以buffer方式
        res = client.upload_by_buffer(content.read())
        # 如果上传成功，会返回如下字典
        # {
        #     'Group name': group_name,
        #     'Remote file_id': remote_file_id, # 返回的文件的ID
        #     'Status': 'Upload successed.', # 上传是否成功
        #     'Local file name': '',
        #     'Uploaded size': upload_size,
        #     'Storage IP': storage_ip
        # }

        # 判断文件是否上传成功
        if res.get('Status') != 'Upload successed.':
            # 由于数据库需要保存对应的文件路径，故必须返回内容，返回的内容会储存到数据库中
            raise Exception('上传文件到fdfs系统失败')

        # 如果未失败，获取返回值中的文件按id
        file_id = res.get('Remote file_id')

        # 将id返回给数据库
        return file_id

    def exists(self, name):
        '''判断文件是否存在'''
        # django系统默认在上传文件前，会判断文件是否已存在，由于返回的id具有唯一性，不会存在相同的用户名，所以只需返回False表示没有重复的用户名即可
        return False

    def url(self, name):
        '''返回一个可访问到文件的url路径'''
        # name为文件id
        return self.base_url + name
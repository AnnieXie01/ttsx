from django.db import models

class BaseModel(models.Model):

    create_time = models.DateField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateField(auto_now=True, verbose_name='更新时间')
    is_delete = models.BooleanField(default=False, verbose_name='是否删除')

    class Meta:
        # 指定这个类是一个抽象模型类
        abstract = True
from django.shortcuts import render
from django.views.generic import View
from apps.goods.models import GoodsSKU, GoodsType, IndexGoodsBanner, IndexPromotionBanner, GoodsImage, Goods

# Create your views here.


class IndexView(View):
    '''商品首页'''
    def get(self, request):
        # 获取商品种类对象
        types = GoodsType.objects.all()
        goods_banners = IndexGoodsBanner.objects.all().order_by()

        return render(request, 'index.html')
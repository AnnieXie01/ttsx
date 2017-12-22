from django.conf.urls import url
from apps.user.views import Register, ActiveView, LoginView, LogoutView
from apps.user.views import CenterInfoView, CenterOrderView, CenterSiteView
from django.contrib.auth.decorators import login_required

urlpatterns = [
    url(r'^register$', Register.as_view(), name='register'),
    url(r'^active/(.*)$', ActiveView.as_view(), name='active'),
    url(r'^login$', LoginView.as_view(), name='login'),
    url(r'^logout$', LogoutView.as_view(), name='logout'),
    url(r'^user_center_info$', login_required(CenterInfoView.as_view()), name='center_info'),
    url(r'^user_center_order$', login_required(CenterOrderView.as_view()), name='center_order'),
    url(r'^user_center_site$', login_required(CenterSiteView.as_view()), name='center_site'),
]
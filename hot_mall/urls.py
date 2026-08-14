"""hot_mall URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from goods import views as goods_views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('pos/', include('pos.urls', namespace='pos')),
    path('', include('contents.urls', namespace='contents')),
    path('', include('users.urls', namespace='users')),
    path('', include('verifications.urls')),
    path('', include('areas.urls')),
    path('', include('goods.urls', namespace='goods')),
    path('', include('gms.urls', namespace='gms')),
    path('', include('suppliers.urls', namespace='suppliers')),
    path('search/', goods_views.AutoSearchView.as_view(), name='haystack_search'),
    path('', include('carts.urls', namespace='carts')),
    path('', include('orders.urls', namespace='orders')),
    path('', include('payment.urls', namespace='payment')),
    path('lottery/', include('hot_mall.apps.lottery.urls', namespace='lottery')),
    path('search/cart.html', lambda request: redirect('/carts')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

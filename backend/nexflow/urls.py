from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('', include('tasks.urls')),
    path('', include('meetings.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static('/css/', document_root=settings.STATICFILES_DIRS[0] / 'css')
    urlpatterns += static('/js/', document_root=settings.STATICFILES_DIRS[0] / 'js')
    urlpatterns += static('/images/', document_root=settings.STATICFILES_DIRS[0] / 'images')


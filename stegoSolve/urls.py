from django.contrib import admin
from django.urls import path
from steg_app import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.upload_view, name='upload'),
    path('analyse/exif/',    views.analyse_exif,    name='analyse_exif'),
    path('analyse/strings/', views.analyse_strings, name='analyse_strings'),
    path('analyse/steghide/',   views.analyse_steghide,   name='analyse_steghide'),
    path('analyse/metadata', views.analyse_metadata, name="analyse_metadata"),
    path('analyse/binwalk', views.analyse_binwalk, name="analyse_binwalk"),
    path('analyse/stegsolve', views.analyse_stegsolve, name="analyse_stegsolve"),
    path('analyse/zsteg', views.analyse_zsteg,name='analyse_zsteg'),
    path('analyse/foremost', views.analyse_foremost, name='analyse_foremost'),
    path('analyse/file', views.analyse_file, name='analyse_file'),
    path('analyse/pngcheck', views.analyse_pngcheck, name='analyse_pngcheck'),
    path('analyse/jpeginfo', views.analyse_jpeginfo, name='analyse_jpeginfo'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

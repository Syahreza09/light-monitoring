from django.contrib import admin
from django.urls import path
from light_monitoring import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('api/sensor/lantai4/', views.sensor_lantai4, name='sensor_lantai4'),
    path('admin/', admin.site.urls),
]

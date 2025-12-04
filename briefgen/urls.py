"""
URL configuration for briefgen project.
"""
from django.contrib import admin
from django.urls import path
from generator import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('api/generate-brief/', views.generate_brief, name='generate_brief'),
]


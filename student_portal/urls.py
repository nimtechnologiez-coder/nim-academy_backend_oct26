"""
URL configuration for student_portal project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from django.urls import path
from studentsapp import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', views.admin_login_view, name='admin_login'),
    path('logout/', views.admin_logout_view, name='admin_logout'),
    path('', views.registrations_dashboard, name='registrations_dashboard'),
    path('dashboard/', views.registrations_dashboard, name='registrations_dashboard'),
    path('api/register/', views.api_register, name='api_register'),
    path('api/registrations/', views.api_get_registrations, name='api_get_registrations'),
    path('api/registration/<int:pk>/status/', views.update_registration_status, name='update_registration_status'),
    path('api/registration/<int:pk>/delete/', views.delete_registration, name='delete_registration'),
    path('export-excel/', views.export_excel_view, name='export_excel'),
]


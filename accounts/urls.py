from django.urls import path
from .views import RegisterView,AllProfileManagemenetView,ProfileManagementView
urlpatterns = [
    path('register/',RegisterView.as_view(),name='register_view'),
    path('profile/',ProfileManagementView.as_view(),name="get_current_user"),
    path('',AllProfileManagemenetView.as_view(),name="get_all_users")
]

from django.urls import path, include
from .views import RegisterView, MyProfileView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("me/", MyProfileView.as_view(), name="my_profile"),
    
    path("feed/", include("apps.users.feed_urls")),
]

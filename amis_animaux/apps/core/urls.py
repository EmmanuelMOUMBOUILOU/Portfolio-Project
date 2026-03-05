from django.contrib.auth.views import LogoutView

from django.urls import path
from .views import (
    home, profiles_list, profile_detail, send_match,
    messages_home, messages_conversation, start_conversation,
    match_screen, register_view, login_view, logout_view,
    me_profile, me_animal_add, me_animal_edit, me_animal_delete,
    matches_page, match_update_status, ajax_send_match
)

urlpatterns = [
    path("", home, name="home"),
    path("profiles/", profiles_list, name="profiles_list"),
    path("profiles/<int:user_id>/", profile_detail, name="profile_detail"),
    path("profiles/<int:user_id>/match/", send_match, name="send_match"),
    path("register/", register_view, name="register"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("me/", me_profile, name="me_profile"),
    path("me/animals/add/", me_animal_add, name="me_animal_add"),
    path("me/animals/<int:animal_id>/edit/", me_animal_edit, name="me_animal_edit"),
    path("me/animals/<int:animal_id>/delete/", me_animal_delete, name="me_animal_delete"),

    # Chat (templates)
    path("messages/", messages_home, name="messages_home"),
    path("messages/start/<int:user_id>/", start_conversation, name="start_conversation"),
    path("messages/<int:conversation_id>/", messages_conversation, name="messages_conversation"),

    # Écran match
    path("match/<int:match_id>/", match_screen, name="match_screen"),
    path("matches/", matches_page, name="matches_page"),
    path("matches/<int:match_id>/update/", match_update_status, name="match_update_status"),
    path("ajax/match/<int:user_id>/", ajax_send_match, name="ajax_send_match"),
]

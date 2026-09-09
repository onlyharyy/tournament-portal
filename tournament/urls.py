from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from scoreboard import views

urlpatterns = [
    path("", views.home, name="home"),
    path("live-score/", views.scoreboard, name="scoreboard"),
    path("register/", views.register, name="register"),
    path("face-match/", views.face_match, name="face_match"),
    path("confirm-arrival/", views.confirm_arrival, name="confirm_arrival"),
    path("admin-login/", views.admin_login, name="admin_login"),
    path("logout/", views.admin_logout, name="admin_logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/schools/", views.school_dashboard, name="school_dashboard"),
    path("settings/", views.tournament_settings, name="tournament_settings"),
    path("faculties/", views.faculties, name="faculties"), path("faculties/add/", views.faculty_add, name="faculty_add"), path("faculties/<int:pk>/edit/", views.faculty_edit, name="faculty_edit"), path("faculties/<int:pk>/delete/", views.faculty_delete, name="faculty_delete"),
    path("players/", views.players, name="players"), path("players/add/", views.player_add, name="player_add"), path("players/<int:pk>/edit/", views.player_edit, name="player_edit"), path("players/<int:pk>/delete/", views.player_delete, name="player_delete"),
    path("schools/", views.schools, name="schools"), path("schools/add/", views.school_add, name="school_add"), path("schools/<int:pk>/edit/", views.school_edit, name="school_edit"), path("schools/<int:pk>/delete/", views.school_delete, name="school_delete"),
    path("games/", views.games, name="games"), path("games/add/", views.game_add, name="game_add"), path("games/<int:pk>/edit/", views.game_edit, name="game_edit"), path("games/<int:pk>/delete/", views.game_delete, name="game_delete"),
    path("scores/", views.scores, name="scores"), path("scores/add/", views.score_add, name="score_add"), path("scores/<int:pk>/edit/", views.score_edit, name="score_edit"), path("scores/<int:pk>/delete/", views.score_delete, name="score_delete"),
    path("django-admin/", admin.site.urls),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

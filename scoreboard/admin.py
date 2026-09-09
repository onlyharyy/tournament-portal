from django.contrib import admin
from .models import Attendance, Faculty, Game, Player, School, Score, TournamentConfig

@admin.register(TournamentConfig)
class TournamentConfigAdmin(admin.ModelAdmin):
    list_display = ("name", "registration_open", "scoreboard_public", "face_checkin_enabled", "updated_at")

@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "created_at")
    search_fields = ("name", "code")

@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ("name", "faculty_code", "school", "gender", "registered_publicly")
    list_filter = ("school", "gender", "registered_publicly")
    search_fields = ("name", "faculty_code", "phone", "email")

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ("name", "player_code", "school", "standard", "gender", "present")
    list_filter = ("school", "standard", "gender", "present")
    search_fields = ("name", "player_code", "phone", "email", "faculty_coordinator__name")

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("player", "confirmed", "scanned_at")
    list_filter = ("confirmed", "scanned_at")
    search_fields = ("player__name", "player__player_code")

@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ("name", "active")
    list_filter = ("active",)

@admin.register(Score)
class ScoreAdmin(admin.ModelAdmin):
    list_display = ("player", "game", "points", "updated_at")
    list_filter = ("game", "player__school")
    search_fields = ("player__name", "player__player_code")

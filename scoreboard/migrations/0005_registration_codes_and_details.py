from django.db import migrations, models


def populate_codes(apps, schema_editor):
    School = apps.get_model("scoreboard", "School")
    Faculty = apps.get_model("scoreboard", "Faculty")
    Player = apps.get_model("scoreboard", "Player")
    import re

    def initials(value):
        return "".join(w[0] for w in re.findall(r"[A-Za-z]+", value or "")).upper() or "X"

    for index, school in enumerate(School.objects.order_by("created_at", "id"), start=1):
        if not school.code or school.code.startswith("KC") is False:
            school.code = f"KC{index:02d}{initials(school.name)}"
            school.save(update_fields=["code"])
    for faculty in Faculty.objects.select_related("school").order_by("id"):
        if not faculty.faculty_code:
            faculty.faculty_code = f"{faculty.school.code}{initials(faculty.name)}"
            faculty.save(update_fields=["faculty_code"])
    for player in Player.objects.select_related("school", "faculty_coordinator").order_by("id"):
        if not player.player_code or player.player_code.startswith("PLR-"):
            player.player_code = f"{player.school.code}{initials(player.faculty_coordinator.name)}{initials(player.name)}"
            player.save(update_fields=["player_code"])


class Migration(migrations.Migration):
    dependencies = [("scoreboard", "0004_tournament_config_attendance_face_fields")]
    operations = [
        migrations.AddField(model_name="tournamentconfig", name="email_sender", field=models.EmailField(default="prajapatiharry198@gmail.com", max_length=254)),
        migrations.AddField(model_name="player", name="date_of_birth", field=models.DateField(blank=True, null=True)),
        migrations.AddField(model_name="player", name="age", field=models.PositiveIntegerField(blank=True, null=True)),
        migrations.AddField(model_name="player", name="division", field=models.CharField(blank=True, max_length=30)),
        migrations.AddField(model_name="player", name="enrollment_no", field=models.CharField(blank=True, max_length=80)),
        migrations.AlterField(model_name="school", name="code", field=models.CharField(blank=True, max_length=30, unique=True)),
        migrations.AlterField(model_name="faculty", name="faculty_code", field=models.CharField(blank=True, max_length=50, unique=True)),
        migrations.AlterField(model_name="player", name="phone", field=models.CharField(blank=True, max_length=20)),
        migrations.AlterField(model_name="player", name="player_code", field=models.CharField(blank=True, max_length=50, unique=True)),
        migrations.RunPython(populate_codes, migrations.RunPython.noop),
    ]

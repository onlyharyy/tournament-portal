from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("scoreboard", "0003_alter_player_aadhaar_number_alter_player_gender_and_more")]

    operations = [
        migrations.CreateModel(
            name="TournamentConfig",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(default="Unwritten Rules", max_length=200)),
                ("tagline", models.CharField(default="Inter-School Real-World Championship", max_length=255)),
                ("description", models.TextField(default="One day outside the classroom. Experiences that stay for life.")),
                ("date", models.DateField(blank=True, null=True)),
                ("venue", models.CharField(default="Main Ground", max_length=255)),
                ("organizer", models.CharField(default="Karyakram Catalysts", max_length=200)),
                ("contact_phone", models.CharField(blank=True, max_length=30)),
                ("contact_email", models.EmailField(blank=True, max_length=254)),
                ("schools_count", models.PositiveIntegerField(default=10)),
                ("students_count", models.PositiveIntegerField(default=200)),
                ("missions_count", models.PositiveIntegerField(default=5)),
                ("days_count", models.PositiveIntegerField(default=1)),
                ("registration_open", models.BooleanField(default=True)),
                ("scoreboard_public", models.BooleanField(default=True)),
                ("face_checkin_enabled", models.BooleanField(default=True)),
                ("poster", models.ImageField(blank=True, null=True, upload_to="tournament/")),
                ("trophy", models.ImageField(blank=True, null=True, upload_to="tournament/")),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"verbose_name": "Tournament Settings", "verbose_name_plural": "Tournament Settings"},
        ),
        migrations.CreateModel(
            name="Attendance",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("scanned_at", models.DateTimeField(auto_now_add=True)),
                ("confirmed", models.BooleanField(default=False)),
                ("player", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attendance_records", to="scoreboard.player")),
            ],
            options={"ordering": ["-scanned_at"]},
        ),
        migrations.AddField(model_name="faculty", name="gender", field=models.CharField(blank=True, choices=[("Male", "Male"), ("Female", "Female"), ("Other", "Other")], max_length=20)),
        migrations.AddField(model_name="faculty", name="photo", field=models.ImageField(blank=True, null=True, upload_to="faculty/")),
        migrations.AddField(model_name="faculty", name="face_descriptor", field=models.JSONField(blank=True, null=True)),
        migrations.AddField(model_name="faculty", name="registered_publicly", field=models.BooleanField(default=False)),
        migrations.AddField(model_name="player", name="face_descriptor", field=models.JSONField(blank=True, null=True)),
        migrations.AddField(model_name="player", name="present", field=models.BooleanField(default=False)),
        migrations.AddField(model_name="player", name="arrived_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.AlterField(model_name="player", name="aadhaar_number", field=models.CharField(blank=True, max_length=12)),
        migrations.AddField(model_name="game", name="description", field=models.TextField(blank=True)),
    ]

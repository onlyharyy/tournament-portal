from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("scoreboard", "0005_registration_codes_and_details")]

    operations = [
        migrations.AddField(
            model_name="faculty",
            name="present",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="faculty",
            name="arrived_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name="FacultyAttendance",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("scanned_at", models.DateTimeField(auto_now_add=True)),
                ("confirmed", models.BooleanField(default=False)),
                ("faculty", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attendance_records", to="scoreboard.faculty")),
            ],
            options={"ordering": ["-scanned_at"]},
        ),
    ]

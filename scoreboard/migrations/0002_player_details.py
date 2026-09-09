from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [("scoreboard", "0001_initial")]
    operations = [
        migrations.AddField(model_name="player", name="gender", field=models.CharField(choices=[("Male","Male"),("Female","Female"),("Other","Other")], max_length=20, default="Other")),
        migrations.AddField(model_name="player", name="phone", field=models.CharField(max_length=20, default="")),
        migrations.AddField(model_name="player", name="email", field=models.EmailField(blank=True, max_length=254)),
        migrations.AddField(model_name="player", name="aadhaar_number", field=models.CharField(max_length=12, default="")),
        migrations.AddField(model_name="player", name="faculty_coordinator", field=models.CharField(max_length=150, default="")),
        migrations.AddField(model_name="player", name="photo", field=models.ImageField(blank=True, null=True, upload_to="players/")),
    ]

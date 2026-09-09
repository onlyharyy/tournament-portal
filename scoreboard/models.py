import re
import unicodedata

from django.db import models


def _initials(value):
    words = re.findall(r"[A-Za-z]+", unicodedata.normalize("NFKD", value or ""))
    letters = "".join(word[0] for word in words).upper()
    return letters or "X"


def _name_initials(value):
    return _initials(value)


def _next_school_serial():
    max_serial = 0
    for code in School.objects.values_list("code", flat=True):
        match = re.match(r"^KC(\d+)[A-Z]+$", code or "")
        if match:
            max_serial = max(max_serial, int(match.group(1)))
    return max_serial + 1


class TournamentConfig(models.Model):
    name = models.CharField(max_length=200, default="Unwritten Rules")
    tagline = models.CharField(max_length=255, default="Inter-School Real-World Championship")
    description = models.TextField(default="One day outside the classroom. Experiences that stay for life.")
    date = models.DateField(null=True, blank=True)
    venue = models.CharField(max_length=255, default="Main Ground")
    organizer = models.CharField(max_length=200, default="Karyakram Catalysts")
    contact_phone = models.CharField(max_length=30, blank=True)
    contact_email = models.EmailField(blank=True)
    email_sender = models.EmailField(default="prajapatiharry198@gmail.com")
    schools_count = models.PositiveIntegerField(default=10)
    students_count = models.PositiveIntegerField(default=200)
    missions_count = models.PositiveIntegerField(default=5)
    days_count = models.PositiveIntegerField(default=1)
    registration_open = models.BooleanField(default=True)
    scoreboard_public = models.BooleanField(default=True)
    face_checkin_enabled = models.BooleanField(default=True)
    poster = models.ImageField(upload_to="tournament/", blank=True, null=True)
    trophy = models.ImageField(upload_to="tournament/", blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Tournament Settings"
        verbose_name_plural = "Tournament Settings"

    def __str__(self):
        return self.name

    @classmethod
    def current(cls):
        obj = cls.objects.first()
        if obj is None:
            obj = cls.objects.create()
        return obj


class School(models.Model):
    name = models.CharField(max_length=150, unique=True)
    code = models.CharField(max_length=30, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.code:
            serial = _next_school_serial()
            self.code = f"KC{serial:02d}{_initials(self.name)}"
            while School.objects.filter(code=self.code).exclude(pk=self.pk).exists():
                serial += 1
                self.code = f"KC{serial:02d}{_initials(self.name)}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.code})"

    @property
    def total_score(self):
        return self.players.aggregate(total=models.Sum("scores__points"))["total"] or 0


class Faculty(models.Model):
    GENDER_CHOICES = [("Male", "Male"), ("Female", "Female"), ("Other", "Other")]
    name = models.CharField(max_length=150)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="faculty")
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    faculty_code = models.CharField(max_length=50, unique=True, blank=True)
    photo = models.ImageField(upload_to="faculty/", blank=True, null=True)
    face_descriptor = models.JSONField(blank=True, null=True)
    registered_publicly = models.BooleanField(default=False)
    present = models.BooleanField(default=False)
    arrived_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.faculty_code and self.school_id and self.name:
            school = self.school if self.pk else School.objects.get(pk=self.school_id)
            self.faculty_code = f"{school.code}{_name_initials(self.name)}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} — {self.school.name}"


class Player(models.Model):
    GENDER_CHOICES = [("Male", "Male"), ("Female", "Female"), ("Other", "Other")]
    name = models.CharField(max_length=150)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="players")
    faculty_coordinator = models.ForeignKey(Faculty, on_delete=models.PROTECT, related_name="students")
    standard = models.CharField(max_length=30, blank=True)
    division = models.CharField(max_length=30, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    enrollment_no = models.CharField(max_length=80, blank=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    aadhaar_number = models.CharField(max_length=12, blank=True)
    photo = models.ImageField(upload_to="players/", blank=True, null=True)
    face_descriptor = models.JSONField(blank=True, null=True)
    player_code = models.CharField(max_length=50, unique=True, blank=True)
    present = models.BooleanField(default=False)
    arrived_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.player_code and self.school_id and self.faculty_coordinator_id and self.name:
            school = self.school if self.pk else School.objects.get(pk=self.school_id)
            faculty = self.faculty_coordinator if self.pk else Faculty.objects.get(pk=self.faculty_coordinator_id)
            self.player_code = f"{school.code}{_name_initials(faculty.name)}{_name_initials(self.name)}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} — {self.school.name}"

    @property
    def total_score(self):
        return self.scores.aggregate(total=models.Sum("points"))["total"] or 0


class Attendance(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="attendance_records")
    scanned_at = models.DateTimeField(auto_now_add=True)
    confirmed = models.BooleanField(default=False)

    class Meta:
        ordering = ["-scanned_at"]

    def __str__(self):
        return f"{self.player.name} — {self.scanned_at:%Y-%m-%d %H:%M}"


class FacultyAttendance(models.Model):
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name="attendance_records")
    scanned_at = models.DateTimeField(auto_now_add=True)
    confirmed = models.BooleanField(default=False)

    class Meta:
        ordering = ["-scanned_at"]

    def __str__(self):
        return f"{self.faculty.name} — {self.scanned_at:%Y-%m-%d %H:%M}"


class Game(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Score(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="scores")
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="scores")
    points = models.IntegerField(default=0)
    remarks = models.CharField(max_length=255, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-points", "-updated_at"]
        constraints = [models.UniqueConstraint(fields=["player", "game"], name="unique_player_game_score")]

    def __str__(self):
        return f"{self.player.name} — {self.game.name}: {self.points}"

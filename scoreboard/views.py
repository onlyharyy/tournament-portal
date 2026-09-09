import base64
import json
import math
import uuid
from datetime import date

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import Attendance, Faculty, FacultyAttendance, Game, Player, School, Score, TournamentConfig


def _save_data_url(instance, field_name, data_url, prefix):
    if not data_url or "," not in data_url:
        return False
    try:
        _, encoded = data_url.split(",", 1)
        raw = base64.b64decode(encoded)
        getattr(instance, field_name).save(
            f"{prefix}_{uuid.uuid4().hex[:10]}.jpg", ContentFile(raw), save=False
        )
        return True
    except (ValueError, TypeError):
        return False


def _parse_date(value):
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _age_from_dob(dob):
    if not dob:
        return None
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def _send_registration_email(person, category, config):
    if not person.email:
        return
    code = person.faculty_code if category == "Teacher" else person.player_code
    school = person.school.name
    subject = f"{config.name} — Registration Confirmed ({code})"
    body = (
        f"Dear {person.name},\n\n"
        f"Your {category.lower()} registration for {config.name} has been confirmed.\n\n"
        f"Registration code: {code}\n"
        f"School: {school}\n"
        f"Category: {category}\n"
    )
    if category == "Student":
        body += (
            f"Faculty Coordinator: {person.faculty_coordinator.name}\n"
            f"Standard / Class: {person.standard}\n"
            f"Division: {person.division or '—'}\n"
            f"Date of Birth: {person.date_of_birth or '—'}\n"
            f"Age: {person.age or '—'}\n"
            f"Student ID / Enrollment No.: {person.enrollment_no or '—'}\n"
        )
    else:
        body += "Faculty Coordinator registration is complete.\n"
    body += (
        f"Tournament date: {config.date or 'To be announced'}\n"
        f"Venue: {config.venue}\n\n"
        "Please keep this code safe. It is your official tournament registration reference.\n\n"
        f"Regards,\n{config.organizer}"
    )
    send_mail(subject, body, config.email_sender or settings.DEFAULT_FROM_EMAIL, [person.email], fail_silently=True)


def home(request):
    config = TournamentConfig.current()
    return render(request, "home.html", {"config": config})


def scoreboard(request):
    config = TournamentConfig.current()
    if not config.scoreboard_public and not request.user.is_authenticated:
        return render(request, "feature_off.html", {"title": "Live Scoreboard", "message": "The live scoreboard is currently unavailable."})
    players = list(Player.objects.select_related("school").annotate(total=Sum("scores__points")).order_by("-total", "name"))
    schools = list(School.objects.annotate(total=Sum("players__scores__points")).order_by("-total", "name"))
    games = Game.objects.filter(active=True).prefetch_related("scores__player__school")
    return render(request, "scoreboard.html", {"players": players, "schools": schools, "games": games, "config": config})


def register(request):
    config = TournamentConfig.current()
    if not config.registration_open and not request.user.is_authenticated:
        return render(request, "feature_off.html", {"title": "Registration Closed", "message": "Participant registration is currently closed by the tournament administrator."})
    schools = School.objects.all()
    faculties = Faculty.objects.select_related("school").all()
    if request.method == "POST":
        category = request.POST.get("category")
        try:
            with transaction.atomic():
                if category == "teacher":
                    school = get_object_or_404(School, pk=request.POST.get("school"))
                    name = request.POST.get("name", "").strip()
                    email = request.POST.get("email", "").strip()
                    phone = request.POST.get("phone", "").strip()
                    descriptor = json.loads(request.POST.get("face_descriptor", "[]"))
                    if not name or not email or not phone or not request.POST.get("gender") or len(descriptor) != 128:
                        raise ValueError("Name, gender, school, phone, email and a valid single-face selfie are required.")
                    obj = Faculty(
                        name=name, school=school, gender=request.POST.get("gender", ""), phone=phone,
                        email=email, face_descriptor=descriptor, registered_publicly=True,
                    )
                    if not _save_data_url(obj, "photo", request.POST.get("photo_data"), "faculty"):
                        raise ValueError("A valid selfie is required.")
                    obj.save()  # code is generated automatically
                    transaction.on_commit(lambda p=obj, c=config: _send_registration_email(p, "Teacher", c))
                    return render(request, "registration_success.html", {"person": obj, "category": "Teacher", "config": config})

                if category == "student":
                    school = get_object_or_404(School, pk=request.POST.get("school"))
                    faculty = get_object_or_404(Faculty, pk=request.POST.get("faculty_coordinator"), school=school)
                    name = request.POST.get("name", "").strip()
                    email = request.POST.get("email", "").strip()
                    phone = request.POST.get("phone", "").strip()
                    descriptor = json.loads(request.POST.get("face_descriptor", "[]"))
                    dob = _parse_date(request.POST.get("date_of_birth", ""))
                    age = _age_from_dob(dob)
                    submitted_age = request.POST.get("age", "").strip()
                    if not dob and submitted_age.isdigit():
                        age = int(submitted_age)
                    if (not name or not email or not phone or not request.POST.get("gender") or not dob
                            or not request.POST.get("standard") or not request.POST.get("division")
                            or not request.POST.get("aadhaar_number") or len(descriptor) != 128):
                        raise ValueError("All student fields are required, including DOB, division, mobile, Aadhaar and a valid selfie.")
                    obj = Player(
                        name=name, school=school, faculty_coordinator=faculty,
                        standard=request.POST.get("standard", "").strip(),
                        division=request.POST.get("division", "").strip(),
                        date_of_birth=dob, age=age,
                        enrollment_no=request.POST.get("enrollment_no", "").strip(),
                        gender=request.POST.get("gender", ""), phone=phone,
                        email=email, aadhaar_number=request.POST.get("aadhaar_number", "").strip(),
                        face_descriptor=descriptor,
                    )
                    if not obj.standard or not obj.gender or not obj.division or not obj.phone or not obj.aadhaar_number or not obj.date_of_birth:
                        raise ValueError("Standard, division, gender, DOB, mobile and Aadhaar are required for students.")
                    if not _save_data_url(obj, "photo", request.POST.get("photo_data"), "player"):
                        raise ValueError("A valid selfie is required.")
                    obj.save()  # code is generated automatically
                    transaction.on_commit(lambda p=obj, c=config: _send_registration_email(p, "Student", c))
                    return render(request, "registration_success.html", {"person": obj, "category": "Student", "config": config})

                raise ValueError("Please choose Student or Teacher.")
        except (ValueError, json.JSONDecodeError) as exc:
            messages.error(request, str(exc))
    return render(request, "register.html", {"schools": schools, "faculties": faculties, "config": config})


def _distance(a, b):
    if not isinstance(a, list) or not isinstance(b, list) or len(a) != len(b):
        return 999.0
    return math.sqrt(sum((float(x) - float(y)) ** 2 for x, y in zip(a, b)))


@login_required
def face_match(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "POST required."}, status=405)
    config = TournamentConfig.current()
    if not config.face_checkin_enabled:
        return JsonResponse({"ok": False, "error": "Face check-in is currently disabled."}, status=403)
    try:
        incoming = json.loads(request.body.decode("utf-8")).get("descriptor", [])
    except (ValueError, json.JSONDecodeError):
        return JsonResponse({"ok": False, "error": "Invalid face data."}, status=400)
    if len(incoming) != 128:
        return JsonResponse({"ok": False, "error": "A valid face descriptor is required."}, status=400)

    best = None
    for faculty in Faculty.objects.select_related("school").exclude(face_descriptor__isnull=True):
        distance = _distance(incoming, faculty.face_descriptor)
        if best is None or distance < best[0]:
            best = (distance, "faculty", faculty)
    for player in Player.objects.select_related("school", "faculty_coordinator").exclude(face_descriptor__isnull=True):
        distance = _distance(incoming, player.face_descriptor)
        if best is None or distance < best[0]:
            best = (distance, "player", player)

    if best is None or best[0] > 0.52:
        return JsonResponse({"ok": False, "error": "No registered participant matched this face.", "distance": round(best[0], 3) if best else None})
    distance, kind, person = best
    if kind == "faculty":
        data = {
            "id": person.id, "type": "faculty", "name": person.name, "school": person.school.name,
            "code": person.faculty_code, "gender": person.gender, "email": person.email,
            "phone": person.phone, "present": person.present,
        }
    else:
        data = {
            "id": person.id, "type": "player", "name": person.name, "school": person.school.name,
            "code": person.player_code, "standard": person.standard, "division": person.division,
            "gender": person.gender, "faculty": person.faculty_coordinator.name, "email": person.email,
            "phone": person.phone, "present": person.present,
        }
    return JsonResponse({"ok": True, "distance": round(distance, 3), "person": data, "player": data if kind == "player" else None})


@login_required
def confirm_arrival(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "POST required."}, status=405)
    config = TournamentConfig.current()
    if not config.face_checkin_enabled:
        return JsonResponse({"ok": False, "error": "Face check-in is disabled."}, status=403)
    kind = request.POST.get("type", "player")
    person_id = request.POST.get("person_id") or request.POST.get("player_id")
    now = timezone.now()
    if kind == "faculty":
        person = get_object_or_404(Faculty, pk=person_id)
        person.present = True
        person.arrived_at = now
        person.save(update_fields=["present", "arrived_at"])
        FacultyAttendance.objects.create(faculty=person, confirmed=True)
    else:
        person = get_object_or_404(Player, pk=person_id)
        person.present = True
        person.arrived_at = now
        person.save(update_fields=["present", "arrived_at"])
        Attendance.objects.create(player=person, confirmed=True)
    return JsonResponse({"ok": True, "message": f"{person.name} from {person.school.name} has arrived."})


@login_required
def dashboard(request):
    config = TournamentConfig.current()
    return render(request, "dashboard.html", {
        "config": config,
        "player_count": Player.objects.count(),
        "faculty_count": Faculty.objects.count(),
        "school_count": School.objects.count(),
        "game_count": Game.objects.count(),
        "score_count": Score.objects.count(),
        "present_count": Player.objects.filter(present=True).count(),
    })


@login_required
def school_dashboard(request):
    schools = School.objects.all().prefetch_related("faculty", "players__faculty_coordinator", "players__scores")
    selected_id = request.GET.get("school")
    selected_school = None
    if selected_id:
        selected_school = get_object_or_404(
            School.objects.prefetch_related("faculty", "players__faculty_coordinator", "players__scores"),
            pk=selected_id,
        )
    return render(request, "school_dashboard.html", {
        "schools": schools,
        "selected_school": selected_school,
        "config": TournamentConfig.current(),
    })


@login_required
def tournament_settings(request):
    config = TournamentConfig.current()
    if request.method == "POST":
        config.name = request.POST.get("name", config.name).strip()
        config.tagline = request.POST.get("tagline", config.tagline).strip()
        config.description = request.POST.get("description", config.description).strip()
        config.venue = request.POST.get("venue", config.venue).strip()
        config.organizer = request.POST.get("organizer", config.organizer).strip()
        config.contact_phone = request.POST.get("contact_phone", "").strip()
        config.contact_email = request.POST.get("contact_email", "").strip()
        config.email_sender = request.POST.get("email_sender", config.email_sender).strip()
        config.date = request.POST.get("date") or None
        for field in ["schools_count", "students_count", "missions_count", "days_count"]:
            try:
                setattr(config, field, max(0, int(request.POST.get(field) or 0)))
            except ValueError:
                pass
        config.registration_open = request.POST.get("registration_open") == "on"
        config.scoreboard_public = request.POST.get("scoreboard_public") == "on"
        config.face_checkin_enabled = request.POST.get("face_checkin_enabled") == "on"
        if request.FILES.get("poster"):
            config.poster = request.FILES["poster"]
        if request.FILES.get("trophy"):
            config.trophy = request.FILES["trophy"]
        config.save()
        messages.success(request, "Tournament settings updated successfully.")
        return redirect("tournament_settings")
    return render(request, "tournament_settings.html", {"config": config})


@login_required
def faculties(request):
    return render(request, "manage/faculties.html", {"faculties": Faculty.objects.select_related("school")})


@login_required
def faculty_add(request):
    if request.method == "POST":
        school = get_object_or_404(School, pk=request.POST["school"])
        obj = Faculty(name=request.POST["name"].strip(), school=school, gender=request.POST.get("gender", ""), phone=request.POST["phone"], email=request.POST.get("email", ""), registered_publicly=False)
        obj.save()  # automatic code
        return redirect("faculties")
    return render(request, "manage/faculty_form.html", {"schools": School.objects.all()})


@login_required
def faculty_edit(request, pk):
    obj = get_object_or_404(Faculty, pk=pk)
    if request.method == "POST":
        obj.name = request.POST["name"].strip(); obj.school_id = request.POST["school"]; obj.gender = request.POST.get("gender", ""); obj.phone = request.POST["phone"]; obj.email = request.POST.get("email", ""); obj.save()
        return redirect("faculties")
    return render(request, "manage/faculty_form.html", {"object": obj, "schools": School.objects.all()})


@login_required
def faculty_delete(request, pk):
    get_object_or_404(Faculty, pk=pk).delete(); return redirect("faculties")


@login_required
def players(request):
    return render(request, "manage/players.html", {"players": Player.objects.select_related("school", "faculty_coordinator").all(), "config": TournamentConfig.current()})


@login_required
def player_add(request):
    return _player_form(request)


@login_required
def player_edit(request, pk):
    return _player_form(request, get_object_or_404(Player, pk=pk))


def _player_form(request, obj=None):
    if request.method == "POST":
        data = request.POST
        obj = obj or Player()
        obj.name = data["name"].strip(); obj.school_id = data["school"]; obj.standard = data.get("standard", ""); obj.division = data.get("division", ""); obj.date_of_birth = _parse_date(data.get("date_of_birth", "")); obj.age = _age_from_dob(obj.date_of_birth) or (int(data["age"]) if data.get("age", "").isdigit() else None); obj.enrollment_no = data.get("enrollment_no", ""); obj.gender = data["gender"]; obj.phone = data.get("phone", ""); obj.email = data.get("email", ""); obj.aadhaar_number = data.get("aadhaar_number", ""); obj.faculty_coordinator_id = data["faculty_coordinator"]
        if data.get("photo_data"): _save_data_url(obj, "photo", data.get("photo_data"), "player")
        if data.get("face_descriptor"): obj.face_descriptor = json.loads(data.get("face_descriptor"))
        obj.save()  # automatic code for new players
        return redirect("players")
    return render(request, "manage/form.html", {"title": "Player", "object": obj, "schools": School.objects.all(), "faculties": Faculty.objects.select_related("school").all(), "type": "players"})


@login_required
def player_delete(request, pk):
    get_object_or_404(Player, pk=pk).delete(); return redirect("players")


@login_required
def schools(request):
    return render(request, "manage/list.html", {"title": "Schools", "items": School.objects.all(), "type": "schools"})


@login_required
def school_add(request): return _school_form(request)


@login_required
def school_edit(request, pk): return _school_form(request, get_object_or_404(School, pk=pk))


def _school_form(request, obj=None):
    if request.method == "POST":
        obj = obj or School(); obj.name = request.POST["name"].strip(); obj.save()  # automatic school code
        return redirect("schools")
    return render(request, "manage/simple_form.html", {"title": "School", "object": obj, "type": "schools"})


@login_required
def school_delete(request, pk): get_object_or_404(School, pk=pk).delete(); return redirect("schools")


@login_required
def games(request): return render(request, "manage/list.html", {"title": "Games", "items": Game.objects.all(), "type": "games"})
@login_required
def game_add(request): return _game_form(request)
@login_required
def game_edit(request, pk): return _game_form(request, get_object_or_404(Game, pk=pk))

def _game_form(request, obj=None):
    if request.method == "POST":
        obj = obj or Game(); obj.name = request.POST["name"]; obj.description = request.POST.get("description", ""); obj.active = request.POST.get("active") == "on"; obj.save(); return redirect("games")
    return render(request, "manage/simple_form.html", {"title": "Game", "object": obj, "type": "games"})
@login_required
def game_delete(request, pk): get_object_or_404(Game, pk=pk).delete(); return redirect("games")


@login_required
def scores(request): return render(request, "manage/list.html", {"title": "Scores", "items": Score.objects.select_related("player", "game"), "type": "scores"})
@login_required
def score_add(request): return _score_form(request)
@login_required
def score_edit(request, pk): return _score_form(request, get_object_or_404(Score, pk=pk))

def _score_form(request, obj=None):
    if request.method == "POST":
        obj = obj or Score(); obj.player_id = request.POST["player"]; obj.game_id = request.POST["game"]; obj.points = int(request.POST["points"]); obj.remarks = request.POST.get("remarks", ""); obj.save(); return redirect("scores")
    return render(request, "manage/simple_form.html", {"title": "Score", "object": obj, "players": Player.objects.select_related("school"), "games": Game.objects.all(), "type": "scores"})
@login_required
def score_delete(request, pk): get_object_or_404(Score, pk=pk).delete(); return redirect("scores")


def admin_login(request):
    if request.user.is_authenticated: return redirect("dashboard")
    if request.method == "POST":
        user = authenticate(request, username=request.POST.get("username"), password=request.POST.get("password"))
        if user is not None: login(request, user); return redirect("dashboard")
        messages.error(request, "Invalid username or password.")
    return render(request, "admin_login.html")


def admin_logout(request): logout(request); return redirect("home")

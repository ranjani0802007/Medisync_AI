import json
import re
from functools import wraps

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .models import KV, Case, Doctor

COUNCIL_RE = re.compile(r"^[A-Za-z]{0,5}[-\s]?\d{4,8}$")


def body(r):
    try:
        return json.loads(r.body or "{}")
    except ValueError:
        return {}


def err(msg, status=400):
    return JsonResponse({"error": msg}, status=status)


def num(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def user_json(u):
    if not u.is_authenticated:
        return None
    if u.is_staff:
        return {"n": "Admin Console", "role": "admin"}
    return {"n": u.first_name or u.username, "role": "doctor", "sp": u.last_name or "Internal Medicine"}


def need_auth(f):
    @wraps(f)
    def w(r, *a, **k):
        if not r.user.is_authenticated:
            return err("Please sign in.", 401)
        return f(r, *a, **k)
    return w


@require_GET
def me(r):
    return JsonResponse({"user": user_json(r.user)})


@csrf_exempt
@require_POST
def register(r):
    d = body(r)
    name = d.get("name", "").strip()
    email = d.get("email", "").strip().lower()
    council = d.get("council", "").strip()
    sp = d.get("sp") or "Internal Medicine"
    if not name or not email or len(d.get("password", "")) < 6:
        return err("Enter your name, email and a password of at least 6 characters.")
    if not COUNCIL_RE.match(council):
        return err("Enter a valid Medical Council number, for example TN-482913.")
    if User.objects.filter(username=email).exists():
        return err("This email is already registered.")
    if not name.startswith("Dr"):
        name = "Dr. " + name
    u = User.objects.create_user(email, email, d["password"], first_name=name, last_name=sp)
    Doctor.objects.update_or_create(name=name, defaults=dict(
        user=u, specialization=sp, experience=num(d.get("ex")),
        qualification="Council " + council, council_no=council, rating="New"))
    login(r, u)
    return JsonResponse({"user": user_json(u)})


@csrf_exempt
@require_POST
def login_view(r):
    d = body(r)
    u = authenticate(r, username=d.get("email", "").strip().lower(), password=d.get("password", ""))
    if not u:
        return err("Wrong email or password.", 401)
    login(r, u)
    return JsonResponse({"user": user_json(u)})


@csrf_exempt
@require_POST
def logout_view(r):
    logout(r)
    return JsonResponse({"ok": True})


@csrf_exempt
@require_POST
def demo(r):
    if not settings.DEMO_MODE:
        return err("Demo sign-in is disabled.", 403)
    d = body(r)
    role = d.get("role")
    if role == "admin":
        name, sp, staff = "Admin Console", "", True
    elif role == "specialist":
        name, sp, staff = d.get("name") or "Dr. Demo", d.get("sp") or "Internal Medicine", False
    else:
        name, sp, staff = "Dr. Priya Menon", "Internal Medicine", False
    email = re.sub(r"[^a-z0-9]+", ".", name.lower()).strip(".") + "@medisync.test"
    u, created = User.objects.get_or_create(
        username=email, defaults=dict(first_name=name, last_name=sp, is_staff=staff))
    if created:
        u.set_unusable_password()
        u.save()
    login(r, u, backend="django.contrib.auth.backends.ModelBackend")
    return JsonResponse({"user": user_json(u)})


def kv(key, default):
    row = KV.objects.filter(key=key).first()
    return row.value if row else default


@require_GET
@need_auth
def state(r):
    cases = [c.data for c in Case.objects.order_by("pos")]
    docs = []
    for x in Doctor.objects.order_by("id"):
        try:
            rt = float(x.rating)
        except ValueError:
            rt = "New"
        docs.append({"n": x.name, "sp": x.specialization, "ex": x.experience, "q": x.qualification,
                     "rt": rt, "rc": x.review_count, "tags": x.tags, "rv": x.reviews})
    return JsonResponse({"empty": not cases and not docs, "cases": cases, "docs": docs,
                         "pl": kv("pl", []), "al": kv("al", []), "n": kv("n", 2001)})


@csrf_exempt
@require_POST
@need_auth
def sync(r):
    d = body(r)
    with transaction.atomic():
        for i, c in enumerate(d.get("cases", [])):
            Case.objects.update_or_create(case_id=c["id"], defaults=dict(
                owner=c.get("owner", ""), status=c.get("status", ""), risk=c.get("risk", ""), pos=i, data=c))
        for x in d.get("docs", []):
            Doctor.objects.update_or_create(name=x["n"], defaults=dict(
                specialization=x.get("sp", ""), experience=num(x.get("ex")), qualification=x.get("q", ""),
                rating=str(x.get("rt", "New")), review_count=num(x.get("rc")),
                tags=x.get("tags") or [], reviews=x.get("rv") or []))
        for k in ("pl", "al"):
            KV.objects.update_or_create(key=k, defaults={"value": d.get(k, [])})
        KV.objects.update_or_create(key="n", defaults={"value": d.get("n", 2001)})
    return JsonResponse({"ok": True})

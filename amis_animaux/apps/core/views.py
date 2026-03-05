from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count
from django.core.paginator import Paginator
from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse

from apps.animals.models import Animal
from apps.matches.models import Match
from apps.messaging.models import Conversation, Message
from .forms import ProfileForm, AnimalForm


def home(request):
    popular = (
        User.objects.select_related("profile")
        .prefetch_related(Prefetch("animals", queryset=Animal.objects.order_by("-created_at")))
        .filter(animals__isnull=False)
        .distinct()
        .order_by("-date_joined")[:12]
    )
    return render(request, "core/home.html", {"popular": popular})


def profiles_list(request):
    q = (request.GET.get("q") or "").strip()
    location = (request.GET.get("location") or "").strip()
    species = (request.GET.get("species") or "").strip()
    age_min = (request.GET.get("age_min") or "").strip()
    age_max = (request.GET.get("age_max") or "").strip()

    qs = (
        User.objects.select_related("profile")
        .prefetch_related(Prefetch("animals", queryset=Animal.objects.order_by("-created_at")))
        .filter(animals__isnull=False)
        .distinct()
        .order_by("-date_joined")
    )

    if q:
        qs = qs.filter(Q(username__icontains=q) | Q(profile__bio__icontains=q))
    if location:
        qs = qs.filter(profile__location__icontains=location)
    if species:
        qs = qs.filter(animals__species__iexact=species).distinct()

    if age_min.isdigit():
        qs = qs.filter(profile__age__gte=int(age_min))

    if age_max.isdigit():
        qs = qs.filter(profile__age__lte=int(age_max))

    paginator = Paginator(qs, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    # 🔥 Remplace sent_match_ids par un dict des statuts

    sent_matches = {}

    if request.user.is_authenticated:
        matches = Match.objects.filter(sender=request.user)
        sent_matches = {
            m.receiver_id: m.status
            for m in matches
        }

    return render(
        request,
        "core/profiles_list.html",
        {
            "page_obj": page_obj,
            "sent_matches": sent_matches,  # 🔥 important
            "q": q,
            "location": location,
            "species": species,
            "age_min": age_min,
            "age_max": age_max,
        },
    )

def profile_detail(request, user_id):
    u = get_object_or_404(
        User.objects.select_related("profile").prefetch_related("animals"),
        id=user_id
    )

    existing_match = None
    if request.user.is_authenticated and request.user.id != u.id:
        existing_match = Match.objects.filter(sender=request.user, receiver=u).order_by("-created_at").first()

    return render(request, "core/profile_detail.html", {"u": u, "existing_match": existing_match})


@login_required
def send_match(request, user_id):
    if request.method != "POST":
        return redirect("profile_detail", user_id=user_id)

    receiver = get_object_or_404(User, id=user_id)

    if receiver.id == request.user.id:
        messages.error(request, "Tu ne peux pas te matcher toi-même.")
        return redirect("profile_detail", user_id=user_id)

    if Match.objects.filter(sender=request.user, receiver=receiver).exists():
        messages.info(request, "Demande déjà envoyée.")
        return redirect("profile_detail", user_id=user_id)

    Match.objects.create(sender=request.user, receiver=receiver, status="pending")
    messages.success(request, "Demande envoyée ❤️")
    return redirect("profile_detail", user_id=user_id)


@login_required
def messages_home(request):
    # Liste des conversations de l’utilisateur
    convos = Conversation.objects.filter(participants=request.user).order_by("-created_at")
    # Si une conversation existe, on ouvre la plus récente
    if convos.exists():
        return redirect("messages_conversation", conversation_id=convos.first().id)
    return render(request, "core/messages_empty.html")


@login_required
def start_conversation(request, user_id):
    """
    Crée (ou récupère) une conversation 1-1 entre request.user et user_id
    puis redirige vers /messages/<conversation_id>/
    """
    other = get_object_or_404(User, id=user_id)
    if other.id == request.user.id:
        messages.error(request, "Tu ne peux pas démarrer une conversation avec toi-même.")
        return redirect("profiles_list")

    # Chercher une conversation à 2 participants existante
    existing = (
        Conversation.objects
        .filter(participants=request.user)
        .filter(participants=other)
        .annotate(pcount=Count("participants"))
        .filter(pcount=2)
        .first()
    )

    if existing:
        return redirect("messages_conversation", conversation_id=existing.id)

    convo = Conversation.objects.create()
    convo.participants.add(request.user, other)
    return redirect("messages_conversation", conversation_id=convo.id)


@login_required
def messages_conversation(request, conversation_id):
    # Vérifier que l’utilisateur fait partie de la conversation
    convo = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    convos = Conversation.objects.filter(participants=request.user).order_by("-created_at")

    # Chargement messages
    msgs = Message.objects.filter(conversation=convo).select_related("sender").order_by("timestamp")

    # Envoi message
    if request.method == "POST":
        content = (request.POST.get("content") or "").strip()
        if content:
            Message.objects.create(conversation=convo, sender=request.user, content=content)
            return redirect("messages_conversation", conversation_id=convo.id)
        messages.error(request, "Message vide.")

    # Participants (pour afficher le nom de l'autre)
    participants = list(convo.participants.all())
    other = next((u for u in participants if u.id != request.user.id), None)

    return render(
        request,
        "core/messages.html",
        {
            "convos": convos,
            "convo": convo,
            "other": other,
            "msgs": msgs,
        },
    )


@login_required
def match_screen(request, match_id):
    """
    Écran “C’est un match !”
    Simple: accessible si tu es sender ou receiver.
    Recommandé: n’afficher que si status == accepted (sinon message)
    """
    m = get_object_or_404(Match, id=match_id)

    if request.user not in (m.sender, m.receiver):
        messages.error(request, "Accès refusé.")
        return redirect("home")

    if m.status != "accepted":
        messages.info(request, "Ce match n’est pas encore accepté.")
        return redirect("profiles_list")

    # on identifie les deux personnes
    u1, u2 = m.sender, m.receiver

    return render(request, "core/match.html", {"m": m, "u1": u1, "u2": u2})


def register_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        email = (request.POST.get("email") or "").strip()
        password1 = request.POST.get("password1") or ""
        password2 = request.POST.get("password2") or ""

        # validations simples
        if not username:
            messages.error(request, "Le username est obligatoire.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "Ce username est déjà pris.")
        elif password1 != password2:
            messages.error(request, "Les mots de passe ne correspondent pas.")
        elif len(password1) < 6:
            messages.error(request, "Le mot de passe doit faire au moins 6 caractères.")
        else:
            user = User.objects.create_user(username=username, email=email, password=password1)
            login(request, user)
            messages.success(request, "Compte créé ✅ Bienvenue !")
            return redirect("profiles_list")

    return render(request, "core/register.html")


def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = request.POST.get("password") or ""

        user = authenticate(request, username=username, password=password)
        if user is None:
            messages.error(request, "Identifiants invalides.")
        else:
            login(request, user)
            messages.success(request, "Connexion réussie ✅")
            next_url = request.GET.get("next")
            return redirect(next_url or "profiles_list")

    return render(request, "core/login.html")


def logout_view(request):
    logout(request)
    messages.info(request, "Déconnecté.")
    return redirect("home")


@login_required
def me_profile(request):
    profile = request.user.profile  # grâce au signal

    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil mis à jour ✅")
            return redirect("me_profile")
        messages.error(request, "Corrige les erreurs du formulaire.")
    else:
        form = ProfileForm(instance=profile)

    animals = Animal.objects.filter(owner=request.user).order_by("-created_at")

    return render(
        request,
        "core/me_profile.html",
        {"form": form, "animals": animals},
    )


@login_required
def me_animal_add(request):
    if request.method == "POST":
        form = AnimalForm(request.POST)
        if form.is_valid():
            animal = form.save(commit=False)
            animal.owner = request.user
            animal.save()
            messages.success(request, "Animal ajouté ✅")
            return redirect("me_profile")
        messages.error(request, "Corrige les erreurs du formulaire.")
    else:
        form = AnimalForm()

    return render(request, "core/me_animal_add.html", {"form": form})


@login_required
def me_animal_edit(request, animal_id):
    animal = get_object_or_404(Animal, id=animal_id, owner=request.user)

    if request.method == "POST":
        form = AnimalForm(request.POST, instance=animal)
        if form.is_valid():
            form.save()
            messages.success(request, "Animal modifié ✅")
            return redirect("me_profile")
        messages.error(request, "Corrige les erreurs.")
    else:
        form = AnimalForm(instance=animal)

    return render(request, "core/me_animal_edit.html", {"form": form})


@login_required
def me_animal_delete(request, animal_id):
    animal = get_object_or_404(Animal, id=animal_id, owner=request.user)

    if request.method == "POST":
        animal.delete()
        messages.success(request, "Animal supprimé 🗑️")
        return redirect("me_profile")

    return render(request, "core/me_animal_delete.html", {"animal": animal})

@login_required
def matches_page(request):
    user = request.user
    received = Match.objects.filter(receiver=user).order_by("-created_at")
    sent = Match.objects.filter(sender=user).order_by("-created_at")

    return render(
        request,
        "core/matches.html",
        {"received": received, "sent": sent},
    )


@login_required
def match_update_status(request, match_id):
    if request.method != "POST":
        return redirect("matches_page")

    m = get_object_or_404(Match, id=match_id)

    # Seul le receiver peut accepter/refuser
    if m.receiver != request.user:
        messages.error(request, "Tu n’as pas le droit de modifier ce match.")
        return redirect("matches_page")

    action = request.POST.get("action")

    if m.status != "pending":
        messages.info(request, "Ce match n’est plus en attente.")
        return redirect("matches_page")

    if action == "accept":
        m.status = "accepted"
        m.save()
        messages.success(request, "Match accepté ❤️")
        # bonus simple: redirige vers l’écran match
        return redirect("match_screen", match_id=m.id)

    if action == "reject":
        m.status = "rejected"
        m.save()
        messages.info(request, "Match refusé.")
        return redirect("matches_page")

    messages.error(request, "Action invalide.")
    return redirect("matches_page")

@login_required
def ajax_send_match(request, user_id):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "POST required"}, status=405)

    receiver = get_object_or_404(User, id=user_id)

    if receiver.id == request.user.id:
        return JsonResponse({"ok": False, "error": "self match"}, status=400)

    m = Match.objects.filter(sender=request.user, receiver=receiver).first()
    if m:
        return JsonResponse({"ok": True, "status": m.status, "already": True})

    Match.objects.create(sender=request.user, receiver=receiver, status="pending")
    return JsonResponse({"ok": True, "status": "pending", "already": False})

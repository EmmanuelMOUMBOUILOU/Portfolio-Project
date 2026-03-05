from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

from apps.animals.models import Animal
from apps.users.models import Profile


User = get_user_model()


DEMO_USERS = [
    {"username": "sophie", "email": "sophie@test.com", "location": "Paris", "bio": "Balades, parcs et cafés. Mon chien adore jouer 🐾"},
    {"username": "thomas", "email": "thomas@test.com", "location": "Lyon", "bio": "Sport & nature. On cherche des copains pour courir !"},
    {"username": "julie", "email": "julie@test.com", "location": "Marseille", "bio": "Team soleil ☀️ Plage, balades et animaux heureux."},
    {"username": "amine", "email": "amine@test.com", "location": "Toulouse", "bio": "J’aime les chiens, les randos et les rencontres simples."},
    {"username": "clara", "email": "clara@test.com", "location": "Nice", "bio": "Chats + chill + discussions. On se retrouve au parc ?"},
    {"username": "kevin", "email": "kevin@test.com", "location": "Bordeaux", "bio": "Sorties, balades, bonne vibe. Mon compagnon est très sociable."},
]

DEMO_ANIMALS = [
    # owner_username, name, species, age
    ("sophie", "Felix", "Cat", 2),
    ("sophie", "Rocky", "Dog", 4),
    ("thomas", "Max", "Dog", 3),
    ("thomas", "Nala", "Cat", 1),
    ("julie", "Luna", "Dog", 2),
    ("julie", "Milo", "Cat", 3),
    ("amine", "Rex", "Dog", 5),
    ("amine", "Tina", "Cat", 2),
    ("clara", "Mimi", "Cat", 4),
    ("clara", "Paco", "Dog", 1),
    ("kevin", "Simba", "Cat", 2),
    ("kevin", "Buddy", "Dog", 6),
]


class Command(BaseCommand):
    help = "Seed demo users/profiles/animals for Amis des Animaux."

    def add_arguments(self, parser):
        parser.add_argument("--password", type=str, default="12345678", help="Password for all demo users")
        parser.add_argument("--reset", action="store_true", help="Delete existing demo users/animals first")

    @transaction.atomic
    def handle(self, *args, **options):
        password = options["password"]
        reset = options["reset"]

        if reset:
            demo_usernames = [u["username"] for u in DEMO_USERS]
            self.stdout.write(self.style.WARNING("Reset: deleting demo animals and users..."))

            Animal.objects.filter(owner__username__in=demo_usernames).delete()
            Profile.objects.filter(user__username__in=demo_usernames).delete()
            User.objects.filter(username__in=demo_usernames).delete()

        created_users = 0
        created_animals = 0

        # 1) Create users (+ profile via signal)
        for u in DEMO_USERS:
            user, created = User.objects.get_or_create(
                username=u["username"],
                defaults={"email": u["email"]},
            )
            if created:
                user.set_password(password)
                user.save()
                created_users += 1

            # Ensure profile exists (signal should do it, but safe)
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.location = u["location"]
            profile.bio = u["bio"]
            profile.save()

        # 2) Create animals
        for owner_username, name, species, age in DEMO_ANIMALS:
            owner = User.objects.get(username=owner_username)
            animal, created = Animal.objects.get_or_create(
                owner=owner,
                name=name,
                defaults={"species": species, "age": age},
            )
            if created:
                created_animals += 1

        self.stdout.write(self.style.SUCCESS(f"Done. Users created: {created_users}, Animals created: {created_animals}"))
        self.stdout.write(self.style.SUCCESS(f"All demo users password: {password}"))

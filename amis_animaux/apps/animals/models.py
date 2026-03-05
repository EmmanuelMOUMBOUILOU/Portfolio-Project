from django.conf import settings
from django.db import models


class Animal(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="animals"
    )
    name = models.CharField(max_length=100)
    species = models.CharField(max_length=50)
    age = models.PositiveIntegerField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.species})"
    
class Meta:
    constraints = [
        models.UniqueConstraint(fields=["owner", "name"], name="unique_owner_animal_name")
    ]

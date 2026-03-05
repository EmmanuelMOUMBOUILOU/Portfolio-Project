from django.contrib import admin
from .models import Animal


@admin.register(Animal)
class AnimalAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "species", "age", "owner", "created_at")
    list_filter = ("species",)
    search_fields = ("name", "owner__username")

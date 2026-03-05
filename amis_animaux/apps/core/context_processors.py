from apps.matches.models import Match

def matches_badge(request):
    if request.user.is_authenticated:
        count = Match.objects.filter(
            receiver=request.user,
            status="pending"
        ).count()
        return {"matches_badge_count": count}
    return {"matches_badge_count": 0}

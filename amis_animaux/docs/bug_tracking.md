

# Bug Tracking – Amis des Animaux

## Overview

During the development of the **Amis des Animaux** application, several bugs and technical issues were encountered and resolved.
This document lists the main bugs discovered during development, their causes, and how they were fixed.

The goal of this tracking is to ensure transparency in the development process and demonstrate debugging and problem-solving skills.

---

# Bug 1 – Profile not automatically created

## Description

When a new user registered, the **Profile model was not automatically created**, which caused errors when accessing `request.user.profile`.

Example error:

```
AttributeError: 'User' object has no attribute 'profile'
```

## Cause

The signal responsible for creating the profile after user creation was not properly connected.

## Solution

A Django signal (`post_save`) was implemented in `users/signals.py`.

```
@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
```

The signal was then imported inside `apps.py` to ensure it is loaded when Django starts.

Result: Profile is automatically created for each new user.

Status: FIXED

---

# Bug 2 – Avatar images not displayed

## Description

Uploaded profile avatars were not appearing on the website.

## Cause

The Django **MEDIA configuration was missing**, preventing uploaded images from being served in development.

## Solution

Added media configuration in `settings.py`:

```
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
```

And added static serving in `urls.py`:

```
from django.conf import settings
from django.conf.urls.static import static

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

Status: FIXED

---

# Bug 3 – Users could edit animals that were not theirs

## Description

Initially, the animal edit view allowed any authenticated user to modify any animal.

## Cause

The query did not restrict the animal to the logged-in user.

## Solution

The query was secured using:

```
get_object_or_404(Animal, id=animal_id, owner=request.user)
```

This ensures only the owner can edit or delete their animal.

Status: FIXED

---

# Bug 4 – Duplicate match requests

## Description

Users could send multiple match requests to the same user.

## Cause

The backend did not check if a match already existed before creating a new one.

## Solution

Added a verification before creating a match:

```
existing = Match.objects.filter(sender=request.user, receiver=receiver).first()

if existing:
    return JsonResponse({"ok": True, "already": True})
```

Status: FIXED

---

# Bug 5 – Match button not updating dynamically

## Description

The match button on the profiles page required a page refresh to reflect the new status.

## Cause

The initial implementation used a standard form submission.

## Solution

Implemented AJAX using JavaScript fetch API.

```
fetch(`/ajax/match/${userId}/`, {
  method: "POST",
  headers: { "X-CSRFToken": csrftoken }
})
```

The UI now updates instantly without reloading the page.

Status: FIXED

---

# Bug 6 – Missing CSRF token in AJAX requests

## Description

AJAX match requests initially failed with a CSRF verification error.

Error example:

```
403 Forbidden – CSRF verification failed
```

## Cause

Django requires CSRF protection for POST requests.

## Solution

Added CSRF token retrieval from cookies and passed it in request headers.

```
headers: {
  "X-CSRFToken": csrftoken
}
```

Status: FIXED

---

# Bug 7 – Matches badge not updating

## Description

The navigation bar did not display the number of pending match requests.

## Cause

The data was not available globally in templates.

## Solution

Implemented a Django **context processor** that counts pending matches.

```
Match.objects.filter(receiver=request.user, status="pending").count()
```

The result is injected into every template.

Status: FIXED

---

# Bug 8 – Profile filter errors

## Description

Filtering profiles by age and species sometimes returned incorrect results.

## Cause

Incorrect query filtering combining animal attributes and profile attributes.

## Solution

Adjusted ORM queries to properly filter:

* user profile fields
* animal fields

using `.distinct()` to avoid duplicate results.

Status: FIXED

---

# Conclusion

All major issues encountered during development were resolved successfully.
The debugging process improved the stability and security of the application.

The application now functions correctly and provides a stable MVP for demonstration and evaluation.

---
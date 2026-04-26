from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_PLAYER = 'player'
    ROLE_COACH = 'coach'
    ROLE_MANAGER = 'manager'
    ROLE_CHOICES = [
        (ROLE_PLAYER, 'Player'),
        (ROLE_COACH, 'Coach'),
        (ROLE_MANAGER, 'Manager'),
    ]

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=ROLE_PLAYER)
    aub_id = models.CharField(max_length=20, blank=True)
    avatar_initials = models.CharField(max_length=3, blank=True)

    def is_coach(self):
        return self.role == self.ROLE_COACH

    def is_manager(self):
        return self.role == self.ROLE_MANAGER

    def is_staff_role(self):
        """True for coach or manager — anyone with elevated access."""
        return self.role in {self.ROLE_COACH, self.ROLE_MANAGER}

    def get_initials(self):
        parts = self.get_full_name().split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[-1][0]).upper()
        return self.username[:2].upper()

    def save(self, *args, **kwargs):
        self.avatar_initials = self.get_initials()
        super().save(*args, **kwargs)

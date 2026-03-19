from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = [
        ('manager', 'Gestor'),
        ('participant', 'Participante'),
        ('auditor', 'Auditor'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='participant')
    participant = models.ForeignKey(
        'participants.Participant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
    )
    must_change_password = models.BooleanField(default=False)

    @property
    def is_manager(self):
        return self.role == 'manager' or self.is_superuser

    @property
    def is_auditor(self):
        return self.role == 'auditor'

    @property
    def is_participant_user(self):
        return self.role == 'participant'

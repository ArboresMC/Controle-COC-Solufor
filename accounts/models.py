from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('manager', 'Gestor'),
        ('participant', 'Participante'),
        ('auditor', 'Auditor'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='participant')
    organization = models.ForeignKey(
        'participants.Organization',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
    )
    participant = models.ForeignKey(
        'participants.Participant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
    )
    must_change_password = models.BooleanField(default=False)

    def clean(self):
        super().clean()
        if self.participant_id and self.organization_id and self.participant.organization_id != self.organization_id:
            raise ValidationError('O usuário não pode apontar para um participante de outra organização.')

    def save(self, *args, **kwargs):
        if self.participant_id and self.participant and self.participant.organization_id:
            self.organization_id = self.participant.organization_id
        super().save(*args, **kwargs)

    @property
    def is_manager(self):
        return self.role == 'manager' or self.is_superuser

    @property
    def is_auditor(self):
        return self.role == 'auditor'

    @property
    def is_participant_user(self):
        return self.role == 'participant'

    @property
    def current_organization(self):
        if self.participant_id and self.participant:
            return self.participant.organization
        return self.organization

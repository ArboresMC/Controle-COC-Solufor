from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.functional import cached_property


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
    # Acesso adicional a múltiplos participantes — usado APENAS no módulo de
    # Manejo Florestal, para o caso de uma empresa "mini-gestora" que opera o
    # sistema em nome de outros participantes do grupo. Não afeta o COC, que
    # continua restrito a `participant` (FK acima).
    participantes_manejo = models.ManyToManyField(
        'participants.Participant',
        blank=True,
        related_name='usuarios_manejo',
        verbose_name='Participantes adicionais (Manejo Florestal)',
        help_text='Permite que este usuário gerencie Manejo Florestal de mais de um participante. Não se aplica ao módulo de Cadeia de Custódia.',
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

    @cached_property
    def is_manejo_multi(self):
        """True se este usuário opera Manejo Florestal de mais de um participante
        (o "mini-gestor" descrito na decisão de produto). Não tem efeito sobre CoC.
        Usa cached_property (em vez de property) porque é consultado mais de uma
        vez por requisição (sidebar do base.html + templates de listagem do
        Manejo) — sem cache, cada acesso disparava uma nova query .exists()."""
        return self.pk is not None and self.participantes_manejo.exists()

    def manejo_participant_ids(self):
        """IDs de todos os participantes de Manejo que este usuário pode acessar:
        o participante principal (se ativo_fm) + os participantes extras do M2M."""
        ids = set(self.participantes_manejo.filter(ativo_fm=True).values_list('id', flat=True))
        if self.participant_id and getattr(self.participant, 'ativo_fm', False):
            ids.add(self.participant_id)
        return ids

    @property
    def current_organization(self):
        if self.participant_id and self.participant:
            return self.participant.organization
        return self.organization

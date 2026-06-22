from django.contrib import admin
from .models import Especie, Propriedade, InventarioEntrada, SaidaManejo

admin.site.register(Especie)
admin.site.register(Propriedade)
admin.site.register(InventarioEntrada)
admin.site.register(SaidaManejo)

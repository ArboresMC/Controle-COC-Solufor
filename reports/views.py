import json
from decimal import Decimal
from unicodedata import normalize

from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin

# IMPORTS DO SEU PROJETO (ajuste se necessário)
from .models import ImportJob
from participants.models import Participant
from .services import (
    load_workbook,
    summarize_workbook,
    preview_workbook,
    count_workbook_rows,
)


class ImportWorkbookView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        participant_id = request.POST.get('participant_id')
        participant = get_object_or_404(Participant, id=participant_id)

        uploaded_file = request.FILES.get('workbook')
        if not uploaded_file:
            messages.error(request, "Nenhum arquivo enviado.")
            return redirect('reports:import')

        workbook = load_workbook(uploaded_file, data_only=True)

        summary = summarize_workbook(workbook)
        preview = preview_workbook(workbook)

        uploaded_file.seek(0)
        total_rows = count_workbook_rows(workbook)

        # CORREÇÃO: garantir que dados são JSON serializáveis
        safe_summary = json.loads(json.dumps(summary, default=str))
        safe_preview = json.loads(json.dumps(preview, default=str))

        job = ImportJob.objects.create(
            participant=participant,
            created_by=request.user,
            workbook=uploaded_file,
            original_filename=getattr(uploaded_file, 'name', ''),
            status=ImportJob.STATUS_PENDING,
            summary=safe_summary,
            preview=safe_preview,
            error_messages=[],
            progress_current=0,
            progress_total=total_rows,
        )

        messages.success(request, "Importação iniciada com sucesso.")
        return redirect('reports:import_status', job_id=job.id)

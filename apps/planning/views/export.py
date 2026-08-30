"""Exportul Reinigungsplan (XLSX)."""

from django.core.exceptions import PermissionDenied
from django.http import FileResponse
from django.shortcuts import get_object_or_404

from ..models import Site
from ..reinigungsplan import build_workbook, filename


def reinigungsplan_view(request, pk):
    """
    Reinigungsplan-ul obiectivului, ca XLSX. Doar pentru contul care deține
    obiectivul — e un document operațional, nu o pagină publică.
    """
    account = request.account
    if account is None:
        raise PermissionDenied
    site = get_object_or_404(Site, pk=pk, account=account)
    return FileResponse(
        build_workbook(site),
        as_attachment=True,
        filename=filename(site),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

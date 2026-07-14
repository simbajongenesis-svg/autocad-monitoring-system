from django.contrib import admin
from django.urls import path, reverse
from django.template.response import TemplateResponse
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Count
from django.http import HttpResponse # Needed for CSV export
import csv # Needed for CSV export

# Custom imports for CSV generation metadata
from django.utils.timezone import now
from datetime import datetime

from .models import PanelRecord


# ==============================================================================
# PanelRecord Admin Configuration
# ==============================================================================

@admin.register(PanelRecord)
class PanelRecordAdmin(admin.ModelAdmin):
    # List display fields for the main changelist view
    #list_display = ("date", "fq_number", "jo_number", "panel_name", "customer_name", "is_archived")
    # Filters, search fields, and default ordering
    #list_filter = ("is_archived",)
    #search_fields = ("fq_number", "jo_number", "panel_name", "customer_name")
    ordering = ("-id",)
    # Custom actions (standard Django admin feature)
    actions = ["print_selected_records", "delete_selected"]
    list_per_page = 999999

    # --- 1. Custom Admin URLs ---

    def get_urls(self):
        """Adds custom URLs for archives and CSV export to the admin site."""
        urls = super().get_urls()
        custom_urls = [
            # Main Archive view (list of months)
            path("archives/", self.admin_site.admin_view(self.archive_months_view), name="archive_months"),
            # Specific month's archived records view
            path("archives/<str:month>/", self.admin_site.admin_view(self.archive_records_view), name="archive_records"),
            # Unarchive single record action
            path("unarchive/<int:record_id>/", self.admin_site.admin_view(self.unarchive_record_view), name="unarchive_record"),
            # CSV export for a specific month
            path("export/<str:month>/", self.admin_site.admin_view(self.export_archive_csv), name="export_archive_csv"),
        ]
        return custom_urls + urls

    # --- 2. Archive Views ---

    def archive_months_view(self, request):
        """Displays a list of all months that contain archived records."""
        months = (
            PanelRecord.objects.filter(is_archived=True, date__isnull=False)
            # Group by year-month (SQLite-compatible date formatting)
            .extra(select={'month': "strftime('%%Y-%%m', date)"})
            .values('month')
            .annotate(count=Count('id')) # Count records per month
            .order_by('-month') # Show most recent month first
        )
        
        context = dict(
            self.admin_site.each_context(request),
            title="Archived Months",
            # Filter out any entries where the month might be null
            months=[m for m in months if m["month"]],
        )
        return TemplateResponse(request, "monitoring/archive_months.html", context)

    def archive_records_view(self, request, month):
        """Displays all archived records for the selected month (YYYY-MM)."""
        records = PanelRecord.objects.filter(
            is_archived=True, 
            date__startswith=month # Filter by YYYY-MM prefix
        ).order_by("-date")
        
        context = dict(
            self.admin_site.each_context(request),
            title=f"Archived Records — {month}",
            month=month,
            records=records,
        )
        return TemplateResponse(request, "monitoring/archive_records.html", context)

    def unarchive_record_view(self, request, record_id):
        """Handles unarchiving a single record and redirects back to the archive list."""
        record = get_object_or_404(PanelRecord, id=record_id)
        
        record.is_archived = False
        record.save()
        
        # Get the month string for redirection
        record_month = record.date.strftime("%Y-%m")
        
        # Display a success message to the user
        self.message_user(request, f"Record {record.id}, {record.customer_name} has been unarchived! Please check it in the Panel Records.")
        
        # Redirect back to the archive view for the record's month
        return redirect("admin:archive_records", month=record_month)


    # --- 3. CSV Export Functionality ---

    def export_archive_csv(self, request, month):
        """Exports all archived records for a specific month (YYYY-MM) to a CSV file."""
        
        # Filter the records based on the requested month
        records = PanelRecord.objects.filter(is_archived=True, date__startswith=month)

        # Set up the HTTP response for CSV file download
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="Archived_Records_{month}.csv"'

        writer = csv.writer(response)

        # Write header metadata for better context/tracking
        writer.writerow([f"AutoCAD Monitoring — Archived Records ({month})"])
        writer.writerow([f"Generated on: {now().strftime('%Y-%m-%d %H:%M:%S')}"])
        writer.writerow([])  # blank line for spacing

        # Write the main table headers (column titles)
        writer.writerow([
            'ID', 'Date', 'FQ#', 'JO#', 'Panel', 'Customer', 'Quantity',
            'Received By', 'Box Type', 'Main CB', 'CB Model', 'Color',
            'Remarks', 'Archived'
        ])

        # Write data rows from the queryset
        for record in records:
            writer.writerow([
                record.id,
                record.date.strftime("%Y-%m-%d") if record.date else "", # Format date cleanly
                record.fq_number,
                record.jo_number,
                record.panel_name,
                record.customer_name,
                record.quantity,
                record.received_by,
                record.box_type,
                record.main_cb,
                record.cb_model,
                record.color,
                record.remarks or "", # Ensure remarks is not None
                "Yes" if record.is_archived else "No", # Human-readable archive status
            ])

        return response
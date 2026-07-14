from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_list_or_404, render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db.models.functions import TruncMonth
from django.db.models import Count
from .models import PanelRecord
from django.contrib.admin.views.decorators import staff_member_required
from django.template.response import TemplateResponse
from django.contrib import messages

# --- Standard Library Imports for CSV Handling ---
import csv
import json
from io import TextIOWrapper
from datetime import datetime

# ==============================================================================
# 1. API Views (JSON Response)
# ==============================================================================

def panel_records_json(request):
    """
    Returns a JSON list of all non-archived PanelRecords. 
    Can be filtered by 'month' via a GET parameter (e.g., ?month=2025-10).
    """
    # Start with records that are NOT archived (i.e., active/current records)
    records = PanelRecord.objects.filter(is_archived=False).order_by("-id")

    # Apply monthly filter if a month is specified in the query string
    month = request.GET.get("month")
    if month:
        records = records.filter(date__startswith=month)

    # Serialize the queryset data into a list of dictionaries
    data = list(records.values(
        "id", "date", "fq_number", "jo_number", "panel_name",
        "customer_name", "quantity", "received_by",
        "box_type", "main_cb", "cb_model", "color", "remarks"
    ))

    return JsonResponse({"data": data})

@csrf_exempt
@staff_member_required
def archive_record(request, record_id):
    """
    API endpoint to archive a single PanelRecord via POST request.
    Sets is_archived to True.
    """
    if request.method == "POST":
        try:
            record = PanelRecord.objects.get(id=record_id)
            record.is_archived = True
            record.save()
            return JsonResponse({"success": True})
        except PanelRecord.DoesNotExist:
            return JsonResponse({"success": False, "error": "Record not found"}, status=404)
    
    # Handle non-POST requests gracefully
    return JsonResponse({"success": False, "error": "Invalid request method"}, status=400)


# ==============================================================================
# 2. Archive Management Views (Admin Interface)
# ==============================================================================

@staff_member_required
def archive_months(request):
    """
    Displays a list of all months containing archived records.
    Aggregates the total count of records for each month.
    """
    months = (
        PanelRecord.objects.filter(is_archived=True, date__isnull=False)
        # Use .extra() for SQLite compatibility to format the date as YYYY-MM
        .extra(select={'month': "strftime('%%Y-%%m', date)"})
        .values('month')
        .annotate(count=Count('id'))
        .order_by('-month') # Show most recent month first
    )

    # Filter out any entries where the date resulted in a null/empty month string
    months = [m for m in months if m['month']]

    context = {"months": months}
    return TemplateResponse(request, "monitoring/archive_months.html", context)


@staff_member_required
def archive_records(request, month):
    """
    Displays the list of archived PanelRecords for a specific month (YYYY-MM).
    """
    records = (
        PanelRecord.objects.filter(
            is_archived=True,
            date__startswith=month # Efficiently filter records for the given YYYY-MM
        )
        .order_by("-date")
    )

    context = {
        "month": month,
        "records": records,
    }

    return TemplateResponse(request, "monitoring/archive_records.html", context)


@staff_member_required
def unarchive_record(request, record_id):
    """
    Reverses the archival status of a single record (sets is_archived to False).
    Works for both normal POST and AJAX requests.
    """
    record = get_object_or_404(PanelRecord, id=record_id)

    if request.method == "POST":
        record.is_archived = False
        record.save()
        record_month = record.date.strftime("%Y-%m")

        # ✅ Return JSON if the request is from AJAX
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": True})

        # ✅ Otherwise, redirect back (for normal form submissions)
        return redirect("monitoring:archive_records", month=record_month)

    # If it's not POST, return an error
    return JsonResponse({"success": False, "error": "Invalid request method."}, status=400)

# NOTE: This 'archive_records_view' seems to be a redundant or misplaced function
# from an Admin class and should likely be removed if it's not mapped to a URL.
# Leaving it here as it was in the original code, but noting its redundancy.
def archive_records_view(self, request, month):
    """
    [Possible Redundant Admin Method] Fetches and displays archived records by month.
    """
    records = (
        PanelRecord.objects.filter(is_archived=True)
        .extra(select={'month': "strftime('%%Y-%%m', date)"})
        .filter(month=month)
        .order_by('date')
    )

    # Note: This dictionary creation assumes it's used within a ModelAdmin context,
    # as it calls self.admin_site.each_context(request).
    context = dict(
        self.admin_site.each_context(request),
        title=f"Archived Records — {month}",
        month=month,
        records=records,
    )
    return TemplateResponse(request, "monitoring/archive_records.html", context)


# ==============================================================================
# 3. CSV Import/Backup View
# ==============================================================================

@staff_member_required
def import_backup_csv(request):
    """
    Handles CSV file uploads for bulk record import/backup restoration.
    Requires staff privileges and a file named 'csv_file' in the POST request.
    """
    if request.method == "POST" and request.FILES.get("csv_file"):
        # Wrap the uploaded file to ensure proper text decoding (UTF-8)
        csv_file = TextIOWrapper(request.FILES["csv_file"].file, encoding="utf-8")

        # --- Header Search Logic (Robustness against unnecessary rows) ---
        all_lines = [line.strip() for line in csv_file if line.strip()]
        header_index = None
        
        # Look for the line containing "Date" and "JO#" to reliably find the header
        for i, line in enumerate(all_lines):
            if "Date" in line and "JO#" in line:
                header_index = i
                break

        if header_index is None:
            messages.error(request, "❌ CSV file format invalid — could not find header row (requires 'Date' and 'JO#').")
            return redirect("monitoring:archive_months")

        # Read only from the found header row onward
        csv_data = "\n".join(all_lines[header_index:])
        reader = csv.DictReader(csv_data.splitlines())

        # --- Field Validation ---
        required_fields = [
            "ID", "Date", "FQ#", "JO#", "Panel", "Customer", "Quantity",
            "Received By", "Box Type", "Main CB", "CB Model", "Color", "Remarks", "Archived"
        ]
        missing = [f for f in required_fields if f not in reader.fieldnames]
        if missing:
            messages.error(request, f"❌ Missing columns in CSV: {', '.join(missing)}")
            return redirect("monitoring:archive_months")

        # --- Record Creation ---
        imported_count = 0
        for row in reader:
            try:
                # Determine is_archived status from various string inputs (True, 1, Yes)
                archived_value = str(row.get("Archived", "")).strip().lower() in ["true", "1", "yes"]

                PanelRecord.objects.create(
                    date=datetime.strptime(row["Date"], "%Y-%m-%d").date(), # Ensure it's a date object
                    fq_number=row["FQ#"],
                    jo_number=row["JO#"],
                    panel_name=row["Panel"],
                    customer_name=row["Customer"],
                    quantity=int(row["Quantity"]) if row["Quantity"] else 0,
                    received_by=row["Received By"],
                    box_type=row["Box Type"],
                    main_cb=row["Main CB"],
                    cb_model=row["CB Model"],
                    color=row["Color"],
                    remarks=row.get("Remarks", ""),
                    is_archived=archived_value,
                )

                imported_count += 1

            except Exception as e:
                # Log the error and skip the problematic row, then continue
                messages.error(request, f"⚠️ Error importing data on row {reader.line_num} (ID: {row.get('ID', 'N/A')}): {e}")
                continue

        messages.success(request, f"✅ Successfully imported {imported_count} records!")
        return redirect("monitoring:archive_months")

    # Handle cases where the request is not POST or no file was uploaded
    messages.error(request, "⚠️ No CSV file uploaded or invalid request method.")
    return redirect("monitoring:archive_months")

def archive_multiple_records(request):
    if request.method == "POST":
        ids = request.POST.getlist("ids[]")
        print("Received IDs:", ids)
        records = PanelRecord.objects.filter(id__in=ids)
        count = records.count()
        records.update(is_archived=True)
        return JsonResponse({"success": True, "count": count})
    return JsonResponse({"success": False})

@staff_member_required
@csrf_exempt
def export_archive_csv(request, month):
    if request.method == "POST":
        try:
            body = json.loads(request.body)
            ids = body.get("ids", [])
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON payload."}, status=400)

        queryset = PanelRecord.objects.filter(is_archived=True, date__startswith=month)
        if ids:
            queryset = queryset.filter(id__in=ids)

        response = HttpResponse(content_type="text/csv")
        filename = f"Archived_Records_{month}.csv"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        writer = csv.writer(response)

        # Header details
        writer.writerow(["AutoCAD Monitoring Archive Report"])
        writer.writerow([f"Month: {month}"])
        writer.writerow([f"Exported on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])
        writer.writerow([])

        # ✅ Add “Archived” column to header
        writer.writerow([
            "ID", "Date", "FQ#", "JO#", "Panel", "Customer", "Quantity",
            "Received By", "Box Type", "Main CB", "CB Model", "Color",
            "Remarks", "Archived"
        ])

        # ✅ Include Archived status in data
        for record in queryset:
            writer.writerow([
                record.id,
                record.date,
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
                record.remarks,
                "True" if record.is_archived else "False"
            ])

        return response

    return JsonResponse({"success": False, "error": "Invalid request method."}, status=400)

@staff_member_required
@require_POST
def print_selected_records(request):
    ids = request.POST.getlist("ids[]")

    # If they came as one comma-separated string, split it manually
    if len(ids) == 1 and "," in ids[0]:
        ids = ids[0].split(",")

    if not ids:
        return JsonResponse({"success": False, "error": "No records selected."}, status=400)

    records = PanelRecord.objects.filter(id__in=ids).order_by("id")

    if records.count() != 15:
        return JsonResponse({
            "success": False,
            "error": "Please select exactly 15 records before printing."
        }, status=400)

    return TemplateResponse(
        request,
        "monitoring/print_selected_records.html",
        {"records": records}
    )

@staff_member_required
@csrf_exempt
def bulk_unarchive_records(request):
    """
    Unarchives multiple PanelRecord entries (sets is_archived=False).
    Expects JSON payload with { "ids": [1, 2, 3] }.
    """
    if request.method == "POST":
        try:
            body = json.loads(request.body)
            ids = body.get("ids", [])
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

        records = PanelRecord.objects.filter(id__in=ids, is_archived=True)
        count = records.count()
        records.update(is_archived=False)

        return JsonResponse({"success": True, "count": count})

    return JsonResponse({"success": False, "error": "Invalid request method"}, status=400)

from django.urls import path
from . import views

app_name = "monitoring"

urlpatterns = [
    path("panel-records-json/", views.panel_records_json, name="panel_records_json"),
    path("archive-record/<int:record_id>/", views.archive_record, name="archive_record"),
    path("archives/", views.archive_months, name="archive_months"),
    path("archives/<str:month>/", views.archive_records, name="archive_records"),
    path("unarchive/<int:record_id>/", views.unarchive_record, name="unarchive_record"),
    path("admin/archives/import/", views.import_backup_csv, name="admin_import_csv"),
    path("archive-multiple-records/", views.archive_multiple_records, name="archive_multiple_records"),
    path("archives/<str:month>/export-csv/", views.export_archive_csv, name="export_archive_csv"),
    path("bulk-unarchive-records/", views.bulk_unarchive_records, name="bulk_unarchive_records"),
    path(
        "admin/monitoring/panelrecord/print-selected/",
        views.print_selected_records,
        name="print_selected_records",
    ),
]

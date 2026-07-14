from django.core.management.base import BaseCommand
import csv
from monitoring.models import PanelRecord

class Command(BaseCommand):
    help = "Import panel records from CSV (exported from phpMyAdmin)"

    def handle(self, *args, **kwargs):
        with open("monitoring_panelrecord.csv", newline='', encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            count = 0
            for row in reader:
                PanelRecord.objects.create(
                    date=row["date"],
                    fq_number=row["fq_number"],
                    jo_number=row["jo_number"],
                    panel_name=row["panel_name"],
                    customer_name=row["customer_name"],
                    quantity=row["quantity"],
                    received_by=row["received_by"],
                    box_type=row["box_type"],
                    main_cb=row["main_cb"],
                    cb_model=row["cb_model"],
                    color=row["color"],
                    remarks=row["remarks"],
                )
                count += 1
            self.stdout.write(self.style.SUCCESS(f"✅ Successfully imported {count} records"))

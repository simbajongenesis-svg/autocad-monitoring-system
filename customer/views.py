from django.http import JsonResponse
from .models import Customer

def customers_json(request):
    customers = Customer.objects.select_related("sender").all().order_by("fullname_or_companyname")

    data = [
        {
            "id": c.id,
            "fullname_or_companyname": c.fullname_or_companyname,
            "care_of": c.care_of or "",
            "address": c.address or "",
            "contact_number": c.contact_number or "",
            "notes_or_remarks": c.notes_or_remarks or "",
        }
        for c in customers
    ]
    return JsonResponse({"data": data})


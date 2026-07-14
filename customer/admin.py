from django.contrib import admin
from django.urls import reverse, path
from django.utils.html import format_html
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.db.models import Q
from .models import Customer, Sender


# ------------------------------------------------------------------------
# Base Customer Admin (used for CustomCustomerAdmin)
# ------------------------------------------------------------------------
class CustomerAdmin(admin.ModelAdmin):
    
    """def print_button(self, obj):
        base_url = reverse("admin:customer_print", args=[obj.id])
        return format_html(
            '<a href="#" class="button print-btn" data-url="{}">🖨️ Print</a>',
            base_url
        )
    print_button.short_description = "Print"
    """
    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path(
                "<int:customer_id>/print/",
                self.print_view,
                name="customer_print"
            ),
            path(
                "<int:customer_id>/print/<str:option>/",
                self.print_view,
                name="customer_print_option"
            ),
        ]
        return my_urls + urls

# ------------------------------------------------------------------------
# Sender Admin
# ------------------------------------------------------------------------
@admin.register(Sender)
class SenderAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'address', 'contact_number')


# ------------------------------------------------------------------------
# Custom Customer Admin with Print + AJAX Search
# ------------------------------------------------------------------------
class CustomCustomerAdmin(CustomerAdmin):
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("print/<int:customer_id>/", 
                 self.admin_site.admin_view(self.print_view), 
                 name="customer_print"),

            # ✅ print with option (2copy, etc.)
            path("print/<int:customer_id>/<str:option>/", 
                 self.admin_site.admin_view(self.print_view), 
                 name="customer_print_option"),

            path("print-all/", 
                 self.admin_site.admin_view(self.print_all_view), 
                 name="customer_print_all"),

            path("ajax/customers/", 
                 self.admin_site.admin_view(self.ajax_customers), 
                 name="customer_ajax_customers"),
        ]
        return custom_urls + urls


    def print_view(self, request, customer_id, option=None):
        customer = Customer.objects.get(pk=customer_id)
        sender = customer.sender

        if option == "2copy":
            html = render_to_string("customer/print_customer_2copy.html", {
                "customer": customer,
                "sender": sender,
            })

        elif option == "4copy":
            html = render_to_string("customer/print_customer_4copy.html", {
                "customer": customer,
                "sender": sender,
            })

        else:
            html = render_to_string("customer/print_customer.html", {
                "customer": customer,
                "sender": sender,
            })

        return HttpResponse(html)



    def print_all_view(self, request):
        customers = Customer.objects.all().order_by("fullname_or_companyname")
        html = render_to_string("customer/print_all_customers.html", {
            "customers": customers,
        })
        return HttpResponse(html)

    def ajax_customers(self, request):
        search = request.GET.get("search[value]", "")
        start = int(request.GET.get("start", 0))
        length = int(request.GET.get("length", 10))

        queryset = Customer.objects.all()
        if search:
            queryset = queryset.filter(
                Q(fullname_or_companyname__icontains=search)
                | Q(care_of__icontains=search)
                | Q(address__icontains=search)
                | Q(contact_number__icontains=search)
                | Q(notes_or_remarks__icontains=search)
                | Q(sender__company_name__icontains=search)
            )

        total = Customer.objects.count()
        filtered = queryset.count()

        data = []
        for c in queryset[start:start + length]:
            data.append({
                "name": c.fullname_or_companyname,
                "care_of": c.care_of or "",
                "address": c.address or "",
                "contact": c.contact_number or "",
                "sender": c.sender.company_name if c.sender else "",
                "notes": c.notes_or_remarks or "",
                "actions": format_html(
                    '<div class="d-flex justify-content-center gap-2">'
                    '<a href="{}" class="btn btn-sm btn-outline-primary"><i class="fas fa-edit"></i></a>'
                    '<a href="{}" class="btn btn-sm btn-outline-danger"><i class="fas fa-trash"></i></a>'
                    '<a href="{}" target="_blank" class="btn btn-sm btn-outline-success">🖨️</a>'
                    '</div>',
                    reverse('admin:customer_customer_change', args=[c.id]),
                    reverse('admin:customer_customer_delete', args=[c.id]),
                    reverse('admin:customer_print', args=[c.id])
                )
            })

        return JsonResponse({
            "draw": int(request.GET.get("draw", 1)),
            "recordsTotal": total,
            "recordsFiltered": filtered,
            "data": data,
        })




    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["print_all_url"] = reverse("admin:customer_print_all")
        return super().changelist_view(request, extra_context=extra_context)


# ------------------------------------------------------------------------
# ✅ Register CustomCustomerAdmin (safe way)
# ------------------------------------------------------------------------
admin.site.register(Customer, CustomCustomerAdmin)

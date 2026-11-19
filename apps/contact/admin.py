from django.contrib import admin

from .models import Enquiry


@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "kind",
        "email",
        "phone",
        "course",
        "whatsapp_status",
        "whatsapp_attempted_at",
        "created_at",
    )
    list_filter = ("kind", "created_at")
    search_fields = ("name", "email", "phone", "subject", "message")
    readonly_fields = (
        "submission_key",
        "whatsapp_status",
        "whatsapp_message_id",
        "whatsapp_error_code",
        "whatsapp_attempted_at",
        "created_at",
    )
    date_hierarchy = "created_at"

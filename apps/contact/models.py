import uuid

from django.db import models


class Enquiry(models.Model):
    class Kind(models.TextChoices):
        CALLBACK = "callback", "Callback request"
        CONTACT = "contact", "Contact message"

    class WhatsAppStatus(models.TextChoices):
        NOT_SENT = "not_sent", "Not sent"
        PENDING = "pending", "Pending"
        SENDING = "sending", "Sending"
        ACCEPTED = "accepted", "Accepted by Meta"
        FAILED = "failed", "Failed"
        UNKNOWN = "unknown", "Outcome unknown"

    submission_key = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    kind = models.CharField(max_length=16, choices=Kind.choices, db_index=True)
    name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=32, blank=True)
    course = models.CharField(max_length=80, blank=True)
    subject = models.CharField(max_length=160, blank=True)
    message = models.TextField(max_length=3000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    whatsapp_status = models.CharField(
        max_length=16,
        choices=WhatsAppStatus.choices,
        default=WhatsAppStatus.PENDING,
        db_index=True,
    )
    whatsapp_message_id = models.CharField(max_length=255, blank=True)
    whatsapp_error_code = models.CharField(max_length=64, blank=True)
    whatsapp_attempted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "enquiry"
        verbose_name_plural = "enquiries"

    def __str__(self):
        return f"{self.get_kind_display()} from {self.name}"

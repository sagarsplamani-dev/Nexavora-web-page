from django.core.management.base import BaseCommand, CommandError

from apps.contact.services.whatsapp import (
    WhatsAppAPIError,
    WhatsAppConfigurationError,
    send_template_message,
)


class Command(BaseCommand):
    help = "Send Meta's hello_world WhatsApp template to the configured admin recipient."

    def handle(self, *args, **options):
        try:
            message_id = send_template_message("hello_world", "en_US")
        except WhatsAppConfigurationError as error:
            missing = ", ".join(error.setting_names)
            raise CommandError(
                f"WhatsApp configuration is missing or invalid: {missing}"
            ) from None
        except WhatsAppAPIError as error:
            raise CommandError(
                f"WhatsApp test message failed with error code {error.code}."
            ) from None

        self.stdout.write(
            self.style.SUCCESS(
                f"Meta accepted the WhatsApp test message. Message ID: {message_id}"
            )
        )

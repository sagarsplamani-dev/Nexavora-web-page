from django.db import migrations, models


def mark_pre_integration_enquiries_not_sent(apps, schema_editor):
    Enquiry = apps.get_model("contact", "Enquiry")
    Enquiry.objects.using(schema_editor.connection.alias).filter(
        whatsapp_status="pending",
        whatsapp_attempted_at__isnull=True,
        whatsapp_message_id="",
    ).update(
        whatsapp_status="not_sent",
        whatsapp_error_code="",
    )


class Migration(migrations.Migration):

    dependencies = [
        ("contact", "0002_enquiry_whatsapp_notification"),
    ]

    operations = [
        migrations.AlterField(
            model_name="enquiry",
            name="whatsapp_status",
            field=models.CharField(
                choices=[
                    ("not_sent", "Not sent"),
                    ("pending", "Pending"),
                    ("sending", "Sending"),
                    ("accepted", "Accepted by Meta"),
                    ("failed", "Failed"),
                    ("unknown", "Outcome unknown"),
                ],
                db_index=True,
                default="pending",
                max_length=16,
            ),
        ),
        migrations.RunPython(
            mark_pre_integration_enquiries_not_sent,
            migrations.RunPython.noop,
        ),
    ]

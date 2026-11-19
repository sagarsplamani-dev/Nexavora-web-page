import uuid

from django.db import migrations, models


def populate_submission_keys(apps, schema_editor):
    Enquiry = apps.get_model("contact", "Enquiry")
    database = schema_editor.connection.alias
    for enquiry in Enquiry.objects.using(database).filter(submission_key__isnull=True).iterator():
        Enquiry.objects.using(database).filter(pk=enquiry.pk).update(
            submission_key=uuid.uuid4()
        )


class Migration(migrations.Migration):

    dependencies = [
        ("contact", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="enquiry",
            name="submission_key",
            field=models.UUIDField(
                editable=False,
                null=True,
            ),
        ),
        migrations.RunPython(
            populate_submission_keys,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="enquiry",
            name="submission_key",
            field=models.UUIDField(
                default=uuid.uuid4,
                editable=False,
                unique=True,
            ),
        ),
        migrations.AddField(
            model_name="enquiry",
            name="whatsapp_status",
            field=models.CharField(
                choices=[
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
        migrations.AddField(
            model_name="enquiry",
            name="whatsapp_message_id",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="enquiry",
            name="whatsapp_error_code",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="enquiry",
            name="whatsapp_attempted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]

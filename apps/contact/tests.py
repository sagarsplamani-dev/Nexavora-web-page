import json
import uuid
from io import BytesIO
from unittest.mock import patch
from urllib.error import HTTPError

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.contact.services.whatsapp import (
    WhatsAppConfigurationError,
    notify_enquiry,
    send_template_message,
)

from .models import Enquiry


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class EnquirySubmissionTests(TestCase):
    def setUp(self):
        self.submission_key = str(uuid.uuid4())

    def test_homepage_renders_course_sections_and_forms(self):
        response = self.client.get(reverse("core:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="data-science"')
        self.assertContains(response, 'id="data-analytics"')
        self.assertContains(response, "Request Call Back")
        self.assertContains(response, "Send a message")
        self.assertContains(response, "Data Science Curriculum")
        self.assertContains(response, "Data Analytics Curriculum")
        self.assertContains(response, "Practical Projects")
        self.assertContains(response, "Connecting SQL Databases with Python")
        self.assertContains(response, 'href="#analytics-curriculum"')
        self.assertContains(response, 'href="#ds-projects"')
        self.assertContains(response, 'id="popup_phone"')
        self.assertContains(response, 'id="id_phone"')
        self.assertContains(response, 'name="submission_key"')
        self.assertContains(response, 'href="tel:9686712017"')
        self.assertContains(response, "wa.me/919686712017")
        self.assertNotContains(response, "8792781059")

    def test_callback_request_is_saved(self):
        with patch("apps.core.views.notify_enquiry") as notify:
            response = self.client.post(
                reverse("core:home"),
                {
                    "form_type": Enquiry.Kind.CALLBACK,
                    "submission_key": self.submission_key,
                    "name": "Asha Rao",
                    "email": "asha@example.com",
                    "phone": "9876543210",
                    "course": "Data Science",
                    "message": "Please share course details.",
                    "website": "",
                },
            )

        self.assertRedirects(response, "/?submitted=callback#advisor", fetch_redirect_response=False)
        enquiry = Enquiry.objects.get()
        self.assertEqual(enquiry.kind, Enquiry.Kind.CALLBACK)
        self.assertEqual(enquiry.course, "Data Science")
        notify.assert_called_once_with(enquiry)

    def test_repeated_callback_submission_key_sends_one_notification(self):
        submission = {
            "form_type": Enquiry.Kind.CALLBACK,
            "submission_key": self.submission_key,
            "name": "Asha Rao",
            "email": "asha@example.com",
            "phone": "9876543210",
            "course": "Data Science",
            "website": "",
        }
        with patch("apps.core.views.notify_enquiry") as notify:
            first_response = self.client.post(reverse("core:home"), submission)
            second_response = self.client.post(reverse("core:home"), submission)

        self.assertRedirects(
            first_response,
            "/?submitted=callback#advisor",
            fetch_redirect_response=False,
        )
        self.assertRedirects(
            second_response,
            "/?submitted=callback#advisor",
            fetch_redirect_response=False,
        )
        self.assertEqual(Enquiry.objects.count(), 1)
        notify.assert_called_once()

    def test_unexpected_notification_error_does_not_interrupt_callback(self):
        with patch(
            "apps.core.views.notify_enquiry",
            side_effect=RuntimeError("test provider failure"),
        ):
            response = self.client.post(
                reverse("core:home"),
                {
                    "form_type": Enquiry.Kind.CALLBACK,
                    "submission_key": self.submission_key,
                    "name": "Asha Rao",
                    "email": "asha@example.com",
                    "phone": "9876543210",
                    "course": "Data Science",
                    "website": "",
                },
            )

        self.assertRedirects(
            response,
            "/?submitted=callback#advisor",
            fetch_redirect_response=False,
        )
        enquiry = Enquiry.objects.get()
        self.assertEqual(enquiry.whatsapp_status, Enquiry.WhatsAppStatus.FAILED)
        self.assertEqual(enquiry.whatsapp_error_code, "unexpected_error")

    def test_callback_requires_a_valid_mobile_and_course(self):
        response = self.client.post(
            reverse("core:home"),
            {
                "form_type": Enquiry.Kind.CALLBACK,
                "submission_key": self.submission_key,
                "name": "Asha Rao",
                "email": "asha@example.com",
                "phone": "12345",
                "course": "",
                "website": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Enter a 10-digit mobile number.")
        self.assertContains(response, "This field is required.")
        self.assertEqual(Enquiry.objects.count(), 0)

    def test_invalid_popup_callback_reopens_with_errors(self):
        response = self.client.post(
            reverse("core:home"),
            {
                "form_type": Enquiry.Kind.CALLBACK,
                "form_source": "popup",
                "submission_key": self.submission_key,
                "name": "Asha Rao",
                "email": "asha@example.com",
                "phone": "12345",
                "course": "Data Science",
                "website": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["open_call_popup"])
        self.assertContains(response, "Enter a 10-digit mobile number.")
        self.assertEqual(Enquiry.objects.count(), 0)

    def test_contact_message_is_saved(self):
        with patch("apps.core.views.notify_enquiry") as notify:
            response = self.client.post(
                reverse("core:home"),
                {
                    "form_type": Enquiry.Kind.CONTACT,
                    "submission_key": self.submission_key,
                    "name": "Asha Rao",
                    "email": "asha@example.com",
                    "subject": "Course question",
                    "phone": "",
                    "message": "Please contact me.",
                    "website": "",
                },
            )

        self.assertRedirects(response, "/?submitted=contact#contact", fetch_redirect_response=False)
        enquiry = Enquiry.objects.get()
        self.assertEqual(enquiry.kind, Enquiry.Kind.CONTACT)
        self.assertEqual(enquiry.subject, "Course question")
        notify.assert_called_once_with(enquiry)

    def test_invalid_callback_does_not_create_enquiry(self):
        response = self.client.post(
            reverse("core:home"),
            {
                "form_type": Enquiry.Kind.CALLBACK,
                "submission_key": self.submission_key,
                "name": "",
                "email": "not-an-email",
                "course": "unknown-course",
                "website": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Enter a valid email address.")
        self.assertEqual(Enquiry.objects.count(), 0)

    def test_honeypot_submission_is_rejected(self):
        response = self.client.post(
            reverse("core:home"),
            {
                "form_type": Enquiry.Kind.CONTACT,
                "submission_key": self.submission_key,
                "name": "Asha Rao",
                "email": "asha@example.com",
                "subject": "Course question",
                "message": "Please contact me.",
                "website": "spam.example",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Unable to accept this submission.")
        self.assertEqual(Enquiry.objects.count(), 0)

    def test_syllabus_download_is_available(self):
        response = self.client.get(reverse("core:syllabus"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/plain; charset=utf-8")
        self.assertIn("attachment;", response["Content-Disposition"])
        self.assertContains(response, "Introduction to Data Analytics")

    def test_admin_can_manage_enquiries(self):
        user = get_user_model().objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="test-password-123",
        )
        Enquiry.objects.create(
            kind=Enquiry.Kind.CONTACT,
            name="Asha Rao",
            email="asha@example.com",
            subject="Course question",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("admin:contact_enquiry_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Asha Rao")


@override_settings(
    WHATSAPP_ACCESS_TOKEN="test-token-not-a-real-secret",
    WHATSAPP_PHONE_NUMBER_ID="123456789",
    WHATSAPP_BUSINESS_ACCOUNT_ID="987654321",
    WHATSAPP_ADMIN_PHONE="919876543210",
    WHATSAPP_GRAPH_API_VERSION="v27.0",
    WHATSAPP_NOTIFICATION_TEMPLATE="nexavora_enquiry_alert",
    WHATSAPP_TEMPLATE_LANGUAGE="en_US",
)
class WhatsAppNotificationTests(TestCase):
    def create_enquiry(self):
        return Enquiry.objects.create(
            kind=Enquiry.Kind.CALLBACK,
            name="Asha Rao",
            email="asha@example.com",
            phone="9876543210",
            course="Data Science",
            message="Please share course details.",
        )

    def test_template_message_uses_cloud_api_bearer_auth_and_body_parameters(self):
        response = BytesIO(
            json.dumps({"messages": [{"id": "wamid.test-message"}]}).encode()
        )
        with patch(
            "apps.contact.services.whatsapp.urlopen",
            return_value=response,
        ) as urlopen:
            message_id = send_template_message(
                "nexavora_enquiry_alert",
                "en_US",
                ["1", "Callback request", "Asha Rao"],
            )

        self.assertEqual(message_id, "wamid.test-message")
        request = urlopen.call_args.args[0]
        self.assertEqual(
            request.full_url,
            "https://graph.facebook.com/v27.0/123456789/messages",
        )
        self.assertEqual(
            request.get_header("Authorization"),
            "Bearer test-token-not-a-real-secret",
        )
        self.assertEqual(urlopen.call_args.kwargs["timeout"], 8)
        request_payload = json.loads(request.data)
        self.assertEqual(request_payload["to"], "919876543210")
        self.assertEqual(
            request_payload["template"]["components"][0]["parameters"][2]["text"],
            "Asha Rao",
        )

    def test_hello_world_message_omits_template_components(self):
        response = BytesIO(
            json.dumps({"messages": [{"id": "wamid.test-message"}]}).encode()
        )
        with patch(
            "apps.contact.services.whatsapp.urlopen",
            return_value=response,
        ) as urlopen:
            send_template_message("hello_world", "en_US")

        request_payload = json.loads(urlopen.call_args.args[0].data)
        self.assertNotIn("components", request_payload["template"])

    @override_settings(WHATSAPP_ACCESS_TOKEN="")
    def test_missing_credentials_report_setting_names_without_secret_values(self):
        with self.assertRaises(WhatsAppConfigurationError) as error:
            send_template_message("hello_world", "en_US")

        self.assertIn("WHATSAPP_ACCESS_TOKEN", error.exception.setting_names)
        self.assertNotIn("test-token-not-a-real-secret", str(error.exception))

    def test_notification_failure_is_recorded_without_deleting_enquiry(self):
        enquiry = self.create_enquiry()
        with patch(
            "apps.contact.services.whatsapp.urlopen",
            side_effect=HTTPError(
                "https://graph.facebook.com",
                401,
                "Unauthorized",
                {},
                BytesIO(b'{"error":{"code":190}}'),
            ),
        ):
            notify_enquiry(enquiry)

        enquiry.refresh_from_db()
        self.assertEqual(Enquiry.objects.count(), 1)
        self.assertEqual(enquiry.whatsapp_status, Enquiry.WhatsAppStatus.FAILED)
        self.assertEqual(enquiry.whatsapp_error_code, "http_401_graph_190")

    @override_settings(WHATSAPP_ACCESS_TOKEN="")
    def test_missing_credentials_record_failure_without_api_call(self):
        enquiry = self.create_enquiry()
        with patch("apps.contact.services.whatsapp.urlopen") as urlopen:
            notify_enquiry(enquiry)

        enquiry.refresh_from_db()
        self.assertEqual(enquiry.whatsapp_status, Enquiry.WhatsAppStatus.FAILED)
        self.assertEqual(enquiry.whatsapp_error_code, "configuration_error")
        urlopen.assert_not_called()

    def test_rate_limit_error_is_recorded_without_exposing_response_body(self):
        enquiry = self.create_enquiry()
        with self.assertLogs("apps.contact.services.whatsapp", level="WARNING") as logs:
            with patch(
                "apps.contact.services.whatsapp.urlopen",
                side_effect=HTTPError(
                    "https://graph.facebook.com",
                    429,
                    "Too Many Requests",
                    {},
                    BytesIO(b'{"error":{"code":4,"message":"sensitive provider detail"}}'),
                ),
            ):
                notify_enquiry(enquiry)

        enquiry.refresh_from_db()
        self.assertEqual(enquiry.whatsapp_status, Enquiry.WhatsAppStatus.FAILED)
        self.assertEqual(enquiry.whatsapp_error_code, "http_429_graph_4")
        self.assertNotIn("sensitive provider detail", "\n".join(logs.output))

    def test_unknown_network_outcome_is_not_resent_for_same_enquiry(self):
        enquiry = self.create_enquiry()
        with patch(
            "apps.contact.services.whatsapp.urlopen",
            side_effect=TimeoutError,
        ) as urlopen:
            notify_enquiry(enquiry)
            notify_enquiry(enquiry)

        enquiry.refresh_from_db()
        self.assertEqual(enquiry.whatsapp_status, Enquiry.WhatsAppStatus.UNKNOWN)
        self.assertEqual(urlopen.call_count, 1)

    def test_accepted_message_id_is_recorded_and_not_sent_twice(self):
        enquiry = self.create_enquiry()
        response = BytesIO(
            json.dumps({"messages": [{"id": "wamid.accepted"}]}).encode()
        )
        with patch(
            "apps.contact.services.whatsapp.urlopen",
            return_value=response,
        ) as urlopen:
            notify_enquiry(enquiry)
            notify_enquiry(enquiry)

        enquiry.refresh_from_db()
        self.assertEqual(enquiry.whatsapp_status, Enquiry.WhatsAppStatus.ACCEPTED)
        self.assertEqual(enquiry.whatsapp_message_id, "wamid.accepted")
        self.assertEqual(urlopen.call_count, 1)

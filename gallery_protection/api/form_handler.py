import frappe
from frappe import _
import json
from frappe.utils import now_datetime, format_datetime

@frappe.whitelist(allow_guest=True)
def handle_form_submission():

    data = frappe.request.get_json()
    data["submitted_at"] = format_datetime(now_datetime(), "full")


    frappe.enqueue(
        method="gallery_protection.api.form_handler.send_form_mail",
        queue="short",  # or "default"
        job_name="Send Contact Form Mail",
        now=False,
        data=data
    )

    return {"status": "queued", "message": "Form received. Thank you!"}


def send_form_mail(data):

    html_body = frappe.render_template("gallery_protection/templates/email/form_template.html", data)

    frappe.sendmail(
        recipients=["contact@amanksolutions.com"],
        subject=f"New Contact Request on {data['leadCompany']}",
        message=html_body,
    )


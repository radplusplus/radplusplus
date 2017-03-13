# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
import erpnext
from frappe import _
from frappe.utils import cstr, validate_email_add, cint, comma_and, has_gravatar, nowdate
from frappe.model.mapper import get_mapped_doc

from erpnext.controllers.selling_controller import SellingController
from erpnext.utilities.address_and_contact import load_address_and_contact
from erpnext.accounts.party import set_taxes

sender_field = "email_id"

@frappe.whitelist()
def get_lead_details(lead, posting_date=None, company=None):
        if not lead: return {}

        # 2017-03-10 - renmai - copié la fonction get_lead_details au lieu de l'appel du module erpnext.
        # Partait en boucle.
        from erpnext.accounts.party import set_address_details
        out = frappe._dict()

        lead_doc = frappe.get_doc("Lead", lead)
        lead = lead_doc

        out.update({
                "territory": lead.territory,
                "customer_name": lead.company_name or lead.lead_name,
                "contact_display": lead.lead_name,
                "contact_email": lead.email_id,
                "contact_mobile": lead.mobile_no,
                "contact_phone": lead.phone,
        })

        set_address_details(out, lead, "Lead")

        taxes_and_charges = set_taxes(None, 'Lead', posting_date, company,
                billing_address=out.get('customer_address'), shipping_address=out.get('shipping_address_name'))
        if taxes_and_charges:
                out['taxes_and_charges'] = taxes_and_charges

        # 2017-01-18 - RM - Ajout de balise pour mettre le lead name en gras.
        out.update({"contact_display": "<b>" + lead.lead_name + "</b>"})

        # 2017-01-18 - RM - permet d afficher le telephone et le courriel dans contact_display. Pour les rapports Jasper.
        if lead.phone:
                out['contact_display'] = out['contact_display'] + "<br>" + lead.phone
        if lead.email_id:
                out['contact_display'] = out['contact_display'] + "<br>" + lead.email_id

        return out

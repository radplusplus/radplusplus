# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
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

	out = erpnext.crm.doctype.lead.get_lead_details(lead, posting_date, company)

	# 2017-01-18 - RM - Ajout de balise pour mettre le lead name en gras.
	out.update({"contact_display": "<b>" + lead.lead_name + "</b>"})

	# 2017-01-18 - RM - permet d afficher le telephone et le courriel dans contact_display. Pour les rapports Jasper.
	if lead.phone:
		out['contact_display'] = out['contact_display'] + "<br>" + lead.phone 
	if lead.email_id:
		out['contact_display'] = out['contact_display'] + "<br>" + lead.email_id

	return out

# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe, json
from frappe.utils import cstr, cint, get_fullname
from frappe import msgprint, _
from frappe.model.mapper import get_mapped_doc
from erpnext.setup.utils import get_exchange_rate
from erpnext.utilities.transaction_base import TransactionBase
from erpnext.accounts.party import get_party_account_currency

subject_field = "title"
sender_field = "contact_email"

# 2017-01-08 - RM
# Crée une demande de soumission à partir d'une apportunité
# 2017-02-17 - JDLP
# Transferer le code de Erpnext vers Radplusplus
@frappe.whitelist()
def make_request_for_quotation(source_name, target_doc=None):
	doclist = get_mapped_doc("Opportunity", source_name, {
		"Opportunity": {
			"doctype": "Request for Quotation",
			"field_map": {
				"name": "opportunity",
			}
		},
		"Opportunity Item": {
			"doctype": "Request for Quotation Item",
			"field_map": {
				"uom": "stock_uom"
			}
		}
	}, target_doc)

	return doclist

# -*- coding: utf-8 -*-
# Copyright (c) 2015, RAD plus plus inc. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import radplusplus
from frappe.model.document import Document
from radplusplus.radplusplus.reorder_item import reorder_item

class MRP(Document):
	pass
	
@frappe.whitelist()
def generate():
	#frappe.msgprint(frappe._('Hello! '))
	radplusplus.radplusplus.reorder_item.reorder_item()


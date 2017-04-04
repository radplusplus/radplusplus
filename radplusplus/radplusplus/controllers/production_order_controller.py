#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
import erpnext
from frappe import _
from frappe.utils import cstr, flt
from erpnext.manufacturing.doctype.bom.bom import get_bom_items_as_dict

print_debug = True

@frappe.whitelist()
def production_order_before_save(production_order, args):
	if print_debug: frappe.errprint("production_order_before_save")
	set_required_items(production_order)
	
def set_required_items(self):
		'''set required_items for production to keep track of reserved qty'''
		
		if print_debug: frappe.errprint("set_required_items")
		
		if self.source_warehouse:
			item_dict = get_bom_items_as_dict(self.bom_no, self.company, qty=self.qty,
				fetch_exploded = self.use_multi_level_bom)

			for item in item_dict.values():
				self.append('required_items', {'item_code': item.item_code,
					'required_qty': item.qty})

			#print frappe.as_json(self.required_items)

# -*- coding: utf-8 -*-
# Copyright (c) 2015, RAD plus plus inc. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _

class ConfiguratorBatch(Document):
	def validate(self):
		self.item_attribute_value_list()
			
	def item_attribute_value_list(self):
		from radplusplus.radplusplus.controllers.configurator import update_user_translations 
		update_user_translations(frappe.db.get_value("User", frappe.session.user, "language"))
		
		validate = True
		template = frappe.get_doc("Item", self.template)
		for attribute in template.get("attributes"):
			attribute_validated = False
			for row in self.get("item_attribute_values"):
				if attribute_validated:
					continue
				if row.attribute_name_key == attribute.attribute and row.selected:
					attribute_validated = True
			if not attribute_validated:
				frappe.throw(_("No value selected for {0}").format(_(attribute.attribute)))
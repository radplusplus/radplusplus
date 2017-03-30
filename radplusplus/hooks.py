# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "radplusplus"
app_title = "radplusplus"
app_publisher = "RAD plus plus inc."
app_description = "RAD additions to erpnext"
app_icon = "octicon octicon-file-directory"
app_color = "'blue'"
app_email = "info@radplusplus.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/radplusplus/css/radplusplus.css"
# app_include_js = "/assets/radplusplus/js/radplusplus.js"

# include js, css files in header of web template
# web_include_css = "/assets/radplusplus/css/radplusplus.css"
# web_include_js = "/assets/radplusplus/js/radplusplus.js"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "radplusplus.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "radplusplus.install.before_install"
# after_install = "radplusplus.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "radplusplus.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}
# }

# List of events

# validate
# before_save
# after_save
# before_insert
# after_insert
# before_submit
# before_cancel
# before_update_after_submit
# on_update
# on_submit
# on_cancel
# on_update_after_submit
doc_events = {
	"Item": {
		"after_insert": "radplusplus.radplusplus.controllers.item_variant.item_after_insert",
		"on_trash": "radplusplus.radplusplus.doctype.item_variant_hashcode.item_variant_hashcode.delete_from_item"
	}
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"radplusplus.tasks.all"
# 	],
# 	"daily": [
# 		"radplusplus.tasks.daily"
# 	],
# 	"hourly": [
# 		"radplusplus.tasks.hourly"
# 	],
# 	"weekly": [
# 		"radplusplus.tasks.weekly"
# 	]
# 	"monthly": [
# 		"radplusplus.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "radplusplus.install.before_tests"

# Overriding Whitelisted Methods
# ------------------------------
#
override_whitelisted_methods = {
	"frappe.model.mapper.make_mapped_doc":"radplusplus.handler.make_mapped_doc",
	"erpnext.selling.doctype.sales_order.sales_order.make_material_request":"radplusplus.sales_order_radpp.make_material_request",
	"erpnext.erpnext.stock.utils.get_stock_balance":"radplusplus.radplusplus.radplusplus.stock.get_stock_balance",
	"erpnext.stock.doctype.material_request.material_request.make_purchase_order" : "radplusplus.stock.doctype.material_request.material_request.make_purchase_order",
	"erpnext.stock.doctype.material_request.material_request.make_request_for_quotation" : "radplusplus.stock.doctype.material_request.material_request.make_request_for_quotation",
	"erpnext.stock.doctype.material_request.material_request.make_purchase_order_based_on_supplier" : "radplusplus.stock.doctype.material_request.material_request.make_purchase_order_based_on_supplier",
	"erpnext.stock.doctype.material_request.material_request.make_stock_entry" : "radplusplus.stock.doctype.material_request.material_request.make_stock_entry",
	"erpnext.stock.doctype.material_request.material_request.raise_production_orders" : "radplusplus.stock.doctype.material_request.material_request.raise_production_orders",
	"erpnext.crm.doctype.lead.lead.get_lead_details" : "radplusplus.crm.doctype.lead.lead.get_lead_details",
	"erpnext.crm.doctype.opportunity.opportunity.get_lead_details" : "radplusplus.crm.doctype.opportunity.opportunity.get_lead_details",
	"erpnext.controllers.item_variant.create_variant" : "radplusplus.radplusplus.controllers.item_variant.create_variant"
	}
#"erpnext.controllers.item_variant.get_variant" : "radplusplus.radplusplus.controllers.item_variant.get_variant"

doctype_js = {
	"Sales Order":["public/js/configurator.js"],
	"Quotation":["public/js/configurator.js"],
	"Purchase Order":["public/js/configurator.js"],
	"Stock Entry":["public/js/configurator.js"],
	"Variant Price List":["public/js/configurator.js"],
	"Opportunity":["public/js/configurator.js"],
}
# doctype_list_js = {
	# "Sales Order":["public/js/configurator.js"],
# }

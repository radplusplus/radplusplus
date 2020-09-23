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

boot_session = "radplusplus.startup.boot.boot_session"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_js = [
	"/assets/js/radplusplus.min.js",
	"/assets/js/configurator.min.js"
	]
	

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
# doc_events = {
	# "Production Order": {
		# "on_cancel": "radplusplus.radplusplus.controllers.manufacturing_controllers.on_cancel"
	# }
# }

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
override_whitelisted_methods = {
	"erpnext.erpnext.stock.utils.get_stock_balance":"radplusplus.radplusplus.radplusplus.stock.get_stock_balance",
	"erpnext.crm.doctype.lead.lead.get_lead_details" : "radplusplus.radplusplus.controllers.selling_controllers.get_lead_details",
	"erpnext.crm.doctype.opportunity.opportunity.get_lead_details" : "radplusplus.radplusplus.controllers.selling_controllers.get_lead_details",
	"erpnext.controllers.item_variant.create_variant" : "radplusplus.radplusplus.controllers.item_variant.create_variant",
	"erpnext.controllers.item_variant.get_variant" : "radplusplus.radplusplus.doctype.item_variant_hashcode.item_variant_hashcode.get_variant",
	"erpnext.manufacturing.doctype.work_order.work_order.make_stock_entry":"radplusplus.radplusplus.controllers.manufacturing_controllers.make_stock_entry",
	"erpnext.selling.doctype.sales_order.sales_order.make_work_orders" : "radplusplus.radplusplus.controllers.manufacturing_controllers.make_work_orders",
	"erpnext.stock.get_item_details.get_item_details" : "radplusplus.radplusplus.controllers.stock_controllers.get_item_details_translated",
	"frappe.email.doctype.standard_reply.standard_reply.get_standard_reply" : "radplusplus.radplusplus.controllers.communication_controllers.get_standard_reply",
	"erpnext.selling.doctype.sales_order.sales_order.make_delivery_note":"radplusplus.radplusplus.controllers.selling_controllers.make_delivery_note"
	}


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
		"after_insert": "radplusplus.radplusplus.doctype.bom_maker.bom_maker.make_bom"
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
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "radplusplus.event.get_events"
# }


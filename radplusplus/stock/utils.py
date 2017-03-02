# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
import json
from frappe.utils import flt, cstr, nowdate, nowtime


@frappe.whitelist()
def get_stock_balance(item_code, warehouse, posting_date=None, posting_time=None, with_valuation_rate=False, batch_no=None):
	"""Returns stock balance quantity at given warehouse on given posting date or current date.

	If `with_valuation_rate` is True, will return tuple (qty, rate)"""

	from erpnext.stock.stock_ledger import get_previous_sle

	if not posting_date: posting_date = nowdate()
	if not posting_time: posting_time = nowtime()

	last_entry = get_previous_sle({
		"item_code": item_code,
		"warehouse":warehouse,
		"posting_date": posting_date,
		"posting_time": posting_time,
		"batch_no": batch_no }) #JDLP - 2017-01-30 - batch_no

	if with_valuation_rate:
		return (last_entry.qty_after_transaction, last_entry.valuation_rate) if last_entry else (0.0, 0.0)
	else:
		return last_entry.qty_after_transaction or 0.0

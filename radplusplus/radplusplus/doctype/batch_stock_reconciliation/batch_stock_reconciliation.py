# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
import erpnext
import frappe.defaults
from frappe import msgprint, _
from frappe.utils import cstr, flt, cint
from erpnext.stock.stock_ledger import update_entries_after
from erpnext.controllers.stock_controller import StockController
from erpnext.stock.utils import get_stock_balance
from frappe.utils.xlsxutils import make_xlsx
import json

class OpeningEntryAccountError(frappe.ValidationError): pass
class EmptyStockReconciliationItemsError(frappe.ValidationError): pass

print_debug = False

class BatchStockReconciliation(StockController):
	def __init__(self, arg1, arg2=None):
		super(BatchStockReconciliation, self).__init__(arg1, arg2)
		self.head_row = ["Item Code", "Warehouse", "Quantity", "Valuation Rate"]

	def validate(self):
		if not self.expense_account:
			self.expense_account = frappe.db.get_value("Company", self.company, "stock_adjustment_account")
		if not self.cost_center:
			self.cost_center = frappe.db.get_value("Company", self.company, "cost_center")
		self.validate_posting_time()
		self.remove_items_with_no_change()
		self.validate_data()
		self.validate_expense_account()
		self.set_total_qty_and_amount()

	def on_submit(self):
		self.update_stock_ledger()
		self.make_gl_entries()

	def on_cancel(self):
		self.delete_and_repost_sle()
		self.make_gl_entries_on_cancel()

	def remove_items_with_no_change(self):
		"""Remove items if qty or rate is not changed"""
		self.difference_amount = 0.0
		def _changed(item):			
			qty, rate = get_stock_balance(item.item_code, item.warehouse,
					self.posting_date, self.posting_time, with_valuation_rate=True)
			
			#JDLP - 2017-01-30 - batch_no
			if item.batch_no:
				qty = get_item_warehouse_batch_actual_qty(item.item_code, item.warehouse, item.batch_no, self.posting_date, self.posting_time)
			
			if (item.qty==None or item.qty==qty) and (item.valuation_rate==None or item.valuation_rate==rate):
				return False
			else:
				# set default as current rates
				if item.qty==None:
					item.qty = qty

				if item.valuation_rate==None:
					item.valuation_rate = rate

				item.current_qty = qty
				item.current_valuation_rate = rate
				self.difference_amount += (flt(item.qty or qty) * flt(item.valuation_rate or rate) - (flt(qty) * flt(rate)))
				return True

		items = filter(lambda d: _changed(d), self.items)

		if not items:
			frappe.throw(_("None of the items have any change in quantity or value."),
				EmptyStockReconciliationItemsError)

		elif len(items) != len(self.items):
			self.items = items
			for i, item in enumerate(self.items):
				item.idx = i + 1
			frappe.msgprint(_("Removed items with no change in quantity or value."))

	def validate_data(self):
		def _get_msg(row_num, msg):
			return _("Row # {0}: ").format(row_num+1) + msg

		self.validation_messages = []
		item_warehouse_combinations = []

		default_currency = frappe.db.get_default("currency")

		for row_num, row in enumerate(self.items):
			# find duplicates
			if [row.item_code, row.warehouse, row.batch_no] in item_warehouse_combinations:#JDLP - 2017-01-30 - batch_no
				self.validation_messages.append(_get_msg(row_num, _("Duplicate entry")))
			else:
				item_warehouse_combinations.append([row.item_code, row.warehouse, row.batch_no])#JDLP - 2017-01-30 - batch_no

			self.validate_item(row.item_code, row_num+1)

			# validate warehouse
			if not frappe.db.get_value("Warehouse", row.warehouse):
				self.validation_messages.append(_get_msg(row_num, _("Warehouse not found in the system")))

			# if both not specified
			if row.qty in ["", None] and row.valuation_rate in ["", None]:
				self.validation_messages.append(_get_msg(row_num,
					_("Please specify either Quantity or Valuation Rate or both")))

			# do not allow negative quantity
			if flt(row.qty) < 0:
				self.validation_messages.append(_get_msg(row_num,
					_("Negative Quantity is not allowed")))

			# do not allow negative valuation
			if flt(row.valuation_rate) < 0:
				self.validation_messages.append(_get_msg(row_num,
					_("Negative Valuation Rate is not allowed")))

			if row.qty and not row.valuation_rate:
				row.valuation_rate = get_stock_balance(row.item_code, row.warehouse,
							self.posting_date, self.posting_time, with_valuation_rate=True)[1]
				if not row.valuation_rate:
					# try if there is a buying price list in default currency
					buying_rate = frappe.db.get_value("Item Price", {"item_code": row.item_code,
						"buying": 1, "currency": default_currency}, "price_list_rate")
					if buying_rate:
						row.valuation_rate = buying_rate
						
			#JDLP - 2017-01-30 - batch_no
			# if batch_no is required and not provided.
			has_batch_no = frappe.db.get_value("Item", {"item_code": row.item_code}, "has_batch_no")
			if has_batch_no == 1 and row.batch_no is None:
				self.validation_messages.append(_get_msg(row_num,
					_("Batch number is required")))
				#raise frappe.ValidationError, _("Item: {0} managed batch-wise, batch number is required").format(item_code)

			if has_batch_no == 0 and row.batch_no is not None:
				self.validation_messages.append(_get_msg(row_num,
					_("Batch number should be empty")))
				#raise frappe.ValidationError, _("Item: {0} is not managed batch-wise, batch number should be empty").format(item_code)
			#JDLP - 2017-01-30 - batch_no
			
		# throw all validation messages
		if self.validation_messages:
			for msg in self.validation_messages:
				msgprint(msg)

			raise frappe.ValidationError(self.validation_messages)

	def validate_item(self, item_code, row_num):
		from erpnext.stock.doctype.item.item import validate_end_of_life, \
			validate_is_stock_item, validate_cancelled_item

		# using try except to catch all validation msgs and display together

		try:
			item = frappe.get_doc("Item", item_code)

			# end of life and stock item
			validate_end_of_life(item_code, item.end_of_life, item.disabled, verbose=0)
			validate_is_stock_item(item_code, item.is_stock_item, verbose=0)

			# item should not be serialized
			if item.has_serial_no == 1:
				raise frappe.ValidationError, _("Serialized Item {0} cannot be updated \
					using Stock Reconciliation").format(item_code)

			#JDLP - 2017-01-30 - batch_no
			# item managed batch-wise not allowed
			# if item.has_batch_no == 1:
				# raise frappe.ValidationError, _("Item: {0} managed batch-wise, can not be reconciled using \
					# Stock Reconciliation, instead use Stock Entry").format(item_code)

			
			# docstatus should be < 2
			validate_cancelled_item(item_code, item.docstatus, verbose=0)

		except Exception, e:
			self.validation_messages.append(_("Row # ") + ("%d: " % (row_num)) + cstr(e))

	def update_stock_ledger(self):
		"""	find difference between current and expected entries
			and create stock ledger entries based on the difference"""
		from erpnext.stock.stock_ledger import get_previous_sle

		for row in self.items:
			previous_sle = get_previous_sle({
				"item_code": row.item_code,
				"warehouse": row.warehouse,
				"posting_date": self.posting_date,
				"posting_time": self.posting_time,
				"batch_no": row.batch_no #JDLP - 2017-01-30 - batch_no
			})

			if not row.batch_no:				
				row.qty_after_transaction = row.qty
				row.qty = 0
				
				if previous_sle:
					if row.qty_after_transaction in ("", None):
						row.qty_after_transaction = previous_sle.get("qty_after_transaction", 0)

					if row.valuation_rate in ("", None):
						row.valuation_rate = previous_sle.get("valuation_rate", 0)

				if row.qty_after_transaction and not row.valuation_rate:
					frappe.throw(_("Valuation Rate required for Item in row {0}").format(row.idx))

				
				if ((previous_sle and row.qty_after_transaction == previous_sle.get("qty_after_transaction")
					and row.valuation_rate == previous_sle.get("valuation_rate"))
					or (not previous_sle and not row.qty_after_transaction)):
						continue
			else:
				balance_qty = 0
				balance_rate = 0
				if previous_sle:
					balance_qty = previous_sle.get("qty_after_transaction", 0)
					balance_rate = previous_sle.get("valuation_rate", 0)
				previous_qty = get_item_warehouse_batch_actual_qty(row.item_code, row.warehouse, row.batch_no, self.posting_date, self.posting_time)
				
				row.qty = row.qty - previous_qty
				row.qty_after_transaction = balance_qty + row.qty
				
				if (balance_qty+row.qty) != 0:
					row.valuation_rate = flt(((balance_qty*balance_rate)+(row.qty*row.valuation_rate))/(balance_qty+row.qty))
				
				if row.qty and not row.valuation_rate:
					frappe.throw(_("Valuation Rate required for Item in row {0}").format(row.idx))

				if ((previous_sle and row.qty_after_transaction == balance_qty
					and row.valuation_rate == previous_sle.get("valuation_rate"))
					or (not previous_sle and not row.qty_after_transaction)):
						continue

			if print_debug: frappe.msgprint("row: " + cstr(row))
			self.insert_entries(row)

	def insert_entries(self, row):
		"""Insert Stock Ledger Entries"""
		args = frappe._dict({
			"doctype": "Stock Ledger Entry",
			"item_code": row.item_code,
			"warehouse": row.warehouse,
			"posting_date": self.posting_date,
			"posting_time": self.posting_time,
			"voucher_type": self.doctype,
			"voucher_no": self.name,
			"company": self.company,
			"stock_uom": frappe.db.get_value("Item", row.item_code, "stock_uom"),
			"is_cancelled": "No",
			"actual_qty": row.qty,
			"qty_after_transaction": row.qty_after_transaction,
			"valuation_rate": row.valuation_rate,
			"batch_no": row.batch_no #JDLP - 2017-01-30 - batch_no
		})
		if print_debug: frappe.msgprint("sle: " + cstr(args))
		#frappe.throw(_("sle {0}").format(cstr(args)))
		self.make_sl_entries([args])

	#JDLP - 2017-04-18 Methode copie de Stock_ledger
	#non utilise
	def radpp_make_sl_entries(self, sl_entries, is_amended=None, allow_negative_stock=False, via_landed_cost_voucher=False):
		if sl_entries:
			from erpnext.stock.utils import update_bin
			from erpnext.stock.stock_ledger import make_entry, set_as_cancel, delete_cancelled_entry

			cancel = True if sl_entries[0].get("is_cancelled") == "Yes" else False
			if cancel:
				set_as_cancel(sl_entries[0].get('voucher_no'), sl_entries[0].get('voucher_type'))

			for sle in sl_entries:
				sle_id = None
				if sle.get('is_cancelled') == 'Yes':
					sle['actual_qty'] = -flt(sle['actual_qty'])

				#if sle.get("actual_qty") or sle.get("voucher_type")=="Batch Stock Reconciliation":
				#	frappe.msgprint("make_entry: ")
				sle_id = self.radpp_make_entry(sle, allow_negative_stock, via_landed_cost_voucher)

				args = sle.copy()
				args.update({
					"sle_id": sle_id,
					"is_amended": is_amended
				})
				update_bin(args, allow_negative_stock, via_landed_cost_voucher)

			if cancel:
				delete_cancelled_entry(sl_entries[0].get('voucher_type'), sl_entries[0].get('voucher_no'))

	#JDLP - 2017-04-18 Methode copie de Stock_ledger
	#non utilise
	def radpp_make_entry(self, args, allow_negative_stock=False, via_landed_cost_voucher=False):
		args.update({"doctype": "Stock Ledger Entry"})
	
		sle = frappe.get_doc(args)
		sle.flags.ignore_permissions = 1
		sle.allow_negative_stock=allow_negative_stock
		sle.via_landed_cost_voucher = via_landed_cost_voucher
		sle.valuation_rate = flt(sle.valuation_rate)
		sle.insert()
		
		parent = frappe.get_doc(sle.voucher_type,sle.voucher_no)
		
		# assert
		previous_sle_args = {
			"item_code": sle.item_code,
			"warehouse": sle.warehouse,
			"posting_date": parent.posting_date,
			"posting_time": parent.posting_time,
			"sle": sle.name
		}
		from erpnext.stock.stock_ledger import get_previous_sle
		previous_sle = get_previous_sle(previous_sle_args)
		prev_stock_value = (previous_sle.stock_value or 0.0) if previous_sle else 0.0
		sle.valuation_rate = args['valuation_rate']
		sle.qty_after_transaction = args['qty_after_transaction']
		sle.stock_queue = [[sle.qty_after_transaction, sle.valuation_rate]]
		sle.stock_value = flt(sle.qty_after_transaction) * flt(sle.valuation_rate)
			
		# rounding as per precision
		sle.stock_value = flt(sle.stock_value, sle.precision)

		stock_value_difference = sle.stock_value - prev_stock_value
		sle.prev_stock_value = sle.stock_value

		# update current sle
		sle.stock_queue = json.dumps(sle.stock_queue)
		sle.stock_value_difference = stock_value_difference
		frappe.get_doc(sle).db_update()	
		sle.save()
		sle.submit()
		return sle.name
	
	def delete_and_repost_sle(self):
		"""	Delete Stock Ledger Entries related to this voucher
			and repost future Stock Ledger Entries"""
			
		#JDLP - 2017-01-30 - batch_no
		existing_entries = frappe.db.sql("""select distinct item_code, warehouse, batch_no
			from `tabStock Ledger Entry` where voucher_type=%s and voucher_no=%s""",
			(self.doctype, self.name), as_dict=1)

		# delete entries
		frappe.db.sql("""delete from `tabStock Ledger Entry`
			where voucher_type=%s and voucher_no=%s""", (self.doctype, self.name))

		# repost future entries for selected item_code, warehouse
		for entries in existing_entries:
			update_entries_after({
				"item_code": entries.item_code,
				"warehouse": entries.warehouse,
				"posting_date": self.posting_date,
				"posting_time": self.posting_time,
				"batch_no": entries.batch_no #JDLP - 2017-01-30 - batch_no
			})

	def get_gl_entries(self, warehouse_account=None):
		if not self.cost_center:
			msgprint(_("Please enter Cost Center"), raise_exception=1)

		return super(BatchStockReconciliation, self).get_gl_entries(warehouse_account,
			self.expense_account, self.cost_center)

	def validate_expense_account(self):
		if not cint(frappe.defaults.get_global_default("auto_accounting_for_stock")):
			return

		if not self.expense_account:
			msgprint(_("Please enter Expense Account"), raise_exception=1)
		elif not frappe.db.sql("""select name from `tabStock Ledger Entry` limit 1"""):
			if frappe.db.get_value("Account", self.expense_account, "report_type") == "Profit and Loss":
				frappe.throw(_("Difference Account must be a Asset/Liability type account, since this Stock Reconciliation is an Opening Entry"), OpeningEntryAccountError)

	def set_total_qty_and_amount(self):
		for d in self.get("items"):
			d.amount = flt(d.qty) * flt(d.valuation_rate)
			d.current_amount = flt(d.current_qty) * flt(d.current_valuation_rate)
			d.quantity_difference = flt(d.qty) - flt(d.current_qty)
			d.amount_difference = flt(d.amount) - flt(d.current_amount)

	def get_items_for(self, warehouse):
		self.items = []
		for item in get_items(warehouse, self.posting_date, self.posting_time):
			self.append("items", item)

	def submit(self):
		if len(self.items) > 100:
			self.queue_action('submit')
		else:
			self._submit()

	def cancel(self):
		if len(self.items) > 100:
			self.queue_action('cancel')
		else:
			self._cancel()

@frappe.whitelist()
def get_items(warehouse, posting_date, posting_time, as_dict = 0, as_list = 0):
	items = frappe.get_list("Bin", fields=["item_code"], filters={"warehouse": warehouse}, as_list=1)

	items += frappe.get_list("Item", fields=["name"], filters= {"is_stock_item": 1, "has_serial_no": 0,
		"has_batch_no": 0, "has_variants": 0, "disabled": 0, "default_warehouse": warehouse},
			as_list=1)

	res = []
	
	for item in set(items):
		stock_bal = get_stock_balance(item[0], warehouse, posting_date, posting_time,
			with_valuation_rate=True)
		#JDLP - 2017-01-30, ajout de batch
		if frappe.db.get_value("Item",item[0],"disabled") == 0 and frappe.db.get_value("Item",item[0],"has_batch_no") == 0:				
			if as_dict:
				res.append({
					"item_code": item[0],
					"warehouse": warehouse,
					"qty": stock_bal[0],
					"item_name": frappe.db.get_value('Item', item[0], 'item_name'),
					"valuation_rate": stock_bal[1],
					"current_qty": stock_bal[0],
					"current_valuation_rate": stock_bal[1],
					"batch_no": ""
				})
			if as_list:
				item_attributes = frappe.get_all("Item Variant Attribute",{"parent":item[0]},["attribute","attribute_value"])
				species = ""
				construction = ""
				flooring_grade = ""
				flooring_width = ""
				thickness = ""
				if item_attributes:
					if print_debug: frappe.errprint("item_attributes : " + cstr(item_attributes))
					for attribute in item_attributes:
						if attribute.attribute == "Essence" : species = attribute.attribute_value
						if attribute.attribute == "Hardwood Construction" : construction = attribute.attribute_value
						if attribute.attribute == "Flooring Grade" : flooring_grade = attribute.attribute_value
						if attribute.attribute == "Flooring Width" : flooring_width = attribute.attribute_value
						if attribute.attribute == "Flooring Thickness" : thickness = attribute.attribute_value
				res.append([
					item[0],
					"",
					stock_bal[0],
					stock_bal[1],
					species,
					construction,
					flooring_grade,
					flooring_width,
					thickness,
					"",
					"",
					"",
					""
				])

	return res

#JDLP - 2017-01-30
#Ajouter a get_items les item avec numero de lot
#Si la balance de l'item est 0 ne rien ajouter
#Si la quantite du lot est 0 ne pas l'ajouter
@frappe.whitelist()
def get_items_with_batch_no(warehouse, posting_date, posting_time, as_dict = 0, as_list = 0):
	res = get_items(warehouse, posting_date, posting_time)
	items = frappe.get_list("Item", fields=["name"], filters= {"is_stock_item": 1, "has_serial_no": 0,
	"has_batch_no": 1, "has_variants": 0, "disabled": 0}, as_list=1)
	
	for item in set(items):
		#msgprint("item:" + cstr(item))
		stock_bal = get_stock_balance(item[0], warehouse, posting_date, posting_time, with_valuation_rate=True)
		if stock_bal[0] == 0: continue
		batches = frappe.get_all('Batch', filters={'item': item[0]}, fields=['name'])
		for batch in batches:
			#msgprint("batche:" + cstr(batch["name"]))
			qty = get_item_warehouse_batch_actual_qty(item[0], warehouse, batch["name"], posting_date, posting_time)
			if qty == 0: continue
			if as_list:
				item_attributes = frappe.get_all("Item Variant Attribute",{"parent":item[0]},["attribute","attribute_value"])
				species = ""
				construction = ""
				flooring_grade = ""
				flooring_width = ""
				thickness = ""
				doc_batch = frappe.get_doc("Batch",{"name":batch["name"]})
				if item_attributes:
					if print_debug: frappe.errprint("item_attributes : " + cstr(item_attributes))
					for attribute in item_attributes:
						if attribute.attribute == "Essence" : species = attribute.attribute_value
						if attribute.attribute == "Hardwood Construction" : 
							if attribute.attribute_value == "Massif":
								construction = "Massif"
							else:
								construction = "Ing."
						if attribute.attribute == "Flooring Grade" : flooring_grade = attribute.attribute_value
						if attribute.attribute == "Flooring Width" : flooring_width = attribute.attribute_value
						if attribute.attribute == "Flooring Thickness" : thickness = attribute.attribute_value
				values = [
					item[0],
					batch["name"],
					qty,
					stock_bal[1],
					species,
					construction,
					flooring_grade,
					flooring_width,
					thickness,
					doc_batch.qty_per_box,
					doc_batch.customer_batch_number,
					doc_batch.milling,
					doc_batch.description
				]
			if as_dict:
				values = {
					"item_code": item[0],
					"warehouse": warehouse,
					"qty": qty,
					"item_name": frappe.db.get_value('Item', item[0], 'item_name'),
					"valuation_rate": stock_bal[1],
					"current_qty": qty,
					"current_valuation_rate": stock_bal[1],
					"batch_no": batch["name"]
				}
			res.append(values)
	
	return res

@frappe.whitelist()
def get_stock_balance_for(item_code, warehouse, posting_date, posting_time, batch_no = None):
	frappe.has_permission("Stock Reconciliation", "write", throw = True)
	
	qty, rate = get_stock_balance(item_code, warehouse,
		posting_date, posting_time, with_valuation_rate=True, batch_no=batch_no)
		
	if batch_no:
		qty = get_item_warehouse_batch_actual_qty(item_code, warehouse, batch_no, posting_date, posting_time)
		
	return {
		'qty': qty,
		'rate': rate
	}
	
@frappe.whitelist()
def get_item_warehouse_batch_actual_qty(item_code, warehouse, batch_no, posting_date, posting_time):
	actual_qty =  frappe.db.sql("""SELECT
		round(sum(`tabStock Ledger Entry`.actual_qty),2)
		FROM
		`tabStock Ledger Entry`
		WHERE
		`tabStock Ledger Entry`.item_code = '{item_code}' AND
		`tabStock Ledger Entry`.warehouse = '{warehouse}' AND
		`tabStock Ledger Entry`.batch_no = '{batch_no}' AND
		((`tabStock Ledger Entry`.posting_date = '{posting_date}' AND 
		`tabStock Ledger Entry`.posting_time <= '{posting_time}') OR
		`tabStock Ledger Entry`.posting_date < '{posting_date}')""".format(
					item_code=item_code,
					warehouse=warehouse,
					batch_no=batch_no,
					posting_date=posting_date,
					posting_time=posting_time)
		, as_dict=False)
		
	if all(actual_qty[0]):
		actual_qty = actual_qty[0][0]
	else:
		actual_qty = 0
	return actual_qty

def get_columns():
	return ["item_code","warehouse","batch_no","qty","valuation_rate"]
	
def get_file_name(warehouse):
	return "{0}.{1}".format(warehouse.replace(" ", "-").replace("/", "-"), "xlsx")
	
@frappe.whitelist()
def download(warehouse, posting_date, posting_time):
	
	# columns.append(frappe._dict(label=_("Item Code"), fieldtype=str, fieldname="item_code"))
	# columns.append(frappe._dict(label=_("Warehouse"), fieldtype=str, fieldname="warehouse"))
	# columns.append(frappe._dict(label=_("Batch No"), fieldtype=str, fieldname="batch_no"))
	# columns.append(frappe._dict(label=_("Quantity"), fieldtype=int, fieldname="qty"))
	# columns.append(frappe._dict(label=_("Rate"), fieldtype=float, fieldname="valuation_rate"))
	
	columns =[
		"Code item",
		"Lot",
		"Quantite",		
		"Taux",
		"Essence",
		"Construction",
		"Grade",
		"Largeur",
		"Epaisseur",
		"Qte/bte",
		"Ref client",
		"Moul.",
		"Info"
	]
	
	data = get_items_with_batch_no(warehouse, posting_date, posting_time, as_list = 1)
	data.insert(0, columns) 
	#if print_debug: frappe.errprint("rows : " + cstr(rows))
	# data = []
	# data.append(columns)
	# data.append(rows)
	if print_debug: frappe.errprint("data : " + cstr(data))
		
	xlsx_file = get_xls(data)

	if not xlsx_file:
		frappe.msgprint(_('No Data'))
		return

	frappe.local.response.filecontent = xlsx_file.getvalue()
	frappe.local.response.type = 'binary'
	frappe.local.response.filename = get_file_name(warehouse)

@frappe.whitelist()
def upload(ignore_encoding=False):	
	if getattr(frappe, "uploaded_file", None):
		with open(frappe.uploaded_file, "r") as upfile:
			fcontent = upfile.read()
	else:
		from frappe.utils.file_manager import get_uploaded_content
		fname, fcontent = get_uploaded_content()
	
	
		
	return cstr(fcontent)
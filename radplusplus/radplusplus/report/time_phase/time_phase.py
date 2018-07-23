# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
import datetime
import time
from frappe import _

def execute(filters=None):
	#frappe.msgprint(frappe._('execute - Debut '))
	columns = get_columns()
	#frappe.msgprint(frappe._('get_columns - Fin '))
	to_receive = get_purchase_without_receipt(filters)
	#frappe.msgprint(frappe._('get_purchase_without_receipt - Fin '))
	to_produce = get_production_in_progress(filters)
	to_deliver = get_sales_order_not_delivered(filters)
	required_for_production = get_required_for_production(filters)
	#frappe.msgprint(frappe._('get_production_in_progress - Fin '))
	#sl_entries = get_stock_ledger_entries(filters)
	item_details = get_item_details(filters)
	opening_row = get_opening_balance(filters, columns)
	
	data = []
	data_temp = []
	
	if opening_row:
		data.extend(opening_row)

	for tpline in to_receive:
		item_detail = item_details[tpline.item_code]

		data_temp.append([tpline.item_code, (tpline.expected_delivery_date if tpline.expected_delivery_date else tpline.schedule_date),
			tpline.parenttype, tpline.parent, tpline.idx, tpline.qty - tpline.received_qty, 0.0, 0.0, tpline.warehouse, (tpline.batch_no if tpline.batch_no else ""),
			(tpline.serial_no if tpline.serial_no else "")])
	
	for tpline in to_produce:
		item_detail = item_details[tpline.production_item]

		data_temp.append([tpline.production_item, tpline.planned_start_date.date(), "Production Order", tpline.name,"",
			tpline.qty - tpline.produced_qty,0.0, 0.0, tpline.fg_warehouse,
			(tpline.batch_no if tpline.batch_no else ""), (tpline.serial_no if tpline.serial_no else "")])
			
	for tpline in to_deliver:
		item_detail = item_details[tpline.item_code]

		data_temp.append([tpline.item_code, tpline.delivery_date, tpline.parenttype, tpline.parent, tpline.idx,
			0.0,tpline.qty - tpline.delivered_qty, 0.0, tpline.warehouse,
			(tpline.batch_no if tpline.batch_no else "") ,(tpline.serial_no if tpline.serial_no else "")])
	#frappe.msgprint(frappe._('required_for_production '+str(len(required_for_production))))		
	for tpline in required_for_production:
		item_detail = item_details[tpline.item_code]

		data_temp.append([tpline.item_code, tpline.planned_start_date.date(), tpline.parenttype, tpline.parent, tpline.idx,
			0.0,tpline.required_qty - tpline.transferred_qty, 0.0, tpline.source_warehouse,
			(tpline.batch_no if tpline.batch_no else "") ,(tpline.serial_no if tpline.serial_no else "")])
			
	#data_temp.sort(1)
	from operator import itemgetter	
	data_temp.sort(key=itemgetter(1))
	data.extend(data_temp)
	if not (filters.item_code and filters.company):
		return columns, data
		
	for index, row in enumerate(data):
		#frappe.msgprint(frappe._('balance[qty_after_transaction] : ' + str(balance.get('qty_after_transaction'))))
		if index > 0:
			row[7] = data[index -1][7]+row[5]-row[6]
		if index == 0:
			row[7] = row[5]-row[6]
		if index < (len(data) - 1):
			next_ = data[index + 1]
		
	return columns, data

def get_columns():
	#frappe.msgprint(frappe._('get_columns '))
	return [_("Item Code") + ":Link/Item:200", _("Date") + ":Date:80", _("Reference Type") + "::160", 
		_("Reference") + ":Dynamic Link/"+_("Reference Type")+":100", _("Line") + "::50",
		_("Qty to receive") + ":Float:100", _("Qty needed") + ":Float:100", _("On hand qty") + ":Float:100", 
		_("Warehouse") + ":Link/Warehouse:200", _("Batch") + ":Link/Batch:100",_("Serial #") + ":Link/Serial No:100"
	]
def get_required_for_production(filters):
	#frappe.msgprint(frappe._('get_required_for_production ' + str(get_required_for_production_conditions(filters))))
	return frappe.db.sql("""select tpline.planned_start_date as planned_start_date, tppoi.required_qty as required_qty, 
			tppoi.transferred_qty as transferred_qty, tppoi.item_code as item_code, tpline.source_warehouse as source_warehouse, 
			tppoi.parent as parent, tppoi.parenttype as parenttype, tppoi.idx as idx, tpline.docstatus as docstatus
		from `tabProduction Order Item` tppoi INNER JOIN `tabProduction Order` tpline ON
			tppoi.parent = tpline.name
		where tppoi.required_qty > tppoi.transferred_qty and
			tpline.docstatus = 1
			{time_phase_conditions}
			order by tpline.planned_start_date asc"""\
		.format(time_phase_conditions=get_required_for_production_conditions(filters)), filters, as_dict=1)

def get_required_for_production_conditions(filters):
	conditions = []
	item_conditions=get_item_conditions(filters,"item_code")
	if item_conditions:
		conditions.append("""item_code in (select name from tabItem
			{item_conditions})""".format(item_conditions=item_conditions))
	if filters.get("warehouse"):
		conditions.append(get_warehouse_condition(filters.get("warehouse"),"source_warehouse"))

	#frappe.msgprint(frappe._('get_required_for_production_conditions ' + str(conditions)))
	
	return "and {}".format(" and ".join(conditions)) if conditions else ""
	
def get_sales_order_not_delivered(filters):
	#frappe.msgprint(frappe._('get_sales_order_not_delivered ' + str(get_sales_order_not_delivered(filters))))
	return frappe.db.sql("""select tso.delivery_date , delivered_qty,
			item_code, warehouse, qty, tpline.parent as parent, tpline.parenttype as parenttype, tpline.idx as idx,
			tso.docstatus as docstatus
		from `tabSales Order Item` tpline INNER JOIN `tabSales Order` tso ON
			tpline.parent = tso.name
		where delivered_qty < qty and
			tpline.completed = 0
			tso.status <> "Closed"
			tso.docstatus = 1
			{time_phase_conditions}
			order by tso.delivery_date asc"""\
		.format(time_phase_conditions=get_sales_order_conditions(filters)), filters, as_dict=1)
		
def get_sales_order_conditions(filters):
	conditions = []
	item_conditions=get_item_conditions(filters,"item_code")
	if item_conditions:
		conditions.append("""item_code in (select name from tabItem
			{item_conditions})""".format(item_conditions=item_conditions))
	if filters.get("warehouse"):
		conditions.append(get_warehouse_condition(filters.get("warehouse"),"warehouse"))

	#frappe.msgprint(frappe._('get_purchase_conditions ' + str(conditions)))
	
	return "and {}".format(" and ".join(conditions)) if conditions else ""
	
def get_purchase_without_receipt(filters):
	#frappe.msgprint(frappe._('get_purchase_conditions ' + str(get_purchase_conditions(filters))))
	return frappe.db.sql("""select schedule_date, expected_delivery_date, received_qty,
			item_code, warehouse, qty, parent, parenttype, idx, docstatus
		from `tabPurchase Order Item` tpline
		where received_qty < qty and
			docstatus = 1
			{time_phase_conditions}
			order by schedule_date asc, expected_delivery_date asc, name asc"""\
		.format(time_phase_conditions=get_purchase_conditions(filters)), filters, as_dict=1)

def get_production_in_progress(filters):
	#frappe.msgprint(frappe._('get_production_conditions ' + str(get_production_conditions(filters))))
	return frappe.db.sql("""select planned_start_date, produced_qty, production_item, fg_warehouse,
		qty, name, docstatus
		from `tabProduction Order` tpline
		where produced_qty < qty and
			docstatus = 1
			{time_phase_conditions}
			order by planned_start_date asc"""\
		.format(time_phase_conditions=get_production_conditions(filters)), filters, as_dict=1)

def get_item_details(filters):
	item_details = {}
	for item in frappe.db.sql("""select name, item_name, description, stock_uom
			from `tabItem` {item_conditions}"""\
			.format(item_conditions=get_item_conditions(filters,"name")), filters, as_dict=1):
		item_details.setdefault(item.name, item)

	return item_details

def get_production_conditions(filters):
	#frappe.msgprint(frappe._('get_production_conditions - Debut '))
	conditions = []
	item_conditions=get_item_conditions(filters,"production_item")
	
	if item_conditions:
		conditions.append("""production_item in (select name from tabItem
			{item_conditions})""".format(item_conditions=item_conditions))
	if filters.get("warehouse"):
		conditions.append(get_warehouse_condition(filters.get("warehouse"),"fg_warehouse"))
	
	#frappe.msgprint(frappe._('conditions ' + str(conditions)))

	return "and {}".format(" and ".join(conditions)) if conditions else ""
	
def get_item_conditions(filters,fn):
	conditions = []
	if filters.get("item_code"):
		conditions.append("name=%(item_code)s")
	#if filters.get("warehouse"):
	#	conditions.append(get_warehouse_condition(filters.get("warehouse")))
	
	#frappe.msgprint(frappe._('get_item_conditions ' + str(conditions)))
	
	return "where {}".format(" and ".join(conditions)) if conditions else ""

def get_purchase_conditions(filters):
	conditions = []
	item_conditions=get_item_conditions(filters,"item_code")
	if item_conditions:
		conditions.append("""item_code in (select name from tabItem
			{item_conditions})""".format(item_conditions=item_conditions))
	if filters.get("warehouse"):
		conditions.append(get_warehouse_condition(filters.get("warehouse"),"warehouse"))

	#frappe.msgprint(frappe._('get_purchase_conditions ' + str(conditions)))
	
	return "and {}".format(" and ".join(conditions)) if conditions else ""


def get_opening_balance(filters, columns):
	#frappe.msgprint(frappe._('get_opening_balance ' + str(filters)))
	if not (filters.item_code and filters.company):
		return

	warehouse_list = []
	from erpnext.stock.stock_ledger import get_previous_sle
	if not (filters.item_code and filters.warehouse and filters.company):
		
		for warehouse in frappe.get_list("Warehouse", fields=["name"]):

			last_sle_for_each_warehouse = get_previous_sle({
					"item_code": filters.item_code,
					"warehouse": warehouse['name'],
					"posting_date": datetime.datetime.now().date(),
					"posting_time": datetime.datetime.now().time()
				}) 
				
			if last_sle_for_each_warehouse :
				warehouse_list.append({'warehouse':warehouse['name']}) 
	
	else:
		last_sle_for_each_warehouse = get_previous_sle({
				"item_code": filters.item_code,
				"warehouse": filters.warehouse,
				"posting_date": datetime.datetime.now().date(),
				"posting_time": datetime.datetime.now().time()
			}) 
			
		if last_sle_for_each_warehouse :
			warehouse_list.append({'warehouse':filters.warehouse}) 
	
	# frappe.msgprint(frappe._('len(warehouse_list) : ' + str(warehouse_list)))
	
	last_sle_for_each_warehouse = [
		get_previous_sle({
			"item_code": filters.item_code,
			"warehouse": warehouse['warehouse'],
			"posting_date": datetime.datetime.now().date(),
			"posting_time": datetime.datetime.now().time()
		}) 
		for warehouse 
		in warehouse_list
		]
	
	rows = []
	for index, balance in enumerate(last_sle_for_each_warehouse):
		
		#frappe.msgprint(frappe._('balance[qty_after_transaction] : ' + str(balance.get('qty_after_transaction'))))
		dict_sle_value = {
			2:_("Opening"),
			5:balance['qty_after_transaction'],
			6:0.0,
			8:balance['warehouse']
		}
		if index > 0:
			dict_sle_value[7] = balance['qty_after_transaction']+last_sle_for_each_warehouse[index -1]['qty_after_transaction']
		if index == 0:
			dict_sle_value[7] = balance['qty_after_transaction']
		if index < (len(last_sle_for_each_warehouse) - 1):
			next_ = last_sle_for_each_warehouse[index + 1]
		balance['qty_after_transaction'] = dict_sle_value[7]
		rows.append([dict_sle_value.get(x) if x in dict_sle_value else "" for x in range(len(columns))])
	 
	return rows

def get_warehouse_condition(warehouse,fn):
	warehouse_details = frappe.db.get_value("Warehouse", warehouse, ["lft", "rgt"], as_dict=1)
	#frappe.msgprint(frappe._('warehouse_details : ' + str(warehouse_details)))
	#frappe.msgprint(frappe._('warehouse_details.rgt : ' + str(warehouse_details.rgt)))
	#frappe.msgprint(frappe._('warehouse_details.lft : ' + str(warehouse_details.lft)))
	if warehouse_details:
		return " exists (select name from `tabWarehouse` wh \
			where wh.lft >= %s and wh.rgt <= %s and tpline."%(warehouse_details.lft,
			warehouse_details.rgt)+fn+" = wh.name)"

	return ''

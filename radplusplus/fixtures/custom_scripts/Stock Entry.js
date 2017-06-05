// Copyright (c) 2016, RAD plus plus inc. and contributors
// For license information, please see license.txt

///////////////////////////////////////////////////////////////////////
/////////////////////////// Code specifique ///////////////////////////
/////////////////////////////// Handles ///////////////////////////////
	
frappe.ui.form.on("Stock Entry",{
	onload : function(frm) {
		cur_frm.add_fetch("shipper", "default_warehouse", "to_warehouse");
		cur_frm.add_fetch("shipper", "nom_des_lots", "prefix");
	},
	refresh : function(frm) {
		LoadAttributesValues(false, frm, "items")
	},
	setup : function(frm) {
		frm.fields_dict.items.grid.get_field('template').get_query = function() {
			return erpnext.queries.item({item_group : "Configurateur"});
		};
	}
});

frappe.ui.form.on("Stock Entry Detail",{
	template : function(frm, cdt, cdn){
		SetConfiguratorOf(true, frm, cdt, cdn)		
	},
	create_variant : function(frm, cdt, cdn) {
		CreateItemVariant(true, frm, cdt, cdn, true, true)
	},
	reconfigure : function(doc, cdt, cdn) {
		ReconfigurerItemVariant(false, doc, cdt, cdn)
	},
	configurator_of : function(frm, cdt, cdn) {	
		if (frm.doc.shipper){
			frappe.call({
				method: 'frappe.client.get_value',
				args: {
					'doctype': 'Customer',
					'filters': {'name': frm.doc.shipper},
					'fieldname': [
						'milling'
					]
				},
				callback: function(r) {
					if (!r.exc) {	
						if (r.message.milling) {
							ShowHideAttributes(true, frm, cdt, cdn, false, true, r.message.milling)
						}
						else {
							ShowHideAttributes(true, frm, cdt, cdn, false, true)
						}
					}
				}
			});			
		}
		else {
			ShowHideAttributes(true, frm, cdt, cdn, false, true)
		}
	},
	batch_no : function(frm, cdt, cdn) {
		var row = locals[cdt][cdn];		
		frappe.call({
			method: 'frappe.client.get_value',
			args: {
				'doctype': 'Batch',
				'filters': {'name': row.batch_no},
				'fieldname': [
					'qty_per_box'
				]
			},
			callback: function(r) {
				if (!r.exc) {
					if (r.message.qty_per_box) {							
						row.qty_per_box = r.message.qty_per_box;
						refresh_field("items");						
					}
				}
			}
		});			
	}, 
	construction : function(frm, cdt, cdn) {
		var row = locals[cdt][cdn];		
		if (row.construction == "Massif"){
			row.thickness = '3/4"';
			row.length = "1' à 7'";
			console.log("1' à 7'")
			refresh_field("items");
		}
		if (row.construction == "Hardwood"){
			row.thickness = '3/4"';
			row.length = '1\' to 7\'';
			console.log('1\' to 7\'')
			refresh_field("items");
		}
		if (row.construction.toString().substring(0,10) == "Ingenierie" ){
			row.thickness = __('5/8"');
			row.length = "1' à 8'";
			console.log("1' à 8'")
			refresh_field("items");
		}
		if (row.construction.toString().substring(0,10) == "Engineered"){
			row.thickness = '5/8"';
			row.length = '1\' to 8\'';
			console.log('1\' to 8\'')
			refresh_field("items");
		}
	},
	t_warehouse : function(doc, cdt, cdn) {
		var row = locals[cdt][cdn];
		var me = this;		
		if (cur_frm.doc.purpose == "Material Receipt") {
			frappe.call({
				method: 'frappe.client.get_value',
				args: {
					'doctype': 'Warehouse',
					'filters': {'name': row.t_warehouse},
					'fieldname': [
						'is_customer_warehouse'
					]
				},
				callback: function(r) {
					if (!r.exc) {					
						if (r.message.is_customer_warehouse) {
							row.is_sample_item = r.message.is_customer_warehouse;
							refresh_field("items");
						}
						else {
							row.is_sample_item = 0;
							refresh_field("items");
						}
					}
				}
			});
		}
	},
	s_warehouse : function(doc, cdt, cdn) {
		var row = locals[cdt][cdn];
		var me = this;		
		if (cur_frm.doc.purpose == "Material Transfer for Manufacture") {
			frappe.call({
				method: 'frappe.client.get_value',
				args: {
					'doctype': 'Warehouse',
					'filters': {'name': row.s_warehouse},
					'fieldname': [
						'is_customer_warehouse'
					]
				},
				callback: function(r) {
					if (!r.exc) {					
						if (r.message.is_customer_warehouse) {
							row.is_sample_item = r.message.is_customer_warehouse;
							refresh_field("items");
						}
						else {
							row.is_sample_item = 0;
							refresh_field("items");
						}
					}
				}
			});
		}
		if (me.frm.doc.purpose == "Material Receipt") {
			frappe.call({
				method: 'frappe.client.get_value',
				args: {
					'doctype': 'Warehouse',
					'filters': {'name': row.t_warehouse},
					'fieldname': [
						'is_customer_warehouse'
					]
				},
				callback: function(r) {
					if (!r.exc) {					
						if (r.message.is_customer_warehouse) {
							row.is_sample_item = r.message.is_customer_warehouse;
							refresh_field("items");
						}
						else {
							row.is_sample_item = 0;
							refresh_field("items");
						}
					}
				}
			});
		}
	},
	items_add: function(doc, cdt, cdn) {
			
		var row = frappe.get_doc(cdt, cdn);
		var me = this;		
		cur_frm.script_manager.copy_from_first_row("items", row, ["expense_account", "cost_center"]);

		if(!row.s_warehouse) row.s_warehouse = cur_frm.doc.from_warehouse;
		if(!row.t_warehouse) row.t_warehouse = cur_frm.doc.to_warehouse;
			
		var row = locals[cdt][cdn];
		if (cur_frm.doc.purpose == "Material Transfer for Manufacture") {
			frappe.call({
				method: 'frappe.client.get_value',
				args: {
					'doctype': 'Warehouse',
					'filters': {'name': row.s_warehouse},
					'fieldname': [
						'is_customer_warehouse'
					]
				},
				callback: function(r) {					
					if (!r.exc) {	
						if (r.message.is_customer_warehouse) {
							row.is_sample_item = r.message.is_customer_warehouse;
							refresh_field("items");
						}
						else {
							row.is_sample_item = 0;
							refresh_field("items");
						}
					}
				}
			});
		}
		if (cur_frm.doc.purpose == "Material Receipt") {
			frappe.call({
				method: 'frappe.client.get_value',
				args: {
					'doctype': 'Warehouse',
					'filters': {'name': row.t_warehouse},
					'fieldname': [
						'is_customer_warehouse'
					]
				},
				callback: function(r) {					
					if (!r.exc) {	
						if (r.message.is_customer_warehouse) {
							row.is_sample_item = r.message.is_customer_warehouse;
							refresh_field("items");
						}
						else {
							row.is_sample_item = 0;
							refresh_field("items");
						}
					}
				}
			});
		}
	}
}); 

///////////////////////////// FIN Handles /////////////////////////////

////////////////////////////// Methodes ///////////////////////////////

// 2016-10-24 - JDLP
// Script fonctionnel
// Permet d'assigner les valeurs par defaut
// Ce script doit etre present dans tous les doc utilisant le configurateur
function AssignDefaultValues(printDebug, frm, cdt, cdn) {
    if (printDebug) console.log(__("AssignDefaultValues"));
    if (printDebug) console.log(__("Debug mode ON"));

    var soi = locals[cdt][cdn];
    if (soi && soi.item_code) {
		// 2016-11-02 - JDLP - 
        StockEntryDetailOnItemChange(printDebug, frm, cdt, cdn);
    }
    if (printDebug) console.log(__("END AssignDefaultValues"));
}

// 2016-11-22 - JDLP
// J'ai deplace le code de "erpnext\stock\doctype\stock_entry\stock_entry.js" "cur_frm.cscript.item_code"
// Ceci rentrait en conflit avec le configurateur
function StockEntryDetailOnItemChange(printDebug, frm, cdt, cdn){
	if (printDebug) console.log(__("StockEntryDetailOnItemChange"));
	var d = locals[cdt][cdn];			
	if(d.item_code) {
		args = {
			'item_code'			: d.item_code,
			'warehouse'			: cstr(d.s_warehouse) || cstr(d.t_warehouse),
			'transfer_qty'		: d.transfer_qty,
			'serial_no	'		: d.serial_no,
			'bom_no'			: d.bom_no,
			'expense_account'	: d.expense_account,
			'cost_center'		: d.cost_center,
			'company'			: cur_frm.doc.company
		};
		return frappe.call({
			doc: cur_frm.doc,
			method: "get_item_details",
			args: args,
			callback: function(r) {
				if(r.message) {
					var d = locals[cdt][cdn];
					$.each(r.message, function(k, v) {
						d[k] = v;
					});
					refresh_field("items");
					SetVariantOf(true, frm, cdt, cdn, true, false)
				}
			}
		});
	}	
}
//////////////////////////// Fin Methodes /////////////////////////////
///////////////////////// FIN Code specifique /////////////////////////
///////////////////////////////////////////////////////////////////////

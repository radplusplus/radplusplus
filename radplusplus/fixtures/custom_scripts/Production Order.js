// Copyright (c) 2016, RAD plus plus inc. and contributors
// For license information, please see license.txt

// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

/////////////////////////////// Handles ///////////////////////////////
frappe.ui.form.on("Production Order",{
	"onload": function(frm) {		
		// 2017-03-28 - RENMAI
		// Permet d'assigner le client l'ordre de fabrication selon la commande de vente selectionnee.
		if(frm.sales_order) {
			frappe.db.get_value("Sales Order", { name: cur_frm.doc.sales_order },
				"customer", function(data){
			cur_frm.set_value("customer", data.customer); });
		}
	}
});

erpnext.production_order.set_default_warehouse = function(frm) {
	if (!(frm.doc.wip_warehouse || frm.doc.fg_warehouse || frm.doc.source_warehouse)) {
		console.log("IF");
		frappe.call({
			method: "radplusplus.radplusplus.controllers.manufacturing_controllers.get_default_warehouse",
			callback: function(r) {
				if(!r.exe) {
					console.log("callback");
					frm.set_value("wip_warehouse", r.message.wip_warehouse);
					frm.set_value("fg_warehouse", r.message.fg_warehouse);
					frm.set_value("source_warehouse", r.message.source_warehouse);
				}
			}
		});
	}
}

cur_frm.cscript['Stop Production Order'] = function() {
	frappe.call({
		method:"radplusplus.radplusplus.controllers.manufacturing_controllers.stop_unstop",
		args: {
			"self": me.frm.doc.name,
			"status": "Stopped"
		},
		callback: function(r) {
			cur_frm.refresh();
		}
	});
}

cur_frm.cscript['Unstop Production Order'] = function() {
	frappe.call({
		method:"radplusplus.radplusplus.controllers.manufacturing_controllers.stop_unstop",
		args: {
			"self": me.frm.doc.name,
			"status": "Unstopped"
		},
		callback: function(r) {
			cur_frm.refresh();
		}
	});
}

$.extend(cur_frm.cscript, {
	bom_no: function() {
		cur_frm.doc.production_order_item = {};
		cur_frm.doc.operations = {};
		erpnext.utils.map_current_doc({
			method: "radplusplus.radplusplus.controllers.manufacturing_controllers.set_production_order_materials_and_operations",
			source_name: this.frm.doc.bom_no
		})
	},

	qty: function() {
		update_details();
	},

	customer: function() {
		update_details();
	}
});

function update_details() {
	console.log("Update_Details")
    frappe.call({
		method:"radplusplus.radplusplus.controllers.manufacturing_controllers.update_details",
		args: {
			"self": cur_frm.doc
		},
		callback: function(r) {
			frappe.model.sync(r.message);
			cur_frm.refresh();
		}
	});
}
// Copyright (c) 2016, RAD plus plus inc. and contributors
// For license information, please see license.txt


// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

/////////////////////////////// Handles ///////////////////////////////

frappe.ui.form.on("BOM Operation",{
	"operation": function(frm, cdt, cdn) {	
		var d = locals[cdt][cdn];

		if(!d.operation) return;

		frappe.call({
			"method": "frappe.client.get",
			args: {
				doctype: "Operation",
				name: d.operation
			},
			callback: function (data) {
				if(data.message.description) {
					frappe.model.set_value(d.doctype, d.name, "description", data.message.description);
				}
				if(data.message.workstation) {
					frappe.model.set_value(d.doctype, d.name, "workstation", data.message.workstation);
				}
				frappe.model.set_value(d.doctype, d.name, "no_oper", d.idx *10);			
				//msgprint("d : " + d.idx);
			}
		})
	}
});

frappe.ui.form.on("BOM Item",{
	"item_code": function(frm, cdt, cdn) {	
		var d = locals[cdt][cdn];

		if(!d.item_code) return;

		frappe.model.set_value(d.doctype, d.name, "no_mtl", d.idx *10);
	}
});



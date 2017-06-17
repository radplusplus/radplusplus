// Copyright (c) 2016, RAD plus plus inc. and contributors
// For license information, please see license.txt

frappe.ui.form.on('MRP', {
	refresh: function(frm) {
		frm.add_custom_button(__('Make sugestion'), function(){
			frappe.call({
				method:"radplusplus.radplusplus.doctype.mrp.mrp.generate",
				args:{
				},
				callback: function(r){
				}
			})
		})
	}
});

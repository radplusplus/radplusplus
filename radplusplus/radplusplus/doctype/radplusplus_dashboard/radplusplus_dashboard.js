// Copyright (c) 2016, RAD plus plus inc. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Radplusplus Dashboard', {
	refresh: function(frm) {

	},
	
	make_bom_from_template: function(frm) {
		frappe.prompt([{label:"Template", fieldtype:"Link", options:"Item", reqd: 1},
						{label:"Create new if exist", fieldtype:"Check", reqd: 1}],
			function(data) {
				frappe.call({
					method:"myrador.myrador.doctype.bom_maker.bom_maker.make_bom_from_template",
					args: {
						template: data.template,						
						create_new_if_exist: data.create_new_if_exist
					},
					callback: function(r) {
						msgprint(__("Result : " + r)); return;
					}
				});
			}
		, __("Select template"), __("Make"));
	}
});

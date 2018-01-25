// Copyright (c) 2016, RAD plus plus inc. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Configurator Bom', {
	refresh: function(frm) {

	}
});

frappe.ui.form.on("Configurator Bom", "onload", function(frm, cdt, cdn) {
       var soi = locals[cdt][cdn];
       frappe.call({
        method: "radplusplus.radplusplus.controllers.configurator.get_required_attributes_fields",
        args: {
            "user_name": frappe.session.user,
            "item_code": frm.doc.configurator_template
        },
        callback: function(res) {
			var values = (res.message || []);
			var hash = {};
			for(var i=0; i<values.length; i++) {
				hash[values[i][0].toString()] = values[i][1];
			}
			frm.doc.configurator_fields = hash;
		}			
    });
});


frappe.ui.form.on("Configurator Bom", "operations_on_form_rendered", function (frm, cdt, cdn) {
	console.log(__("operations_on_form_rendered :"));
	var grid_row = cur_frm.open_grid_row();
	RefreshAttributeOptions(frm, cdt, cdn, "operations", grid_row.doc.attribute);
})

frappe.ui.form.on("Configurator Bom", "items_on_form_rendered", function (frm, cdt, cdn) {
	console.log(__("operations_on_form_rendered :"));
	var grid_row = cur_frm.open_grid_row();
	RefreshAttributeOptions(frm, cdt, cdn, "items", grid_row.doc.attribute);
})

frappe.ui.form.on("Configurator Bom Operation", "attribute", function(frm, cdt, cdn) {
       RefreshAttribute(frm, cdt, cdn, "operations");
});

frappe.ui.form.on("Configurator Bom Item", "attribute", function(frm, cdt, cdn) {
       RefreshAttribute(frm, cdt, cdn, "items");
});



function RefreshAttribute(frm, cdt, cdn, childs_table_name) {
    var soi = locals[cdt][cdn];
	if (soi != null)
		RefreshAttributeOptions(frm, cdt, cdn, childs_table_name, soi.attribute )
}


function RefreshAttributeOptions(frm, cdt, cdn, childs_table_name, attribute) {
	if (attribute != null){
		
		frappe.call({
			method: "radplusplus.radplusplus.controllers.configurator.get_attributes_values",
			args: {
				"attribute": attribute
			},
			callback: function(res) {
				//Convertir le message en Array
				printDebug = false
				if (printDebug) console.log(__("res :" + res));
				var rows = (res.message || {});
				dictionary = rows;
				if (printDebug) console.log(__("rows :" + rows));

				var field = cur_frm.fields_dict[childs_table_name].grid.fields_map["attribute_value"];

				//Construire les options
				var options = [];
				for (i = 0; i < rows.length; ++i) {
					options.push({
							'key': rows[i][1],
							'value': rows[i][1]
						});
				}				

				//l'assigner au field
				frappe.utils.filter_dict(cur_frm.fields_dict[childs_table_name].grid.docfields, {
					"fieldname": "attribute_value"
				})[0].options = options;
				refresh_field(childs_table_name);
			}
		});		
	}
}
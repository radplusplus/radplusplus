// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

/////////////////////////////// Handles ///////////////////////////////

frappe.ui.form.on("Item",{
	"update_description": function(frm) {	
		// 2016-03-28 - RENMAI - Mettre à jour les descriptions de l'item.
		frappe.call({
			"method": "radplusplus.radplusplus.controllers.item_variant.update_unique_description",
			args: { 
				"variant_of": frm.doc.variant_of,
				"variant_name": frm.doc.name
			},
			callback:function(r){ 				
			}
		})
	}
});

// 2016-08-29 - JDLP
// Permet de remplir le champ configurator_of uniquement avec des items qui sont des 
// modeles.
cur_frm.fields_dict['configurator_of'].get_query = function(doc) {
    return {
        filters: {
            "has_variants": 1
        }
    }
}


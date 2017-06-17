// Copyright (c) 2016, RAD plus plus inc. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Configurator Batch', {
	refresh: function(frm) {

	},
	make_variants: function(frm, cdt, cdn) {
		frappe.call({
			method: "radplusplus.radplusplus.controllers.item_variant.create_batch_variants",
			args: {
				"batch_name": frm.doc.name,
				"configurator_of": frm.doc.configurator_of,
			},
			callback: function(res) {
				//Convertir le message en Array
				var variants = (res.message || []);
				
				msgprint("Les pièces ont été crées.");
					
				frm.timeline.insert_comment("Comment", variants);
				
			}
		});
	},
	add_attributes: function(doc, cdt, cdn) {
		//Retrouver les attribut qui s'appliquent
		frappe.call({
			method: "radplusplus.radplusplus.controllers.item_variant.get_item_attributes_values",
			args: {"item_code": doc.fields_dict.configurator_of.value},
			callback: function(res) {
				//Convertir le message en Array
				var attributes = (res.message || []);
				console.log(__("cur_frm.doc.item_attribute_values.length :" + cur_frm.doc.item_attribute_values.length));
				
				//pour chaque field 
				for (var k = 0; k < cur_frm.doc.item_attribute_values.length; k++) {
					var row = cur_frm.doc.item_attribute_values[k];
					
		
					var found = false;	
					
					//pour chaque attribut
					for (var j = 0; j < attributes.length; j++) {
						//Pointeur sur grid
						console.log(__("Row : " + row.attribute_name + ":" + row.item_attribute_value));
						console.log(__("Attributes : " + attributes[j][0] + ":" + attributes[j][1]));
						console.log(__("found : " + found));
						
						if (row.attribute_name == attributes[j][0] && row.item_attribute_value == attributes[j][1] ) {
							console.log(__("Match *****"));
							attributes.splice(j,1);
							found = true;
						}
						
						if (found){
							console.log(__("Sortie de boucle attributes "));
							break;
						}
					}
					
				}
					
				console.log(__("attributes.length :" + attributes.length));
				
				for (var j = 0; j < attributes.length; j++) {
					var new_row = frappe.model.add_child(cur_frm.doc, "Configurator Batch Attribute", "item_attribute_values");
					new_row.attribute_name = attributes[j][0];
					new_row.item_attribute_value = attributes[j][1];
					new_row.selected = false;
				}
				
				refresh_field("item_attribute_values");
			}
		});
	},
	configurator_of: function(doc, cdt, cdn) {
		//Retrouver les attribut qui s'appliquent
		frappe.call({
			method: "radplusplus.radplusplus.controllers.item_variant.get_item_attributes_values",
			args: {"item_code": doc.fields_dict.configurator_of.value},
			callback: function(res) {
				//Convertir le message en Array
				var attributes = (res.message || []);
				
				//effacer
				
				//pour chaque attribut
				for (var j = 0; j < attributes.length; j++) {
					var new_row = frappe.model.add_child(cur_frm.doc, "Configurator Batch Attribute", "item_attribute_values");
					new_row.attribute_name = attributes[j][0];
					new_row.item_attribute_value = attributes[j][1];
					new_row.selected = false;
				}
				
				refresh_field("item_attribute_values");
			}
		});
	}
});

cur_frm.fields_dict['configurator_of'].get_query = function(doc) {
    return {
        filters: {
            "has_configuration": 1
        }
    }
}

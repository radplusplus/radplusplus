frappe.provide("radplusplus");

radplusplus.configurator = class configurator {
	constructor(opts) {
		$.extend(this, opts);
		this.initiated = true;
	}
	
	load_attributes_values() {
		var me = this;
		//Obtenir les champs parent, attribute_value de tous les Item Attribute Value.
		frappe.call({
			method: "radplusplus.radplusplus.controllers.configurator.get_configurator_attributes_values",
			args: {
				"user_name": frappe.session.user
			},
			callback: function(res) {
				//Convertir le message en Array
				
				var rows = (res.message || {});
				var dictionary = rows;
				for (var key in dictionary) {			
					if (typeof me.frm.fields_dict[me.child_field_name].grid.fields_map[key] === 'undefined') continue;
					
					var field = me.frm.fields_dict[me.child_field_name].grid.fields_map[key];
					if (field.fieldtype != "Select") continue;
					
					// do something with key
					var values = dictionary[key];
					
					// Construire les options
					var options = [];
					
					for (var i = 0; i < values.length; ++i) {
						var tuple = values[i];
						
						options.push({
							'key': tuple[0],
							'value':  tuple[1]
						});
					}
					
					//l'assigner au field
					frappe.utils.filter_dict(me.frm.fields_dict[me.child_field_name].grid.docfields, {"fieldname": key})[0].options = options;
				}
			}
		});
	}
	
	show_hide_attributes(cdt, cdn) {		
		var me = this;

		if (locals[cdt][cdn]) {
			
			var row = locals[cdt][cdn];
			
			var template = ""
			
			if (row.configurator_of){
				template = row.configurator_of
			}
			
			//Retrouver les attributs qui s'appliquent
			frappe.call({
				method: "radplusplus.radplusplus.controllers.configurator.get_all_attributes_fields",
				args: {"item_code": template},  
				callback: function(res) {
					
					//Convertir le message en Array
					var attributes = (res.message || {});
					
					var attributes = {};
					for (var i = 0, len = res.message.length; i < len; i++) {
						attributes[res.message[i].field_name] = res.message[i];
					}
										
					//Pointeur sur grid
					var grid = me.frm.fields_dict["items"].grid;
							
					$.each(grid.docfields, function(i, field) {						
						if (typeof attributes[field.fieldname] !== 'undefined'){
							field.depends_on = "eval:false";
							
							if (attributes[field.fieldname].parent != null){
								field.depends_on = "eval:true";								
								var field_value = frappe.model.get_value(row.doctype, row.name, field.fieldname);
								if (!field_value){ 
									var first_value = frappe.utils.filter_dict(me.frm.fields_dict["items"].grid.docfields, {"fieldname": field.fieldname})[0].options[0]["value"]
									frappe.model.set_value(row.doctype, row.name, field.fieldname, first_value);
								}
							}
						}
						
						refresh_field(field);							
						
					});

					refresh_field("items");
				}
			});
		}
	}
			
	// Permet d'afficher ou non les attributs configurables en fonction de "configurator_of"
	set_configurator_of(cdt, cdn) {		
		var me = this;
		
		var soi = locals[cdt][cdn];
		
		//Si un code à été saisit
		if (soi && soi.template) {
			
			// Retrouver la valeur de configurator_of
			frappe.call({
				method: "frappe.client.get_value",
				args: {
					"doctype": "Item",
					"filters": {
						"item_code": soi.template
					},
					"fieldname": ["configurator_of"]
				},
				callback: function(res) {
					var grid_row = me.frm.open_grid_row();
					frappe.model.set_value(soi.doctype, soi.name, "configurator_of", res.message.configurator_of);
				}
			});
		}
		else{
			var grid_row = me.frm.open_grid_row();
			frappe.model.set_value(soi.doctype, soi.name, "configurator_of", "");
		}
	}

	// Permet d'afficher la description formatée de l'item selon la langue du document en cours
	load_translated_description(cdt, cdn) {
		var me = this;

		//Si un code à été saisit
		if (locals[cdt][cdn] && locals[cdt][cdn].item_code) {

			var soi = locals[cdt][cdn];

			frappe.call({
				method: "radplusplus.radplusplus.doctype.item_language.item_language.item_description_query",
				args: {
					"doctype": cdt,
					"docname" : cdn,
					"item_code" : soi.item_code
				},
				callback: function(res) {
					soi.description = res.message;
					var grid_row = me.frm.open_grid_row();
					grid_row.grid_form.fields_dict.description.set_value("test");
				}
			});
		}
	}

	// Il permet de creer un item variant lorsque le bouton create_variant est active.
	create_item_variant(cdt, cdn, validate_attributes) {
		var me = this;
		//Si un code à été saisit
		if (locals[cdt][cdn] && locals[cdt][cdn].template) {

			var soi = locals[cdt][cdn];

			//Lancer le call
			frappe.call({
				method: "radplusplus.radplusplus.controllers.configurator.get_required_attributes_fields",
				args: {
					"item_code": soi.template
				},
				callback: function(res) {							
					//Convertir le message en Array
					var attributes = (res.message || []);
					var variantAttributes = {};

					//pour chaque attribut
					for (var j = 0; j < attributes.length; j++) {
						var attribute_name = attributes[j].name;
						var fieldname = attributes[j].field_name;
						var currItem = soi[attributes[j].field_name];
						
						if (currItem != undefined)
						{
							var idx = me.frm.cur_grid.grid_form.fields_dict[attributes[j].field_name].df.idx;
							var options = me.frm.cur_grid.grid_form.fields[idx - 1].options;
							for (var o = 0; o < options.length; o++) {
								if (options[o].value == currItem) {
									currItem = options[o].key;
									break;
								}
							}
						}
						//Vérifier que la valeur n'est pas "A venir"
						if (currItem == undefined || validate_attributes && currItem.toLowerCase().trim() == "à venir")
							frappe.throw(__("Tous les attributs doivent être définis."));

						//Ajouter la valuer dans la liste d'attributs								
						variantAttributes[attributes[j].name] = currItem;
					}

					//Lancer la création du variant
					//Convertir la liste d'attributs en json string
					var attjson = JSON.stringify(variantAttributes);

					//Lancer le call
					frappe.call({
						method: "radplusplus.radplusplus.controllers.item_variant.create_variant_and_submit",
						args: {
							"template_item_code": soi.configurator_of,
							"args": attjson
						},
						callback: function(res) {
							var doclist = frappe.model.sync(res.message);
							var variant = doclist[0];
							var grid_row = me.frm.open_grid_row();

							grid_row.grid_form.fields_dict.item_code.set_value(variant.name);
							
							frappe.model.set_value(soi.doctype, soi.name, "template", "");
						}
					});
				}
			});
		}
	}

	// Il permet de reconfigurer un item variant provenant d'un configurateur.
	reconfigurer_item_variant(cdt, cdn) {		
		var me = this;
		
		//Si un code à été saisit
		if (locals[cdt][cdn] && locals[cdt][cdn].item_code) {

			var soi = locals[cdt][cdn];
			
			//Trouver le modele de l'item
			frappe.call({
				method: "frappe.client.get_value",
				args: {
					"doctype": "Item",
					"filters": {
						"name": soi.item_code
					},
					"fieldname": ["variant_of"]
				},
				callback: function(res) {
					if (res.message.variant_of){
						
						var variant_of = res.message.variant_of;
						
						frappe.call({
							method: "radplusplus.radplusplus.controllers.configurator.get_item_variant_attributes_values",
							args: {
								"user_name": frappe.session.user,
								"item_code": soi.item_code
							},
							callback: function(res) {
								//Convertir le message en Array
								var attributes = (res.message || []);
								var variantAttributes = {};
								var grid_row = me.frm.open_grid_row();

								//pour chaque attribut
								for (var j = 0; j < attributes.length; j++) {
									if (grid_row.grid_form.fields_dict[attributes[j][0]]){
										grid_row.grid_form.fields_dict[attributes[j][0]].set_value(attributes[j][1]);
									}
									
								}

								//Assigner l'item_code du configurateur
								frappe.call({
									method: "frappe.client.get_value",
									args: {
										"doctype": "Item",
										"filters": {
											"configurator_of": variant_of
										},
										"fieldname": ["name"]
									},
									callback: function(res) {
										soi.configurator_of = res.message.name;
										grid_row.grid_form.fields_dict.template.set_value(soi.configurator_of);
									}
								});

							}
						});
					}
				}
			});
		}
	}

	// Il permet de focuser sur template plutot que item_code.
	set_focus(field) {	
		// next is table, show the table
		if(field.df.fieldtype=="Table") {
			if(!field.grid.grid_rows.length) {
				field.grid.add_new_row(1);
			} else {
				field.grid.grid_rows[0].toggle_view(true);
			}
		}
		else if(field.editor) {
			field.editor.set_focus();
		}
		else if(field.$input) {
			field.$input.focus();
		}
	}
}
		
	
	

	


///////////////////////////////////////////////////////////////////////
//////////////////////////// CONFIGURATEUR ////////////////////////////
///// Cette partie peut être récyclé                              /////
///// Cette partie est dependante de :                            /////
///// AssignDefaultValues(printDebug, frm, cdt, cdn)              /////

// 2016-08-18
// Script fonctionnel.
// Permet de remplir les options des champs de type sélection avec les valeurs possibles de item attribute.
// 2016-09-17 - JDLP : Adaptation pour frappe V 7
function LoadAttributesValues(printDebug, frm, child_field_name) {
    if (printDebug) console.log(__(printDebug, "LoadAttributesValues**********************"));
	
    //Obtenir les champs "parent", "attribute_value" de tous les "Item Attribute Value"
    frappe.call({
        method: "radplusplus.radplusplus.controllers.configurator.get_configurator_attributes_values",
        args: {
            "user_name": user
        },
        callback: function(res) {
            //Convertir le message en Array
			
            if (printDebug) console.log(__(printDebug, "res :" + res));
            var rows = (res.message || {});
			dictionary = rows;
            if (printDebug) console.log(__(printDebug, "rows :" + rows));
			for (var key in dictionary) {
				
				var field = cur_frm.fields_dict[child_field_name].grid.fields_map[key];
				if (field.fieldtype != "Select") continue;
				
				// do something with key
				if (printDebug) console.log(__(printDebug, key + ":" ));
				values = dictionary[key];
				
				//Construire les options
				var options = [];
				
				for (i = 0; i < values.length; ++i) {
					var tuple = values[i];
					if (printDebug) console.log(__(printDebug,"key=" + tuple[0] + " : value=" + tuple[1]));
					
					options.push({
						'key': tuple[0],
						'value':  tuple[1]
					});
				}
				
				//l'assigner au field
				frappe.utils.filter_dict(cur_frm.fields_dict[child_field_name].grid.docfields, {
					"fieldname": key
				})[0].options = options;
			}
		}
    });
}

// 2016-08-29 - JDLP
// Permet d'afficher ou non les attributs configurables en fonction de "configurator_of"
// 2016-09-17 - JDLP :
//		Adaptation pour frappe V 7
// 		Isolation dans une fonction
// 2016-10-26 - JDLP :
//		Modifications majeures pour utiliser un call en pyhton
function ShowHideAttributes(printDebug, frm, cdt, cdn, reload_defaults, refresh_items) {
    if (printDebug) console.log(__(printDebug, "ShowHideAttributes*****************************"));

    //Si un code à été saisit
    if (locals[cdt][cdn] && locals[cdt][cdn].item_code) {

        var soi = locals[cdt][cdn];
        if (printDebug) console.log(__(printDebug, "soi:" + soi.item_code));
		
        // Retrouver la valeur de variant_of
        frappe.call({
            method: "frappe.client.get_value",
            args: {
                "doctype": "Item",
                "filters": {
                    "item_code": soi.item_code
                },
                "fieldname": ["variant_of"]
            },
            callback: function(res) {
                soi.variant_of = res.message.variant_of;
            }
        });
        // Retrouver la valeur de configurator_of
        frappe.call({
            method: "frappe.client.get_value",
            args: {
                "doctype": "Item",
                "filters": {
                    "item_code": soi.item_code
                },
                "fieldname": ["configurator_of"]
            },
            callback: function(res) {
                soi.configurator_of = res.message.configurator_of;
            }
        });

        if (soi.variant_of) soi.configurator_of = soi.variant_of;
        if (soi.configurator_of) soi.variant_of = soi.configurator_of;

        //Retrouver les attribut qui s'appliquent
        frappe.call({
            method: "radplusplus.radplusplus.controllers.configurator.get_required_attributes_fields",
            args: {"item_code": soi.item_code},
            callback: function(res) {
                if (printDebug) console.log(__(printDebug, "CALL BACK get_required_attributes_fields"));
                //Convertir le message en Array
                var attributes = (res.message || []);

                if (printDebug) console.log(__(printDebug, "attributes:" + attributes));
                //Pointeur sur grid
                var grid = cur_frm.fields_dict["items"].grid;

                //pour chaque field de type "show" le désactiver
                for (var j = 0; j < grid.docfields.length; j++) {
                    var field = grid.docfields[j];

                    // Si c'est un field du configurateur
					// Et qu'il n'est pas dans la liste des attributs
                    if (field.fieldtype == "Check" && field.fieldname.toLowerCase().startsWith("show"))
					{
						locals[cdt][cdn][field.fieldname] = 0;
						var field_name = field.fieldname.toLowerCase().substring(4);
						for (var k = 0; k < attributes.length; k++) {
							if (attributes[k][1] == field_name)
							{
								locals[cdt][cdn][field.fieldname] = 1;
								break;
							}
						}						
					}
                }

                //si au moins un attribut, il s'agit d'un configurateur
                locals[cdt][cdn]["has_configuration"] = attributes.length > 0;

                //Reloader les valeurs par défaut suite aux changements
                if (reload_defaults)
                    AssignDefaultValues(printDebug, frm, cdt, cdn);

                if (refresh_items)
                    refresh_field("items");

                if (printDebug) console.log(__(printDebug, "CALL BACK get_required_attributes_fields END"));
            }
        });
    }
}

// 2016-12-17 - RM
// Permet d'afficher la description formatée de l'item selon la langue du document en cours
function LoadTranslatedDescription(printDebug, frm, cdt, cdn) {
    if (printDebug) console.log(__(printDebug, "LoadTranslatedDescription*****************************"));

    //Si un code à été saisit
    if (locals[cdt][cdn] && locals[cdt][cdn].item_code) {

        var soi = locals[cdt][cdn];
        if (printDebug) console.log(__(printDebug, "cdt:" + cdt));
		if (printDebug) console.log(__(printDebug, "cdn:" + cdn));

		frappe.call({
			method: "radplusplus.radplusplus.doctype.item_language.item_language.item_description_query",
			args: {
				"doctype": cdt,
				"docname" : cdn,
				"item_code" : soi.item_code
			},
			callback: function(res) {
				if (printDebug) console.log(__(printDebug, "res.message:" + res.message));
				soi.description = res.message;
				if (printDebug) console.log(__(printDebug, "soi.description:" + soi.description));
				var grid_row = cur_frm.open_grid_row();
                grid_row.grid_form.fields_dict.description.set_value("test");

				if (printDebug) console.log(__(printDebug, "cur_frm.description:" + cur_frm.description));
				
				if (printDebug) console.log(__(printDebug, "CALL BACK item_description_query END"));
			}
        });
    }
}

// 2016-08-07 - RM
// Script fonctionnel.
// Il permet de creer un item variant lorsque le bouton create_variant est active.
// 2016-08-23 - JDLP/RM
// 2016-10-17 - JDLP - Lancer une erreur si une des attributs est à "A venir".
// 2016-10-27 - JDLP - Modifications Majeures pour utiliser la méthode get_show_attributes en python
function CreateItemVariant(printDebug, frm, cdt, cdn, validate_attributes, refresh_items) {
    if (printDebug) console.log(__(printDebug, "CreateItemVariant"));

    //Si un code à été saisit
    if (locals[cdt][cdn] && locals[cdt][cdn].item_code) {

        var soi = locals[cdt][cdn];
        if (printDebug) console.log(__(printDebug, "soi:" + soi.item_code));

        //Lancer le call
        frappe.call({
            method: "radplusplus.radplusplus.controllers.configurator.get_required_attributes_fields",
            args: {
                "item_code": soi.item_code
            },
            callback: function(res) {
                if (printDebug) console.log(__(printDebug, "CALL BACK get_required_attributes_fields"));
                //Convertir le message en Array
                var attributes = (res.message || []);
                var variantAttributes = {};

                //pour chaque attribut
                for (var j = 0; j < attributes.length; j++) {
                    if (printDebug) console.log(__(printDebug, attributes[j]));
                    var attribute_name = attributes[j][0];
                    var fieldname = attributes[j][1];

                    var currItem = soi[fieldname];
					if (currItem != undefined)
					{
						var idx = frm.cur_grid.grid_form.fields_dict[fieldname].df.idx;
						var options = frm.cur_grid.grid_form.fields[idx - 1].options;
						for (var o = 0; o < options.length; o++) {
							if (options[o].value == currItem) {
								currItem = options[o].key;
								break;
							}
						}
						if (printDebug) console.log(__(printDebug, "currItem:" + currItem));
					}
                    //Vérifier que la valeur n'est pas "A venir"
                    if (currItem == undefined || validate_attributes && currItem.toLowerCase().trim() == "à venir")
                        frappe.throw(__(printDebug, "Tous les attributs doivent être définis."));

                    //Ajouter la valuer dans la liste d'attributs								
                    variantAttributes[attribute_name] = currItem;
                }

                //Lancer la création du variant
                //Convertir la liste d'attributs en json string
                var attjson = JSON.stringify(variantAttributes);
                if (printDebug) console.log(__(printDebug, "Json:"));
                if (printDebug) console.log(__(printDebug, " :" + attjson));

                //Lancer le call
                frappe.call({
                    method: "erpnext.controllers.item_variant.create_variant_and_submit",
                    args: {
                        "template_item_code": soi.configurator_of,
                        "args": attjson
                    },
                    callback: function(res) {
                        if (printDebug) console.log(__(printDebug, "CALL create_variant_and_submit"));
                        var doclist = frappe.model.sync(res.message);
                        var variant = doclist[0];
                        var grid_row = cur_frm.open_grid_row();

                        grid_row.grid_form.fields_dict.item_code.set_value(variant.name);

                        if (printDebug) console.log(__(printDebug, "CALL BACK create_variant_and_submit END"));
                    }
                });

                if (refresh_items)
                    refresh_field("items");

                if (printDebug) console.log(__(printDebug, "CALL BACK get_show_attributes END"));
            }
        });
    }
    if (printDebug) console.log(__(printDebug, "END CreateItemVariant"));
}

// 2016-11-01 - JDLP
// Script fonctionnel.
// Il permet de reconfigurer un item variant provenant d'un configurateur.
function ReconfigurerItemVariant(printDebug, doc, cdt, cdn) {
    if (printDebug) console.log(__(printDebug, "ReconfigurerItemVariant"));
    if (printDebug) console.log(__(printDebug, "Debug mode ON"));

    //Si un code à été saisit
    if (locals[cdt][cdn] && locals[cdt][cdn].item_code) {

        var soi = locals[cdt][cdn];
        if (printDebug) console.log(__(printDebug, "soi:" + soi.item_code));

        //Lancer le call
        frappe.call({
            method: "radplusplus.radplusplus.controllers.configurator.get_item_variant_attributes_values",
            args: {
                "user_name": user,
                "item_code": soi.item_code
            },
            callback: function(res) {
                if (printDebug) console.log(__(printDebug, "CALL BACK get_item_variant_attributes_values"));
                //Convertir le message en Array
                var attributes = (res.message || []);
                var variantAttributes = {};
                var grid_row = cur_frm.open_grid_row();

                //pour chaque attribut
                for (var j = 0; j < attributes.length; j++) {
                    if (printDebug) console.log(__(printDebug, attributes[j]));
                    grid_row.grid_form.fields_dict[attributes[j][0]].set_value(attributes[j][1]);
                }

                //Assigner l'item_code du configurateur
                frappe.call({
                    method: "frappe.client.get_value",
                    args: {
                        "doctype": "Item",
                        "filters": {
                            "configurator_of": soi.variant_of
                        },
                        "fieldname": ["name"]
                    },
                    callback: function(res) {
                        soi.configurator_of = res.message.name;
                        grid_row.grid_form.fields_dict.item_code.set_value(soi.configurator_of);
                        if (printDebug) console.log(__(printDebug, "soi.configurator_of:" + soi.configurator_of));
                    }
                });

                if (printDebug) console.log(__(printDebug, "CALL BACK get_item_variant_attributes_values END"));
            }
        });
    }
    if (printDebug) console.log(__("END ReconfigurerItemVariant"));
}

////////////////////////// FIN CONFIGURATEUR //////////////////////////
//////////////////////////////////////////
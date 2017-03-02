///////////////////////////////////////////////////////////////////////
//////////////////////////// CONFIGURATEUR ////////////////////////////
///// Cette partie peut être récyclé                              /////
///// Cette partie est dependante de :                            /////
///// AssignDefaultValues(printDebug, frm, cdt, cdn)              /////



var langLoaded = false;
function RefreshLang(printDebug, frm, child_field_name) {
	if (!langLoaded) {
	// Ne pas actialiser si déjà fait
		if (frappe._messages && !langLoaded) {
			if (printDebug) console.log("RefreshLang*********************************");
			//Actualiser le dictionnaire de traduction "_messages" avec la langue de l'utilisateur
			//Cette section sera probalement enlèvé car c'est un bug dans frappe/erpnext
			//2016-12-16 - JDLP - On suppose uniquement en/fr
			frappe.call({
				method: "frappe.client.get_value",
				args: {
					"doctype": "User",
					"fieldname": ["language"],
					"limit_page_length": 9999,
					"filters": {
						"name": user
					}
				},
				callback: function(res) {
					var user_lang = res.message.language;
					if (printDebug) console.log("user_lang:" + user_lang);

					//Retrouver les translations "fr"
					frappe.call({
						method: "frappe.client.get_list",
						args: {
							"doctype": "Translation",
							"fields": ["source_name", "target_name", "language_code"],
							"limit_page_length": 9999,
							"filters": {
								"language_code": "fr"
							}
						},
						callback: function(res) {
							var rows = (res.message || []);
							if (printDebug) console.log("nb rows:" + rows.length);
							for (var i = 0; i < rows.length; i++) {
								var row = rows[i];
								var source = row.source_name;
								var target = row.target_name;
								
								//renverser le dictionnnaire si l'utilateur est en "en"
								if (user_lang == "en") {
									var tmp = target;
									target = source;
									source = tmp;
								}							
								
								if (printDebug) console.log(source + ":" + target);
								if (printDebug) console.log("before:" + frappe._messages[source]);
								frappe._messages[source] = target;
								if (printDebug) console.log("after:" + frappe._messages[source]);
								if (printDebug) console.log("-------------------------------------------");
							}
							langLoaded = true;
							LoadAttributesFieldsMapping(printDebug, frm, child_field_name);
						}
					});
				}
			});
		}
	}
	else{
		LoadAttributesFieldsMapping(printDebug, frm, child_field_name);
		
	}
}


// 2016-12-16 - JDLP
// Variable pour contenir le mapping entre les item attributes names et les fields.
var attribute_field_map = {};
var attributesFieldLoaded = false;
function LoadAttributesFieldsMapping(printDebug, frm, child_field_name){
	//if (attributesFieldLoaded) return;
	
	if (!attributesFieldLoaded){
		
		if (printDebug) console.log("LoadAttributesFieldsMapping*********************************");
		frappe.call({
			method: "frappe.client.get_list",
			args: {
				"doctype": "Item Attribute",
				"fields": ["name", "field_name"],
				"limit_page_length": 9999
			},
			callback: function(res) {
				var rows = (res.message || []);
				if (printDebug) console.log("nb rows:" + rows.length);
				for (var i = 0; i < rows.length; i++) {
					var row = rows[i];
					if (printDebug) console.log(row.name + ":" + row.field_name);
					attribute_field_map[row.name] = row.field_name;
				}
				attributesFieldLoaded = true;
				LoadAttributesValuesCallBack(printDebug, frm, child_field_name);
			}
		});
	}
	else{
		LoadAttributesValuesCallBack(printDebug, frm, child_field_name);		
	}
	
}

function __radpp(printDebug, message) {
    message = __(message);
    message = frappe._messages.hasOwnProperty(message) ? frappe._messages[message] : message;
	return message;
}

// 2016-08-18
// Script fonctionnel.
// Permet de remplir les options des champs de type sélection avec les valeurs possibles de item attribute.
// 2016-09-17 - JDLP : Adaptation pour frappe V 7
function LoadAttributesValues(printDebug, frm, child_field_name) {
    if (printDebug) console.log(__radpp(printDebug, "LoadAttributesValues**********************"));
	
	RefreshLang(printDebug, frm, child_field_name);
	

}

function LoadAttributesValuesCallBack(printDebug, frm, child_field_name) {
    if (printDebug) console.log(__radpp(printDebug, "LoadAttributesValues**********************"));
    //Obtenir les champs "parent", "attribute_value" de tous les "Item Attribute Value"
    frappe.call({
        method: "frappe.client.get_list",
        args: {
            "doctype": "Item Attribute Value",
            "fields": ["parent", "attribute_value", "Ordering", "abbr"],
            "limit_page_length": 9999,
            "order_by": "parent, Ordering, attribute_value ASC"
        },
        callback: function(res) {

            //Convertir le message en Array
            var rows = (res.message || []);
            var item_attribute_recherche = (res.message[0].parent || "");
            if (printDebug) console.log(__radpp(printDebug, "Nombre d'item attribute value :" + rows.length));
            //pour chacun des attributs
            for (var i = 0; i < rows.length; i++) {
                var row = rows[i];
                item_attribute_recherche = row.parent;
                if (printDebug) console.log(__radpp(printDebug, "item_attribute_recherche:" + item_attribute_recherche));
                
				var field_name = attribute_field_map[item_attribute_recherche];
				
				if (printDebug) console.log(__radpp(printDebug, "field_name:" + field_name));
				
				if (cur_frm.fields_dict[child_field_name].grid.fields_map[field_name]) {
					var field = cur_frm.fields_dict[child_field_name].grid.fields_map[field_name];
					if (field.fieldtype != "Select") continue;
					
					//Construire les options
					var options = [];

					//tant que prochain attribut posède le parent correspondent a item_attribute_recherche
					//récupérer les attribute_value et les placer dans la liste "options"
					//while (row.parent == rows[i + 1].parent && i + 1 < rows.length) {
					if (printDebug) console.log(__radpp(printDebug, "rows[i].parent:" + rows[i].parent));
					while (rows[i].parent == item_attribute_recherche && i + 1 < rows.length) {
						row = rows[i];
						if (printDebug) console.log("key:" + row.attribute_value);
						if (printDebug) console.log("value:" + __radpp(printDebug, row.attribute_value));
						options.push({
							'key': row.attribute_value,
							'value': __radpp(printDebug, row.attribute_value)
						});
						if (rows[i + 1].parent == item_attribute_recherche) {
							i++; //le même i que la boucle principale
						} else {
							//briser la boucle des attribute_value
							break;
						}
					}
					
					//l'assigner au field
					frappe.utils.filter_dict(cur_frm.fields_dict[child_field_name].grid.docfields, {
						"fieldname": attribute_field_map[item_attribute_recherche]
					})[0].options = options;
				}
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
    if (printDebug) console.log(__radpp(printDebug, "ShowHideAttributes*****************************"));

    //Si un code à été saisit
    if (locals[cdt][cdn] && locals[cdt][cdn].item_code) {

        var soi = locals[cdt][cdn];
        if (printDebug) console.log(__radpp(printDebug, "soi:" + soi.item_code));

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
            method: "radplusplus.radplusplus.controllers.item_variant.get_show_attributes",
            args: {
                "printDebug": printDebug,
                "item_code": soi.item_code
            },
            callback: function(res) {
                if (printDebug) console.log(__radpp(printDebug, "CALL BACK get_show_attributes"));
                //Convertir le message en Array
                var attributes = (res.message || []);

                //Pointeur sur grid
                var grid = cur_frm.fields_dict["items"].grid;

                //pour chaque field de type "show" le désactiver
                for (var j = 0; j < grid.docfields.length; j++) {
                    var field = grid.docfields[j];

                    if (field.fieldtype == "Check") {
                        if (printDebug) console.log(__radpp(printDebug,  field.fieldtype + ":" + field.fieldname));
                    }

                    // Si c'est un field du configurateur
                    if (field.fieldtype == "Check" && field.fieldname.toLowerCase().startsWith("show"))
					{
                        locals[cdt][cdn][field.fieldname] = 0;
					}
                }

                //pour chaque attribut
                for (var j = 0; j < attributes.length; j++) {
                    if (printDebug) console.log(__radpp(printDebug, attributes[j]));
					var mappingField = MappingAttributeToField(attributes[j][0]);
                    var fieldname = ("show" + mappingField);
                    if (printDebug) console.log(__radpp(printDebug, fieldname));

                    //activer le field
                    locals[cdt][cdn][fieldname] = 1;
                }

                //si au moins un attribut, il s'agit d'un configurateur
                locals[cdt][cdn]["has_configuration"] = attributes.length > 0;

                //Reloader les valeurs par défaut suite aux changements
                if (reload_defaults)
                    AssignDefaultValues(printDebug, frm, cdt, cdn);

                if (refresh_items)
                    refresh_field("items");

                if (printDebug) console.log(__radpp(printDebug, "CALL BACK get_show_attributes END"));
            }
        });
    }
}

// 2016-12-17 - RM
// Permet d'afficher la description formatée de l'item selon la langue du document en cours
function LoadTranslatedDescription(printDebug, frm, cdt, cdn) {
    if (printDebug) console.log(__radpp(printDebug, "LoadTranslatedDescription*****************************"));

    //Si un code à été saisit
    if (locals[cdt][cdn] && locals[cdt][cdn].item_code) {

        var soi = locals[cdt][cdn];
        if (printDebug) console.log(__radpp(printDebug, "cdt:" + cdt));
		if (printDebug) console.log(__radpp(printDebug, "cdn:" + cdn));

		frappe.call({
			method: "radplusplus.radplusplus.doctype.item_language.item_language.item_description_query",
			args: {
				"doctype": cdt,
				"docname" : cdn,
				"item_code" : soi.item_code
			},
			callback: function(res) {
				if (printDebug) console.log(__radpp(printDebug, "res.message:" + res.message));
				soi.description = res.message;
				if (printDebug) console.log(__radpp(printDebug, "soi.description:" + soi.description));
				var grid_row = cur_frm.open_grid_row();
                grid_row.grid_form.fields_dict.description.set_value("test");

				if (printDebug) console.log(__radpp(printDebug, "cur_frm.description:" + cur_frm.description));
				
				if (printDebug) console.log(__radpp(printDebug, "CALL BACK item_description_query END"));
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
    if (printDebug) console.log(__radpp(printDebug, "CreateItemVariant"));

    //Si un code à été saisit
    if (locals[cdt][cdn] && locals[cdt][cdn].item_code) {

        var soi = locals[cdt][cdn];
        if (printDebug) console.log(__radpp(printDebug, "soi:" + soi.item_code));

        //Lancer le call
        frappe.call({
            method: "radplusplus.radplusplus.controllers.item_variant.get_show_attributes",
            args: {
                "item_code": soi.item_code
            },
            callback: function(res) {
                if (printDebug) console.log(__radpp(printDebug, "CALL BACK get_show_attributes"));
                //Convertir le message en Array
                var attributes = (res.message || []);
                var variantAttributes = {};

                //pour chaque attribut
                for (var j = 0; j < attributes.length; j++) {
                    if (printDebug) console.log(__radpp(printDebug, attributes[j]));
                    var fieldname = MappingAttributeToField(attributes[j][0]);

                    var currItem = soi[fieldname];
                    var idx = frm.cur_grid.grid_form.fields_dict[fieldname].df.idx;
                    var options = frm.cur_grid.grid_form.fields[idx - 1].options;
                    for (var o = 0; o < options.length; o++) {
                        if (options[o].value == currItem) {
                            currItem = options[o].key;
                            break;
                        }
                    }
                    if (printDebug) console.log(__radpp(printDebug, "currItem:" + currItem));

                    //Vérifier que la valeur n'est pas "A venir"
                    if (validate_attributes && currItem.toLowerCase().trim() == "à venir")
                        frappe.throw(__radpp(printDebug, "Tous les attributs doivent être définis."));

                    //Ajouter la valuer dans la liste d'attributs								
                    variantAttributes[attributes[j][1]] = currItem;
                }

                //Lancer la création du variant
                //Convertir la liste d'attributs en json string
                var attjson = JSON.stringify(variantAttributes);
                if (printDebug) console.log(__radpp(printDebug, "Json:"));
                if (printDebug) console.log(__radpp(printDebug, " :" + attjson));

                //Lancer le call
                frappe.call({
                    method: "radplusplus.radplusplus.controllers.item_variant.create_variant_and_submit",
                    args: {
                        "template_item_code": soi.configurator_of,
                        "args": attjson
                    },
                    callback: function(res) {
                        if (printDebug) console.log(__radpp(printDebug, "CALL create_variant_and_submit"));
                        var doclist = frappe.model.sync(res.message);
                        var variant = doclist[0];
                        var grid_row = cur_frm.open_grid_row();

                        grid_row.grid_form.fields_dict.item_code.set_value(variant.name);

                        if (printDebug) console.log(__radpp(printDebug, "CALL BACK create_variant_and_submit END"));
                    }
                });

                if (refresh_items)
                    refresh_field("items");

                if (printDebug) console.log(__radpp(printDebug, "CALL BACK get_show_attributes END"));
            }
        });
    }
    if (printDebug) console.log(__radpp(printDebug, "END CreateItemVariant"));
}

// 2016-11-01 - JDLP
// Script fonctionnel.
// Il permet de reconfigurer un item variant provenant d'un configurateur.
function ReconfigurerItemVariant(printDebug, doc, cdt, cdn) {
    if (printDebug) console.log(__radpp(printDebug, "ReconfigurerItemVariant"));
    if (printDebug) console.log(__radpp(printDebug, "Debug mode ON"));

    //Si un code à été saisit
    if (locals[cdt][cdn] && locals[cdt][cdn].item_code) {

        var soi = locals[cdt][cdn];
        if (printDebug) console.log(__radpp(printDebug, "soi:" + soi.item_code));

        //Lancer le call
        frappe.call({
            method: "radplusplus.radplusplus.controllers.item_variant.get_item_variant_attributes_values",
            args: {
                "item_code": soi.item_code
            },
            callback: function(res) {
                if (printDebug) console.log(__radpp(printDebug, "CALL BACK get_item_variant_attributes_values"));
                //Convertir le message en Array
                var attributes = (res.message || []);
                var variantAttributes = {};
                var grid_row = cur_frm.open_grid_row();

                //pour chaque attribut
                for (var j = 0; j < attributes.length; j++) {
                    if (printDebug) console.log(__radpp(printDebug, attributes[j]));
                    var fieldname = MappingAttributeToField(attributes[j][0]);
                    grid_row.grid_form.fields_dict[fieldname].set_value(__radpp(printDebug, attributes[j][1]));
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
                        if (printDebug) console.log(__radpp(printDebug, "soi.configurator_of:" + soi.configurator_of));
                    }
                });

                if (printDebug) console.log(__radpp(printDebug, "CALL BACK get_item_variant_attributes_values END"));
            }
        });
    }
    if (printDebug) console.log(__radpp("END ReconfigurerItemVariant"));
}

// 2016-12-11 - JDLP
// [Fix]  Méthode pour faire le match entre un attribute name et le field du formulaire
function MappingAttributeToField(attribute_name) {
	return attribute_field_map[attribute_name];
    switch (attribute_name) {
        case "Baluster Model":
            return "baluster_model";
            break;
        case "Color":
            return "color";
            break;
	case "Oil Color":
            return "oil_color";
            break;
        case "Hardwood Construction":
            return "construction";
            break;
        case "Co^te´ droit":
            return "cote_droit";
            break;
        case "Co^te´ gauche":
            return "cote_gauche";
            break;
        case "Devant marche":
            return "devant_marche";
            break;
        case "Épaisseur marche":
            return "epaisseur_marche";
            break;
        case "Finish Type":
            return "finish_type";
            break;
        case "Finition escalier":
            return "finition_escalier";
            break;
        case "Flooring Grade":
            return "flooring_grade";
            break;
        case "Flooring Width":
            return "flooring_width";
            break;
        case "Gloss":
            return "gloss";
            break;
        case "Hand Scraped":
            return "hand_scraped";
            break;
        case "Handrail Model":
            return "handrail_model";
            break;
        case "Height of Baluster":
            return "height_of_baluster";
            break;
        case "Height of Post":
            return "height_of_post";
            break;
        case "Largeur en pouce":
            return "largeur_pouce";
            break;
        case "Length":
            return "length";
            break;
        case "Longueur marche":
            return "longueur_marche";
            break;
        case "Longueur en pied":
            return "longueur_pied";
            break;
        case "Micro-V":
            return "micro_v";
            break;
        case "Milling":
            return "milling";
            break;
        case "Mode`le contre marche":
            return "modele_contre_marche";
            break;
        case "Moulding Model":
            return "moulding_model";
            break;
        case "Packaging":
            return "packaging";
            break;
        case "Partie assise":
            return "partie_assise";
            break;
        case "Post Model":
            return "post_model";
            break;
	case "Modèle de plancher":
            return "modele_de_plancher";
            break;
        case "Profondeur marche":
            return "profondeur_marche";
            break;
        case "Essences de bois":
            return "species";
            break;
        case "Step Faces":
            return "step_faces";
            break;
        case "Flooring Thickness":
            return "thickness";
            break;
        case "Type de limon":
            return "type_limon";
            break;
        case "Wirebrushed":
            return "wirebrushed";
            break;
        case "Wood Grade":
            return "wood_grade";
            break;
        case "Wood Width":
            return "wood_width";
            break;
    }
}
////////////////////////// FIN CONFIGURATEUR //////////////////////////
//////////////////////////////////////////
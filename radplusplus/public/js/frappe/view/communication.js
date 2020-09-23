// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

frappe.views.CustomCommunicationComposer = frappe.views.CommunicationComposer.extend({
	prepare: function() {
		this.setup_subject_and_recipients();
		this.setup_print_language();
		this.setup_print();
		this.setup_attach();
		this.setup_email();
		this.setup_last_edited_communication();
		this.setup_email_template();
		
		// radpp - 2018-12-10 		
		this.dialog.fields_dict["email_template"].set_value(frappe.model.get_value("Print Format", this.dialog.fields_dict.select_print_format.get_value(), "email_template"));

		this.dialog.fields_dict.recipients.set_value(this.recipients || '');
		this.dialog.fields_dict.cc.set_value(this.cc || '');
		this.dialog.fields_dict.bcc.set_value(this.bcc || '');

		if(this.dialog.fields_dict.sender) {
			this.dialog.fields_dict.sender.set_value(this.sender || '');
		}
		this.dialog.fields_dict.subject.set_value(this.subject || '');

		this.setup_earlier_reply();	
		
		
		
	},
});

frappe.views.CommunicationComposer = frappe.views.CustomCommunicationComposer
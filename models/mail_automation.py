from odoo import fields, models, _, api
from odoo.tools.safe_eval import safe_eval


class MailAutomationConfig(models.Model):
    _name = "mail.automation.config"

    def mail_automation_trigger(self):
        active_records = self.env['mail.automation.config'].search([('activated', '=', True)])
        for automation_config in active_records:
            log_vector = []
            matching_records = self.env[automation_config.model_id.model].search(safe_eval(automation_config.domain_to_check))
            log_vector.append('AUTOMATIZACIÓN LANZADA')
            if matching_records:
                log_vector.append('Analizando ' + str(len(matching_records)) +' registros')
            else:
                log_vector.append('No se encontraron registros')
            for matching_record in matching_records:
                sending_condition = True
                matching_record_link = "<tr><td><a href='/web#id={}&view_type=form&model={}'target='_blank'>".format(matching_record.id, matching_record._name)
                matching_record_link += "<i class='fa fa-arrow-right'></i> {}".format(matching_record.display_name)
                if not automation_config.repeat:
                    if automation_config.id in matching_record.mail_automation_history_ids.mapped('config_id.id'):
                        sending_condition = False
                        matching_record_link += " | YA ENVIADO"
                else:
                    if automation_config.max_number_of_mails:
                        matching_mails = matching_record.mail_automation_history_ids.filtered(lambda x: x.config_id.id == automation_config.id) or []
                        if len(matching_mails) >= automation_config.max_number_of_mails:
                            sending_condition = False
                            matching_record_link += " | YA ENVIADO " + str(len(matching_mails)) + " veces"
                    if sending_condition and automation_config.waiting_days_since_last_mail:
                        if matching_record.mail_automation_history_ids and (fields.Date.context_today(self) - max(matching_record.mail_automation_history_ids.mapped('date'))).days < automation_config.waiting_days_since_last_mail:
                            matching_record_link += " | ESPERANDO REENVIO"
                            sending_condition = False
                if sending_condition and automation_config.additional_python_condition_function:
                    sending_condition = eval(automation_config.additional_python_condition_function)
                if sending_condition:
                    matching_record.send_mail_automation(automation_config)
                    matching_record_link += " | ENVIO LANZADO"
                matching_record_link += "</a></td></tr>"
                log_vector.append(matching_record_link)
                automation_log = {
                    'text': '\n'.join(log_vector),
                    'config_id': automation_config.id,
                }
                self.env['mail.automation.log'].create(automation_log)




    name = fields.Char(string="Name", required=True)
    model_id = fields.Many2one('ir.model')
    model_name = fields.Char(related='model_id.model')
    domain_to_check = fields.Char()
    repeat = fields.Boolean()
    waiting_days_since_last_mail = fields.Float()
    max_number_of_mails = fields.Float()
    model_user_fields_id = fields.Many2one('ir.model.fields')
    user_if_not_found_id = fields.Many2one('res.users')

    template_id = fields.Many2many('mail.template')
    activated = fields.Boolean(default=True)
    log_history_ids = fields.One2many('mail.automation.log', 'config_id')
    write_data = fields.Char()
    additional_python_condition_function = fields.Text()


class MailAutomationLog(models.Model):
    _name = "mail.automation.log"

    text = fields.Html()
    config_id = fields.Many2one('mail.automation.config')

class MailAutomationHistory(models.Model):
    _name = "mail.automation.history"

    date = fields.Date()
    config_id = fields.Many2one('mail.automation.config')
    partner_ids = fields.Many2many(comodel_name='res.partner')
    res_model = fields.Char()
    res_id = fields.Float()


class MailAutomationMixin(models.AbstractModel):
    _name = 'mail.automation.mixing'

    mail_automation_history_ids = fields.Many2many(comodel_name='mail.automation.history')

    def send_mail_automation(self, config_id):
        user = False
        if config_id.model_user_fields_id:
            user = eval("self." + config_id.model_user_fields_id.name)
        if not user:
            user = config_id.user_if_not_found_id or self.env.user
        for template in config_id.template_id:
            self.with_context(force_send=True).with_user(user).message_post_with_template(template.id,
                                                                          email_layout_xmlid='mail.mail_notification_light')
        if config_id.write_data:
            vals_to_write = safe_eval(config_id.write_data)
        else:
            vals_to_write = {}
        vals_to_write['mail_automation_history_ids'] = [(0, 0, {
            'date': fields.Date.context_today(self),
            'config_id': config_id.id,
            'res_model': self._name,
            'res_id': self.id,
                                                        })]
        self.write(vals_to_write)
        return False


class CrmLead(models.Model, MailAutomationMixin):
    _inherit = 'crm.lead'


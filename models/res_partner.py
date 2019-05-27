# coding=utf-8
import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class res_partner(models.Model):
    _inherit = 'res.partner'

    wxcorp_user_id = fields.Many2one('wx.corpuser', '关联企业号用户')
    wx_opendid = fields.Many2one('wx.user', string='微信公众用户', help="微信公众")

    def send_corp_text(self, text):
        msg = {
            "mtype": "text",
            "content": text,
        }
        self.env['wx.corpuser'].send_messagebypartner(partner=self, msg=text)

    @api.multi
    def send_partner_corp_text(self):
        self.ensure_one()

        new_context = dict(self._context) or {}
        new_context['default_model'] = 'res.partner'
        new_context['default_method'] = 'send_corp_text'
        new_context['record_ids'] = self.id
        return {
            'name': u'发送企业微信消息',
            'type': 'ir.actions.act_window',
            'res_model': 'wx.confirm',
            'res_id': None,
            'view_mode': 'form',
            'view_type': 'form',
            'context': new_context,
            'view_id': self.env.ref('wx_tools.wx_partner_crop_view_form_send').id,
            'target': 'new'
        }

    def send_template_message(self, data):
        msg = {
            "mtype": "text",
            "content": data,
        }
        #self.env['wx.corpuser'].send_messagebypartner(partner=self, msg=text)

    @api.multi
    def send_partner_wx_template(self):
        self.ensure_one()
        new_context = dict(self._context) or {}
        new_context['default_model'] = 'res.partner'
        new_context['default_method'] = 'send_template_message'
        new_context['record_ids'] = self.id
        return {
            'name': u'公众号模板消息',
            'type': 'ir.actions.act_window',
            'res_model': 'wx.confirm',
            'res_id': None,
            'view_mode': 'form',
            'view_type': 'form',
            'context': new_context,
            'view_id': self.env.ref('wx_tools.wx_partner_wx_template').id,
            'target': 'new'
        }


    def send_wx_text(self, text):
        msg = {
            "mtype": "text",
            "content": text,
        }
        self.env['wx.user'].send_messagebypartner(partner=self, msg=text)

    @api.multi
    def send_partner_wx_text(self):
        self.ensure_one()

        new_context = dict(self._context) or {}
        new_context['default_model'] = 'res.partner'
        new_context['default_method'] = 'send_wx_text'
        new_context['record_ids'] = self.id
        return {
            'name': u'发送微信消息',
            'type': 'ir.actions.act_window',
            'res_model': 'wx.confirm',
            'res_id': None,
            'view_mode': 'form',
            'view_type': 'form',
            'context': new_context,
            'view_id': self.env.ref('wx_tools.wx_partner_wx_view_form_send').id,
            'target': 'new'
        }

    def send_chat(self, data):
        msg = {
            "mtype": "text",
            "content": data,
        }

    def send_partner_corp_card(self):
        self.ensure_one()

        new_context = dict(self._context) or {}
        new_context['default_model'] = 'res.partner'
        new_context['default_method'] = 'send_chat'
        new_context['record_ids'] = self.id
        return {
            'name': u'发业卡片消息',
            'type': 'ir.actions.act_window',
            'res_model': 'wx.confirm',
            'res_id': None,
            'view_mode': 'form',
            'view_type': 'form',
            'context': new_context,
            'view_id': self.env.ref('wx_tools.wx_partner_wx_chat').id,
            'target': 'new'
        }



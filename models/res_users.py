# -*-coding:utf-8-*-
import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class WxResUsers(models.Model):
    _inherit = 'res.users'
    wxcorp_user_id = fields.Many2one('wx.corpuser', '关联企业号用户')
    wx_opendid = fields.Many2one('wx.user', string='微信公众用户', help="微信公众")

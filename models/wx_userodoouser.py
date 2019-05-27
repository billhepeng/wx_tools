# -*-coding:utf-8-*-
from odoo import models, fields, api


class WxUserOdooUser(models.Model):
    _name = 'wx.user.odoouser'
    _description = u'微信用户关联Odoo用户'
    open_id = fields.Char('微信ID')  # 微信UUID
    user_id = fields.Many2one('res.users', readonly=False)  # 用户ID
    password = fields.Char('密码', size=32, required=False)  # 密码
    DeviceId = fields.Char('设备ID')  # 设备ID
    codetype = fields.Char('登录类型')  # 设备ID

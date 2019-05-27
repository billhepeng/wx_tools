# -*-coding:utf-8-*-
from odoo import models, fields, api


class WxPaConfig(models.Model):
    _name = 'wx.paraconfig'
    _description = u'微信参数配置'
    paraconfig_name = fields.Text('配置名称')
    paraconfig_value = fields.Text('配置值')
    paraconfig_remark = fields.Text('备注')


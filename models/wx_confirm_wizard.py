# coding=utf-8
import json
from odoo import models, fields, api


class WxConfirm(models.TransientModel):

    _name = 'wx.confirm'
    _description = u'确认'

    info = fields.Text("信息")
    model = fields.Char('模型')
    method = fields.Char('方法')
    template_id = fields.Char('模板ID')
    data = fields.Text('类容')
    url = fields.Char('URL')

    title = fields.Char('标题')



    api.multi
    def execute(self):
        self.ensure_one()
        active_ids = self._context.get('record_ids')
        rs = self.env[self.model].browse(active_ids)
        ret = getattr(rs, self.method)()
        return ret

    api.multi
    def execute_with_info(self):
        self.ensure_one()
        active_ids = self._context.get('record_ids')
        rs = self.env[self.model].browse(active_ids)
        ret = getattr(rs, self.method)(self.info)

        return ret

    api.multi

    def execute_with_chat(self):
        self.ensure_one()
        active_ids = self._context.get('record_ids')
        rs = self.env[self.model].browse(active_ids)
        ret = getattr(rs, self.method)(self.data)
        self.env['wx.corpuser'].send_text_card(self.title, self.data, self.url, partner=rs)
        return ret

    def execute_with_usermodel(self):
        self.ensure_one()
        active_ids = self._context.get('record_ids')
        rs = self.env[self.model].browse(active_ids)
        ret = getattr(rs, self.method)(self.data)
        data = {
            "first": {
                "value": "销售订单",
                "color": "#173177"
            },
            "keyword1": {
                "value": "date_ref",
                "color": "#173177"
            },
            "keyword2": {
                "value": "订单号:",
                "color": "#173177"
            },
            "keyword3": {
                "value": "时间:",
                "color": "#173177"
            },
            "remark": {
                "value": "联系:",
                "color": "#173177"
            }
        }
        self.env['wx.user'].send_partnertemplate_message(self.template_id, json.loads(self.data), self.url, partner=rs)
        return ret

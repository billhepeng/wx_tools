# -*-coding:utf-8-*-
import logging
from odoo.exceptions import ValidationError, UserError
from datetime import datetime
from odoo import api, models
from ..rpc import corp_client
from ..controllers import client

_logger = logging.getLogger(__name__)


class WXAccountInvoice(models.AbstractModel):
    _inherit = "account.invoice"

    @api.multi
    def action_invoice_open(self):
        res = super(WXAccountInvoice, self).action_invoice_open()
        for order in self:
            title = '订单发票'
            date_ref = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            data_body = "发票:" + order.number
            description = "<div class=\"gray\">" + date_ref + "</div> <div class=\"normal\">" + data_body + "</div>" \
                          "\n<div class=\"highlight\"> 时间:" + order.date_invoice + ""\
                          "\n 金额:%f" % order.amount_total + ""\
                          "\n Tax:%f" % order.amount_tax + ""\
                          "\n 联系:" + order.create_uid.name + "(" + order.create_uid.email + ")</div>"
            if self.partner_id.wxcorp_user_id.userid:
                url = corp_client.corpenv(self.env).server_url+'/web/login?usercode=saleorder&codetype=corp&redirect=' + order.portal_url
                url = corp_client.authorize_url(self, url, 'saleorderinvoice')
                corp_client.send_text_card(self, order.partner_id.wxcorp_user_id.userid, title, description, url, "详情")

            if self.partner_id.wx_opendid.openid:
                data = {
                    "first": {
                        "value": '你收到了一张新发票',
                        "color": "#173177"
                    },
                    "keyword1": {
                        "value": '已审核',
                        "color": "#173177"
                    },
                    "keyword2": {
                        "value": "订单号:" + order.name,
                        "color": "#173177"
                    },
                    "keyword3": {
                        "value": order.amount_total
                    },
                    "keyword4": {
                        "value": order.date_invoice
                    },
                    "remark": {
                        "value": "联系:" + order.create_uid.name + "(" + order.create_uid.email + ")"
                    }
                }
                template_id = 'xdZchgSs4JoTpu8vOl8VW-7aBF8N3zwTCe8xOtWqsIQ'
                url = client.wxenv(self.env).server_url+'/web/login?usercode=saleorder&codetype=wx&redirect=' + order.portal_url
                client.send_template_message(self, self.partner_id.wx_opendid.openid, template_id, data, url,
                                             'saleorderinvoice')
            logging.info("order")
        return res

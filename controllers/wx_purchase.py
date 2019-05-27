# -*-coding:utf-8-*-
import logging
from odoo.exceptions import ValidationError, UserError
from datetime import datetime
from odoo import api, models
from ..rpc import corp_client
from ..controllers import client

_logger = logging.getLogger(__name__)


class WXPurchase(models.AbstractModel):
    _inherit = 'purchase.order'

    @api.multi
    def button_confirm(self):
        res = super(WXPurchase, self).button_confirm()
        for order in self:
            _logger.info(order)
            title = '采购订单'
            date_ref = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            data_body = "订单号:" + order.name
            description = "<div class=\"gray\">" + date_ref + "</div> <div class=\"normal\">" + data_body + "</div>" \
                          "<div class=\"highlight\">" + \
                          "时间:" + order.date_order + \
                          "\n联系:" + order.create_uid.name + "(" + order.create_uid.email + ")</div>"
            if order.partner_id.wxcorp_user_id.userid:
                url = corp_client.corpenv(
                    self.env).server_url + '/web/login?usercode=purchaseorder&codetype=corp&redirect=' + order.website_url
                url = corp_client.authorize_url(self, url, 'purchaseorder')
                corp_client.send_text_card(self, self.partner_id.wxcorp_user_id.userid, title, description, url, "详情")
            if order.partner_id.wx_opendid.openid:
                data = {
                    "first": {
                        "value": "您收到一张新的采购订单:",
                        "color": "#173177"
                    },
                    "keyword1": {
                        "value": order.name
                    },
                    "keyword2": {
                        "value": order.create_uid.name
                    }, "keyword3": {
                        "value": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    },
                    "remark": {
                        "value": "产品:" + order.product_id.display_name +
                                 "\n联系:" + order.create_uid.name,
                    }
                }
                template_id = 'nVJP4GzyfDtHp1pssoW1hq8ajY975xi8qFGoOdaEVbw'
                url = client.wxenv(
                    self.env).server_url + '/web/login?usercode=saleorder&codetype=wx&redirect=' + order.website_url
                client.send_template_message(self, self.partner_id.wx_opendid.openid, template_id, data, url,
                                             'saleorder')
        return res

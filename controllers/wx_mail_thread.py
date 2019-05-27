# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
from odoo.exceptions import ValidationError, UserError
from datetime import datetime
from odoo import api, models
from ..rpc import corp_client
from ..controllers import client

_logger = logging.getLogger(__name__)


class WXMailThread(models.AbstractModel):
    _inherit = 'mail.thread'
    @api.multi
    @api.returns('self', lambda value: value.id)
    def message_post(self, body='', subject=None, message_type='notification', subtype=None, parent_id=False, attachments=None, content_subtype='html', **kwargs):
        weixin_id = kwargs.get('weixin_id')
        message = super(WXMailThread, self).message_post(body=body, subject=subject, message_type=message_type, subtype=subtype, parent_id=parent_id, attachments=attachments, content_subtype=content_subtype, **kwargs)
        if not weixin_id:  # 不是发自来原微信的信息
            if hasattr(self,"anonymous_name"):  #self.anonymous_name:
                objs = self.env['wx.corpuser'].sudo().search([('userid', '=', self.anonymous_name)])
                if objs:  #企业微信
                    _logger.info("wx.corpuser")
                    corp_client.send_message(self, self.anonymous_name, body)
                objs = self.env['wx.user'].sudo().search([('last_uuid', '=',  self.uuid)])
                if objs:  # 公众号服务号
                    _logger.info("wx.user")
                    from ..controllers import client
                    from werobot.client import ClientException
                    entry = client.wxenv(self.env)
                    client = entry
                    try:
                        client.send_text(objs.openid, body)
                    except ClientException as e:
                        _logger.info(u'微信消息发送失败 %s' % e)
            for user in message.channel_ids.channel_partner_ids.ids:  #消息发送来于chat
                _logger.info(user)
                if message.author_id.id == user:
                    continue
                partner = self.env['res.partner'].sudo().browse(user)
                if partner:
                    partner_weixin_id = partner.wxcorp_user_id.weixinid
                    if partner.wxcorp_user_id.weixinid and body:
                        corp_client.send_message(self, partner_weixin_id, body)
                _logger.info(partner)
                #self.ids   self.im_status  'offline'
            if hasattr(self, "wxcorp_user_id") and self.wxcorp_user_id.userid:
                corp_client.send_message(self, self.wxcorp_user_id.userid, body)
        if message.model == 'sale.order' and body:
            _logger.info('sale.order')
            for order in self:
                if order.state == 'draft':
                    continue
                to_wxid = None
                if message.author_id.id == self.partner_id.id:
                    to_wxid = order.create_uid  #消息的作者是订单的供应商
                else:
                    to_wxid = self.partner_id
                title = '订单提醒'
                date_ref = "收到新信息:" + body
                data_body = "订单号:" + order.name
                description = "<div class=\"gray\">" + date_ref + "</div> " \
                              "<div class=\"normal\">" + data_body + "</div>" \
                              "<div class=\"highlight\">" + \
                              "时间:" + order.date_order + \
                              "\n联系:" + message.author_id.name + "</div>"
                if to_wxid.wxcorp_user_id.userid:
                    url = corp_client.corpenv(
                        self.env).server_url + '/web/login?usercode=saleorder&codetype=corp&redirect=' + order.portal_url
                    url = corp_client.authorize_url(self, url, 'saleorder')
                    corp_client.send_text_card(self, to_wxid.wxcorp_user_id.userid, title, description, url, "详情")
                if to_wxid.wx_opendid.openid:
                    data = {
                        "first": {
                            "value": "收到新信息:" + body,
                            "color": "#173177"
                        },
                        "keyword1": {
                            "value": order.name
                        },
                        "keyword2": {
                            "value": message.author_id.name
                        }, "keyword3": {
                            "value":  datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                           # "color": "#173177"
                        },
                        "remark": {
                            "value": "产品:" + order.product_id.display_name
                        }
                    }

                    template_id = 'nVJP4GzyfDtHp1pssoW1hq8ajY975xi8qFGoOdaEVbw'
                    from ..controllers import client
                    url = client.wxenv(
                        self.env).server_url + '/web/login?usercode=saleorder&codetype=wx&redirect=' + order.portal_url
                    client.send_template_message(self, to_wxid.wx_opendid.openid, template_id, data, url,
                                                 'saleorder')
        if message.model == 'purchase.order' and body:
            _logger.info('purchase.order')
            for order in self:
                if order.state == 'draft':
                    continue
                to_wxid = None
                if message.author_id.id == self.partner_id.id:
                    to_wxid = order.create_uid  # 消息的作者是订单的供应商
                else:
                    to_wxid = self.partner_id
                title = '采购订单提醒'
                date_ref = "收到采购订单新信息:" + body
                data_body = "订单号:" + order.name
                description = "<div class=\"gray\">" + date_ref + "</div> " \
                                                                  "<div class=\"normal\">" + data_body + "</div>" \
                                                                  "<div class=\"highlight\">" + \
                              "时间:" + order.date_order + \
                              "\n联系:" + message.author_id.name + "</div>"
                if order.partner_id.wxcorp_user_id.userid:
                    url = corp_client.corpenv(
                        self.env).server_url + '/web/login?usercode=purchaseorder&codetype=corp&redirect=' + order.website_url
                    url = corp_client.authorize_url(self, url, 'saleorder')
                    corp_client.send_text_card(self, self.partner_id.wxcorp_user_id.userid, title, description,
                                               url, "详情")
                if order.partner_id.wx_opendid.openid:
                    data = {
                        "first": {
                            "value": "收到采购订单新信息:" + body,
                            "color": "#173177"
                        },
                        "keyword1": {
                            "value": order.name
                        },
                        "keyword2": {
                            "value":  message.author_id.name
                        }, "keyword3": {
                            "value": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        },
                        "remark": {
                            "value": "产品:" + order.product_id.display_name
                        }
                    }

                    template_id = 'nVJP4GzyfDtHp1pssoW1hq8ajY975xi8qFGoOdaEVbw'
                    from ..controllers import client
                    url = client.wxenv(
                        self.env).server_url + '/web/login?usercode=purchaseorder&codetype=wx&redirect=' + order.website_url
                    client.send_template_message(self, self.partner_id.wx_opendid.openid, template_id, data,
                                                 url,
                                                 'saleorder')
        return message

#-*-coding:utf-8-*-
import logging

from odoo import models, fields, api
from ..controllers import client
from odoo.http import request
from odoo.exceptions import ValidationError, UserError
from ..rpc import corp_client
_logger = logging.getLogger(__name__)


class wx_user(models.Model):
    _name = 'wx.user'
    _description = u'公众号用户'

    nickname = fields.Char(u'昵称', required=True)
    openid = fields.Char(u'用户标志', required=True)
    city = fields.Char(u'城市', )
    country = fields.Char(u'国家', )
    group_id = fields.Selection('_get_groups', string=u'所属组', default='0')
    headimgurl = fields.Char(u'头像', )
    province = fields.Char(u'省份', )
    sex = fields.Selection([(1,u'男'),(2,u'女')], string=u'性别', )
    subscribe = fields.Boolean(u'关注状态', )
    subscribe_time = fields.Char(u'关注时间', )

    headimg= fields.Html(compute='_get_headimg', string=u'头像')
    last_uuid = fields.Char('会话ID')
    _sql_constraints = [
        ('openid_key', 'UNIQUE (openid)', '用户已存在 !')
    ]

    @api.multi
    def name_get(self):
        res = []
        for obj in self:
            return [(obj.id, obj.nickname) for obj in self]

    @api.model
    def sync(self):
        from ..controllers import client
        entry = client.wxenv(self.env)
        client = entry
        next_openid = 'init'
        c_total = 0
        c_flag = 0
        g_flag = True
        objs = self.env['wx.user.group'].search([])
        group_list = [ e.group_id for e in objs]
        while next_openid:
            if next_openid=='init':next_openid = None
            from werobot.client import ClientException
            try:
                followers_dict= client.wxclient.get_followers(next_openid)
            except ClientException as e:
                raise ValidationError(u'微信服务请求异常，异常信息: %s'%e)
            c_total = followers_dict['total']
            m_count = followers_dict['count']
            next_openid = followers_dict['next_openid']
            _logger.info('get %s users'%m_count)
            if next_openid:
                m_openids = followers_dict['data']['openid']
                for openid in m_openids:
                    c_flag +=1
                    _logger.info('total %s users, now sync the %srd %s .'%(c_total, c_flag, openid))
                    rs = self.search( [('openid', '=', openid)] )
                    if rs.exists():
                        info = client.wxclient.get_user_info(openid)
                        info['group_id'] = str(info['groupid'])
                        if g_flag and info['group_id'] not in group_list:
                            self.env['wx.user.group'].sync()
                            g_flag = False
                        rs.write(info)
                    else:
                        info = client.wxclient.get_user_info(openid)
                        info['group_id'] = str(info['groupid'])
                        if g_flag and info['group_id'] not in group_list:
                            self.env['wx.user.group'].sync()
                            g_flag = False
                        self.create(info)

        _logger.info('sync total: %s'%c_total)

    @api.model
    def sync_confirm(self):
        from ..controllers import client
        #client.create_menu(self)
        new_context = dict(self._context) or {}
        new_context['default_info'] = "此操作可能需要一定时间，确认同步吗？"
        new_context['default_model'] = 'wx.user'
        new_context['default_method'] = 'sync'
        #new_context['record_ids'] = self.id
        return {
            'name': u'确认同步公众号用户',
            'type': 'ir.actions.act_window',
            'res_model': 'wx.confirm',
            'res_id': None,
            'view_mode': 'form',
            'view_type': 'form',
            'context': new_context,
            'view_id': self.env.ref('wx_tools.wx_confirm_view_form').id,
            'target': 'new'
        }

    @api.one
    def _get_headimg(self):
        self.headimg= '<img src=%s width="100px" height="100px" />'%(self.headimgurl or '/web/static/src/img/placeholder.png')

    #@api.one
    def _get_groups(self):
        Group = self.env['wx.user.group']
        objs = Group.search([])
        return [(str(e.group_id), e.group_name) for e in objs] or [('0','默认组')]

    @api.multi
    def send_text(self, text):
        from werobot.client import ClientException
        from ..controllers import client
        entry = client.wxenv(self.env)
        client = entry
        for obj in self:
            try:
                client.send_text(obj.openid, text)
            except ClientException as e:
                _logger.info(u'微信消息发送失败 %s'%e)
                raise UserError(u'发送失败 %s'%e)

    # ------------------------------------------------------
    # 发送微信公众号文本消息
    # partner: 供应商对象，如果传入供应商换到供应商对象的openid发送
    # msg: 消息文本
    # user：用户对象 如果传入用户1：找到用户的微信关联账号发送，2：如果没找到1，找到供应商关联的合作伙伴的微信发送
    # partner_id：供应商ID 根据ID找到供应商的微信
    # user_id：用户ID，根据用户ID查找用户 1：找到用户的微信关联账号发送，2：如果没找到1，找到供应商关联的合作伙伴的微信发送
    # ------------------------------------------------------
    @api.multi
    def send_message(self, partner=None, msg='', user=None, partner_id=None, user_id=None):
        from ..controllers import client
        if partner:
            if partner.wx_opendid.openid:
                client.send_text(self, partner.wx_opendid.openid, msg)
            else:
                raise UserError(u'发送失败,客户没有绑定微信')
        if user:
            if user.wx_opendid.openid:
                client.send_text(self, user.wx_opendid.openid, msg)
            elif user.partner_id.wx_opendid.openid:
                client.send_text(self,  user.partner_id.wx_opendid.openid, msg)
            else:
                raise UserError(u'发送失败,客户没有绑定微信')
        if partner_id:
            partner_ = self.env['res.partner'].sudo().browse(partner_id)
            self.send_message(partner=partner_,msg=msg)
        if user_id:
            user_ = self.env['res.users'].sudo().browse(user_id)
            self.send_message(user=user_, msg=msg)

    # ------------------------------------------------------
    # 发送微信公众号模板信息
    # template_id :模板ID，可以在公众号模板中查询   如:nVJP4GzyfDtHp1pssoW1hq8ajY975xi8qFGoOdaEVbw
    # data:模板数据Jsono类型  如下格式:
    #      模板格式：https://mp.weixin.qq.com/wiki?t=resource/res_main&id=mp1433751277
    #            {{first.DATA}}
    #            订单号：{{keyword1.DATA}}
    #            操作人：{{keyword2.DATA}}
    #            时间：{{keyword3.DATA}}
    #            {{remark.DATA}}
    #       模板数据:
    #         {
    #             "first": {
    #                 "value": "你有一张销售订单"
    #             },
    #             "keyword1": {
    #                 "value": "S0001"
    #             },
    #             "keyword2": {
    #                 "value": "何鹏"
    #             },
    #             "keyword3": {
    #                 "value": "20190529"
    #             },
    #             "remark": {
    #                 "value": "联系:hepeng1@163.com"
    #             }
    #         }
    # url:模板连接到的URL 如：http://weixintools.pub.heyanze.com/web/login?usercode=saleorder&codetype=wx&redirect=/my/orders/24
    #     URL解析： usercode:访问URL类型用户于定义是那个业务单元  codetype:(wx=微信公众号 crop=企业号)  redirect:转向内部URL
    # partner: 供应商对象，如果传入供应商换到供应商对象的openid发送
    # user：用户对象 如果传入用户1：找到用户的微信关联账号发送，2：如果没找到1，找到供应商关联的合作伙伴的微信发送
    # partner_id：供应商ID 根据ID找到供应商的微信
    # user_id：用户ID，根据用户ID查找用户 1：找到用户的微信关联账号发送，2：如果没找到1，找到供应商关联的合作伙伴的微信发送
    # ------------------------------------------------------
    @api.multi
    def send_template_message(self, template_id, data, url='', partner=None,user=None, partner_id=None, user_id=None):
        from ..controllers import client
        if partner:
            if partner.wx_opendid.openid:
                client.send_template_message(self, partner.wx_opendid.openid, template_id, data, url)
            else:
                raise UserError(u'发送失败,客户没有绑定微信')
        if user:
            if user.wx_opendid.openid:
                client.send_template_message(self, user.wx_opendid.openid, template_id, data, url)
            elif user.partner_id.wx_opendid.openid:
                client.send_template_message(self, user.partner_id.wx_opendid.openid, template_id, data, url)
            else:
                raise UserError(u'发送失败,客户没有绑定微信')
        if partner_id:
            partner_ = self.env['res.partner'].sudo().browse(partner_id)
            self.send_template_message(template_id, data, url, partner=partner_)
        if user_id:
            user_ = self.env['res.users'].sudo().browse(user_id)
            self.send_template_message(template_id, data, url, user=user_)

    @api.multi
    def send_text_confirm(self):
        self.ensure_one()

        new_context = dict(self._context) or {}
        new_context['default_model'] = 'wx.user'
        new_context['default_method'] = 'send_text'
        new_context['record_ids'] = self.id
        return {
            'name': u'发送微信消息',
            'type': 'ir.actions.act_window',
            'res_model': 'wx.confirm',
            'res_id': None,
            'view_mode': 'form',
            'view_type': 'form',
            'context': new_context,
            'view_id': self.env.ref('wx_tools.wx_confirm_view_form_send').id,
            'target': 'new'
        }







class wx_user_group(models.Model):
    _name = 'wx.user.group'
    _description = u'公众号用户组'

    count = fields.Integer(u'用户数', )
    group_id = fields.Integer(u'组编号', )
    group_name = fields.Char(u'组名', )
    user_ids = fields.One2many('wx.user', 'group_id', u'用户', )


    @api.model
    def sync(self):
        from ..controllers import client
        entry = client.wxenv(self.env)
        client = entry
        from werobot.client import ClientException
        try:
            groups =  client.wxclient.get_groups()
        except ClientException as e:
            raise ValidationError(u'微信服务请求异常，异常信息: %s'%e)
        for group in groups['groups']:
            rs = self.search( [('group_id', '=', group['id']) ] )
            if rs.exists():
                rs.write({
                             'group_name': group['name'],
                             'count': group['count'],
                             })
            else:
                self.create({
                             'group_id': str(group['id']),
                             'group_name': group['name'],
                             'count': group['count'],
                             })

    @api.model
    def sync_confirm(self):
        new_context = dict(self._context) or {}
        new_context['default_info'] = "此操作可能需要一定时间，确认同步吗？"
        new_context['default_model'] = 'wx.user.group'
        new_context['default_method'] = 'sync'
        #new_context['record_ids'] = self.id
        return {
            'name': u'确认同步公众号用户组',
            'type': 'ir.actions.act_window',
            'res_model': 'wx.confirm',
            'res_id': None,
            'view_mode': 'form',
            'view_type': 'form',
            'context': new_context,
            'view_id': self.env.ref('wx_tools.wx_confirm_view_form').id,
            'target': 'new'
        }

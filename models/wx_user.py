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

    @api.multi
    def send_messagebypartner(self, partner=None, msg=''):
        if partner:
            if partner.wxcorp_user_id.userid:
                from ..controllers import client
                client.send_text(self, partner.wx_opendid.openid, msg)
            else:
                raise UserError(u'发送失败,客户没有绑定微信')

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

    @api.multi
    def send_partnertemplate_message(self, template_id, data, url='', partner=None):
        if partner:
            if partner.wx_opendid.openid:
                from ..controllers import client
                client.send_template_message(self, partner.wx_opendid.openid, template_id, data, url)
            else:
                raise UserError(u'发送失败,客户没有绑定微信')





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

# coding=utf-8

import logging

from odoo import models, fields, api
from ..controllers import client
from odoo.http import request
from odoo.exceptions import ValidationError, UserError
from ..rpc import corp_client


_logger = logging.getLogger(__name__)


class wx_corpuser(models.Model):
    _name = 'wx.corpuser'
    _description = u'企业号用户'

    name = fields.Char('昵称', required=True)
    userid = fields.Char('账号', required=True)
    avatar = fields.Char('头像', )
    position = fields.Char('职位', )
    gender = fields.Selection([(1,'男'),(2,'女')], string='性别', )
    weixinid = fields.Char('微信号', )
    mobile = fields.Char('手机号',)
    email = fields.Char('邮箱',)
    status = fields.Selection([(1,'已关注'),(2,'已禁用'),(4,'未关注')], string='状态', default=4)
    extattr = fields.Char('扩展属性', )

    avatarimg = fields.Html(compute='_get_avatarimg', string=u'头像')
    last_uuid = fields.Char('会话ID')

    _sql_constraints = [
        ('userid_key', 'UNIQUE (userid)',  '账号已存在 !'),
        ('weixinid_key', 'UNIQUE (weixinid)',  '微信号已存在 !'),
        ('email_key', 'UNIQUE (email)',  '邮箱已存在 !'),
        ('mobile_key', 'UNIQUE (mobile)',  '手机号已存在 !')
    ]

    @api.multi
    def name_get(self):
        res = []
        for obj in self:
            return [(obj.id, obj.name + ":" + obj.mobile) for obj in self]

    @api.one
    def _get_avatarimg(self):
        self.avatarimg= '<img src=%s width="100px" height="100px" />'%(self.avatar or '/web/static/src/img/placeholder.png')

    @api.model
    def create(self, values):
        _logger.info('wx.corpuser create >>> %s'%str(values))
        if values.get('email', '') == '':
            values.pop('email')
        if not (values.get('weixinid', '') or  values.get('mobile', '') or values.get('email', '') ):
            raise ValidationError('手机号、邮箱、微信号三者不能同时为空')
        from_subscribe = False
        if '_from_subscribe' in values:
            from_subscribe = True
            values.pop('_from_subscribe')
        obj = super(wx_corpuser, self).create(values)
        if not from_subscribe:
            arg = {}
            for k,v in values.items():
                if v!=False and k in ['mobile', 'email', 'weixinid', 'gender']:
                    arg[k] = v
            arg['department'] = 1
            if 'weixinid' in arg:
                arg['weixin_id'] = arg.pop('weixinid')
            from wechatpy.exceptions import WeChatClientException
            try:
                entry = corp_client.corpenv(self.env)
                entry.txl_client.user.create(values['userid'], values['name'], **arg)
            except WeChatClientException as e:
                raise ValidationError(u'微信服务请求异常，异常码: %s 异常信息: %s'%(e.errcode, e.errmsg))
        return obj

    @api.multi
    def write(self, values):
        _logger.info('wx.corpuser write >>> %s %s'%( str(self),str(values) ) )
        objs = super(wx_corpuser, self).write(values)
        arg = {}
        for k,v in values.items():
            if v!=False and k in ['mobile', 'email', 'weixinid', 'gender', 'name']:
                arg[k] = v
        for obj in self:
            if not (obj.weixinid or obj.mobile or obj.email):
                raise ValidationError('手机号、邮箱、微信号三者不能同时为空')
            from wechatpy.exceptions import WeChatClientException
            try:
                entry = corp_client.corpenv(self.env)
                entry.txl_client.user.update(obj.userid, **arg)
            except WeChatClientException as e:
                raise ValidationError(u'微信服务请求异常，异常码: %s 异常信息: %s'%(e.errcode, e.errmsg))
        return objs

    @api.multi
    def unlink(self):
        _logger.info('wx.corpuser unlink >>> %s'%str(self))
        for obj in self:
            try:
                entry = corp_client.corpenv(self.env)
                entry.txl_client.user.delete(obj.userid)
            except:
                pass
        ret = super(wx_corpuser, self).unlink()
        return ret

    @api.model
    def create_from_res_users(self):
        objs = self.env['res.users'].search([])
        for obj in objs:
            _partner = obj.partner_id
            if _partner.mobile or _partner.email:
                flag1 = False
                if _partner.mobile:
                    flag1 = self.search( [ ('mobile', '=', _partner.mobile) ] ).exists()
                flag2 = False
                if _partner.email:
                    flag2 = self.search( [ ('email', '=', _partner.email) ] ).exists()
                flag3 = self.search( [ ('userid', '=', obj.login) ] ).exists()
                if not (flag1 or flag2 or flag3):
                    try:
                        ret = self.create({
                                     'name': obj.name,
                                     'userid': obj.login,
                                     'mobile': _partner.mobile,
                                     'email': _partner.email
                                     })
                        _partner.write({'wxcorp_user_id': ret.id})
                    except:
                        pass

    @api.multi
    def send_text(self, text):
        from wechatpy.exceptions import WeChatClientException
        Param = self.env['ir.config_parameter'].sudo()
        Corp_Agent = Param.get_param('Corp_Agent') or 0
        Corp_Agent = int(Corp_Agent)
        for obj in self:
            try:
                entry = corp_client.corpenv(self.env)
                entry.client.message.send_text(Corp_Agent, obj.userid, text)
            except WeChatClientException as e:
                _logger.info(u'微信消息发送失败 %s'%e)
                raise UserError(u'发送失败 %s'%e)

    @api.multi
    def send_messagebyopenid(self, openid, msg):
        corp_client.send_message(self, openid, msg)

    # ------------------------------------------------------
    # 发送企业号文本消息
    # partner: 供应商对象，如果传入供应商换到供应商对象的openid发送
    # msg: 消息文本
    # user：用户对象 如果传入用户1：找到用户的微信关联账号发送，2：如果没找到1，找到供应商关联的合作伙伴的微信发送
    # partner_id：供应商ID 根据ID找到供应商的微信
    # user_id：用户ID，根据用户ID查找用户 1：找到用户的微信关联账号发送，2：如果没找到1，找到供应商关联的合作伙伴的微信发送
    # ------------------------------------------------------
    @api.multi
    def send_message(self, partner=None, msg='', user=None, partner_id=None, user_id=None):
        if partner:
            if partner.wxcorp_user_id.userid:
                corp_client.send_message(self, partner.wxcorp_user_id.userid, msg)
            else:
                raise UserError(u'发送失败,客户没有绑定微信')
        if user:
            if user.wxcorp_user_id.userid:
                corp_client.send_message(self, user.wxcorp_user_id.userid, msg)
            elif user.partner_id.wxcorp_user_id.userid:
                corp_client.send_message(self, user.partner_id.wxcorp_user_id.userid, msg)
            else:
                raise UserError(u'发送失败,客户没有绑定微信')
        if partner_id:
            partner_ = self.env['res.partner'].sudo().browse(partner_id)
            self.send_message(partner=partner_, msg=msg)
        if user_id:
            user_ = self.env['res.users'].sudo().browse(user_id)
            self.send_message(user=user_, msg=msg)

    # ------------------------------------------------------
    # 发送企业号文本卡片消息
    # title : 发送标题   如:订单提醒
    # description: 卡片信息描述 如下格式:
    # 格式： https://work.weixin.qq.com/api/doc#90000/90135/90236/文本卡片消息
    # 请求示例：
    #      <div class="gray">收到新信息:收到信息请回复，谢谢。</div>
    #      <div class="normal">订单号:SO024</div>
    #      <div class="highlight">时间:2019-05-27 11:21:32 \n联系:Administrator</div>
    # url:信息接到的URL http://weixintools.pub.heyanze.com/web/login?usercode=saleorder&codetype=crop&redirect=/my/orders/24
    #     URL解析： usercode:访问URL类型用户于定义是那个业务单元  codetype:(wx=微信公众号 crop=企业号)  redirect:转向内部URL
    # partner: 供应商对象，如果传入供应商换到供应商对象的openid发送
    # user：用户对象 如果传入用户1：找到用户的微信关联账号发送，2：如果没找到1，找到供应商关联的合作伙伴的微信发送
    # partner_id：供应商ID 根据ID找到供应商的微信
    # user_id：用户ID，根据用户ID查找用户 1：找到用户的微信关联账号发送，2：如果没找到1，找到供应商关联的合作伙伴的微信发送
    # ------------------------------------------------------
    def send_text_card(self, title, description, url, partner=None, user=None, partner_id=None, user_id=None):
        if partner:
            if partner.wxcorp_user_id.userid:
                corp_client.send_text_card(self, partner.wxcorp_user_id.userid, title, description, url)
            else:
                raise UserError(u'发送失败,客户没有绑定微信')
        if user:
            if user.wxcorp_user_id.userid:
                corp_client.send_text_card(self, user.wxcorp_user_id.userid, title, description, url)
            elif user.partner_id.wxcorp_user_id.userid:
                corp_client.send_text_card(self, user.partner_id.wxcorp_user_id.userid, title, description, url)
            else:
                raise UserError(u'发送失败,客户没有绑定微信')
        if partner_id:
            partner_ = self.env['res.partner'].sudo().browse(partner_id)
            self.send_text_card(title, description, url, partner=partner_)
        if user_id:
            user_ = self.env['res.users'].sudo().browse(user_id)
            self.send_text_card(title, description, url, user=user_)

    @api.multi
    def send_text_confirm(self):
        self.ensure_one()

        new_context = dict(self._context) or {}
        new_context['default_model'] = 'wx.corpuser'
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

    @api.model
    def sync_from_remote(self, department_id=7):
        from wechatpy.exceptions import WeChatClientException
        #corp_client.create_menu(self)
        try:
            entry = corp_client.corpenv(self.env)
            users = entry.txl_client.user.list(department_id, fetch_child=True)
            for info in users:
                rs = self.search([('userid', '=', info['userid'])])
                if not rs.exists():
                    info['_from_subscribe'] = True
                    info['gender'] = int(info['gender'])
                    self.create(info)
        except WeChatClientException as e:
            raise ValidationError(u'微信服务请求异常，异常码: %s 异常信息: %s' % (e.errcode, e.errmsg))

    @api.multi
    def sync_from_remote_confirm(self):
        new_context = dict(self._context) or {}
        new_context['default_info'] = "此操作可能需要一定时间，确认同步吗？"
        new_context['default_model'] = 'wx.corpuser'
        new_context['default_method'] = 'sync_from_remote'
        # new_context['record_ids'] = self.id
        return {
            'name': u'确认同步已有企业微信用户至本系统',
            'type': 'ir.actions.act_window',
            'res_model': 'wx.confirm',
            'res_id': None,
            'view_mode': 'form',
            'view_type': 'form',
            'context': new_context,
            'view_id': self.env.ref('wx_tools.wx_confirm_view_form').id,
            'target': 'new'
        }

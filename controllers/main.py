# -*- encoding: utf-8 -*-
##############################################################################
#
#    实现微信登录
##############################################################################

import ast
from odoo.addons.web.controllers.main import Home
from odoo.addons.web.controllers.main import Session
import pytz
import datetime
import logging
from ..rpc import corp_client


from odoo import http
from odoo.http import request
_logger = logging.getLogger(__name__)



#----------------------------------------------------------
# Odoo Web web Controllers
#----------------------------------------------------------
class LoginHome(Home):

    @http.route('/web/login', type='http', auth="none")
    def web_login(self, redirect=None, **kw):
        # OAuth提供商id
        provider_id = kw.get('state', '')
        # 以下微信相关 #
        code = kw.get('code', '')
        codetype = kw.get('codetype', '')
        wx_user_info = {}
        # 获取从WX过来的code
        wx_client_code = corp_client.corpenv(request.env)
        wxcode = wx_client_code.WX_CODE
        if not wxcode:
            wxcode = {}
        logging.info(wxcode)
        if code is False:
            return super(LoginHome, self).web_login(redirect, **kw)
        if code:  # code换取token
            if code not in wxcode:  # 判断用户code是使用
                # 将获取到的用户放到Session中
                if codetype == 'corp':
                    wx_user_info = corp_client.get_user_info(request, code)
                else:
                    from ..controllers import client
                    wx_user_info = client.get_user_info(request, code)
                    wx_user_info['UserId'] = wx_user_info['openid']
                kw.pop('code')
                wx_user_info['codetype'] = codetype
                request.session.wx_user_info = wx_user_info
                wx_client_code.WX_CODE[code] = code
            else:  # 如果使用，直接用session中的用户信息
                wx_user_info = request.session.wx_user_info
            if not wx_user_info or 'UserId' not in wx_user_info:
                return super(LoginHome, self).web_login(redirect, **kw)
            obj = request.env['wx.user.odoouser'].sudo().search([('open_id', '=', wx_user_info['UserId'])])
            if obj.open_id:
                kw['login'] = obj.user_id.login
                kw['password'] = obj.password
                request.params['login'] = obj.user_id.login
                request.params['password'] = obj.password
                uid = request.session.authenticate(request.session.db, obj.user_id.login,  obj.password)
                if redirect:
                    return http.local_redirect(redirect)
                else:
                    return http.local_redirect('/')
            else:
                #request.session.logout()
                uid = request.session.authenticate(request.session.db, obj.user_id.login, '')
                return super(LoginHome, self).web_login(redirect, **kw)
        elif request.session.wx_user_info:  # 存在微信登录访问
            uid = request.session.authenticate(request.session.db, request.params['login'], request.params['password'])
            if uid is not False:
                wx_user_info = request.session.wx_user_info
                wx_user_info['open_id'] = wx_user_info['UserId']
                wx_user_info['user_id'] = uid
                wx_user_info['password'] = request.params['password']
                request.session.wx_user_info = wx_user_info
                userinfo = request.env['wx.user.odoouser'].sudo().search([('open_id', '=', wx_user_info['UserId'])])
                if userinfo:
                    request.env['wx.user.odoouser'].sudo().write(wx_user_info)
                else:
                    obj = request.env['wx.user.odoouser'].sudo().create(wx_user_info)
        return super(LoginHome, self).web_login(redirect, **kw)


class WxSession(Session):
    @http.route('/web/session/logout', type='http', auth="none")
    def logout(self, redirect='/web'):
        uid = request.session.uid
        wx_user_info = request.session.wx_user_info
        ret = super(WxSession, self).logout(redirect)
        if wx_user_info:
            userinfo = request.env['wx.user.odoouser'].sudo().search([('user_id', '=', uid),('codetype', '=', wx_user_info['codetype'])])
            userinfo.unlink()
        return ret


class WxMp(http.Controller):

    @http.route(['/MP_verify_xobfOnBKmFpc9HEU.txt'], type='http', auth="public")
    def mp(self, **kwargs):
        #response = http.send_file('MP_verify_xobfOnBKmFpc9HEU.txt')
        return 'xobfOnBKmFpc9HEU'

    @http.route(['/WW_verify_npgHFdA6yan51Qd5.txt'], type='http', auth="public")
    def mpcrop(self, **kwargs):
        # response = http.send_file('MP_verify_xobfOnBKmFpc9HEU.txt')
        return 'npgHFdA6yan51Qd5'


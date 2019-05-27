# coding=utf-8
import logging

# from werobot.robot import BaseRoBot
# from werobot.session.memorystorage import MemoryStorage
from werobot import WeRoBot
from werobot.client import ClientException
from werobot.logger import enable_pretty_logging

from odoo import exceptions
from .memorystorage import MemoryStorage

from wechatpy.oauth import WeChatOAuth
from wechatpy.component import ComponentOAuth
_logger = logging.getLogger(__name__)


# class WeRoBot(BaseRoBot):
#     pass


WxEnvDict = {}


class WxEntry(object):

    def __init__(self):

        robot = WeRoBot()
        robot.config["APP_ID"] = "appid_xxxxxxxxxxxxxxx"
        robot.config["APP_SECRET"] = "appsecret_xxxxxxxxxxxxxx"
        self.wxclient = robot.client
        #self.wxclient = Client('appid_xxxxxxxxxxxxxxx', 'appsecret_xxxxxxxxxxxxxx')

        self.UUID_OPENID = {}

        # 微信用户客服消息的会话缓存
        self.OPENID_UUID = {}

        self.robot = None

    def send_text(self, openid, text):
        try:
            self.wxclient.send_text_message(openid, text)
        except ClientException as e:
            raise exceptions.UserError(u'发送失败 %s'%e)

    def chat_send(self, db,uuid, msg):
        #_dict = self.UUID_OPENID.get(db,None)
        if self.UUID_OPENID:
            openid = self.UUID_OPENID.get(uuid,None)
            if openid:
                self.send_text(openid, msg)
        return -1

    def upload_media(self, media_type, media_file):
        try:
            return self.wxclient.upload_media(media_type, media_file)
        except ClientException as e:
            raise exceptions.UserError(u'image上传失败 %s'%e)

    def send_image_message(self, openid, media_id):
        try:
            self.wxclient.send_image_message(openid, media_id)
        except ClientException as e:
            raise exceptions.UserError(u'发送image失败 %s'%e)

    def send_image(self, db, uuid, media_id):
        # _dict = self.UUID_OPENID.get(db,None)
        if self.UUID_OPENID:
            openid = self.UUID_OPENID.get(uuid, None)
            if openid:
                self.send_image_message(openid, media_id)
        return -1

    def init(self, env):
        dbname = env.cr.dbname
        global WxEnvDict
        if dbname in WxEnvDict:
            del WxEnvDict[dbname]
        WxEnvDict[dbname] = self

        Param = env['ir.config_parameter'].sudo()
        self.wx_token = Param.get_param('wx_token') or ''
        self.wx_appid = Param.get_param('wx_appid') or ''
        self.wx_AppSecret = Param.get_param('wx_AppSecret') or ''
        self.server_url = Param.get_param('server_url') or ''
        #robot.config["TOKEN"] = self.wx_token
        #self.wxclient.appid = self.wx_appid
        #self.wxclient.appsecret = self.wx_AppSecret
        self.wxclient.config["APP_ID"] = self.wx_appid
        self.wxclient.config["APP_SECRET"] = self.wx_AppSecret
        self.wxclient.config["server_url"] = self.server_url
        try:
            # 刷新 AccessToken
            self.wxclient._token = None
            _ = self.wxclient.token
        except:
            import traceback;traceback.print_exc()
            _logger.error(u'初始化微信客户端token失败，请在微信对接配置中填写好相关信息！')

        session_storage = MemoryStorage()
        robot = WeRoBot(token=self.wx_token, enable_session=True, logger=_logger, session_storage=session_storage)
        enable_pretty_logging(robot.logger)
        self.robot = robot

        users = env['wx.user'].sudo().search([('last_uuid','!=',None)])
        for obj in users:
            self.OPENID_UUID[obj.openid] = obj.last_uuid
            self.UUID_OPENID[obj.last_uuid] = obj.openid
        print('wx client init: %s %s'%(self.OPENID_UUID, self.UUID_OPENID))


def wxenv(env):
    return WxEnvDict[env.cr.dbname]


def authorize_url(self, url, state):
    entry = wxenv(self.env)
    wxclient = entry.wxclient
    wxoauth = ComponentOAuth(wxclient.appid, component_appid='', component_access_token=wxclient.token,
                             redirect_uri=url, scope='snsapi_userinfo', state=state)
    return wxoauth.authorize_url


def send_template_message(self, user_id, template_id, data, url='', state=''):
    entry = wxenv(self.env)
    wxclient = entry.wxclient
    wxoauth = ComponentOAuth(wxclient.appid, component_appid='', component_access_token=wxclient.token,
                             redirect_uri=url, scope='snsapi_userinfo', state=state)
    logging.info(wxoauth.authorize_url)
    return wxclient.send_template_message(user_id, template_id, data, wxoauth.authorize_url)


def send_text(self, openid, text):
    entry = wxenv(self.env)
    client = entry
    client.send_text(openid, text)


def create_menu(self):
    entry = wxenv(self.env)
    wxclient = entry.wxclient
    server_url=entry.server_url
    menu1_url = ''
    menu1_name = ''
    menu1 = self.env["wx.paraconfig"].sudo().search([('paraconfig_name', '=', 'menu1_url')])
    if menu1:
        menu1_url = menu1[0].paraconfig_value
        menu1_name = menu1[0].paraconfig_remark
    url = server_url + '/web/login?usercode=saleorder&codetype=wx&redirect='+menu1_url
    wxoauth = ComponentOAuth(wxclient.appid, component_appid='', component_access_token=wxclient.token,
                             redirect_uri=url, scope='snsapi_userinfo', state='login')
    url = wxoauth.authorize_url
    logging.info(url)
    menu2_url = ''
    menu2_name = ''
    menu2 = self.env["wx.paraconfig"].sudo().search([('paraconfig_name', '=', 'menu2_url')])
    if menu2:
        menu2_url = menu2[0].paraconfig_value
        menu2_name = menu2[0].paraconfig_remark
    url2 = wxoauth.get_authorize_url(server_url + '/web/login?usercode=saleorder&codetype=wx&redirect='+menu2_url,
                                     scope='snsapi_userinfo', state='home')
    logging.info(url2)
    menu3_url = ''
    menu3_name = ''
    menu3 = self.env["wx.paraconfig"].sudo().search([('paraconfig_name', '=', 'menu3_url')])
    if menu3:
        menu3_url = menu3[0].paraconfig_value
        menu3_name = menu3[0].paraconfig_remark

    url3 = wxoauth.get_authorize_url(
        server_url + '/web/login?usercode=saleorder&codetype=wx&redirect=' + menu3_url,
        scope='snsapi_userinfo', state='sale')
    logging.info(url3)
    menu = {
        "button": [
            {
                "type": "view",
                "name": menu1_name,
                "url": url
            },
            {
                "type": "view",
                "name": menu2_name,
                "url": url2
            }, {
                "type": "view",
                "name": menu3_name,
                "url": url3
            }
        ]
    }
    wxclient.create_menu(menu)
    return -1


def get_user_info(self, code):
    entry = wxenv(self.env)
    wxclient = entry.wxclient
    oauth = WeChatOAuth(wxclient.appid,wxclient.appsecret, redirect_uri='', scope='snsapi_base', state='login')
    access_token=oauth.fetch_access_token(code)
    user_info = oauth.get_user_info(access_token['openid'],access_token=access_token['access_token'])
    logging.info(user_info)
    return user_info

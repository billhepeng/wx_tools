# coding=utf-8
import logging

from wechatpy.enterprise import WeChatClient
from wechatpy.enterprise.client.api import WeChatOAuth
from wechatpy.client.api.base import BaseWeChatAPI
_logger = logging.getLogger(__name__)


CorpEnvDict = {}


class CorpEntry(object):

    def __init__(self):

        self.crypto_handle = None

        # 用于agent应用API交互的client
        self.client = None

        # 用于通讯录API交互的client
        self.txl_client = None

        # 当前Agent
        self.current_agent = None

        self.server_url= ''

        self.UUID_OPENID = {}

        # 微信用户客服消息的会话缓存
        self.OPENID_UUID = {}

        # 微信用户对应的Odoo用户ID缓存
        self.OPENID_UID = {}

        # 微信用户(绑定了Odoo用户)和Odoo用户的会话缓存(由Odoo用户发起, key 为 db-uid)
        self.UID_UUID = {}
        # 微信 CODE
        self.WX_CODE = {}

    def init_client(self, appid, secret):
        self.client = WeChatClient(appid, secret)

        return self.client

    def init_txl_client(self, appid, secret):
        self.txl_client = WeChatClient(appid, secret)
        return self.txl_client

    def chat_send(self, db, uuid, msg):
        #_dict = UUID_OPENID.get(db,None)
        if self.UUID_OPENID:
            openid = self.UUID_OPENID.get(uuid,None)
            if openid:
                self.client.message.send_text(self.current_agent, openid, msg)
        return -1

    def init(self, env):
        global CorpEnvDict
        CorpEnvDict[env.cr.dbname] = self

        Param = env['ir.config_parameter'].sudo()

        Corp_Token = Param.get_param('Corp_Token') or ''
        Corp_AESKey = Param.get_param('Corp_AESKey') or ''

        Corp_Id = Param.get_param('Corp_Id') or ''       # 企业号
        Corp_Secret = Param.get_param('Corp_Secret') or ''
        Corp_Agent = Param.get_param('Corp_Agent') or ''
        Corp_Agent_Secret = Param.get_param('Corp_Agent_Secret') or ''
        server_url = Param.get_param('server_url') or ''

        from wechatpy.enterprise.crypto import WeChatCrypto
        _logger.info('Create crypto: %s %s %s'%(Corp_Token, Corp_AESKey, Corp_Id))
        try:
            self.crypto_handle = WeChatCrypto(Corp_Token, Corp_AESKey, Corp_Id)
            CorpEnvDict['Corp_Id'] = Corp_Id
        except:
            _logger.error(u'初始化微信客户端实例失败，请在微信对接配置中填写好相关信息！')

        self.current_agent = Corp_Agent
        self.server_url = server_url
        self.init_client(Corp_Id, Corp_Agent_Secret)
        self.init_txl_client(Corp_Id, Corp_Secret)
        users = env['wx.corpuser'].sudo().search([('last_uuid','!=',None)])
        for obj in users:
            self.OPENID_UUID[obj.userid] = obj.last_uuid
            self.UUID_OPENID[obj.last_uuid] = obj.userid
        print('corp client init: %s %s'%(self.OPENID_UUID, self.UUID_OPENID))


def corpenv(env):
    return CorpEnvDict[env.cr.dbname]


def corppara(env):
    return CorpEnvDict


def send_message(self, openid, msg):
    entry = corpenv(self.env)
    entry.client.message.send_text(entry.current_agent, openid, msg)


def send_text_card(self, user_ids, title, description, url, btntxt='详情'):
    entry = corpenv(self.env)
    entry.client.message.send_text_card(entry.current_agent, user_ids, title, description, url, btntxt)
    return -1


def create_menu(self):
    entry = corpenv(self.env)
    oauth = WeChatOAuth(entry.client)
    server_url = entry.server_url
    menu1_url = ''
    menu1_name = ''
    menu1 = self.env["wx.paraconfig"].sudo().search([('paraconfig_name', '=', 'menu1_url')])
    if menu1:
        menu1_url = menu1[0].paraconfig_value
        menu1_name = menu1[0].paraconfig_remark
    url = oauth.authorize_url(server_url+'/web/login?usercode=menu&codetype=corp&'
                                         'redirect='+menu1_url, 'menu1')
    logging.info(url)

    menu2_url = ''
    menu2_name = ''
    menu2 = self.env["wx.paraconfig"].sudo().search([('paraconfig_name', '=', 'menu2_url')])
    if menu2:
        menu2_url = menu2[0].paraconfig_value
        menu2_name = menu2[0].paraconfig_remark

    url2 = oauth.authorize_url(server_url+'/web/login?usercode=menu&codetype=corp&redirect=/web#home', 'home')
    logging.info(url2)

    menu3_url = ''
    menu3_name = ''
    menu3 = self.env["wx.paraconfig"].sudo().search([('paraconfig_name', '=', 'menu3_url')])
    if menu3:
        menu3_url = menu3[0].paraconfig_value
        menu3_name = menu3[0].paraconfig_remark
    url3 = oauth.authorize_url(server_url+'/web/login?usercode=menu&codetype=corp&'
                                          'redirect='+menu3_url, 'menu3')
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
    entry.client.menu.create(entry.current_agent, menu)
    return -1


def authorize_url(self, url, state):
    entry = corpenv(self.env)
    oauth = WeChatOAuth(entry.client)
    url = oauth.authorize_url(url, state)
    logging.info(url)
    return url


def get_user_info(self, code):
    entry = corpenv(self.env)
    oauth = WeChatOAuth(entry.client)
    user_info = oauth.get_user_info(code)
    logging.info(user_info)
    return user_info

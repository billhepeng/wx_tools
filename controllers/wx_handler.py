# coding=utf-8

import logging


# 企业号相关
from wechatpy.enterprise.crypto import WeChatCrypto
from wechatpy.exceptions import InvalidSignatureException, InvalidAppIdException
from wechatpy.enterprise.exceptions import InvalidCorpIdException
from wechatpy.enterprise import parse_message, create_reply
# 公众号相关
from wechatpy.utils import check_signature

import werkzeug


from odoo import http
from odoo.http import request


_logger = logging.getLogger(__name__)


def abort(code):
    return werkzeug.wrappers.Response('Unknown Error: Application stopped.', status=code, content_type='text/html;charset=utf-8')


class WxCorpHandler(http.Controller):

    def __init__(self):
        from ..rpc import corp_client
        entry = corp_client.CorpEntry()
        entry.init(request.env)
        self.crypto = entry.crypto_handle

    @http.route('/corp_handler', type='http', auth="none", methods=['GET', 'POST'], csrf=False)
    def handle(self, **kwargs):
        msg_signature = request.params.get("msg_signature")
        timestamp = request.params.get("timestamp")
        nonce = request.params.get("nonce")

        echo_str = request.params.get('echostr', '')

        if request.httprequest.method == 'GET':
            try:
                echo_str = self.crypto.check_signature(
                    msg_signature,    #新增
                    timestamp,
                    nonce,
                    echo_str
                )
            except InvalidSignatureException:
                abort(403)
            return echo_str

        # POST
        msg = None
        try:
            msg = self.crypto.decrypt_message(
                request.httprequest.data,
                msg_signature,
                timestamp,
                nonce
            )
        except (InvalidSignatureException, InvalidCorpIdException):
            abort(403)
        msg = parse_message(msg)
        ss = '------------------%s %s'%(msg.type, msg)
        _logger.info(ss)
        ret = ''
        if msg.type == 'text':
            #reply = create_reply(msg.content, msg).render()
            from .handlers.text_handler import kf_handler
            ret = kf_handler(request, msg.content, msg.source,**kwargs)
        elif msg.type == 'event':
            if msg.event=='subscribe':
                from .handlers.event_handler import subscribe_handler
                ret = subscribe_handler(request, msg)
            elif msg.event=='unsubscribe':
                from .handlers.event_handler import unsubscribe_handler
                ret = unsubscribe_handler(request, msg)
        reply = create_reply(ret, msg).render()
        res = self.crypto.encrypt_message(reply, request.params.get("nonce"), request.params.get("timestamp"))
        return res


class WxAppHandler(http.Controller):

    def __init__(self):
        Param = request.env()['ir.config_parameter'].sudo()

        self.TOKEN = Param.get_param('wx_token') or 'K5Dtswpte'
        self.AES_KEY = Param.get_param('AES_KEY') or ''
        self.APPID = Param.get_param('APPID') or '' # 公众号

    @http.route('/_wx_handler', type='http', auth="none", methods=['GET', 'POST'])
    def handle_encrypt(self, **kwargs):
        msg_signature = request.params.get('msg_signature', '')
        signature = request.params.get('signature', '')
        timestamp = request.params.get('timestamp', '')
        nonce = request.params.get('nonce', '')

        encrypt_type = request.params.get('encrypt_type', 'raw')

        echo_str = request.args.get('echostr', '')

        try:
            check_signature(self.TOKEN, signature, timestamp, nonce)
        except InvalidSignatureException:
            abort(403)

        if request.httprequest.method == 'GET':
            return echo_str

        # POST
        if encrypt_type == 'raw':
            # plaintext mode
            msg = parse_message(request.httprequest.data)
            if msg.type == 'text':
                reply = create_reply(msg.content, msg)
            else:
                reply = create_reply('Sorry, can not handle this for now', msg)
            return reply.render()
        else:
            # encryption mode
            from wechatpy.crypto import WeChatCrypto

            crypto = WeChatCrypto(self.TOKEN, self.AES_KEY, self.APPID)   # 公众号
            try:
                msg = crypto.decrypt_message(
                    request.httprequest.data,
                    msg_signature,
                    timestamp,
                    nonce
                )
            except (InvalidSignatureException, InvalidAppIdException):
                abort(403)
            else:
                msg = parse_message(msg)
                if msg.type == 'text':
                    reply = create_reply(msg.content, msg)
                else:
                    reply = create_reply('Sorry, can not handle this for now', msg)
                return crypto.encrypt_message(reply.render(), nonce, timestamp)


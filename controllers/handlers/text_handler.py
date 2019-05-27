# coding=utf-8
import datetime
import logging
import odoo

from ...rpc import corp_client

_logger = logging.getLogger(__name__)
def kf_handler(request, content, wx_id, **kwargs):
    client = corp_client.corpenv(request.env)
    openid = wx_id
    # 获取关联的系统用户
    uid = client.OPENID_UID.get(openid, False)
    _logger.info(uid)
    if not uid:
        objs = request.env['wx.corpuser'].sudo().search( [ ('userid', '=', openid) ] )
        if objs.exists():
            corpuser_id = objs[0].id
            objs2 = request.env['res.partner'].sudo().search( [ ('wxcorp_user_id', '=', corpuser_id) ] )
            if objs2.exists():
                uid = objs2[0].id
                client.OPENID_UID[openid] = uid

    uuid = None
    kf_flag = False
    if uid:
        _key = '%s-%s'%(request.db, uid)
        if _key in client.UID_UUID:
            # 微信员工(绑定了odoo用户UID) -> Odoo用户
            _data = client.UID_UUID[_key]
            _now = datetime.datetime.now()
            if _now - _data['last_time']<=  datetime.timedelta(seconds=10*60):
                uuid = _data['uuid']

    if not uuid:
        # 识别为客服型消息
        kf_flag = True
        # 客服会话ID
        uuid = client.OPENID_UUID.get(openid, None)

    ret_msg = ''
    _logger.info(uuid)
    if not uuid:
        # 客服消息第一次发过来时
        rs = request.env['wx.corpuser'].sudo().search( [('userid', '=', openid)] )
        if not rs.exists():
            corp_user = request.env['wx.corpuser'].sudo().create({
                '_from_subscribe': True,
                'name': openid,
                'userid': openid,
                'weixinid': openid
            })
        else:
            corp_user = rs[0]
        anonymous_name = corp_user.userid

        channel = request.env.ref('wx_tools.channel_corp')
        channel_id = channel.id

        session_info = request.env['im_livechat.channel'].sudo().get_mail_channel(channel_id, anonymous_name)
        if session_info:
            uuid = session_info['uuid']
            client.OPENID_UUID[openid] = uuid
            client.UUID_OPENID[uuid] = openid
            corp_user.write({'last_uuid': uuid})
            request.env['wx.corpuser.uuid'].sudo().create({'userid': openid, 'uuid': uuid})
        ret_msg = channel.default_message

    if uuid:
        message_type = 'comment'
        message_content = content

        author_id = False  # message_post accept 'False' author_id, but not 'None'
        if request.session.uid:
            author_id = request.env['res.users'].sudo().browse(from_uid).partner_id.id
        else:
            author_id = uid
        # if kf_flag:
        #     author_id = False
        mail_channel = request.env["mail.channel"].sudo().search([('uuid', '=', uuid)], limit=1)
        kwargs['weixin_id'] = openid;
        kwargs['wx_type'] = 'corp';
        message = mail_channel.sudo().with_context(mail_create_nosubscribe=True).message_post(author_id=author_id, email_from=False, body=message_content, message_type=message_type, subtype='mail.mt_comment', content_subtype='plaintext',**kwargs)
    return ret_msg


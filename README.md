
Odoo 微信工具


Odoo 接入企业微信，接入微信公众号


**接口调用说明**
====================
    1：发送企业号文本卡片消息 
    方法签名: 模型:wx.corpuser
    def send_text_card(self, title, description, url, partner=None, user=None, partner_id=None, user_id=None):
        title : 发送标题   如:订单提醒
        description: 卡片信息描述 如下格式:
        格式： https://work.weixin.qq.com/api/doc90000/90135/90236/文本卡片消息
        请求示例：
          <div class="gray">收到新信息:收到信息请回复，谢谢。</div>
          <div class="normal">订单号:SO024</div>
          <div class="highlight">时间:2019-05-27 11:21:32 \n联系:Administrator</div>
        url:信息接到的URL http://weixintools.pub.heyanze.com/web/login?usercode=saleorder&codetype=crop&redirect=/my/orders/24
         URL解析： usercode:访问URL类型用户于定义是那个业务单元  codetype:(wx=微信公众号 crop=企业号)  redirect:转向内部URL
        partner: 供应商对象，如果传入供应商换到供应商对象的openid发送
        user：用户对象 如果传入用户1：找到用户的微信关联账号发送，2：如果没找到1，找到供应商关联的合作伙伴的微信发送
        partner_id：供应商ID 根据ID找到供应商的微信
        user_id：用户ID，根据用户ID查找用户 1：找到用户的微信关联账号发送，2：如果没找到1，找到供应商关联的合作伙伴的微信发
    
    2：发送企业号文本消息
     方法签名 模型:wx.corpuser
     def send_message(self, partner=None, msg='', user=None, partner_id=None, user_id=None):
         partner: 供应商对象，如果传入供应商换到供应商对象的openid发送
         msg: 消息文本
         user：用户对象 如果传入用户1：找到用户的微信关联账号发送，2：如果没找到1，找到供应商关联的合作伙伴的微信发送
         partner_id：供应商ID 根据ID找到供应商的微信
         user_id：用户ID，根据用户ID查找用户 1：找到用户的微信关联账号发送，2：如果没找到1，找到供应商关联的合作伙伴的微信发送   
   
    3 发送微信公众号文本消息
    方法签名 模型:wx.user
    def send_message(self, partner=None, msg='', user=None, partner_id=None, user_id=None):
      partner: 供应商对象，如果传入供应商换到供应商对象的openid发送
      msg: 消息文本
      user：用户对象 如果传入用户1：找到用户的微信关联账号发送，2：如果没找到1，找到供应商关联的合作伙伴的微信发送
      partner_id：供应商ID 根据ID找到供应商的微信
      user_id：用户ID，根据用户ID查找用户 1：找到用户的微信关联账号发送，2：如果没找到1，找到供应商关联的合作伙伴的微信发送
    4 发送微信公众号模板信息
    方法签名 模型:wx.user
     def send_template_message(self, template_id, data, url='', partner=None,user=None, partner_id=None, user_id=None):
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
        
   
     
    
   
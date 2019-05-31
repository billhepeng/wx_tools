# -*- coding: utf-8 -*-

{
    'name': 'wx_tools',
    'version': '1.0.0',
    'category': 'Social Network',
    'summary': '微信工具',
    'author': 'wx_tools',
    'website': '',
    'application': True,
    'auto_data_include': ['views'],
    'data': [

        'security/ir.model.access.csv',

        'data/wx_init_data.xml',
        'views/parent_menus.xml',

        'views/wx_action_act_article_views.xml',
        'views/wx_action_act_custom_views.xml',
        'views/wx_action_act_text_views.xml',
        'views/wx_articlesreply_article_views.xml',
        'views/wx_autoreply_views.xml',
        'views/wx_config_settings_views.xml',
        'views/wx_menu_item_left_views.xml',
        'views/wx_menu_item_middle_views.xml',
        'views/wx_menu_item_right_views.xml',
        'views/wx_menu_views.xml',
        'views/wx_user_group_views.xml',
        'views/wx_user_views.xml',
        'views/wx_config_corpsettings_views.xml',
        'views/wx_corpuser_views.xml',
        'views/wx_confirm_views.xml',

        'views/wx_inherit_ext.xml',
        'views/wx_res_partner_views.xml',
        'views/wx_user_views.xml',
        'views/wx_userodoouser.xml',
        'views/wx_para_config.xml',

        'views/wx_tools_templates.xml'
    ],
    'qweb': ['static/src/xml/wx_tools.xml'],
    'depends': ['web', 'im_livechat', 'purchase'],
    'installable': True,
    'active': False,
    'web': True,
}

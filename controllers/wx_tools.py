# -*-coding:utf-8-*-
import logging

import werkzeug

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class WxTools(http.Controller):
    @http.route('/trial', auth='public', type='http', website=True)
    def trial(self, **kw):
        values = {
            'plan': 'test',
        }
        return request.render('try_trial', values)

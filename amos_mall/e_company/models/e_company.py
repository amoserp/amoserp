# -*- coding: utf-8 -*-

from odoo import _, api, fields, models, modules, tools
import base64
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError
import uuid
import os
from jinja2 import Template

ORDER_STATES = [
    (u'新建', u'新建'),
    (u'上架', u'上架'),
    (u'下架', u'下架'),
]

READONLY_STATES = {
    u'上架': [('readonly', True)],
    u'下架': [('readonly', True)],
}


class e_company(models.Model):
    _inherit = 'res.company'

    delivery_time = fields.Char(string=u'发货时间', default='72小时内')
    delivery_service = fields.Char(string=u'配送服务', default='72小时内')
    customer_service = fields.Char(string=u'客服时间', default='9:00-18:00(工作日)')
    database_uuid = fields.Char(string=u'数据库号码', default='')
    login = fields.Char(string=u'登陆帐号', default='')


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


class e_ad(models.Model):
    _name = 'e.ad'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = u'广告'
    _order = 'name asc'

    name = fields.Char(string=u'名称', track_visibility='onchange')

    type = fields.Selection([
        ('image', u'图片'),
        ('video', u'视频'),
    ], string=u'类型', default='image')

    location = fields.Selection([
        ('open_app', 'APP开屏'),
        ('home_video', '视频广告'),
        ('home_banner', '首页幻灯'),
        ('drop_down', '下拉刷新'),
        ('Keyword', '关键词广告'),
    ], string=u'位置', default='open_app')

    attachment_ids = fields.One2many('ir.attachment', 'res_id',
                                     domain=[('res_model', '=', 'e.ad')], string=u'图片', ondelete='cascade',
                                     states=READONLY_STATES)

    param = fields.Text(u'参数', states=READONLY_STATES)
    state = fields.Selection(ORDER_STATES, u'单据状态', copy=False, default=u'新建', track_visibility='onchange')


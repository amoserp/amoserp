# -*- coding: utf-8 -*-

from odoo import _, api, fields, models, modules, tools
import base64
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError
import uuid
import os
from jinja2 import Template
import requests
import json
import datetime
import logging
import uuid
import re

from odoo import models, api, fields, SUPERUSER_ID
from odoo.exceptions import AccessError, UserError
from odoo.tools.translate import _

_logger = logging.getLogger(__name__)

ORDER_STATES = [
    (u'新建', u'待付款'),
    (u'已支付', u'已支付'),
]

READONLY_STATES = {
    u'已支付': [('readonly', True)],
}


class e_order(models.Model):
    _name = 'e.order'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = u'购物车订单系统'
    _order = 'name asc'

    @api.depends('order_line.price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_total = 0.0
            for line in order.order_line:
                amount_total += line.price_total
            order.update({
                'amount_total': amount_total,
            })


    def _default_access_token(self):
        return str(uuid.uuid4())
    access_token = fields.Char('Token', required=True, default=_default_access_token, readonly=True)

    name = fields.Char(string=u'名称', track_visibility='onchange')
    date_order = fields.Date(u'日期', track_visibility='onchange', states=READONLY_STATES,
                             default=fields.Date.context_today)
    company_id = fields.Many2one('res.company', '店铺',
                                 default=lambda self: self.env['res.company']._company_default_get('e.order'))
    amount_total = fields.Float(string='合计', store=True, readonly=True, compute='_amount_all',
                                track_visibility='always', track_sequence=6)
    order_line = fields.One2many('e.order.line', 'order_id', string='购物车明细', states=READONLY_STATES, auto_join=True)
    user_id = fields.Many2one('res.users', string='客户', index=True, track_visibility='onchange',
                              track_sequence=2, default=lambda self: self.env.user)
    note = fields.Text('备注')
    origin = fields.Char(string='对方单号')
    source = fields.Selection([
        ('微信公众号', u'微信公众号'),
        ('微信小程序', u'微信小程序'),
        ('钉钉小程序', u'钉钉小程序'),
        ('IOSAPP', u'IOSAPP'),
        ('Android', u'Android'),
    ], string=u'来源', default='微信公众号')
    state = fields.Selection(ORDER_STATES, u'单据状态', copy=False, default=u'新建', track_visibility='onchange')



    def unlink(self):
        for order in self:
            if order.state != '新建' and order.user_id.id == self._uid:
                if order.company_id.id in self.env.user.company_ids:
                    raise UserError(u'%s:只能删除新建单据!' % order._description)
        return super(e_order, self).unlink()

    def action_draft(self):
        self.state = u'新建'

    def action_done(self):
        self.state = u'新建'



    #####################################执行订单同步到用户库 判断用户是否开始
    @api.model
    def _get_company_credentials(self):
        secret = self.company_id.database_uuid
        url = self.company_id.website
        login = self.company_id.login
        return {'login': login, 'secret': secret, 'url': url}

    def syn_order(self):
        """
        同步订单：订单客户付款成功后就执行订单同步，并下行各类消息，考虑使用xml-rpc,post,还有直接插入数据库
        如果使用优惠券，就会生成一行优惠券产品，价格取负
        后期判断一张订单只能使用一张优惠券，优惠券id触发无效，表示关联到那个销售订单，并生成一个网址可以查看
        :return:
        """
        credentials = self._get_company_credentials()
        requestBody = json.dumps({'cobrand': {'cobrandLogin': credentials['login'], 'cobrandPassword': credentials['secret']}})
        try:
            resp = requests.post(url=credentials['url'] + '/cobrand/login', data=requestBody, timeout=30)
        except requests.exceptions.Timeout:
            raise UserError(_('Timeout: the server did not reply within 30s'))
        self.check_yodlee_error(resp)
        company_id = self.company_id or self.env.user.company_id
        company_id.yodlee_access_token = resp.json().get('session').get('cobSession')


    def check_yodlee_error(self, resp):
        try:
            resp_json = resp.json()
            if resp_json.get('errorCode'):
                if resp.json().get('errorCode') in ('Y007', 'Y008', 'Y009', 'Y010'):
                    return 'invalid_auth'
                message = _('Error %s, message: %s, reference code: %s' % (resp_json.get('errorCode'), resp_json.get('errorMessage'), resp_json.get('referenceCode')))
                message = ("%s\n\n" + _('(Diagnostic: %r for URL %s)')) % (message, resp.status_code, resp.url)
                if self and self.id:
                    self._update_status('FAILED', resp_json)
                    self.log_message(message)
                raise UserError(message)
            resp.raise_for_status()
        except (requests.HTTPError, ValueError):
            message = ('%s\n\n' + _('(Diagnostic: %r for URL %s)')) % (resp.text.strip(), resp.status_code, resp.url)
            self.log_message(message)
            raise UserError(message)
    ######################################订单同步结束

class e_order_line(models.Model):
    _name = 'e.order.line'
    _description = u'购物车明细'
    _order = 'order_id, sequence, id'

    @api.depends('product_uom_qty', 'price_unit')
    def _compute_amount(self):
        for line in self:
            price = line.price_unit * line.price_unit
            line.update({
                'price_total': price,
            })

    order_id = fields.Many2one('e.order', string='明细行', required=True, ondelete='cascade', index=True,
                               copy=False, readonly=True)
    name = fields.Text(string='备注')
    product_id = fields.Many2one('e.product', string='产品', change_default=True, ondelete='restrict')
    product_uom_qty = fields.Float(string='数量', required=True, default=1.0)
    product_uom = fields.Char(string=u'单位')
    price_unit = fields.Float('单价', required=True, default=0.0)
    sequence = fields.Integer(string='排序', default=10)
    company_id = fields.Many2one(related='order_id.company_id', string='店铺', store=True, readonly=True)
    price_total = fields.Float(compute='_compute_amount', string='小计', readonly=True, store=True)
    user_id = fields.Many2one(related='order_id.user_id', store=True, string='客户', readonly=True)

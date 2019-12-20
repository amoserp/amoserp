# -*- coding: utf-8 -*-
# &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
# AmosERP odoo11.0
# QQ:35350428
# 邮件:35350428@qq.com
# 手机：13584935775
# 作者：'amos'
# 公司网址： www.odoo.pw  www.100china.cn www.100china.cn
# Copyright 昆山一百计算机有限公司 2012-2018 Amos
# 日期：2018/09/12 15:01
# &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError
from odoo.osv import expression
from .import public_key as a
import math
from datetime import datetime, timedelta



class stock_warehouse_orderpoint(models.Model):
    _name = "stock.warehouse.orderpoint"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = u"最小库存规则"

    sequence = fields.Integer(string=u'排序', default=10)
    name = fields.Char(string=u'编号', default='New')
    active = fields.Boolean(u"是否有效", default=True)
    product_id = fields.Many2one('product.product', string=u'物资', )
    product_min_qty = fields.Float(string=u'最小数量', default=0.0)
    product_max_qty = fields.Float(string=u'最大数量', default=0.0)
    company_id = fields.Many2one('res.company', string=u'公司',
                                 default=lambda self: self.env['res.company']._company_default_get(
                                     'stock.warehouse.orderpoint'), )
    warehouse_id = fields.Many2one('stock.warehouse', string=u'仓库', )
    lead_days = fields.Integer(string=u'提前期', default=1, help=u'物资到手日期')
    lead_type = fields.Selection([
        ('net', u'物资入库天数'),
        ('supplier', u'采购天数')
    ], string=u'类型', required=True, default='supplier')

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].get(self._name) or 'New'
        return super(stock_warehouse_orderpoint, self).create(vals)


    _sql_constraints = [
        ('orderpoint_uniq', 'unique(product_id, company_id,warehouse_id)', u'物资，公司,仓库必须唯一!'),
    ]
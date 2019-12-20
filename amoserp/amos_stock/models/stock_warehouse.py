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

class stock_warehouse(models.Model):
    _name = 'stock.warehouse'
    _description = u'仓库'

    WAREHOUSE_TYPE = [
        ('stock', u'库存'),
        ('supplier', u'供应商'),
        ('customer', u'客户'),
        ('inventory', u'盘点'),
        ('production', u'生产'),
        ('others', u'其他'),
    ]


    code = fields.Char(string=u'编号', required=True,copy=False, readonly=True, index=True, default=lambda self: u'New')
    name = fields.Char(string=u'仓库名称', )
    active = fields.Boolean(default=True, string=u'有效')
    company_id = fields.Many2one('res.company', string=u'公司',default=lambda self: self.env['res.company']._company_default_get(''))
    type = fields.Selection(WAREHOUSE_TYPE, u'类型', default='stock')
    user_id = fields.Many2one('res.users', string=u'负责人', default=lambda self: self.env.user)


    @api.model
    def create(self, vals):
        if vals.get('code', 'New') == 'New':
            vals['code'] = self.env['ir.sequence'].next_by_code(self._name) or 'New'
        line = super(stock_warehouse, self).create(vals)
        return line


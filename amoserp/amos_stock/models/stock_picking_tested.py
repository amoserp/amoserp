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
from datetime import datetime, timedelta
import json
from lxml import etree
import odoo.addons.decimal_precision as dp

READONLY_STATES = {
    u'待处理': [('readonly', True)],
    u'入库单': [('readonly', True)],
    u'报废单': [('readonly', True)],
    u'评估中': [('readonly', True)],
}


class stock_picking_tested(models.Model):
    _name = "stock.picking.tested"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = u"不合格处理单"
    _order = "id desc"

    state = fields.Selection([
        (u'待处理', u'待处理'),
        (u'入库单', u'修理'),
        (u'评估中', u'评估中'),
        (u'报废单', u'报废'),
    ], string=u'状态', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3,
        default='待处理')
    name = fields.Char(string=u'单据编号', required=True, copy=False, readonly=True, index=True, default='/')
    partner_id = fields.Many2one('res.partner', '业务伙伴', states=READONLY_STATES)
    company_id = fields.Many2one('res.company', '公司', index=True, required=True, states=READONLY_STATES,
                                 default=lambda self: self.env['res.company']._company_default_get('stock.picking'))
    user_id = fields.Many2one('res.users', string=u'物资管理员', index=True, track_visibility='onchange',
                              states=READONLY_STATES)
    department_id = fields.Many2one('hr.department', string=u'专业队', states=READONLY_STATES)
    origin = fields.Char(string=u'单据来源', copy=False, states=READONLY_STATES)
    other_id = fields.Many2one('res.users', string=u'其它管理员', index=True, track_visibility='onchange',
                               states=READONLY_STATES)
    auditor_id = fields.Many2one('res.users', string=u'部门经理', index=True, track_visibility='onchange',
                                 states=READONLY_STATES)
    auditor_id_date = fields.Datetime(string=u'部门经理审核日期', states=READONLY_STATES)
    active = fields.Boolean(default=True, string=u'是否归档', track_visibility='onchange')
    order_line = fields.One2many('stock.picking.tested.line', 'order_id', string=u'明细行', states=READONLY_STATES,
                                 copy=True, auto_join=True)
    product_id = fields.Many2one('product.product', string=u'物资名称', change_default=True, ondelete='restrict', states=READONLY_STATES)
    move_id = fields.Many2one('stock.move', string='原明细行', )
    date_order = fields.Date(u'单据日期', track_visibility='onchange', states=READONLY_STATES,
                             default=fields.Date.context_today)
    date_done = fields.Datetime('调拨日期', copy=False, readonly=True, states=READONLY_STATES)
    note = fields.Text(u'备注', states=READONLY_STATES)

    interval_type = fields.Selection(related='product_id.interval_type', string=u'PM 周期', default='days',
                                     states=READONLY_STATES)
    interval_number = fields.Integer(related='product_id.interval_number', string='定时执行次参数', states=READONLY_STATES)
    test_date_done = fields.Datetime(related='product_id.test_date_done', string='上次检查合格日期', store=True, )
    picking_id = fields.Many2one('stock.picking', string=u'送检单', states=READONLY_STATES)
    picking_in_id = fields.Many2one('stock.picking', string=u'送检还入单', states=READONLY_STATES)
    scrap_id = fields.Many2one('stock.picking', string=u'报废单', states=READONLY_STATES)
    product_uom_qty = fields.Float(string=u'不合格数量', required=True, default=1.0 ,states=READONLY_STATES,
                                   digits=dp.get_precision('Product Unit of Measure'))


    @api.model
    def _select_reference(self):
        records = self.env['ir.model'].search([])
        return [(record.model, record.name) for record in records] + [('', '')]

    id_object = fields.Reference(string=u'关联', selection='_select_reference', states=READONLY_STATES)

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code(self._name) or '/'
        line = super(stock_picking_tested, self).create(vals)

        #::::创建全局查询
        context = dict(self._context or {})
        url = self.env.user.s(line, context, line._description, line.name,line.name)
        #:::::结束 创建全局查询

        return line


    def unlink(self):
        for order in self:
            if order.state != u'待处理':
                raise UserError(u'%s:只能删除 待处理 单据!' % order._description)
        return super(stock_picking_tested, self).unlink()


    def button_draft(self):

        if self.scrap_id:
            if self.scrap_id.state != '新建':
                raise UserError(u'警告：请删除 报废单！')
            self.scrap_id.unlink()

        self.write({'state': u'待处理'})



    def button_add_stock_picking_scrap(self):
        """ 直接创建报废单 """

        if self.scrap_id:
            if self.scrap_id.state != '新建':
                raise UserError(u'警告：请删除 报废单 再生在！')
            self.scrap_id.unlink()


        picking_type = self.env.ref('amos_stock.stock_picking_type_scrap')
        if not picking_type.warehouse_id:
            raise UserError(u'警告：当前默认的入库类型未设置默认仓库！')

        lines = []
        ref_id = 'stock.move,%s' % self.move_id.id
        pram = {
            'name': self.move_id.name,
            'product_id': self.move_id.product_id.id,
            'ref_id': ref_id,
            'product_uom_qty': self.move_id.product_uom_qty,
            'price_unit': self.move_id.price_unit,
            'warehouse_id': picking_type.warehouse_id.id,
        }
        lines.append((0, 0, pram))

        ref_id = '%s,%s' % (self._name, self.id)
        origin = '%s[%s]' % (self._description, self.name)

        values = {
            'partner_id': self.partner_id.id,
            'user_id': picking_type.user_id.id or self._uid,
            'other_id': self.user_id.id,
            'origin': origin,
            'ref_id': ref_id,
            'move_lines': lines,
            'picking_type_id': picking_type.id,
        }
        scrap = self.env['stock.picking'].sudo().with_context(default_picking_type_id=picking_type.id).create(values)

        values = {
            'scrap_id': scrap.id,
            'state': '报废单',
        }
        self.sudo().write(values)

        self.ensure_one()

        context = dict(self._context or {})
        context['default_picking_type_id'] = picking_type.id

        form_id = self.env.ref('amos_stock.odoo_stock_picking_scrap_form').id
        return {'type': 'ir.actions.act_window',
                'res_model': 'stock.picking',
                'view_mode': 'form',
                'views': [(form_id, 'form')],
                'res_id': scrap.id,
                'context': context,
                # 'target': 'new',
                'flags': {'form': {'action_buttons': True}}}

    def button_add_stock_picking_tested_in(self):
        """ 直接创建报废单 """

        picking_type = self.env.ref('amos_stock.stock_picking_type_tested_a')
        if not picking_type.warehouse_id:
            raise UserError(u'警告：当前默认的入库类型未设置默认仓库！')

        lines = []
        ref_id = 'stock.move,%s' % self.move_id.id
        pram = {
            'name': self.move_id.name,
            'product_id': self.move_id.product_id.id,
            'ref_id': ref_id,
            'product_uom_qty': self.product_uom_qty,
            'price_unit': self.move_id.price_unit,
            'warehouse_id': picking_type.warehouse_id.id,
        }
        lines.append((0, 0, pram))

        ref_id = '%s,%s' % (self.picking_id._name, self.picking_id.id)
        origin = '%s[%s]' % (self._description, self.name)

        values = {
            'partner_id': self.partner_id.id,
            'user_id': picking_type.user_id.id or self._uid,
            'other_id': self.user_id.id,
            'origin': origin,
            'ref_id': ref_id,
            'move_lines': lines,
            'picking_type_id': picking_type.id,
        }
        picking = self.env['stock.picking'].sudo().with_context(default_picking_type_id=picking_type.id).create(values)

        values = {
            'picking_in_id': picking.id,
            'state': '入库单',
        }
        self.sudo().write(values)

        self.ensure_one()

        context = dict(self._context or {})
        context['default_picking_type_id'] = picking_type.id

        form_id = self.env.ref('amos_stock.odoo_stock_picking_tested_in_form').id
        return {'type': 'ir.actions.act_window',
                'res_model': 'stock.picking',
                'view_mode': 'form',
                'views': [(form_id, 'form')],
                'res_id': picking.id,
                'context': context,
                # 'target': 'new',
                'flags': {'form': {'action_buttons': True}}}


class stock_picking_tested_line(models.Model):
    _name = "stock.picking.tested.line"
    _description = u"不合格工具"

    order_id = fields.Many2one('stock.picking.tested', string=u'明细', required=True, ondelete='cascade', index=True,
                               copy=False)
    move_id = fields.Many2one('stock.move', string=u'借用明细', required=True)
    name = fields.Char(string=u'物资全称', )
    note = fields.Text(u'备注')
    product_id = fields.Many2one(related='move_id.product_id', string=u'物资名称', store=True)
    product_uom = fields.Many2one(related='product_id.uom_id', string=u'单位', readonly=True, store=True)
    date_done = fields.Datetime(elated='move_id.date_done', string='调拨日期')
    other_id = fields.Many2one(related='move_id.other_id', string=u'借用人', store=True, )
    picking_id = fields.Many2one(related='move_id.picking_id', string=u'原单据', store=True)
    department_id = fields.Many2one(related='move_id.department_id', string=u'专业部', store=True, )


    @api.model
    def _select_reference(self):
        records = self.env['ir.model'].search([])
        return [(record.model, record.name) for record in records] + [('', '')]

    ref_id = fields.Reference(string=u'关联', selection='_select_reference')


class stock_picking_tested_inherit1(models.Model):
    _inherit = 'stock.picking'

    tested_lines = fields.One2many('stock.picking.tested', 'picking_id', string=u'不合格处理单')

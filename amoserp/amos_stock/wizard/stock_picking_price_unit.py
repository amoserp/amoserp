# -*- coding: utf-8 -*-
# &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
# Odoo Connector
# QQ:35350428
# 邮件:sale@100china.cn
# 手机：13584935775
# 作者：'amos'
# 公司网址： www.odoo.pw  www.100china.cn
# Copyright 昆山一百计算机有限公司 2012-2016 Amos
# 日期：2014-06-18
# &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError
from odoo.osv import expression
import odoo.addons.decimal_precision as dp

class stock_picking_price_unit_wizard(models.TransientModel):
    _name = 'stock.picking.price_unit.wizard'
    _description = u'库存价格修改'

    stock_lines = fields.One2many('stock.picking.price_unit.wizard.line', 'order_line', string=u'库存明细', copy=False)

    @api.model
    def default_get(self, fields):
        rec = super(stock_picking_price_unit_wizard, self).default_get(fields)
        context = dict(self._context or {})
        active_model = context.get('active_model')
        active_id = context.get('active_id')

        stock = self.env[active_model].browse(active_id)

        lines = []
        for o in stock.move_lines:
            pram = {
                'product_id': o.product_id.id,
                'product_uom_qty': o.product_uom_qty,
                'product_uom': o.product_uom,
                'name': o.name,
                'price_unit': o.price_unit,
                'line_id': o.id,
            }
            lines.append((0, 0, pram))

        rec.update({
            'stock_lines': lines,
        })
        return rec

    def action_done(self):
        lines = []
        order = self.env[self._context['active_model']].browse(self._context.get('active_id'))

        body = ''
        for line in self.stock_lines:
            if line.price_unit !=line.line_id.price_unit:
                body += u'<font style="color:red;font-size: 120%%">%s  原[%s] → [%s]</font>' % (
                    line.name, line.line_id.price_unit, line.price_unit)
                values = {
                    'price_unit': line.price_unit,
                }
                line.line_id.sudo().write(values)
        #::::判断是否有销售采购的应收应付如果是改价格

        id_object = '%s,%s' % (order._name,order.id)
        account = self.env['account.account'].search([('id_object', '=', id_object)], limit=1)
        if account:
            values = {
                'amount': order.amount,
            }
            account.sudo().write(values)

        order.message_post(body=body)


class stock_picking_price_unit_wizard_line(models.TransientModel):
    _name = "stock.picking.price_unit.wizard.line"
    _description = u"库存价格修改明细"

    order_line = fields.Many2one('stock.picking.price_unit.wizard', string=u'明细', ondelete='cascade', copy=False)
    product_id = fields.Many2one('product.product', string=u'物资')
    product_uom_qty = fields.Float(string=u'数量', required=True, default=1.0,digits=dp.get_precision('Product Unit of Measure'))
    name = fields.Char(string=u'物资全称', )
    product_uom = fields.Char(related='product_id.product_uom',string=u'单位', readonly=True)
    note = fields.Text(u'备注')
    price_unit = fields.Float(u'单价', required=True,  default=0.0)
    line_id = fields.Many2one('stock.move', string=u'库存明细', copy=False)
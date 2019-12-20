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


class inventory_product_wizard(models.TransientModel):
    _name = 'inventory.product.wizard'
    _description = u'盘点产品'

    category_ids = fields.Many2many('product.category', 'inventory_product_wizard_product_category_rel', 'product_id',
                                    'category_id',string='产品分类',)
    warehouse_ids = fields.Many2many('stock.warehouse', 'inventory_product_wizard_stock_warehouse_rel', 'product_id',
                                    'category_id', string='仓库', )


    def action_done(self):
        context = dict(self._context or {})
        active_id = context.get('active_id')
        active_model = context.get('active_model')
        picking = self.env[active_model].browse(active_id)

        if self.category_ids:
            domain=[('categ_id', 'in', self.category_ids._ids)]
            product = self.env['product.product'].search(domain)
            for line in product:
                if line.warehouse_ids:
                    for warehouse in product.warehouse_ids:
                        if warehouse.id in self.warehouse_ids._ids:

                            domain=[('picking_id', '=', picking.id),('product_id', '=', line.id),('warehouse_id', '=', warehouse.id)]
                            move = self.env['stock.move'].search(domain, limit=1)
                            values = {
                                'picking_id': picking.id,
                                'product_id': line.id,
                                'name': line.name_get()[0][1],
                                'product_qty': warehouse.location_qty,
                                'product_uom_qty': warehouse.location_qty,
                                'warehouse_id': warehouse.id,
                            }
                            if move:
                                move.sudo().write(values)
                            else:
                                self.env['stock.move'].sudo().create(values)
            else:
                for line in product:
                    for warehouse in line.warehouse_ids:
                        domain = [('picking_id', '=', picking.id), ('product_id', '=', line.id),
                                  ('warehouse_id', '=', warehouse.id)]
                        move = self.env['stock.move'].search(domain, limit=1)
                        values = {
                            'picking_id': picking.id,
                            'product_id': line.id,
                            'name': line.name_get()[0][1],
                            'product_qty': warehouse.location_qty,
                            'product_uom_qty': warehouse.location_qty,
                            'warehouse_id': warehouse.id,
                        }
                        if move:
                            move.sudo().write(values)
                        else:
                            self.env['stock.move'].sudo().create(values)
        else:
            #只选了仓库
            domain = [('warehouse_id', 'in', self.warehouse_ids._ids)]
            product = self.env['product.stock'].search(domain)
            for line in product:
                for warehouse in line:
                    domain = [('picking_id', '=', picking.id), ('product_id', '=', line.name.id),
                              ('warehouse_id', '=', warehouse.warehouse_id.id)]
                    move = self.env['stock.move'].search(domain, limit=1)
                    values = {
                        'picking_id': picking.id,
                        'product_id': line.name.id,
                        'name': line.name_get()[0][1],
                        'product_qty': warehouse.location_qty,
                        'product_uom_qty': warehouse.location_qty,
                        'warehouse_id': warehouse.warehouse_id.id,
                    }
                    if move:
                        move.sudo().write(values)
                    else:
                        self.env['stock.move'].sudo().create(values)

        return True
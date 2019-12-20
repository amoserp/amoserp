# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError


class union_product_stock_wizard(models.TransientModel):
    _name = "union.product.stock.wizard"
    _description = u"仓库合并并删除前者"

    form_warehouse = fields.Many2one('product.stock', string=u'从物资仓库', required=True)
    to_warehouse = fields.Many2one('product.stock', string=u'到物资仓库', required=True)


    def union_product(self):
        form_warehouse = self.form_warehouse
        to_warehouse = self.to_warehouse

        if form_warehouse.name.id == to_warehouse.name.id:

            if form_warehouse.warehouse_id.id == to_warehouse.warehouse_id.id and form_warehouse.company_id.id == to_warehouse.company_id.id:
                raise UserError(u'合并库位不能一致!')
            values = {
                'location_qty': to_warehouse.location_qty + form_warehouse.location_qty
            }
            to_warehouse.write(values)
            values = {
                'location_qty': 0
            }
            form_warehouse.write(values)
            # form_warehouse.unlink()
            # self._cr.execute("DELETE FROM product_stock WHERE id =%s " % (form_warehouse.id))
        else:
            raise UserError(u'合并物资不一致!')

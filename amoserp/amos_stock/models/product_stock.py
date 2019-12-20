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
from . import public_key as a
import math
from datetime import datetime, timedelta

ORDER_STATES = [
    (u'新建', u'新建'),
    (u'处理中', u'处理中'),
    (u'已审核', u'已审核'),
]

READONLY_STATES = {
    u'已审核': [('readonly', True)],
    u'处理中': [('readonly', True)],
}


class product_stock(models.Model):
    _name = 'product.stock'
    _description = u"存货信息"
    _log_access = False


    def _compute_location(self):
        for line in self:
            product_min_qty = 0.00
            product_max_qty = 0.00
            pram = {}
            if line.product_id.type != 'service':
                self._cr.execute(
                    "SELECT product_max_qty,product_min_qty  FROM stock_warehouse_orderpoint where product_id=%s and company_id=%s and warehouse_id=%s limit 1" % (
                        line.product_id.id, line.company_id.id, line.warehouse_id.id))
                data = self._cr.dictfetchall()
                if data != []:
                    product_max_qty = data[0]['product_max_qty']
                    product_min_qty = data[0]['product_min_qty']
                pram['product_min_qty'] = product_min_qty
                pram['product_max_qty'] = product_max_qty
                line.update(pram)


    def _compute_location_qty(self):
        for line in self:
            location_in = 0.00
            location_out = 0.00
            virtual_available_in = 0.00
            virtual_available_out = 0.00
            pram = {}
            if line.product_id.type != 'service':

                #:::::仓库里实物存在的 开始
                sql = "SELECT sum(product_uom_qty)  FROM stock_move where product_id=%s and type='in' and warehouse_id=%s and state='已完成'" % (
                    line.product_id.id, line.warehouse_id.id)
                self._cr.execute(sql)
                point = self._cr.fetchall()
                location_in = point[0][0] or 0.00

                sql = "SELECT sum(product_uom_qty)  FROM stock_move where product_id=%s and type='out' and warehouse_id=%s and state='已完成'" % (
                    line.product_id.id, line.warehouse_id.id)
                self._cr.execute(sql)
                point = self._cr.fetchall()
                location_out = point[0][0] or 0.00
                #:::::仓库里实物存在的 结束
                pram['location_qty'] = location_in - location_out

                # #:::::现有借出 开始
                # sql = "SELECT sum(product_uom_qty)  FROM stock_move where product_id=%s and type='other' and warehouse_id=%s and backorder_id_picking_type_id_name='送检单' and picking_type_id_name='丢失单'" % (
                #     line.product_id.id, line.warehouse_id.id)
                # self._cr.execute(sql)
                # point = self._cr.fetchall()
                # lost_qty = point[0][0] or 0.00
                #
                # sql = "SELECT sum(product_uom_qty)  FROM stock_move where product_id=%s and type='other' and warehouse_id=%s and backorder_id_picking_type_id_name='借出单' and picking_type_id_name='丢失单'" % (
                #     line.product_id.id, line.warehouse_id.id)
                # self._cr.execute(sql)
                # point = self._cr.fetchall()
                # location_in2 = point[0][0] or 0.00
                #
                # #:::::现有借出 结束

                # #:::::预测数量 开始
                sql = "SELECT sum(product_uom_qty)  FROM stock_move where product_id=%s and type='in' and warehouse_id=%s " % (
                    line.product_id.id, line.warehouse_id.id)
                self._cr.execute(sql)
                point = self._cr.fetchall()
                location_in = point[0][0] or 0.00

                sql = "SELECT sum(product_uom_qty)  FROM stock_move where product_id=%s and type='out' and warehouse_id=%s " % (
                    line.product_id.id, line.warehouse_id.id)
                self._cr.execute(sql)
                point = self._cr.fetchall()
                location_out = point[0][0] or 0.00
                #:::::仓库里实物存在的 结束
                pram['virtual_available'] = location_in - location_out
                # #:::::预测数量 结束

                line.update(pram)

    name = fields.Char(string=u'产品全称')
    product_id = fields.Many2one('product.product', string=u'产品', required=True, copy=False)
    warehouse_id = fields.Many2one('stock.warehouse', u'仓库名称', required=True, )
    company_id = fields.Many2one('res.company', string=u'公司')
    uom_id = fields.Many2one(related='product_id.uom_id', string=u'单位')
    location_qty = fields.Float(string=u'现有库存数量', compute='_compute_location_qty', help=u'仓库里实物存在的')
    virtual_available = fields.Float(string=u'预测数量', compute='_compute_location_qty', help=u'预测数量')
    default_code = fields.Char(related='product_id.default_code', string=u'物资编号', readonly=True)
    specification = fields.Char(related='product_id.specification', string=u'物资规格', readonly=True)
    product_name = fields.Char(related='product_id.name', string=u'物资名称', readonly=True)
    product_min_qty = fields.Float(compute='_compute_location', string=u'安全最小数量', readonly=True)
    product_max_qty = fields.Float(compute='_compute_location', string=u'安全最大数量', readonly=True)



    def _compute_lend_out_qty(self):
        for line in self:
            # if not isinstance(line.product_id.id, models.NewId):
                if line.product_id.type != 'service':
                    pram = {}

                    sql = "SELECT sum(product_uom_qty)  FROM stock_move where product_id=%s and type='in' and warehouse_id=%s and state='已完成' and picking_type_id_name='借出还入单'" % (
                    line.product_id.id, line.warehouse_id.id)
                    self._cr.execute(sql)
                    point = self._cr.fetchall()
                    location_in1 = point[0][0] or 0.00

                    sql = "SELECT sum(product_uom_qty)  FROM stock_move where product_id=%s and type='other' and warehouse_id=%s and state='已完成' and backorder_id_picking_type_id_name='借出单' and picking_type_id_name='丢失单'" % (
                        line.product_id.id, line.warehouse_id.id)
                    self._cr.execute(sql)
                    point = self._cr.fetchall()
                    location_in2 = point[0][0] or 0.00

                    location_in = location_in1 + location_in2

                    sql = "SELECT sum(product_uom_qty)  FROM stock_move where product_id=%s and type='out' and warehouse_id=%s and state='已完成' and picking_type_id_name='借出单'" % (
                    line.product_id.id, line.warehouse_id.id)
                    self._cr.execute(sql)
                    point = self._cr.fetchall()
                    location_out = point[0][0] or 0.00

                    pram['lend_out_qty'] =  location_out - location_in
                    line.update(pram)

    lend_out_qty = fields.Float(compute='_compute_lend_out_qty', string=u'现有借出', readonly=True)


    def _compute_tested_out_qty(self):
        for line in self:
            # if not isinstance(line.product_id.id, models.NewId):
                if line.product_id.type != 'service':
                    pram = {}

                    sql = "SELECT sum(product_uom_qty)  FROM stock_move where product_id=%s and type='in' and state='已完成' and warehouse_id=%s and picking_type_id_name='送检还入单'" % (
                    line.product_id.id, line.warehouse_id.id)
                    self._cr.execute(sql)
                    point = self._cr.fetchall()
                    location_in1 = point[0][0] or 0.00

                    sql = "SELECT sum(product_uom_qty)  FROM stock_move where product_id=%s and type='other' and state='已完成' and warehouse_id=%s and backorder_id_picking_type_id_name='送检单' and picking_type_id_name='丢失单'" % (
                        line.product_id.id, line.warehouse_id.id)
                    self._cr.execute(sql)
                    point = self._cr.fetchall()
                    location_in2 = point[0][0] or 0.00

                    location_in = location_in1 + location_in2

                    sql = "SELECT sum(product_uom_qty)  FROM stock_move where product_id=%s and type='out' and state='已完成' and warehouse_id=%s and picking_type_id_name='送检单' " % (
                    line.product_id.id, line.warehouse_id.id)
                    self._cr.execute(sql)
                    point = self._cr.fetchall()
                    location_out = point[0][0] or 0.00

                    pram['tested_out_qty'] =  location_out - location_in
                    line.update(pram)

    tested_out_qty = fields.Float(compute='_compute_tested_out_qty', string=u'现有送检', readonly=True)

    @api.depends('name', 'warehouse_id', 'company_id')
    def name_get(self):
        result = []
        for product in self:
            name = product.warehouse_id.name + ' ' + product.product_id.name + ' ' + product.company_id.name
            result.append((product.id, name))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            name = name.split(' / ')[-1]
            args = [('name', operator, name)] + args
        return self.search(args, limit=limit).name_get()

    def unlink(self):
        for order in self:
            if self._uid != 2:
                raise UserError(u'只有超级管理员才能删除!')
        return super(product_stock, self).unlink()

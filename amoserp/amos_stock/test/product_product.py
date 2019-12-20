# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError
from odoo.osv import expression
import odoo.addons.decimal_precision as dp

ORDER_STATES = [
    (u'新建', u'新建'),
    (u'处理中', u'处理中'),
    (u'已审核', u'已审核'),
]
MANAGER_STATES = [
    (u'未查阅', u'未查阅'),
    (u'已读并确认', u'已读并确认'),
    (u'已读并拒绝', u'已读并拒绝'),
]

READONLY_STATES = {
    u'已审核': [('readonly', True)],
    u'处理中': [('readonly', True)],
}


class product_product(models.Model):
    _inherit = 'product.product'


    def _compute_qty(self):
        for line in self:
            existing_paper_qty = initial_paper_qty = initial_sale_qty = initial_purchase_qty = existing_sale_qty = existing_purchase_qty = initial_real_qty=function_stock =product_reserved_qty= 0.00


            pram = {}
            sale_qty = 0.00 #可销售数量
            existing_real_qty = 0.00 #现有实际数量
            initial_paper_qty = 0.00 #期初数量
            for lines in line.warehouse_ids:
                #     sale_qty += lines.location_qty #可销售数量
                existing_real_qty += lines.location_qty #现有实际数量
                initial_paper_qty += lines.initial_qty #期初数量

            # pram['sale_qty'] = sale_qty #可销售数量
            pram['existing_real_qty'] = existing_real_qty #现有实际数量

            # #:::::::安全最大数量
            # self._cr.execute(
            #     "SELECT sum(product_uom_qty) FROM product_reserved WHERE state='done' and product_id ='%s' " % (
            #         line.id))
            # function_stock = self._cr.fetchone()[0]
            # pram['function_stock'] = function_stock



            # #:::::::安全最大数量
            pram['function_stock'] = function_stock

            # #:::::::期初帐面数量
            pram['initial_paper_qty'] = initial_paper_qty

            # #:::::::期初实际数量
            pram['initial_real_qty'] = initial_real_qty


            # #:::::::期初已采未入
            pram['initial_purchase_qty'] = initial_purchase_qty

            # #:::::::现有帐面数量
            pram['existing_paper_qty'] = existing_paper_qty



            data = self._cr.dictfetchall()
            if data != []:
                existing_purchase_qty = data[0]['qty']
            pram['existing_purchase_qty'] = existing_purchase_qty

            # #:::::::预留物资
            pram['product_reserved_qty'] = product_reserved_qty


            line.update(pram)


    warehouse_ids = fields.One2many('product.stock', 'name', string=u"存货信息", readonly=True)
    warehouse_id = fields.Many2one('stock.warehouse', string=u'默认库位', states=READONLY_STATES,
                                  default=lambda self: self.env.user.company_id.warehouse_id.id,
                                  track_visibility='onchange')
    is_qc = fields.Boolean(default=False, string=u'是否质检',states=READONLY_STATES)
    function_stock = fields.Float(compute='_compute_qty', string=u'安全最大数量', readonly=True)
    initial_paper_qty = fields.Float(compute='_compute_qty', string=u'期初数量', type='float', multi='all',
                                     help=u'显示此物资于各仓库之期初数量的合计值')
    initial_real_qty = fields.Float(compute='_compute_qty', string=u'期初实际数量', type='float', multi='all',
                                    help=u'显示此物资于各仓库之期初实际数量的合计值 期初实际=期初帐面+期初借入-期初借出')
    initial_sale_qty = fields.Float(compute='_compute_qty', string=u'期初受订未出', type='float', multi='all',
                                    help=u'显示此物资上线当时之订购未出数量')
    initial_purchase_qty = fields.Float(compute='_compute_qty', string=u'期初已采未入', type='float', multi='all',
                                        help=u'显示此物资上线当时之采购未入数量')
    existing_paper_qty = fields.Float(compute='_compute_qty', string=u'现有帐面数量', type='float', multi='all',
                                      help=u'现有帐面数量=现有实际数量+现有已采未入-现有受订未出 ')
    existing_real_qty = fields.Float(compute='_compute_qty', string=u'现有实际数量', type='float', multi='all',
                                     help=u'显示此物资于各仓库之现有实际数量的合计值')
    existing_sale_qty = fields.Float(compute='_compute_qty', string=u'现有受订未出', type='float', multi='all',
                                     help=u'显示此物资目前之订购未出数量')
    existing_purchase_qty = fields.Float(compute='_compute_qty', string=u'现有已采未入', type='float', multi='all',
                                         help=u'显示此物资目前之采购未入数量')
    product_reserved_qty = fields.Float(compute='_compute_qty', string=u'预留物资', readonly=True)

    stagnant_period = fields.Integer(string=u'呆滞周期', default=30, help=u"超出这个天数进行提醒")



    def button_warehouse_product(self):
        records = self.search([('type', '!=', 'service')])
        for line in records:
            line.button_done()

    def button_done(self):

        stock_warehouse_obj = self.env['stock.warehouse']
        product_stock_obj = self.env['product.stock']
        obj_array = stock_warehouse_obj.search([])

        for oo in obj_array:
            self._cr.execute(
                "SELECT count(*) FROM product_stock WHERE name ='%s' and company_id ='%s' and warehouse_id ='%s' " % (
                    self.id, oo.company_id.id, oo.id))
            lines = self._cr.fetchall()
            if long(lines[0][0]) == 0:
                pram = {
                    'name': self.id,
                    'warehouse_id': oo.id,
                    'company_id': oo.company_id.id,
                    'uom_id': self.uom_id.name,
                }
                product_stock_obj.create(pram)
        #::::判断如果存在规格价格 合计所有价更新主窗口价

        # #::::更新所有价格
        # for product in self.pricelist:
        #     if product.discount>0:
        #         values = {
        #             'price_unit': product.discount * product.product_id.public_price / 100,
        #         }
        #         product.write(values)

        # public_price = 0.00
        # for line in self.specs_ids:
        #     public_price += line.price_unit
        # if public_price > 0:
        #     self.public_price = public_price


class product_mix_bom(models.Model):
    _name = 'product.mix.bom'

    BOM_TYPE = [
        ('assembly', u'组装单'),
        ('disassembly', u'拆卸单'),
    ]

    name = fields.Char(u'模板名称')
    type = fields.Selection(BOM_TYPE, u'类型', default=lambda self: self.env.context.get('type'))
    line_parent_ids = fields.One2many('product.mix.bom.line', 'bom_id', u'组合件', domain=[('type', '=', 'parent')],
                                      context={'type': 'parent'}, copy=True)
    line_child_ids = fields.One2many('product.mix.bom.line', 'bom_id', u'子件', domain=[('type', '=', 'child')],
                                     context={'type': 'child'}, copy=True)


class product_mix_bom_line(models.Model):
    _name = 'product.mix.bom.line'

    BOM_LINE_TYPE = [
        ('parent', u'组合件'),
        ('child', u'子间'),
    ]

    bom_id = fields.Many2one('product.mix.bom', u'模板')
    type = fields.Selection(BOM_LINE_TYPE, u'类型', default=lambda self: self.env.context.get('type'))
    product_id = fields.Many2one('product.product', u'物资', default=1)
    product_uom_qty = fields.Float(u'数量', default=1.0,digits=dp.get_precision('Product Unit of Measure'))

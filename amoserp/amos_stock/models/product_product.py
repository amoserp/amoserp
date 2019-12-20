# -*- coding: utf-8 -*-
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
import odoo.addons.decimal_precision as dp
from datetime import datetime, timedelta
import pytz
from dateutil.relativedelta import relativedelta

ORDER_STATES = [
    (u'新建', u'新建'),
    (u'处理中', u'处理中'),
    (u'已审核', u'已审核'),
]

READONLY_STATES = {
    u'已审核': [('readonly', True)],
    u'处理中': [('readonly', True)],
}
_intervalTypes = {
    'days': lambda interval: relativedelta(days=interval),
    'weeks': lambda interval: relativedelta(days=7 * interval),
    'months': lambda interval: relativedelta(months=interval),
    'years': lambda interval: relativedelta(years=interval),
}


class product_product(models.Model):
    _inherit = 'product.product'

    def _compute_sale_order_qty(self):
        return 0.00

    def _compute_stock_picking_outsourc_out_qty(self):
        return 0.00

    def _compute_product_qty(self):
        for line in self:
            pram = {}
            qty = 0.00  # 合计数量
            tested_qty = 0.00
            if line.type != 'service':
                for lines in line.warehouse_ids:
                    qty += lines.location_qty  # 合计数量

                # sql = "SELECT sum(product_uom_qty)  FROM stock_move where product_id=%s and type='in' and company_id=%s and  state='处理中' and initial in ('采购申请单','期初销售退货','期初采购入库','期初借入','期初借出','期初数量','期初委外出库还入单','现有委外出库还入单','现有借出还入','现有借入','生产入库','生产计划入库','生产退料','盘盈','采购样品入库','采购订单','期初采购订单','采购样品订单','销售样品退货','收银退货','其它入库')  " % (
                # line.id, line.company_id.id)
                # self._cr.execute(sql)
                # point = self._cr.fetchall()
                # location_in = point[0][0] or 0.00
                #
                # sql = "SELECT sum(product_uom_qty)  FROM stock_move where product_id=%s and type='out' and company_id=%s and  state='处理中' and initial in ('期初销售出库','期初采购退货','期初借入还出','期初借出还入','期初委外出库单','现有委外出库单','现有借出','现有借入还出','生产领料','生产计划领料','盘亏','采购样品退货','期初销售订单','销售订单','电商订单','销售样品订单','销售样品出库','销售电商出库','收银开单','服务工单出库','其它出库','固定资产')  " % (
                # line.id, line.company_id.id)
                # self._cr.execute(sql)
                # point = self._cr.fetchall()
                # location_out = point[0][0] or 0.00
                #
                # #:::减销售订单数量
                #
                #
                # sql = "SELECT sum(product_uom_qty)  FROM sale_bom_line_sum where product_id=%s " % (line.id)
                # self._cr.execute(sql)
                # point = self._cr.fetchall()
                # bom_qty = point[0][0] or 0.00

                sale_order_qty = line._compute_sale_order_qty()
                purchase_order_qty = 0  # line.existing_purchase_qty
                stock_picking_outsourc_out_qty = line._compute_stock_picking_outsourc_out_qty()

                #::送检数量 开始计算
                sql = "SELECT sum(product_uom_qty)  FROM stock_move where product_id=%s and type='in'  and state='已完成' and picking_type_id_name='送检还入单'" % (
                    line.id)
                self._cr.execute(sql)
                point = self._cr.fetchall()
                tested_qty1 = point[0][0] or 0.00

                sql = "SELECT sum(product_uom_qty)  FROM stock_move where product_id=%s and type='other' and backorder_id_picking_type_id_name='送检单' and state='已完成' and picking_type_id_name='丢失单'" % (
                    line.id)
                self._cr.execute(sql)
                point = self._cr.fetchall()
                tested_qty2 = point[0][0] or 0.00

                tested_qty_in = tested_qty1 + tested_qty2

                sql = "SELECT sum(product_uom_qty)  FROM stock_move where product_id=%s and type='out' and state='已完成' and picking_type_id_name='送检单'" % (
                    line.id)
                self._cr.execute(sql)
                point = self._cr.fetchall()
                tested_qty_out = point[0][0] or 0.00
                pram['tested_qty'] = tested_qty_out - tested_qty_in
                #::送检数量 计算结束

                #:::::::合计数量
                pram['qty'] = qty
                #:::::::可销售数量
                pram['forecast_qty'] = sale_order_qty + purchase_order_qty + stock_picking_outsourc_out_qty

                line.update(pram)


    warehouse_ids = fields.One2many('product.stock', 'product_id', string=u"存货信息", readonly=True)
    warehouse_id = fields.Many2one('stock.warehouse', string=u'默认库位', states=READONLY_STATES,
                                   default=lambda self: self.env.user.company_id.warehouse_id.id)
    is_qc = fields.Boolean(default=False, string=u'是否质检', states=READONLY_STATES, track_visibility='onchange')
    qty = fields.Float(compute='_compute_product_qty', string=u'现有数量', type='float', multi='all', help=u'库位之和')
    tested_qty = fields.Float(compute='_compute_product_qty', string=u'送检数量数量', type='float')
    forecast_qty = fields.Float(compute='_compute_product_qty', string=u'预测数量', type='float', multi='all', help=u'库位之和')
    stagnant_period = fields.Integer(string=u'呆滞周期', default=30, help=u"超出这个天数进行提醒")

    test_date_done = fields.Datetime(string='检查合格日期', track_visibility='onchange')
    beginning_result = fields.Char(string='上一次检定结果', track_visibility='onchange')
    interval_type = fields.Selection([
        # ('hours', u'小时'),
        # ('days', u'天'),
        # ('weeks', u'周'),
        ('月', u'月'),
        ('年', u'年'),
    ], string=u'检定周期', default='年', states=READONLY_STATES, track_visibility='onchange')
    interval_number = fields.Integer(default=1, string='周期参数', states=READONLY_STATES, track_visibility='onchange')
    next_time = fields.Date(string=u'下一次检定日期', states=READONLY_STATES, copy=False, track_visibility='onchange')

    product_tested_ids = fields.One2many('stock.move', compute='_view_product_tested_ids', string=u'送检产品')

    @api.depends()
    def _view_product_tested_ids(self):
        for model in self:
            type_id = self.env.ref('amos_stock.stock_picking_type_tested_a').id
            model.product_tested_ids = self.env['stock.move'].sudo().search([('picking_type_id', '=', type_id),('product_id', '=', model.id)])

    def _compute_lend_out_qty(self):
        for line in self:
            lend_out_qty = 0.00
            pram = {}
            for o in line.warehouse_ids:
                lend_out_qty += o.lend_out_qty
            pram['existing_lend_out_qty'] = lend_out_qty
            line.update(pram)

    existing_lend_out_qty = fields.Float(compute='_compute_lend_out_qty', string=u'现有借出', type='float', multi='all')

    purchase_delivery_time = fields.Integer(string=u'采购交期(天)', default=1, states=READONLY_STATES)

    def button_warehouse_product(self):
        records = self.search([('type', '!=', 'service')])
        for line in records:
            line.button_done()

    def button_product_inout(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/report/inout/%s' % self.id,
            'nodestroy': True,
            'target': 'new',
        }

    @api.model
    def update_next_stock_picking_tested(self):
        #::提前一周提示
        now = fields.Datetime.context_timestamp(self, datetime.now())
        nextcall = fields.Datetime.context_timestamp(self, fields.Datetime.from_string(str(now)))
        nextcall += _intervalTypes['days'](-7)
        next_time = fields.Datetime.to_string(nextcall.astimezone(pytz.UTC))

        tested = self.search([('next_time', '>=', next_time)])
        picking_type_id = self.env.ref('amos_stock.stock_picking_type_tested_b').id
        for product in tested:

            if product.qty > 0:
                #::::判断是不是 已创建 如果是跳过
                domain = [('product_id', '=', product.id), ('state', 'in', ['新建', '待审批', '仓库', '扫码']),
                          ('picking_type_id', '=', picking_type_id)]
                rows_count = self.env['stock.move'].search_count(domain)
                if rows_count == 0:
                    move_lines = []
                    pram = {
                        'name': product.name_get(),
                        'product_id': product.id,
                        'product_uom_qty': 1,
                        'price_unit': product.purchase_price,
                        # 'warehouse_id': product.warehouse_id.id,
                        'date_expected': product.next_time,
                        'type': 'out',
                    }
                    move_lines.append((0, 0, pram))

                    values = {
                        'name': '/',
                        'partner_id': product.company_id.partner_id.id,

                        'other_id': product.user_id.id,
                        'picking_type_id': picking_type_id,
                        'move_lines': move_lines,
                    }
                    self.env['stock.picking'].sudo().with_context(default_picking_type_id=picking_type_id).create(
                        values)

    def _next_time(self, now, interval_type, interval_number):
        """
        根据检定日期 检定周期 周期参数 计算下一次检验时间
        :param picking:
        :return:
        """
        if interval_type == '月':
            nextcall = fields.Datetime.context_timestamp(self, fields.Datetime.from_string(str(now)))
            nextcall += _intervalTypes['months'](interval_number)
            next_time = fields.Datetime.to_string(nextcall.astimezone(pytz.UTC))
            return next_time

        elif interval_type == '年':
            nextcall = fields.Datetime.context_timestamp(self, fields.Datetime.from_string(str(now)))
            nextcall += _intervalTypes['years'](interval_number)
            next_time = fields.Datetime.to_string(nextcall.astimezone(pytz.UTC))
            return next_time

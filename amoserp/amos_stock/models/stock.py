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
import odoo
from datetime import datetime, timedelta
import odoo.addons.decimal_precision as dp
from datetime import date, timedelta, datetime
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from dateutil.relativedelta import relativedelta
import pytz

_intervalTypes = {
    'months': lambda interval: relativedelta(months=interval),
    'years': lambda interval: relativedelta(years=interval),
}

READONLY_STATES = {
    u'待审批': [('readonly', True)],
    u'仓库': [('readonly', True)],
    u'扫码': [('readonly', True)],
    u'已完成': [('readonly', True)],
}

PROCUREMENT_PRIORITIES = [('0', '不急'), ('1', '正常的'), ('2', '紧急'), ('3', '非常紧急')]


class stock_picking(models.Model):
    _name = "stock.picking"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = u"仓库管理"
    # _order = "date asc, id desc"
    _order = "id desc"

    state = fields.Selection([
        (u'新建', u'新建'),
        (u'待审批', u'待审批'),
        (u'仓库', u'仓库'),
        (u'扫码', u'扫码'),
        (u'已完成', u'已完成'),
    ], string=u'状态', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3,
        default='新建')
    name = fields.Char(string=u'单据编号', required=True, copy=False, readonly=True, index=True, default='/')
    partner_id = fields.Many2one('res.partner', '业务伙伴', states=READONLY_STATES)
    company_id = fields.Many2one('res.company', '公司', index=True, required=True, states=READONLY_STATES,
                                 default=lambda self: self.env['res.company']._company_default_get('stock.picking'))
    user_id = fields.Many2one('res.users', string=u'物资管理员', index=True, track_visibility='onchange',
                              states=READONLY_STATES)
    department_id = fields.Many2one('hr.department', string=u'专业队', states=READONLY_STATES)

    origin = fields.Char(string=u'单据来源', copy=False, states=READONLY_STATES)
    note = fields.Text(u'备注', states=READONLY_STATES, track_visibility='onchange')
    backorder_id = fields.Many2one('stock.picking', '上级', copy=False, index=True, states=READONLY_STATES)
    backorder_ids = fields.One2many('stock.picking', 'backorder_id', '劈单', states=READONLY_STATES)
    move_type = fields.Selection([
        ('direct', '分批交货'), ('one', '一次性交货')], '运输策略',
        default='direct', required=True,
        help="它指定部分或全部同时交货", states=READONLY_STATES)

    group_id = fields.Char('采购组', help=u'后面加上', states=READONLY_STATES)
    priority = fields.Selection(
        PROCUREMENT_PRIORITIES, string='优先级',
        compute='_compute_priority', inverse='_set_priority', store=True,
        index=True, track_visibility='onchange', )

    scheduled_date = fields.Datetime('安排的日期', compute='_compute_scheduled_date', inverse='_set_scheduled_date',
                                     store=True, index=True, track_visibility='onchange', )
    date = fields.Datetime('创建日期', default=fields.Datetime.now, index=True, track_visibility='onchange')
    date_done = fields.Datetime('调拨日期', copy=False, readonly=True)
    date_order = fields.Date(u'单据日期', track_visibility='onchange', states=READONLY_STATES,
                             default=fields.Date.context_today)
    date_order_str = fields.Char(string=u'文本单据日期', help=u'提供日期文本查询')

    location_id = fields.Many2one('stock.location', "源位置",
                                  default=lambda self: self.env['stock.picking.type'].browse(
                                      self._context.get('default_picking_type_id')).default_location_src_id, )
    location_dest_id = fields.Many2one('stock.location', "目的位置",
                                       default=lambda self: self.env['stock.picking.type'].browse(
                                           self._context.get('default_picking_type_id')).default_location_dest_id, )
    move_lines = fields.One2many('stock.move', 'picking_id', string="出入库明细", copy=True, states=READONLY_STATES)
    picking_type_id = fields.Many2one('stock.picking.type', '作业类型', states=READONLY_STATES)
    picking_type_code = fields.Selection([
        ('incoming', '供应商'),
        ('outgoing', '客户'),
        ('internal', '内部')],
        related='picking_type_id.code', readonly=True)
    picking_type_entire_packs = fields.Boolean(related='picking_type_id.show_entire_packs', readonly=True)
    picking_type_id_name = fields.Char(related='picking_type_id.name', readonly=True, store=True)
    backorder_id_picking_type_id_name = fields.Char(related='backorder_id.picking_type_id_name', readonly=True,
                                                    store=True,string='上级对象类型名称')
    move_line_ids = fields.One2many('stock.move.line', 'picking_id', '分批操作', states=READONLY_STATES)

    # show_check_availability = fields.Boolean(compute='_compute_show_check_availability', )
    # show_validate = fields.Boolean(compute='_compute_show_validate', )

    is_borrow_return = fields.Boolean(default=False, string=u'是否外部借用', track_visibility='onchange',
                                      states=READONLY_STATES)
    is_assets = fields.Boolean(u"是否包含固定资产", compute='_compute_product_id_is_assets', default=False,
                               states=READONLY_STATES)

    owner_id = fields.Many2one('res.partner', '业主', states=READONLY_STATES)
    product_id = fields.Many2one('product.product', '物资', related='move_lines.product_id', readonly=False)

    other_id = fields.Many2one('res.users', string=u'其它用户', index=True, track_visibility='onchange',
                               states=READONLY_STATES)
    auditor_id = fields.Many2one('res.users', string=u'部门经理', index=True, track_visibility='onchange',
                                 states=READONLY_STATES)
    auditor_id_date = fields.Datetime(string=u'部门经理审核日期')

    is_locked = fields.Boolean(default=True, states=READONLY_STATES)
    actions_id = fields.Many2one('ir.actions.act_window', string=u'窗口', help=u'默认不显示')

    @api.model
    def _select_reference(self):
        records = self.env['ir.model'].search([])
        return [(record.model, record.name) for record in records] + [('', '')]

    id_object = fields.Reference(string=u'关联', selection='_select_reference', states=READONLY_STATES)
    active = fields.Boolean(default=True, string=u'是否归档', track_visibility='onchange')
    stop_date = fields.Datetime(string=u'归档日期', readonly=True, index=True, states=READONLY_STATES, copy=False,
                                track_visibility='onchange')


    @api.depends('backorder_ids.state', 'state')
    def _get_document_state(self):
        for lines in self:
            for line in lines.move_lines:
                if line.picking_type_id_name in ['借出单', '送检单']:
                    if line.product_uom_qty == line.stock_out_in_owe_qty:
                        lines.document_state = u'未还'
                    elif line.product_uom_qty > line.stock_out_in_owe_qty and line.stock_out_in_owe_qty != 0:
                        lines.document_state = u'部分归还'
                        break
                    elif line.stock_out_in_owe_qty == 0:
                        lines.document_state = u'全部归还'
                        break
                    else:
                        lines.document_state = u'异常'

    def changeTime(self, allTime):
        day = 24 * 60 * 60
        hour = 60 * 60
        min = 60
        if allTime < 60:
            return u"%d秒" % math.ceil(allTime)
        elif allTime > day:
            days = divmod(allTime, day)
            return u"%d 天 %s" % (int(days[0]), self.changeTime(days[1]))
        elif allTime > hour:
            hours = divmod(allTime, hour)
            return u'%d 小时 %s' % (int(hours[0]), self.changeTime(hours[1]))
        else:
            mins = divmod(allTime, min)
            return u"%d 分 %d 秒" % (int(mins[0]), math.ceil(mins[1]))

    def _compute_duration(self):
        import datetime
        for order in self:

            if order.document_state != '全部归还':
                if order.delivery_date:
                    d1 = order.delivery_date
                    d2 = date.today()
                    a = ''
                    if d2 > d1:
                        delta = d2 - d1
                        data = self.changeTime(delta.seconds)
                        if order.document_state == u'全部归还':
                            return ''
                        if delta.days > 0:
                            # a = u'已过期%s天%s' % (delta.days,data)
                            a = u'已过期%s天' % (delta.days)
                        elif delta.days < 0:
                            a = u'还有%s天到期' % (delta.days)
                        elif delta.days == 0:
                            a = u'已过期%s' % data
                        else:
                            a = data
                    else:
                        delta = d1 - d2
                        # data = self.changeTime(delta.seconds)
                        data = self.changeTime(delta.seconds)
                        if order.document_state == u'全部归还':
                            return ''
                        if delta.days > 0:
                            a = u'还有%s天到期' % (delta.days)
                        elif delta.days < 0:
                            a = u'已过期%s天%s' % (delta.days, data)
                        elif delta.days == 0:
                            # a = u'还有%s 到期' % data
                            a = u'今天到期'
                        else:
                            a = data
                    order.duration = a

    document_state = fields.Char(u'其它状态', compute=_get_document_state, copy=False, store=True, )
    duration = fields.Char(string=u'归还日期表', compute='_compute_duration')
    delivery_date = fields.Date(u'归还日期 ', states=READONLY_STATES,

                                copy=False, track_visibility='onchange')

    @api.model
    def default_get(self, fields):
        res = super(stock_picking, self).default_get(fields)

        pram = {}
        if self._context['default_picking_type_id']:
            picking_type = self.env['stock.picking.type'].sudo().browse(int(self._context['default_picking_type_id']))
            if picking_type.name == '领用单':
                pram['other_id'] = self._uid
                pram['department_id'] = self.env.user.department_id.id
            elif picking_type.name == '借出单':
                pram['other_id'] = self._uid
                pram['department_id'] = self.env.user.department_id.id
                pram['delivery_date'] = (date.today() + timedelta(days=15)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            elif picking_type.name == '报废单':
                pram['other_id'] = self._uid
                pram['department_id'] = self.env.user.department_id.id
                pram['delivery_date'] = (date.today() + timedelta(days=15)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        # lines = []
        # for o in line:
        #     if o.type == 'service':
        #         pass
        #     else:
        #         pram = {
        #             'product_id': o.id,
        #             'attribute_id': o.attribute_id.id,
        #             'product_uom': o.product_uom,
        #             'color_ids': [(6, 0, o.color_ids.ids)],
        #         }
        #         lines.append((0, 0, pram))
        #
        res.update(pram)
        return res

    _sql_constraints = [
        ('name_uniq', 'unique(name, company_id)', 'Reference must be unique per company!'),
    ]

    @api.model
    def create(self, vals):
        # TDE FIXME: clean that brol
        defaults = self.default_get(['name', 'picking_type_id'])
        if vals.get('name', '/') == '/' and defaults.get('name', '/') == '/' and vals.get('picking_type_id',
                                                                                          defaults.get(
                                                                                              'picking_type_id')):
            vals['name'] = self.env['stock.picking.type'].browse(
                vals.get('picking_type_id', defaults.get('picking_type_id'))).sequence_id.next_by_id()

        # TDE FIXME: what ?
        # As the on_change in one2many list is WIP, we will overwrite the locations on the stock moves here
        # As it is a create the format will be a list of (0, 0, dict)
        if vals.get('move_lines') and vals.get('location_id') and vals.get('location_dest_id'):
            for move in vals['move_lines']:
                if len(move) == 3 and move[0] == 0:
                    move[2]['location_id'] = vals['location_id']
                    move[2]['location_dest_id'] = vals['location_dest_id']
        vals['date_order_str'] = fields.Date.context_today(self)
        #::::创建时计算窗体
        line = super(stock_picking, self).create(vals)
        # res._get_actions_id()


        #::::创建全局查询
        context = dict(self._context or {})
        url=self.env.user.s(line,context,line.picking_type_id_name,line.name)
        #:::::结束 创建全局查询
        return line


    def unlink(self):
        for order in self:
            if order.state != u'新建':
                raise UserError(u'只能删除新建单据!')
        return super(stock_picking, self).unlink()

    #
    # @api.onchange('other_id')
    # def onchange_other_id(self):
    #     if not self.other_id:
    #         self.update({
    #             'partner_id': False,
    #         })
    #         return
    #
    #     values = {}
    #     if self.other_id:
    #         values['partner_id'] = self.other_id.partner_id.id
    #     self.update(values)


    @api.depends('move_lines.date_expected')
    def _compute_scheduled_date(self):
        if self.move_type == 'direct':
            _scheduled_date = min(self.move_lines.mapped('date_expected') or [fields.Datetime.now()])
            if _scheduled_date:
                self.scheduled_date =_scheduled_date
        else:
            _scheduled_date = max(self.move_lines.mapped('date_expected') or [fields.Datetime.now()])
            if _scheduled_date :
                self.scheduled_date = _scheduled_date


    def _set_scheduled_date(self):
        self.move_lines.write({'date_expected': self.scheduled_date})


    @api.depends('move_lines.priority')
    def _compute_priority(self):

        if self.mapped('move_lines'):
            priorities = [priority for priority in self.mapped('move_lines.priority') if priority] or ['1']
            self.priority = max(priorities)
        else:
            self.priority = '1'

    def _compute_product_id_is_assets(self):
        """
        物资中是否有固定资产荐 如果有界面字段化调整
        :return:
        """
        for order in self:
            for line in order.move_lines:
                if line.product_id.is_assets:
                    if order.picking_type_id_name == '报废单':
                        if len(order.move_lines._ids) > 1:
                            raise ValidationError(u'警告：每次只能录入一个固定资产报废明细！')
                    order.is_assets = True
                    return True


    def toggle_active(self):
        for record in self:

            if not self.env['res.users'].has_group('amos_stock.stock_manager'):
                raise ValidationError(u'无权:需要 [仓库-管理员] 权限!')

            if record.state == u'已完成':
                record.active = not record.active
                if record.active:
                    record.stop_date = ''
                else:
                    record.stop_date = datetime.now()

    #
    # @api.model
    # def get_empty_list_help(self, help):
    #     """
    #     可以为不同的单据提供动态的说明,这个与default_get 冲突如果要使用要带上下文
    #     :param help:
    #     :return:
    #     """
    #     print(self.default_get)
    #     if help and "oe_view_nocontent_smiling_face" not in help:
    #         defaults = self.default_get(['name', 'picking_type_id'])
    #         picking_type = self.env['stock.picking.type'].browse(defaults.get('picking_type_id', defaults.get('picking_type_id')))
    #         return '<p class="oe_view_nocontent_smiling_face">%s</p>' % (picking_type.name)
    #     return super(stock_picking, self).get_empty_list_help(help)


    def button_compute(self, context=None):
        return []


    def button_loading_draft(self):
        self.write({'state': u'新建'})
        self._get_actions_id()
        return True


    def button_done_draft(self):
        if self.picking_type_id.name == '盘点单':
            # for line in self.backorder_ids:
            #     if line.state != '已完成':
            #         raise UserError(u'警告：请删除 盘盈/盘亏单')
            self.backorder_ids.write({'state': u'新建'})
            self.backorder_ids.unlink()
        elif self.picking_type_id.name in ['盘盈单', '盘亏单']:
            if self._uid == self.other_id.id:
                raise UserError(u'警告：当前单据只能由 %s 取消!' % self.other_id.name)
        elif self.picking_type_id.name in ['借出还入单', '送检还入单', '领用单', '入库单']:
            if self.backorder_ids:
                raise UserError(u'警告：先删除关联单据')
            if self._uid != self.user_id.id:
                raise UserError(u'警告：当前单据只能由物资管理员: %s 取消!' % self.user_id.name)
        elif self.picking_type_id.name in ['借出单']:
            if self.backorder_ids:
                raise UserError(u'警告：先删除 送检还入单f或丢失单')
        elif self.picking_type_id.name in ['送检单']:
            if self.backorder_ids:
                raise UserError(u'警告：先删除关联单据')
            if self.tested_lines:
                raise UserError(u'警告：先删除不合格处理单')
        values = {
            'state': u'新建',
            'user_id': False,
            'date_done': False,
            'auditor_id': False,
            'auditor_id_date': False,
        }
        self.write(values)
        self._get_actions_id()
        return True


    def button_loading(self):

        picking_type = self.env['stock.picking.type'].sudo().browse(int(self._context['default_picking_type_id']))
        #::::是否检查库存
        if picking_type.is_qty:
            for move in self.move_lines:
                if move.product_id.qty < move.product_uom_qty:
                    raise UserError(u'警告：库存不足')

        if self.picking_type_id.name in ['入库单', '借出还入单', '退料单', '送检单', '送检还入单']:
            if self.picking_type_id.name == '借出还入单':
                self._check_lend_qty()
            self.write({'state': u'仓库'})
            self._get_actions_id()
        else:
            self.write({'state': u'待审批'})
            self._get_actions_id()
        return True

    def _check_lend_qty(self):
        """
        校验 借出还入单 数量
        读取原来的借出数量 - 已归还的数量 + 本次归还的数量
        :return:
        """
        if self.id_object:
            for line in self.move_lines:
                if not line.parent_id:
                    raise UserError(u'警告：请从借出单抛入!')
                qty = line.product_uom_qty
                stock_out_in_owe_qty = line.parent_id.stock_out_in_owe_qty
                if stock_out_in_owe_qty == 0:
                    raise UserError(u'警告：归还产品:%s 不存在借出！' % line.product_id.name)

                if qty >stock_out_in_owe_qty:
                    raise UserError(u'警告：超出借出数量!')
        else:
            raise UserError(u'警告：单据错误!')



    def button_stock(self):
        if not self._uid in [1, 2]:
            power = self.env['hr.department.power'].sudo().search(
                [('power_id.name', 'in', ['科长', '经理', '副经理']), ('user_id', '=', self._uid),
                 ('department_id', '=', self.department_id.id)], limit=1)
            if not power:
                raise UserError(u'警告：您不是 %s部门的 [科长、经理、副经理]' % self.department_id.name)
        self.order_done()
        self.write({'state': u'仓库', 'auditor_id': self._uid, 'auditor_id_date': datetime.now()})
        self._get_actions_id()
        return True


    def button_done(self):

        if not self._uid in [1,2]:
            power = self.env['hr.department.power'].sudo().search(
                [('power_id.name', '=', '物资管理员'), ('user_id', '=', self._uid)], limit=1)
            if not power:
                raise UserError(u'警告：您不是 物资管理员,在部门的职位下添加一条）')

        if self.picking_type_id.name == '送检还入单':
            self._product_next_time()
        else:
            self.order_done()
        self.write({'state': u'已完成', 'user_id': self._uid, 'date_done': datetime.now()})
        if self.picking_type_id.name == '盘点单':
            self.add_overage_losses()

        self._get_actions_id()
        return True

    def _product_next_time(self):
        """
        如果是送检还入单 更新下次下一次检定日期
        :param picking:
        :return:
        """
        for move in self.move_lines:
            values = {
                'test_date_done': move.verification_date,
                'next_time': move.next_time,
                'interval_type': move.interval_type,
                'interval_number': move.interval_number,
            }
            move.product_id.write(values)
            body = '%s 更新了，下一次检定日期 来源:%s' % (self.env.user.name, self.name)
            move.product_id.message_post(body=body)

    def _get_actions_id(self):
        """
        根据当前 作业类型 判断当前窗口事件用于工作台跳转
        :return:
        """
        if self.picking_type_id.name == '入库单' and self.state == '新建':
            self.actions_id = self.env.ref('amos_stock.odoo_stock_picking_in_actions_state1').id
        elif self.picking_type_id.name == '入库单' and self.state == '待审批':
            self.actions_id = self.env.ref('amos_stock.odoo_stock_picking_in_actions_state2').id
        elif self.picking_type_id.name == '入库单' and self.state == '仓库':
            self.actions_id = self.env.ref('amos_stock.odoo_stock_picking_in_actions_state3').id
        elif self.picking_type_id.name == '入库单' and self.state == '已完成':
            self.actions_id = self.env.ref('amos_stock.odoo_stock_picking_in_actions_state4').id

        elif self.picking_type_id.name == '领用单' and self.state == '新建':
            self.actions_id = self.env.ref('amos_stock.odoo_stock_picking_out_actions_state1').id
        elif self.picking_type_id.name == '领用单' and self.state == '待审批':
            self.actions_id = self.env.ref('amos_stock.odoo_stock_picking_out_actions_state2').id
        elif self.picking_type_id.name == '领用单' and self.state == '仓库':
            self.actions_id = self.env.ref('amos_stock.odoo_stock_picking_out_actions_state3').id
        elif self.picking_type_id.name == '领用单' and self.state == '已完成':
            self.actions_id = self.env.ref('amos_stock.odoo_stock_picking_out_actions_state4').id

        elif self.picking_type_id.name == '借出单' and self.state == '新建':
            self.actions_id = self.env.ref('amos_stock.odoo_stock_lend_out_actions_state1').id
        elif self.picking_type_id.name == '借出单' and self.state == '待审批':
            self.actions_id = self.env.ref('amos_stock.odoo_stock_lend_out_actions_state2').id
        elif self.picking_type_id.name == '借出单' and self.state == '仓库':
            self.actions_id = self.env.ref('amos_stock.odoo_stock_lend_out_actions_state3').id
        elif self.picking_type_id.name == '借出单' and self.state == '已完成':
            self.actions_id = self.env.ref('amos_stock.odoo_stock_lend_out_actions_state4').id

        elif self.picking_type_id.name == '借出还入单' and self.state == '新建':
            self.actions_id = self.env.ref('amos_stock.odoo_stock_lend_out_in_actions_state1').id
        elif self.picking_type_id.name == '借出还入单' and self.state == '待审批':
            self.actions_id = self.env.ref('amos_stock.odoo_stock_lend_out_in_actions_state2').id
        elif self.picking_type_id.name == '借出还入单' and self.state == '仓库':
            self.actions_id = self.env.ref('amos_stock.odoo_stock_lend_out_in_actions_state3').id
        elif self.picking_type_id.name == '借出还入单' and self.state == '已完成':
            self.actions_id = self.env.ref('amos_stock.odoo_stock_lend_out_in_actions_state4').id


        elif self.picking_type_id.name == '盘点单' and self.state == '新建':
            self.actions_id = self.env.ref('amos_stock.odoo_stock_picking_inventory_actions_state1').id
        elif self.picking_type_id.name == '盘点单' and self.state == '待审批':
            self.actions_id = self.env.ref('amos_stock.odoo_stock_picking_inventory_actions_state2').id
        elif self.picking_type_id.name == '盘点单' and self.state == '仓库':
            self.actions_id = self.env.ref('amos_stock.odoo_stock_picking_inventory_actions_state3').id
        elif self.picking_type_id.name == '盘点单' and self.state == '已完成':
            self.actions_id = self.env.ref('amos_stock.odoo_stock_picking_inventory_actions_state4').id

        elif self.picking_type_id.name == '盘盈单' and self.state == '新建':
            self.actions_id = self.env.ref('amos_stock.odoo_stock_picking_overage_actions_state1').id
        elif self.picking_type_id.name == '盘盈单' and self.state == '待审批':
            self.actions_id = self.env.ref('amos_stock.odoo_stock_picking_overage_actions_state2').id
        elif self.picking_type_id.name == '盘盈单' and self.state == '仓库':
            self.actions_id = self.env.ref('amos_stock.odoo_stock_picking_overage_actions_state3').id
        elif self.picking_type_id.name == '盘盈单' and self.state == '已完成':
            self.actions_id = self.env.ref('amos_stock.odoo_stock_picking_overage_actions_state4').id

        elif self.picking_type_id.name == '盘亏单' and self.state == '新建':
            self.actions_id = self.env.ref('amos_stock.odoo_stock_picking_losses_actions_state1').id
        elif self.picking_type_id.name == '盘亏单' and self.state == '待审批':
            self.actions_id = self.env.ref('amos_stock.odoo_stock_picking_losses_actions_state2').id
        elif self.picking_type_id.name == '盘亏单' and self.state == '仓库':
            self.actions_id = self.env.ref('amos_stock.odoo_stock_picking_losses_actions_state3').id
        elif self.picking_type_id.name == '盘亏单' and self.state == '已完成':
            self.actions_id = self.env.ref('amos_stock.odoo_stock_picking_losses_actions_state4').id

        elif self.picking_type_id.name == '报废单' and self.state == '新建':
            self.actions_id = self.env.ref('amos_stock.odoo_stock_picking_scrap_actions_state1').id
        elif self.picking_type_id.name == '报废单' and self.state == '待审批':
            self.actions_id = self.env.ref('amos_stock.odoo_stock_picking_scrap_actions_state2').id
        elif self.picking_type_id.name == '报废单' and self.state == '仓库':
            self.actions_id = self.env.ref('amos_stock.odoo_stock_picking_scrap_actions_state3').id
        elif self.picking_type_id.name == '报废单' and self.state == '已完成':
            self.actions_id = self.env.ref('amos_stock.odoo_stock_picking_scrap_actions_state4').id

        elif self.picking_type_id.name == '丢失单' and self.state == '新建':
            self.actions_id = self.env.ref('amos_stock.odoo_stock_picking_lose_actions_state1').id
        elif self.picking_type_id.name == '丢失单' and self.state == '待审批':
            self.actions_id = self.env.ref('amos_stock.odoo_stock_picking_lose_actions_state2').id
        elif self.picking_type_id.name == '丢失单' and self.state == '仓库':
            self.actions_id = self.env.ref('amos_stock.odoo_stock_picking_lose_actions_state3').id
        elif self.picking_type_id.name == '丢失单' and self.state == '已完成':
            self.actions_id = self.env.ref('amos_stock.odoo_stock_picking_lose_actions_state4').id

        elif self.picking_type_id.name == '退料单' and self.state == '新建':
            self.actions_id = self.env.ref('amos_stock.odoo_stock_picking_return_actions_state1').id
        elif self.picking_type_id.name == '退料单' and self.state == '待审批':
            self.actions_id = self.env.ref('amos_stock.odoo_stock_picking_return_actions_state2').id
        elif self.picking_type_id.name == '退料单' and self.state == '仓库':
            self.actions_id = self.env.ref('amos_stock.odoo_stock_picking_return_actions_state3').id
        elif self.picking_type_id.name == '退料单' and self.state == '已完成':
            self.actions_id = self.env.ref('amos_stock.odoo_stock_picking_return_actions_state4').id

        elif self.picking_type_id.name == '送检单' and self.state == '新建':
            self.actions_id = self.env.ref('amos_stock.odoo_stock_picking_tested_out_actions_state1').id
        elif self.picking_type_id.name == '送检单' and self.state == '待审批':
            self.actions_id = self.env.ref('amos_stock.odoo_stock_picking_tested_out_actions_state2').id
        elif self.picking_type_id.name == '送检单' and self.state == '仓库':
            self.actions_id = self.env.ref('amos_stock.odoo_stock_picking_tested_out_actions_state3').id
        elif self.picking_type_id.name == '送检单' and self.state == '已完成':
            self.actions_id = self.env.ref('amos_stock.odoo_stock_picking_tested_out_actions_state4').id

        elif self.picking_type_id.name == '送检还入单' and self.state == '新建':
            self.actions_id = self.env.ref('amos_stock.odoo_stock_picking_tested_in_actions_state1').id
        elif self.picking_type_id.name == '送检还入单' and self.state == '待审批':
            self.actions_id = self.env.ref('amos_stock.odoo_stock_picking_tested_in_actions_state2').id
        elif self.picking_type_id.name == '送检还入单' and self.state == '仓库':
            self.actions_id = self.env.ref('amos_stock.odoo_stock_picking_tested_in_actions_state3').id
        elif self.picking_type_id.name == '送检还入单' and self.state == '已完成':
            self.actions_id = self.env.ref('amos_stock.odoo_stock_picking_tested_in_actions_state4').id

    def add_overage_losses(self):
        """
        创建盘盈/盘亏单
        :return:
        """
        inventory_overage_ids = []
        inventory_losses_ids = []
        for line in self.move_lines:

            if line.stock_qty > 0:
                pram = {
                    'name': line.name,
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.stock_qty,
                    'warehouse_id': line.warehouse_id.id,
                    'note': line.note,
                }
                inventory_overage_ids.append((0, 0, pram))
            if line.stock_qty < 0:
                pram = {
                    'name': line.name,
                    'product_id': line.product_id.id,
                    'product_uom_qty': -line.stock_qty,
                    'warehouse_id': line.warehouse_id.id,
                    'note': line.note,
                }
                inventory_losses_ids.append((0, 0, pram))

        id_object = '%s,%s' % (self._name, self.id)

        if inventory_overage_ids:
            # 盘盈单
            overage = self.env['stock.picking'].create({
                'id_object': id_object,
                'origin': self.name,
                'backorder_id': self.id,
                'partner_id': self.user_id.partner_id.id,
                'user_id': self.user_id.id,
                'date_done': self.date_done,
                'other_id': self.other_id.id,
                'department_id': self.department_id.id,
                'auditor_id': self.auditor_id.id,
                'auditor_id_date': self.auditor_id_date,
                'move_lines': inventory_overage_ids,
                'note': self.note,
                'state': u'已完成',
                'picking_type_id': self.env.ref('amos_stock.stock_picking_type_10_a').id,
            })
        if inventory_losses_ids:
            # 盘亏单
            losses = self.env['stock.picking'].create({
                'id_object': id_object,
                'origin': self.name,
                'backorder_id': self.id,
                'partner_id': self.user_id.partner_id.id,
                'user_id': self.user_id.id,
                'date_done': self.date_done,
                'department_id': self.department_id.id,
                'auditor_id': self.auditor_id.id,
                'auditor_id_date': self.auditor_id_date,
                'other_id': self.other_id.id,
                'move_lines': inventory_losses_ids,
                'note': self.note,
                'state': u'已完成',
                'picking_type_id': self.env.ref('amos_stock.stock_picking_type_10_b').id,
            })

    def order_done(self):
        """
        订单确认
        :return:
        """
        if not self.move_lines:
            raise UserError(u'请输入物资明细行!')

        for line in self.move_lines:

            if line.type == 'out':
                domain = [('product_id', '=', line.product_id.id), ('warehouse_id', '=', line.warehouse_id.id)]
                warehouse = self.env['product.stock'].sudo().search(domain, order="id desc", limit=1)
                if warehouse:
                    if line.product_uom_qty > warehouse.location_qty:
                        qty = warehouse.location_qty - line.product_uom_qty
                        raise UserError(u'仓库:%s 物资：%s \n当前库存:%s \n需求数量:%s \n还差数量:%s' % (
                            line.warehouse_id.name, line.name, warehouse.location_qty, line.product_uom_qty, qty))
                else:
                    raise UserError(u'物资仓库不存在!')

            self.product_stock(line.product_id.id, self.company_id.id, line.warehouse_id.id,line.name)


    def product_stock(self, product_id, company_id, warehouse_id,name):
        #:::::判断库存是否存在,如果不存新建物资库位,存在新建
        domain = [
            ('product_id', '=', product_id),
            ('company_id', '=', company_id),
            ('warehouse_id', '=', warehouse_id),
        ]
        rows_count = self.env['product.stock'].sudo().search_count(domain)

        if rows_count == 0:
            query = """INSERT INTO public.product_stock(name,product_id, company_id, warehouse_id)VALUES (%s,%s, %s, %s)"""
            self._cr.execute(query, (name,product_id, company_id, warehouse_id))

    @api.onchange('id_object')
    def _onchange_id_object(self):
        if not self.id_object:
            return

        if self._context.get('event') in ['借出单-借出还入单', '借出单-丢失单']:
            order_lines = []
            for line in self.id_object.move_lines:
                product_uom_qty = line.stock_out_in_owe_qty
                price_unit = line.price_unit
                if product_uom_qty > 0:
                    order_lines.append((0, 0, {
                        'parent_id': line.id,
                        'name': line.name,
                        'product_id': line.product_id.id,
                        'product_uom': line.product_uom,
                        'product_uom_qty': product_uom_qty,
                        'price_unit': price_unit,
                        'warehouse_id': line.warehouse_id.id,
                    }))
            self.move_lines = order_lines

        if self._context.get('event') in ['送检单-丢失单']:
            order_lines = []
            for line in self.id_object.move_lines:
                product_uom_qty = line.stock_out_in_owe_qty
                price_unit = line.price_unit
                if product_uom_qty > 0:
                    order_lines.append((0, 0, {
                        'name': line.name,
                        'product_id': line.product_id.id,
                        'product_uom': line.product_uom,
                        'product_uom_qty': product_uom_qty,
                        'price_unit': price_unit,
                        'warehouse_id': line.warehouse_id.id,
                    }))
            self.move_lines = order_lines

        if self._context.get('event') in ['送检单-送检还入单']:
            order_lines = []
            for line in self.id_object.move_lines:
                if line.is_test:
                    product_uom_qty = line.stock_out_in_owe_qty
                    price_unit = line.price_unit
                    verification_date = fields.Date.context_today(self)
                    if product_uom_qty > 0:
                        order_lines.append((0, 0, {
                            'parent_id': line.id,
                            'name': line.name,
                            'product_id': line.product_id.id,
                            'product_uom': line.product_uom,
                            'product_uom_qty': product_uom_qty,
                            'price_unit': price_unit,
                            'interval_type': line.interval_type,
                            'interval_number': line.interval_number,
                            'verification_date': verification_date,
                            'next_time': line.product_id._next_time(verification_date,line.product_id.interval_type,line.product_id.interval_number),
                            'warehouse_id': line.warehouse_id.id,
                        }))
            self.move_lines = order_lines

        if self._context.get('event') in ['领用单-退料单']:
            order_lines = []
            for line in self.id_object.move_lines:
                product_uom_qty = line.product_uom_qty
                price_unit = line.price_unit
                if product_uom_qty > 0:
                    order_lines.append((0, 0, {
                        'name': line.name,
                        'product_id': line.product_id.id,
                        'product_uom': line.product_uom,
                        'product_uom_qty': product_uom_qty,
                        'price_unit': price_unit,
                        'warehouse_id': line.warehouse_id.id,
                    }))
            self.move_lines = order_lines


    def create_stock_lend_out_in(self):
        """
        创建借出还入单
        :return:
        """

        if not self.state == '已完成':
            raise UserError(u'警告：单据未审核')

        self.ensure_one()
        context = dict(self._context or {})
        context['active_model'] = 'stock.picking'
        context['event'] = '借出单-借出还入单'
        context['default_partner_id'] = self.partner_id.id
        context['default_user_id'] = self.user_id.id
        context['default_other_id'] = self.other_id.id
        context['default_backorder_id'] = self.id

        context['search_default_picking_type_id'] = self.picking_type_id.return_picking_type_id.id
        context['default_picking_type_id'] = self.picking_type_id.return_picking_type_id.id
        context['default_id_object'] = '%s,%s' % (self._name, self.id)

        form_id = self.env.ref('amos_stock.odoo_stock_lend_out_in_form').id
        return {'type': 'ir.actions.act_window',
                'res_model': 'stock.picking',
                'view_mode': 'form',
                'views': [(form_id, 'form')],
                'target': 'current',
                'context': context,
                'flags': {'form': {'action_buttons': True}}}


    def create_stock_lend_out_lose(self):
        """
        创建借出还入单
        :return:
        """

        if not self.state == '已完成':
            raise UserError(u'警告：单据未审核')

        self.ensure_one()
        context = dict(self._context or {})
        context['active_model'] = 'stock.picking'
        context['event'] = '借出单-丢失单'
        context['default_partner_id'] = self.partner_id.id
        context['default_user_id'] = self.user_id.id
        context['default_other_id'] = self.other_id.id
        context['default_backorder_id'] = self.id
        context['default_department_id'] = self.department_id.id

        picking_type_id = self.env.ref('amos_stock.stock_picking_type_lose').id

        context['search_default_picking_type_id'] = picking_type_id
        context['default_picking_type_id'] = picking_type_id
        context['default_id_object'] = '%s,%s' % (self._name, self.id)

        form_id = self.env.ref('amos_stock.odoo_stock_picking_lose_form').id
        return {'type': 'ir.actions.act_window',
                'res_model': 'stock.picking',
                'view_mode': 'form',
                'views': [(form_id, 'form')],
                'target': 'current',
                'context': context,
                'flags': {'form': {'action_buttons': True}}}


    def create_stock_picking_return(self):
        """
        创建创建退料单
        :return:
        """

        if not self.state == '已完成':
            raise UserError(u'警告：单据未审核')

        self.ensure_one()
        context = dict(self._context or {})
        context['active_model'] = 'stock.picking'
        context['event'] = '领用单-退料单'
        context['default_partner_id'] = self.partner_id.id
        context['default_user_id'] = self.user_id.id
        context['default_other_id'] = self.other_id.id
        context['default_backorder_id'] = self.id
        context['default_department_id'] = self.department_id.id

        picking_type_id = self.env.ref('amos_stock.stock_picking_type_return').id

        context['search_default_picking_type_id'] = picking_type_id
        context['default_picking_type_id'] = picking_type_id
        context['default_id_object'] = '%s,%s' % (self._name, self.id)

        form_id = self.env.ref('amos_stock.odoo_stock_picking_return_form').id
        return {'type': 'ir.actions.act_window',
                'res_model': 'stock.picking',
                'view_mode': 'form',
                'views': [(form_id, 'form')],
                'target': 'current',
                'context': context,
                'flags': {'form': {'action_buttons': True}}}


    def create_stock_tested_out_in(self):
        """
        创建送检还入单
        :return:
        """

        if not self.state == '已完成':
            raise UserError(u'警告：单据未审核')

        self.ensure_one()
        context = dict(self._context or {})
        context['active_model'] = 'stock.picking'
        context['event'] = '送检单-送检还入单'
        context['default_partner_id'] = self.partner_id.id
        context['default_user_id'] = self.user_id.id
        context['default_other_id'] = self.other_id.id
        context['default_backorder_id'] = self.id

        context['search_default_picking_type_id'] = self.picking_type_id.return_picking_type_id.id
        context['default_picking_type_id'] = self.picking_type_id.return_picking_type_id.id
        context['default_id_object'] = '%s,%s' % (self._name, self.id)

        form_id = self.env.ref('amos_stock.odoo_stock_picking_tested_in_form').id
        return {'type': 'ir.actions.act_window',
                'res_model': 'stock.picking',
                'view_mode': 'form',
                'views': [(form_id, 'form')],
                'target': 'current',
                'context': context,
                'flags': {'form': {'action_buttons': True}}}


    def create_stock_tested_out_lose(self):
        """
        创建借出还入单
        :return:
        """

        if not self.state == '已完成':
            raise UserError(u'警告：单据未审核')

        self.ensure_one()
        context = dict(self._context or {})
        context['active_model'] = 'stock.picking'
        context['event'] = '送检单-丢失单'
        context['default_partner_id'] = self.partner_id.id
        context['default_user_id'] = self.user_id.id
        context['default_other_id'] = self.other_id.id
        context['default_backorder_id'] = self.id

        picking_type_id = self.env.ref('amos_stock.stock_picking_type_lose').id

        context['search_default_picking_type_id'] = picking_type_id
        context['default_picking_type_id'] = picking_type_id
        context['default_id_object'] = '%s,%s' % (self._name, self.id)

        form_id = self.env.ref('amos_stock.odoo_stock_picking_lose_form').id
        return {'type': 'ir.actions.act_window',
                'res_model': 'stock.picking',
                'view_mode': 'form',
                'views': [(form_id, 'form')],
                'target': 'current',
                'context': context,
                'flags': {'form': {'action_buttons': True}}}


    def is_test_list(self):
        """ 修改是否合格 送检人可以修改 """
        self.ensure_one()

        domain = [('picking_id', '=', self.id)]
        form_id = self.env.ref('amos_stock.odoo_is_test_list').id
        return {
            'name': '是否合格',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.move',
            'view_mode': 'form',
            'views': [(form_id, 'tree')],
            # 'target': 'new',
            'domain': domain,
            'flags': {'form': {'action_buttons': True}}}


    def button_add_stock_picking_tested(self):
        """
        生成不合格处理单
        :return:
        """
        is_test = self.move_lines.filtered(lambda o: o.is_test == False)
        if not is_test:
            # 警告提示
            self.env.user.notify_warning(message='不存在不合格明细行!')
            return True

        for test in self.move_lines:
            picking_type_id = self.env.ref('amos_stock.stock_picking_type_lend_a').id
            if test.is_test == False:
                obj = self.env['stock.picking.tested'].search(
                    [('picking_id', '=', self.id), ('product_id', '=', test.product_id.id)])
                if obj:
                    if obj.state == '待处理':
                        obj.unlink()
                    else:
                        raise UserError(u'警告：单据已转 %s ' % obj.state)

                lines = []
                domain = [('product_id', '=', test.product_id.id), ('picking_type_id', '=', picking_type_id),
                          ('date_done', '>=', test.product_id.test_date_done), ('state', '=', '已完成')]
                product = self.env['stock.move'].sudo().search(domain, order="id desc")
                if product:
                    #::::查询产品上上次检查日期是多少，之后的所有
                    for o in product:
                        ref_id = '%s,%s' % (o._name, o.id)
                        pram = {
                            'move_id': o.id,
                            'name': o.name,
                            'product_uom_qty': o.product_uom_qty,
                            'note': o.note,
                            'ref_id': ref_id,
                        }
                        lines.append((0, 0, pram))

                id_object = '%s,%s' % (self._name, self.id)
                origin = '%s[%s]' % (self._description, self.name)
                values = {
                    'partner_id': self.partner_id.id,
                    'company_id': self.company_id.id,
                    'department_id': self.department_id.id,
                    'other_id': self.other_id.id,
                    'auditor_id': self.auditor_id.id,
                    'origin': origin,
                    'id_object': id_object,
                    'order_line': lines,
                    'product_id': test.product_id.id,
                    'picking_id': self.id,
                    'move_id': test.id,
                    'product_uom_qty': test.stock_out_in_owe_qty,
                    'state': '待处理',
                }
                self.env['stock.picking.tested'].sudo().create(values)

        return True


    def button_print1(self):
        return self.env.ref('%s' % self._context['report']).with_context({'discard_logo_check': True}).report_action(
            self)


    def button_product(self):
        """ 打开指定视图 """
        self.ensure_one()
        orm_id = self.env.ref('amos_stock.view_form_inventory_product_wizard').id
        return {'type': 'ir.actions.act_window',
                'res_model': 'inventory.product.wizard',
                'view_mode': 'form',
                'views': [(orm_id, 'form')],
                # 'res_id': self.parent_id.id,
                'target': 'new',
                'flags': {'form': {'action_buttons': True}}}


    def button_add_product(self):
        """ 打开指定视图
        /odoo/addons/web/static/src/js/chrome/action_manager_act_window.js
        _generateActionFlags 400行
        new inline  隐藏 hasSidebar 工具条

        """
        self.ensure_one()
        context = dict(self._context or {})

        return {
            'name': '添加产品',
            'type': 'ir.actions.act_window',
            'res_model': 'product.product',
            'view_mode': 'form',
            'views': [(self.env.ref('.odoo_product_product_tree_add').id, 'tree')],
            # 'res_id': self.parent_id.id,
            'context': context,
            'target': 'inline',
            'flags': {'form': {'action_buttons': True}}}



    def stock_picking_batch_add(self, _context=None):
        product = self.env['product.product'].sudo().browse(_context['product_id'])
        move = self.env['stock.move'].search([('picking_id', '=', _context['order_id']),('product_id', '=', _context['product_id'])], limit=1)
        if not move:
            values = {
                'name': _context['name'],
                'product_id': _context['product_id'],
                'picking_id': _context['order_id'],
                'product_uom_qty': product.qty,
                'product_qty': product.qty,
            }
            obj = self.env['stock.move'].sudo().create(values)
        else:
            self.env.user.notify_success(message='%s 已存在!' % (product.name))
        return True




class stock_move(models.Model):
    _name = "stock.move"
    _description = u"移库明细"
    _order = 'picking_id, sequence, id'

    @api.depends('product_uom_qty', 'price_unit')
    def _compute_amount(self):
        for line in self:
            price = line.price_unit * line.product_uom_qty
            line.update({
                'price_subtotal': price,
            })

    @api.depends('product_uom_qty', 'product_qty')
    def _compute_stock_qty(self):
        for line in self:
            line.update({
                'stock_qty': line.product_qty - line.product_uom_qty,
            })

    priority = fields.Selection(PROCUREMENT_PRIORITIES, '优先级', default='1')

    parent_id = fields.Many2one('stock.move', string=u'关联',copy=False,help='保存借出单,ID用于计算,已还数量')



    picking_id = fields.Many2one('stock.picking', string=u'明细', ondelete='cascade', index=True, copy=False)
    sequence = fields.Integer(string=u'排序', default=10)
    name = fields.Char(string=u'物资全称', )
    product_id = fields.Many2one('product.product', string=u'物资名称', change_default=True, ondelete='restrict')
    is_assets = fields.Boolean(related='product_id.is_assets', string=u"是否固定资产", readonly=True, store=True)

    product_uom_qty = fields.Float(string=u'数量', required=True, default=1.0,
                                   digits=dp.get_precision('Product Unit of Measure'))
    product_qty = fields.Float(string=u'盘点数量', copy=False, default=0.0)
    stock_qty = fields.Float(string=u'差异数量', compute='_compute_stock_qty', default=0.0)
    product_uom = fields.Many2one(related='product_id.uom_id', string=u'单位', readonly=True, store=True)
    note = fields.Text(u'备注')
    price_unit = fields.Float(u'单价', required=True, default=0.0)
    move_line_ids = fields.One2many('stock.move.line', 'move_id')
    date_expected = fields.Datetime('预计日期', default=fields.Datetime.now, index=True, required=True, )

    location_id = fields.Many2one('stock.location', 'Source Location', auto_join=True, index=True, )
    location_dest_id = fields.Many2one('stock.location', 'Destination Location', auto_join=True, index=True, )

    price_subtotal = fields.Float(compute='_compute_amount', string=u'小计', readonly=True, store=True)

    partner_id = fields.Many2one(related='picking_id.partner_id', string=u'合作伙伴', readonly=True, store=True)
    backorder_id = fields.Many2one(related='picking_id.backorder_id', string=u'劈单', readonly=True, store=True)
    picking_type_id = fields.Many2one(related='picking_id.picking_type_id', string=u'作业类型', readonly=True, store=True)
    picking_type_id_name = fields.Char(related='picking_type_id.name', string=u'作业类型名称', readonly=True, store=True)
    backorder_id_picking_type_id_name = fields.Char(related='picking_id.backorder_id_picking_type_id_name',
                                                    string=u'上级作业类型', readonly=True, store=True)
    warehouse_id = fields.Many2one('stock.warehouse', string=u'仓库')
    type = fields.Selection(related='picking_type_id.type', string=u'类型', readonly=True, store=True)
    state = fields.Selection(related='picking_id.state', string=u'状态', store=True)
    scheduled_date = fields.Datetime(related='picking_id.scheduled_date', string=u'交货日期', readonly=True, store=True)
    company_id = fields.Many2one(related='picking_id.company_id', string=u'公司', readonly=True, store=True)
    user_id = fields.Many2one(related='picking_id.user_id', string=u'负责人', readonly=True, store=True)
    code = fields.Char(related='picking_id.name', string=u'单据编号', readonly=True, store=True)
    is_locked = fields.Boolean(compute='_compute_is_locked', readonly=True)
    active = fields.Boolean(related='picking_id.active', string=u'是否归档', store=True)
    other_id = fields.Many2one(related='picking_id.other_id', string=u'借用人', store=True, )
    department_id = fields.Many2one(related='picking_id.department_id', string=u'专业部', store=True, )
    is_test = fields.Boolean(default=True, string=u'是否合格')
    date_done = fields.Datetime(related='picking_id.date_done', string='调拨日期',)


    verification_date = fields.Date(string='检定日期', track_visibility='onchange',default=fields.Date.context_today)
    interval_type = fields.Selection([
        ('月', u'月'),
        ('年', u'年'),
    ], string=u'检定周期', default='年',  track_visibility='onchange')
    interval_number = fields.Integer(default=1, string='周期参数', track_visibility='onchange')
    next_time = fields.Date(string=u'下一次检定日期', track_visibility='onchange')


    @api.model
    def _select_reference(self):
        records = self.env['ir.model'].search([])
        return [(record.model, record.name) for record in records] + [('', '')]

    ref_id = fields.Reference(string=u'关联', selection='_select_reference')


    def _compute_stock_out_in(self):
        for line in self:
            if line.picking_type_id_name == u'借出单':
                pram = {}
                self.env.cr.execute("SELECT sum(product_uom_qty) AS qty  FROM stock_move "
                                    "where backorder_id=%s "
                                    "and product_id=%s "
                                    "and parent_id=%s "
                                    "and type='in' "
                                    "and picking_type_id_name='借出还入单' "
                                    "and state='%s'" % (line.picking_id.id, line.product_id.id,line.id, u'已完成'))

                stock_out_in_qty = self.env.cr.fetchone()[0] or 0.0

                self.env.cr.execute("SELECT sum(product_uom_qty) AS qty  FROM stock_move "
                                    "where backorder_id=%s "
                                    "and product_id=%s "
                                    "and type='other' "
                                    "and picking_type_id_name='丢失单' "
                                    "and state='%s'" % (line.picking_id.id, line.product_id.id, u'已完成'))

                stock_out_lose_qty = self.env.cr.fetchone()[0] or 0.0

                pram['stock_out_in_qty'] = stock_out_in_qty
                pram['stock_out_lose_qty'] = stock_out_lose_qty
                pram['stock_out_in_owe_qty'] = line.product_uom_qty - stock_out_in_qty - stock_out_lose_qty
                line.update(pram)
            elif line.picking_type_id_name == u'送检单':
                pram = {}
                self.env.cr.execute("SELECT sum(product_uom_qty) AS qty  FROM stock_move "
                                    "where backorder_id=%s "
                                    "and product_id=%s "
                                    "and type='in' "
                                    "and picking_type_id_name='送检还入单' "
                                    "and state='%s'" % (line.picking_id.id, line.product_id.id, u'已完成'))

                stock_out_in_qty = self.env.cr.fetchone()[0] or 0.0

                self.env.cr.execute("SELECT sum(product_uom_qty) AS qty  FROM stock_move "
                                    "where backorder_id=%s "
                                    "and product_id=%s "
                                    "and type='other' "
                                    "and picking_type_id_name='丢失单' "
                                    "and state='%s'" % (line.picking_id.id, line.product_id.id, u'已完成'))

                stock_out_lose_qty = self.env.cr.fetchone()[0] or 0.0

                self.env.cr.execute("SELECT sum(product_uom_qty) AS qty  FROM stock_picking_tested "
                                    "where move_id=%s "
                                    "and product_id=%s " % (line.id, line.product_id.id))

                stock_out_unqualified_qty = self.env.cr.fetchone()[0] or 0.0

                pram['stock_out_in_qty'] = stock_out_in_qty
                pram['stock_out_lose_qty'] = stock_out_lose_qty
                pram['stock_out_unqualified_qty'] = stock_out_unqualified_qty
                pram['stock_out_in_owe_qty'] = line.product_uom_qty - stock_out_in_qty - stock_out_lose_qty -stock_out_unqualified_qty
                line.update(pram)

    stock_out_in_qty = fields.Float(compute='_compute_stock_out_in', string=u'已还数量', type='float')
    stock_out_in_owe_qty = fields.Float(compute='_compute_stock_out_in', string=u'还欠数量', type='float')
    stock_out_lose_qty = fields.Float(compute='_compute_stock_out_in', string=u'丢失数量', type='float')
    stock_out_unqualified_qty = fields.Float(compute='_compute_stock_out_in', string=u'不合格数量', type='float')

    @api.model
    def create(self, vals):

        if vals.get('warehouse_id'):
            pass
        else:
            if vals.get('picking_id'):
                picking = self.env['stock.picking'].browse(int(vals.get('picking_id')))
                vals['warehouse_id'] = picking.picking_type_id.warehouse_id.id

        line = super(stock_move, self).create(vals)

        return line


    @api.onchange('verification_date','interval_type','interval_number')
    def onchange_next_time(self):
        if self.interval_type and self.interval_number and self.verification_date and self.product_id:
            self.next_time = self.product_id._next_time(self.verification_date, self.interval_type,
                                                        self.interval_number)  # 计算日期


    @api.onchange('warehouse_id')
    def onchange_warehouse_id(self):
        context = dict(self._context or {})
        if context.get('default_product_id'):
            if not self.warehouse_id:
                self.update({
                    'product_uom_qty': False,
                    'product_qty': False,
                })
                return

            values = {}
            stock = self.env['product.stock'].search(
                [('product_id', '=', int(context.get('default_product_id'))), ('warehouse_id', '=', self.warehouse_id.id)],
                limit=1)

            if stock:
                values['product_uom_qty'] = stock.location_qty
                values['product_qty'] = False
            else:
                values['product_uom_qty'] = False
                values['product_qty'] = False
            self.update(values)

    @api.depends('picking_id.is_locked')
    def _compute_is_locked(self):
        for move in self:
            if move.picking_id:
                move.is_locked = move.picking_id.is_locked


    @api.onchange('product_id')
    def onchange_product_id(self):
        if not self.product_id:
            return {'domain': {'product_uom': []}}

        picking_type = self.env['stock.picking.type'].sudo().browse(int(self._context['default_picking_type_id']))
        if picking_type.name == '借出单':
            if self.product_id.next_time:
                if self.product_id.next_time <= date.today():
                    raise UserError(
                        u'警告：产品：%s 检定有效期为：%s' % (self.product_id.name_get()[0][1], self.product_id.next_time))
        elif picking_type.name == '送检还入单':
            if self.product_id:
                self.interval_type = self.product_id.interval_type
                self.interval_number = self.product_id.interval_number
                if self.interval_type and self.interval_number:
                    self.next_time = self.product_id._next_time(self.verification_date,self.interval_type,self.interval_number) #计算日期

        if self._context.get('active_id'):
            if self._context['active_id'] == 6:
                if self.product_id:
                    name = self.product_id.name
                    if self.product_id.default_code:
                        name = '[' + self.product_id.default_code + ']' + name
                    if self.product_id.specification:
                        name = name + ' ' + self.product_id.specification
                    self.name = name
                    self.product_uom_qty = self.product_id.qty
            else:

                if self.product_id:
                    name = self.product_id.name
                    if self.product_id.default_code:
                        name = '[' + self.product_id.default_code + ']' + name
                    if self.product_id.specification:
                        name = name + ' ' + self.product_id.specification
                    self.name = name
        else:
            if self._context.get('default_picking_type_id'):
                if self._context['default_picking_type_id'] == 6:
                    if self.product_id:
                        name = self.product_id.name
                        if self.product_id.default_code:
                            name = '[' + self.product_id.default_code + ']' + name
                        if self.product_id.specification:
                            name = name + ' ' + self.product_id.specification
                        self.name = name
                        self.product_uom_qty = self.product_id.qty
                else:

                    if self.product_id:
                        name = self.product_id.name
                        if self.product_id.default_code:
                            name = '[' + self.product_id.default_code + ']' + name
                        if self.product_id.specification:
                            name = name + ' ' + self.product_id.specification
                        self.name = name

    def action_show_details(self):
        self.ensure_one()
        if self.picking_id.picking_type_id.show_reserved:
            view = self.env.ref('amos_stock.view_stock_move_operations')
        else:
            pass
            view = self.env.ref('stock.view_stock_move_nosuggest_operations')

        return {
            'name': '详细作业',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.move',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.id,
            'context': dict(
                self.env.context,
                show_source_location=self.location_id.child_ids and self.picking_type_id.code != 'incoming',
                show_destination_location=self.location_dest_id.child_ids and self.picking_type_id.code != 'outgoing',
                show_package=not self.location_id.usage == 'supplier',
            ),
        }

    def button_is_test(self):
        """
        是否合格
        :return:
        """
        for record in self:
            record.is_test = not record.is_test


class stock_move_line(models.Model):
    _name = "stock.move.line"
    _description = u"移库明细"
    _order = 'picking_id, id'

    picking_id = fields.Many2one('stock.picking', string=u'明细', ondelete='cascade', index=True, copy=False)
    move_id = fields.Many2one('stock.move', 'Stock Move', index=True)
    product_id = fields.Many2one(related='move_id.product_id')
    product_uom_id = fields.Many2one(related='move_id.product_uom', string='单位')
    product_uom_qty = fields.Float('数量', default=0.0, digits=dp.get_precision('Product Unit of Measure'), required=True)





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

from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError
from datetime import datetime, timedelta
import re
from odoo.osv import expression
from odoo import _, api, fields, models, modules, tools
import base64
from odoo.tools import float_compare, pycompat
from amoserp.amos_base.models import public_key as key
from amoserp.amos_base.models.makePinyin import makePinyin, pinyinQuan, pinyinAbbr

ORDER_STATES = [
    (u'新建', u'新建'),
    (u'启用中', u'启用中'),
    (u'已废弃', u'已废弃'),
]

READONLY_STATES = {
    u'启用中': [('readonly', True)],
    u'已废弃': [('readonly', True)],
}


class product_product(models.Model):
    _name = 'product.product'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = u'产品'
    _order = 'name asc'
    _check_company_auto = True

    def _get_default_uom_id(self):
        return self.env["uom.uom"].search([], limit=1, order='id').id

    create_uid_name = fields.Char(related='create_uid.name', string='创建人', store=True)
    write_uid_name = fields.Char(related='write_uid.name', string='修改人', store=True)
    a_z = fields.Char(string=u'首字母', copy=False, states=READONLY_STATES)
    active = fields.Boolean(default=True, string=u'有效', states=READONLY_STATES, track_visibility='onchange')
    color = fields.Integer(string=u'颜色', default=0, states=READONLY_STATES, track_visibility='onchange')
    name = fields.Char(string=u'产品名称', required=True, states=READONLY_STATES, track_visibility='onchange')
    spelling = fields.Char(string=u'全拼', copy=False, states=READONLY_STATES)

    default_code = fields.Char(string=u'产品编码', states=READONLY_STATES, track_visibility='onchange')
    specification = fields.Char(string=u'规格型号', index=True, states=READONLY_STATES, track_visibility='onchange')
    warranty = fields.Float(string=u'质保(月)', default=240, states=READONLY_STATES, track_visibility='onchange')
    sale_price = fields.Float(string=u'销售公开价格', default=0.0, states=READONLY_STATES, track_visibility='onchange',
                              digits='Product Price', group='amos_product.group_purchase_price')
    purchase_price = fields.Float(string=u'采购价格', default=0.0, states=READONLY_STATES, track_visibility='onchange',
                                  digits='Product Price', group='amos_product.group_purchase_price')
    uom_id = fields.Many2one('uom.uom', u'库存单位', default=_get_default_uom_id, required=True, states=READONLY_STATES,
                             track_visibility='onchange', ondelete='restrict')
    stop_date = fields.Date(u'停用日期', track_visibility='onchange', states=READONLY_STATES)
    product_uom = fields.Char(related='uom_id.name', string=u'产品单位', readonly=True, store=True)
    categ_id = fields.Many2one('product.category', string=u'产品分类', states=READONLY_STATES, track_visibility='onchange',
                               ondelete='restrict')
    categ_id_name = fields.Char(related='categ_id.name', string=u'产品分类名称', readonly=True, store=True)

    user_id = fields.Many2one('res.users', u'产品经理', copy=False, states=READONLY_STATES,
                              default=lambda self: self.env.user, track_visibility='onchange')
    user_id_name = fields.Char(related='user_id.name', string=u'产品经理名称', readonly=True, store=True)

    state = fields.Selection(ORDER_STATES, u'单据状态', copy=False, default=u'新建', track_visibility='onchange')
    type = fields.Selection(key._TYPE, u'产品类型', states=READONLY_STATES, copy=False, default='库存商品',
                            track_visibility='onchange')
    abc = fields.Selection(key._ABC, u'ABC', states=READONLY_STATES, copy=False, default='C',
                           track_visibility='onchange',
                           help=u'ABC分类法又称巴雷特分析法.此法的要点是把企业的产品按其金额大小划分为A、B、C三类，然后根据重要性分别对待\n'
                                u'A类产品是指品种少、实物量少而价值高的产品，其成本金额约占70%，而实物量不超过20%\n'
                                u'B类产品介于A类、C类产品之间。其成本金额约占20％，而实物量不超过30％\n'
                                u'C类产品是指品种多、实物量多而价值低的产品，其成本金额约占10％，而实物量不低于50％\n')

    barcode = fields.Char(u'序列号', copy=False, states=READONLY_STATES, track_visibility='onchange')
    company_id = fields.Many2one('res.company', '公司', required=True, index=True, default=lambda self: self.env.company)
    company_id_name = fields.Char(related='company_id.name', string=u'公司名称', readonly=True, store=True)

    in_uom_id = fields.Many2one('uom.uom', string=u'内包装单位', default=_get_default_uom_id, states=READONLY_STATES)
    out_uom_id = fields.Many2one('uom.uom', string=u'外包装单位', default=_get_default_uom_id, states=READONLY_STATES)
    supplierinfo = fields.Many2one('res.partner', string=u'主要供应商', states=READONLY_STATES)
    rack_number = fields.Char(string=u'默认储位', states=READONLY_STATES, track_visibility='onchange')
    set_field1 = fields.Char(string=u'自设栏(一)', states=READONLY_STATES)
    set_field2 = fields.Char(string=u'自设栏(二)', states=READONLY_STATES)
    brand_type = fields.Selection(key._Brand_type, string=u'产品来源', default=u'采购', states=READONLY_STATES)
    in_uom_qty = fields.Float(string=u'内包装单位数量', required=True, default=1, states=READONLY_STATES)
    out_uom_qty = fields.Float(string=u'外包装单位数量', default=1, states=READONLY_STATES)
    mnemonic_code = fields.Char(string=u'产品助记码', states=READONLY_STATES)
    stagnant_period = fields.Integer(string=u'呆滞周期(天)', default=30, help=u"超出这个天数进行提醒", states=READONLY_STATES)
    is_assets = fields.Boolean(u"是否固定资产", default=False, states=READONLY_STATES)
    is_verify = fields.Selection([
        (u'是', u'是'),
        (u'否', u'否'),
    ], string=u'是否需要检定', default='否', track_visibility='onchange')

    content = fields.Html(u'产品介绍', track_visibility='onchange')
    sequence = fields.Integer(string=u'排序', default=10, help=u".")

    initial_cost = fields.Float(u'期初成本', required=True, default=0.0, digits=(10, 2), states=READONLY_STATES)
    average_cost = fields.Float(u'平均成本', required=True, default=0.0, digits=(10, 2), states=READONLY_STATES)

    recent_purchase_date = fields.Date(u'最近采购日期', readonly=True, track_visibility='onchange')  # 定时任务每天自动计算,采购入库时计算
    recent_purchase_in_date = fields.Date(u'最近入库日期', readonly=True, track_visibility='onchange')  # 定时任务每天自动计算,采购入库时计算
    recent_allocation_date = fields.Date(u'最近调拨日期', readonly=True, track_visibility='onchange')  # 定时任务每天自动计算,采购入库时计算
    recent_sale_out_date = fields.Date(u'最近出库日期', readonly=True, track_visibility='onchange')  # 定时任务每天自动计算,采购入库时计算

    # all image fields are base64 encoded and PIL-supported

    # all image_variant fields are technical and should not be displayed to the user
    image_variant_1920 = fields.Image("Variant Image", max_width=1920, max_height=1920)

    # resized fields stored (as attachment) for performance
    image_variant_1024 = fields.Image("Variant Image 1024", related="image_variant_1920", max_width=1024,
                                      max_height=1024, store=True)
    image_variant_512 = fields.Image("Variant Image 512", related="image_variant_1920", max_width=512, max_height=512,
                                     store=True)
    image_variant_256 = fields.Image("Variant Image 256", related="image_variant_1920", max_width=256, max_height=256,
                                     store=True)
    image_variant_128 = fields.Image("Variant Image 128", related="image_variant_1920", max_width=128, max_height=128,
                                     store=True)
    can_image_variant_1024_be_zoomed = fields.Boolean("Can Variant Image 1024 be zoomed",
                                                      compute='_compute_can_image_variant_1024_be_zoomed', store=True)

    # Computed fields that are used to create a fallback to the template if
    # necessary, it's recommended to display those fields to the user.
    image_1920 = fields.Image("Image", compute='_compute_image_1920', inverse='_set_image_1920')
    image_1024 = fields.Image("Image 1024", compute='_compute_image_1024')
    image_512 = fields.Image("Image 512", compute='_compute_image_512')
    image_256 = fields.Image("Image 256", compute='_compute_image_256')
    image_128 = fields.Image("Image 128", compute='_compute_image_128')
    can_image_1024_be_zoomed = fields.Boolean("Can Image 1024 be zoomed", compute='_compute_can_image_1024_be_zoomed')

    @api.depends('image_variant_1920', 'image_variant_1024')
    def _compute_can_image_variant_1024_be_zoomed(self):
        for record in self:
            record.can_image_variant_1024_be_zoomed = record.image_variant_1920 and tools.is_image_size_above(
                record.image_variant_1920, record.image_variant_1024)

    def _compute_image_1920(self):
        """Get the image from the template if no image is set on the variant."""
        for record in self:
            record.image_1920 = record.image_variant_1920

    def _set_image_1920(self):
        for record in self:
            record.image_variant_1920 = record.image_1920

    def _compute_image_1024(self):
        """Get the image from the template if no image is set on the variant."""
        for record in self:
            record.image_1024 = record.image_variant_1024

    def _compute_image_512(self):
        """Get the image from the template if no image is set on the variant."""
        for record in self:
            record.image_512 = record.image_variant_512

    def _compute_image_256(self):
        """Get the image from the template if no image is set on the variant."""
        for record in self:
            record.image_256 = record.image_variant_256

    def _compute_image_128(self):
        """Get the image from the template if no image is set on the variant."""
        for record in self:
            record.image_128 = record.image_variant_128

    def _compute_can_image_1024_be_zoomed(self):
        """Get the image from the template if no image is set on the variant."""
        for record in self:
            record.can_image_1024_be_zoomed = record.can_image_variant_1024_be_zoomed

    @api.model_create_multi
    def create(self, vals_list):
        products = super(product_product, self.with_context(create_product_product=True)).create(vals_list)
        # `_get_variant_id_for_combination` depends on existing variants
        self.clear_caches()
        return products

    def unlink(self):
        for order in self:
            if order.state != '新建':
                raise UserError(u'%s:只能删除新建单据!' % order._description)
        return super(product_product, self).unlink()

    def write(self, values):
        if values.get('name'):
            values['a_z'] = pinyinAbbr(values['name'])[0] or ''
        result = super(product_product, self).write(values)
        return result

    def copy(self, default=None):
        self.ensure_one()
        if default is None:
            default = {}
        if 'name' not in default:
            default['default_code'] = "%s (copy)" % self.default_code
        return super(product_product, self).copy(default=default)

    def toggle_active(self):
        for record in self:
            record.active = not record.active
            if record.active:
                record.stop_date = ''
            else:
                record.stop_date = fields.Date.today()

    @api.onchange('uom_id')
    def onchange_uom_id(self):
        self.in_uom_id = self.uom_id.id
        self.out_uom_id = self.uom_id.id

    def button_dummy(self):
        return True

    def button_robot(self):
        return True

    def name_get(self):
        reads = self.read(['name', 'default_code', 'specification'])
        res = []
        for record in reads:
            name = record['name']
            if record['default_code']:
                name = '[' + record['default_code'] + ']' + record['name']
            if record['specification']:
                name = name + ' ' + record['specification'] or ''
            res.append((record['id'], name))
        return res

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if not args:
            args = []
        if name:
            positive_operators = ['=', 'ilike', '=ilike', 'like', '=like']
            products = self.env['product.product']
            if operator in positive_operators:
                products = self.search(['|', ('name', operator, name), ('specification', operator, name)] + args,
                                       limit=limit)
                if not products:
                    products = self.search([('default_code', '=', name)] + args, limit=limit)
            if not products and operator not in expression.NEGATIVE_TERM_OPERATORS:
                products = self.search(args + [('default_code', operator, name)], limit=limit)
                if not limit or len(products) < limit:
                    limit2 = (limit - len(products)) if limit else False
                    products += self.search(args + [('name', operator, name), ('id', 'not in', products.ids)],
                                            limit=limit2)
            elif not products and operator in expression.NEGATIVE_TERM_OPERATORS:
                products = self.search(args + ['&', ('default_code', operator, name), ('name', operator, name)],
                                       limit=limit)
            if not products and operator in positive_operators:
                ptrn = re.compile('(\[(.*?)\])')
                res = ptrn.search(name)
                if res:
                    products = self.search([('default_code', '=', res.group(2))] + args, limit=limit)
        else:
            products = self.search(args, limit=limit)
        return products.name_get()

    def button_done_draft(self):
        return self.write({'state': u'新建'})

    def button_loading(self):
        if not self.categ_id:
            raise UserError(u'警告：请选择产品分类！')

        # #::::创建全局查询
        # context = dict(self._context or {})
        # url = self.env.user.s(self, context, self._description, self.default_code,self.content)
        # #:::::结束 创建全局查询
        return self.write({'state': u'启用中'})

    def button_done(self):
        return self.write({'state': u'已废弃'})

    def button_add_batch(self):
        context = dict(self._context or {})
        ids = self.browse(context['res_ids'])
        for line in ids:
            line.button_lines(context['params'])
        return True

    def button_lines(self, context=None):
        if context == None:
            context = dict(self._context or {})

        if context['active_model'] == 'stock.picking.type':
            context['active_model'] = 'stock.picking'

        obj = self.env[context['active_model']]
        #::::::跳到当前单据进行添加产品
        if context.get('active_model'):
            def_name = context['active_model'].replace('.', '_') + '_batch_add'
            name = self.name
            if self.default_code:
                name = '[' + self.default_code + ']' + name
            if self.specification:
                name = name + ' ' + self.specification

            #::::::这里注意批量添加因为来源不一样所以需要在源头指定对象ID
            #::::::使用上下文传值方便系统扩展
            _context = {
                'product_id': self.id,
                'name': name,
                'order_id': context['order_id'],
            }
            getattr(obj, def_name)(_context)

        else:
            raise UserError(u'警告：请退回上个窗口重新登陆，当前界面不支持全屏刷新！')
        return True

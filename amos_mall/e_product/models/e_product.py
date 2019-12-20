# -*- coding: utf-8 -*-

from odoo import _, api, fields, models, modules, tools
import base64
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError
import uuid
import os
from jinja2 import Template

ORDER_STATES = [
    (u'新建', u'新建'),
    (u'上架', u'上架'),
    (u'下架', u'下架'),
]

READONLY_STATES = {
    u'上架': [('readonly', True)],
    u'下架': [('readonly', True)],
}


class e_product_tag(models.Model):
    """
    Tag
    """
    _name = "e.product.tag"
    _description = "tag"

    name = fields.Char(u'编号', size=64, required=True)
    color = fields.Integer(string=u'颜色索引', default=0)
    company_id = fields.Many2one('res.company', u'公司',
                                 default=lambda self: self.env['res.company']._company_default_get('e.product.tag'),
                                 states=READONLY_STATES, track_visibility='onchange')




class e_product(models.Model):
    _name = 'e.product'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = u'商品'
    _order = 'name asc'

    name = fields.Char(string=u'产品名称', required=True, states=READONLY_STATES, track_visibility='onchange')
    newtype = fields.Selection([
        ('图片', u'图片'),
        ('标题', u'标题'), ],
        u'类型', default='图片', states=READONLY_STATES)
    is_vip = fields.Boolean(u'VIP服务', states=READONLY_STATES, help=u"只有是VIP会员可见", )
    islock = fields.Boolean(u'是否锁定', help=u'锁定后用户不能再修改', states=READONLY_STATES, default=False)
    urladdress = fields.Char(u'外部地址', size=128, states=READONLY_STATES, default='')

    color = fields.Char(u'字体颜色', size=7, states=READONLY_STATES, default='')

    titlebtf = fields.Boolean(u'B', help=u'是否粗体', states=READONLY_STATES)
    titleitf = fields.Boolean(u'I', help=u'是否斜体', states=READONLY_STATES)
    is_generate = fields.Boolean(string=u'静态', track_visibility='onchange', help=u'生成静态文件')
    pagefontsize = fields.Float(u'字号', states=READONLY_STATES)
    fileexname = fields.Selection([('.html', u'.html'),
                                   ('.htm', u'.htm'),
                                   ('.shtm', u'.shtm'),
                                   ('.xml', u'.xml'),
                                   ],
                                  u'扩展名', default='.html', states=READONLY_STATES)
    web_templet = fields.Many2one('e.product.template', string=u'网站模板', states=READONLY_STATES)
    app_templet = fields.Many2one('e.product.template', string=u'APP模板', states=READONLY_STATES)

    partner_id = fields.Many2one('res.partner', string=u'客户',
                                 states=READONLY_STATES,
                                 change_default=True, index=True, track_visibility='always')

    tag_ids = fields.Many2many('e.product.tag', 'e_product_tag_rel', 'a_id', 'b_id', u'标签(Tag}', states=READONLY_STATES)

    complete_name = fields.Char(string=u'全称', states=READONLY_STATES, track_visibility='onchange', default='')
    default_code = fields.Char(string=u'产品编码', states=READONLY_STATES, track_visibility='onchange', default='')
    specification = fields.Char(string=u'规格型号', index=True, states=READONLY_STATES, track_visibility='onchange', default='')
    cost_price = fields.Float(string=u'原价', default=0.0, states=READONLY_STATES, track_visibility='onchange',
                              digits='Product Price')
    integral = fields.Integer(string=u'积分', default=0,help=u'使用积分加金额')
    sale_price = fields.Float(string=u'销售公开价格', default=0.0, states=READONLY_STATES, track_visibility='onchange',
                              digits='Product Price')
    purchase_price = fields.Float(string=u'采购参考价格', default=0.0, states=READONLY_STATES, track_visibility='onchange',
                                  digits='Product Price')
    uom = fields.Char(string=u'单位', states=READONLY_STATES, track_visibility='onchange', default='')
    user_id = fields.Many2one('res.users', u'产品管理员', copy=False, states=READONLY_STATES,
                              default=lambda self: self.env.user, track_visibility='onchange')
    state = fields.Selection(ORDER_STATES, u'单据状态', copy=False, default=u'新建', track_visibility='onchange')
    barcode = fields.Char(u'序列号', copy=False, states=READONLY_STATES, track_visibility='onchange', default='')
    company_id = fields.Many2one('res.company', u'公司',
                                 default=lambda self: self.env['res.company']._company_default_get('e.product'),
                                 states=READONLY_STATES, track_visibility='onchange')
    note = fields.Text(u'备注', states=READONLY_STATES, track_visibility='onchange')
    navicontenttf = fields.Char('导读', default='',states=READONLY_STATES,)
    ico = fields.Char('ICO', default='',states=READONLY_STATES,)
    describe = fields.Html('描述', default='',states=READONLY_STATES,)
    brand = fields.Char(u'品牌', states=READONLY_STATES, track_visibility='onchange', default='')

    date_start = fields.Date(u'开始日期', states=READONLY_STATES, track_visibility='onchange')
    date_end = fields.Date(u'结束日期', states=READONLY_STATES, track_visibility='onchange')

    sequence = fields.Integer(string=u'排序', default=10)
    qty = fields.Integer(string=u'库存', default=0, states=READONLY_STATES)

    active = fields.Boolean(default=True, string=u'有效', states=READONLY_STATES, track_visibility='onchange')

    peripheral_ids = fields.Many2many('e.product', 'e_product_peripheral_rel', 'product_id', 'e_id', string=u'周边产品',
                                      states=READONLY_STATES)

    attachment_ids = fields.One2many('ir.attachment', 'res_id',
                                     domain=[('res_model', '=', 'e.product')], string=u'图片', ondelete='cascade',
                                     states=READONLY_STATES)

    images = fields.Text(u'产品图片', states=READONLY_STATES)

    attribute_comment = fields.Boolean(u'评论', states=READONLY_STATES)
    attribute_recommend = fields.Boolean(u'推荐', states=READONLY_STATES)
    attribute_roll = fields.Boolean(u'滚动', states=READONLY_STATES)
    attribute_hot = fields.Boolean(u'热销', states=READONLY_STATES)
    attribute_projector = fields.Boolean(u'幻灯', states=READONLY_STATES)
    attribute_head = fields.Boolean(u'头条', states=READONLY_STATES)
    attribute_carefully = fields.Boolean(u'精选', states=READONLY_STATES)
    attribute_placement = fields.Boolean(u'置顶', states=READONLY_STATES)
    attribute_sale = fields.Boolean(u'特卖', states=READONLY_STATES)
    attribute_break_code = fields.Boolean(u'断码', states=READONLY_STATES)
    attribute_selective = fields.Boolean(u'严选', states=READONLY_STATES)

    metakeywords = fields.Char(u'Meta关键字', states=READONLY_STATES)
    metadesc = fields.Text(u'Meta描述', size=300, states=READONLY_STATES)
    click = fields.Integer(u'点击', states=READONLY_STATES, defaults=1)
    web_savepath = fields.Char(u'WEB保存路径', readonly=True, states=READONLY_STATES)
    app_savepath = fields.Char(u'APP保存路径', readonly=True, states=READONLY_STATES)

    def _get_default_access_token(self):
        return str(uuid.uuid4())

    access_token = fields.Char(u'安全令牌', copy=False, default=_get_default_access_token)
    app_style = fields.Selection([('文本', u'文本'),
                                  ('图文', u'图文'),
                                  ('右图左文本', u'右图左文本'),
                                  ('左图右文本', u'左图右文本'),
                                  ('上标题下三图', u'上标题下三图'),
                                  ('上标题下一图', u'上标题下一图'),
                                  ('上标题下视频', u'上标题下视频'),
                                  ],
                                 u'APP风格', default='图文', states=READONLY_STATES)

    _sql_constraints = [
        ('default_code_uniq', 'unique(default_code, company_id)', u'产品编码与公司必须唯一!'),
    ]

    def unlink(self):
        for order in self:
            if order.state != '新建' and order.user_id.id == self._uid:
                if order.company_id.id in self.env.user.company_ids:
                    raise UserError(u'%s:只能删除新建单据!' % order._description)
        return super(e_product, self).unlink()

    def write(self, values):
        result = super(e_product, self).write(values)
        return result

    def copy(self, default=None):
        self.ensure_one()
        if default is None:
            default = {}
        if 'name' not in default:
            default['default_code'] = "%s (copy)" % self.default_code
        return super(e_product, self).copy(default=default)

    def action_draft(self):
        self.state = u'新建'

    def action_done(self):
        #::::自动生成图片资源
        #::::读取当前网址+附件地址 判断是否外网地址
        url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', default=''),
        images = []
        video = []
        for line in self.attachment_ids:
            if line.type == 'url':
                images.append(line.url)
            else:
                if line.mimetype in ['image/gif', 'image/jpe', 'image/jpeg', 'image/jpg', 'image/gif', 'image/png']:
                    images.append('%s/web/image/%s?field=thumbnail' % (url[0], str(line.id)))
                elif line.mimetype in ['video/mp4']:
                    video.append('%s/web/content/%s?download=true' % (url[0], str(line.id)))

        attachment = {
            'images': images,
            'home': images[0],
            'video': video,
        }

        values = {
            'state': '上架',
            'images': attachment,
        }
        self.write(values)

    def action_cancel(self):
        self.state = u'下架'

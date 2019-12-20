# -*- coding: utf-8 -*-
# &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
# Odoo Connector
# QQ:35350428
# 邮件:35350428@qq.com
# 手机：13584935775
# 作者：'amos'
# 公司网址： www.odoo.pw  www.100china.cn  http://i.youku.com/amoserp
# Copyright 昆山一百计算机有限公司 2012-2018 Amos
# 日期：2019/02/02
# &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
import uuid
from itertools import groupby
from datetime import datetime, timedelta
from werkzeug.urls import url_encode
from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.misc import formatLang


class e_product_template(models.Model):
    _name = "e.product.template"
    _description = "静态模板"
    _order = 'id desc'

    name = fields.Char(string=u'名称')
    template = fields.Text(u'模板')
    active = fields.Boolean(default=True, string=u'是否归档', track_visibility='onchange')



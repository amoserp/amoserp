# -*- coding: utf-8 -*-
# &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
# Odoo Connector
# QQ:35350428
# 邮件:35350428@qq.com
# 手机：13584935775
# 作者：'Amos'
# 公司网址： www.odoo.pw  www.100china.cn  http://i.youku.com/amoserp
# Copyright 昆山一百计算机有限公司 2012-2018 Amos
# 日期：2018-3-19
# &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&

from datetime import datetime, timedelta
from dateutil import parser
import time

def date_format(value, format=''):
    if value == '':
        return ''
    if format == '':
        format = '%Y-%m-%d %H:%M:%S'
        value = datetime.strptime(value, format)
        data = (value + timedelta(hours=8)).strftime(format)
        return parser.parse(data).date()
    else:
        value = datetime.strptime(value, format)
        data = (value + timedelta(hours=8)).strftime(format)
        return parser.parse(data)



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:





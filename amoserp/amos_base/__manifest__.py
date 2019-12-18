# -*- coding: utf-8 -*-
# &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
# AmosERP odoo11.0
# QQ:35350428
# 邮件:35350428@qq.com
# 手机：13584935775
# 作者：'odoo'
# 公司网址： www.odoo.pw  www.100china.cn www.amoserp.com
# Copyright 昆山一百计算机有限公司 2012-2020 Amos
# 日期：2019/12/11
# &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&

{
    'name': 'AmosERP-底层',
    'summary': '底层',
    'category': '基础',
    'sequence': 10000,
    'author': 'Amos',
    'website': 'http://www.100china.cn',
    'depends': ['base', 'web','contacts','calendar', 'portal', 'utm'],
    'version': '1.0',
    'data': [
        'data/city_data.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/menuitem.xml',
        'views/res_address_view.xml',
        'views/res_company_view.xml',
        'views/res_users_view.xml',
    ],
    'qweb': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'description': """
    基本功能框架构建
""",
}

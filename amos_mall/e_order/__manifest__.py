# -*- coding: utf-8 -*-
{
    'name': u'草莓-订单系统',
    'summary': '订单系统',
    'version': '1.0',
    'category': u'订单',
    'sequence': 100,
    'author': 'Amos',
    'website': 'http://www.100china.cn',
    'depends': ['base', 'e_product','portal','e_base'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/e_order.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'description': """
    """,
}

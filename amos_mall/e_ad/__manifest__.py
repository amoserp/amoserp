# -*- coding: utf-8 -*-
{
    'name': u'草莓-Ad',
    'summary': 'App广告系统',
    'version': '1.0',
    'category': u'商品',
    'sequence': 100,
    'author': 'Amos',
    'website': 'http://www.100china.cn',
    'depends': ['base', 'mail','e_base'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        # 'views/e_ad.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'description': """
    默认提供静态参数
    """,
}

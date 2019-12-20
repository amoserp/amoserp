# -*- coding: utf-8 -*-
# &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
# Odoo Connector
# QQ:35350428
# 邮件:sale@100china.cn
# 手机：13584935775
# 作者：'wangguangjian'
# 公司网址： www.odoo.pw  www.100china.cn
# Copyright 昆山一百计算机有限公司 2012-2016 Amos
# 日期：2014-06-18
# &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&


import xmlrpclib

# ++++++++++++++++++根据网址取帐户信息
# info = xmlrpclib.ServerProxy('http://127.0.0.1:8049/start').start()
# url, db, username, password = \
#     info['host'], info['database'], info['user'], info['password']
url = 'http://127.0.0.1:9011'
db = 'amoserp3'
username = 'admin'
password = '1'

common = xmlrpclib.ServerProxy('{}/xmlrpc/2/common'.format(url))

# #++++++++++++++++++获取当前用户id
uid = common.authenticate(db, username, password, {})

# #++++++++++++++++++获取当前用户id
models = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(url))

# # #++++++++++++++++++查询并读取出字段信息
pream = models.execute_kw(db, uid, password,
                          'ir.module.module', 'search_read',
                          [[['state', 'in', ['installed', 'to upgrade', 'to remove']]]],
                          {'fields': ['name']})

app = []

for line in pream:
    app.append(line['name'])

print app


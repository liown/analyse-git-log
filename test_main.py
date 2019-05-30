#!/usr/bin/env python
# -*-coding:utf-8 -*-
#
# Author: liown
# Filename: __init__.py
# Time: 2019/5/17 9:06
# Description:

import unittest

#
# class BaseTestCase(unittest.TestCase):
#     def tearDown(self):
#         # 每个测试用例执行之后做操作
#         pass
#
#     def setUp(self):
#         # 每个测试用例执行之前做操作
#         pass
#
#     @classmethod
#     def tearDownClass(cls):
#         # 必须使用 @ classmethod装饰器, 所有test运行完后运行一次
#         pass
#
#     @classmethod
#     def setUpClass(cls):
#         # 必须使用@classmethod 装饰器,所有test运行前运行一次
#         pass


if __name__ == "__main__":
    # 创建测试套件
    suite = unittest.TestSuite()
    all_cases = unittest.defaultTestLoader.discover('.','test_*.py')
    for case in all_cases:
        suite.addTests(case)  # 把所有的测试用例添加进来
    with open("report.txt", "w") as f:
        runner = unittest.TextTestRunner(stream=f, verbosity=2)
        runner.run(suite)
#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
@date: 2015-10-15
@author: zoom.quiet
@comment:

专门用来快速重新调整内置模板的脚本!
'''
import base64

def main():
    print base64.b64encode(open('md2slide_tpl.html').read())

if __name__ == '__main__': main()

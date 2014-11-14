# -*- coding:utf-8 -*-
import requests
import python_mysql as mydb
from pyquery import PyQuery as pq
import re
from decimal import Decimal
import time
from dzdpconfig import *


def process(item):
    ##处理一个条目，返回所有解析信息
    #部分信息在概略页获取，部分在详细页获取
    item = pq(item)
    try:
        shopname = item('.tit h4').text()
    except AttributeError:
        pass
    remark = item('.comment')
    try:
        grade = pq(remark)('span').attr('title')
    except AttributeError:
        grade = '-1'
    try:
        comment = pq(remark)('.review-num b').text()
        #comment会出现没有点评的现象，需要进行字符串处理
        if comment == u'我要点评':
            comment = u'0'
    except AttributeError:
        comment = '-1'
    try:
        //comdetail = item('.comment')
        avg = pq(comdetail)('.price').text()
        #可能没有价格信息
        if avg == u'-':
            avg = u'0'
    except AttributeError:
        avg = '-1'
    try:
        clist = pq(comdetail)('.comment-list')
        ctext = pq(clist).text()
        cnum = re.findall(r'[\d|.]+', str(ctext))
        kouwei = cnum[0]
        huanjing = cnum[1]
        fuwu = cnum[2]
    except AttributeError:
        kouwei = '-1'
        huanjing = '-1'
        fuwu = '-1'
    try:
        tags = item('.address a').text()
    except AttributeError:
        tags = '-1'
    #详细页获取信息
    href = item('.shopname').attr('href')
    itemurl = webroot + href
    itempage = requests.get(itemurl).text
    itemhtml = pq(itempage)
    try:
        addinfo = itemhtml('span').filter(lambda i: pq(this).attr('itemprop') == 'street-address')
        address = pq(addinfo).text()
    except AttributeError:
        address = '-1'
    try:
        phoneinfo = itemhtml('span').filter(lambda i: pq(this).attr('itemprop') == 'tel')
        phone = pq(phoneinfo).text()
    except AttributeError:
        phone = '-1'
    try:
        yytime = ''
        other1 = itemhtml('.other p')
        for p in other1:
            p = pq(p)
            infoname = p('.info-name').text()
            if u'营业' in infoname:
                yytime = p('.item').text()
    except AttributeError:
        yytime = '-1'
    try:
        utags = ''
        for q in other1:
            q = pq(q)
            infoname = q('.info-name').text()
            if u'分类' in infoname:
                utags = q('.item').text().replace(' (', '(')
    except AttributeError:
        utags = '-1'
    return (shopname,grade,comment,avg,kouwei,huanjing,fuwu,tags,address,phone,yytime,utags)


if __name__ == '__main__':
    mysqlconn = mydb.Connection(host=mysql_host, database=mysql_database, user=mysql_user, password=mysql_password)
    urlFile = open(cFile, 'r')
    lines = urlFile.readlines()
    group = len(lines)/3
    for i in range(group):
        #需要将行末的换行符去掉，最后一行单独处理
        if i < group - 1:
            kword = lines[i][:-1]
            firstUrl = lines[3*i + 1][:-1]
            nextUrl = lines[3*i + 2][:-1]
        else:
            kword = lines[i][:-1]
            firstUrl = lines[3*i + 1][:-1]
            nextUrl = lines[3*i + 2]
        firstPage = requests.get(firstUrl).text
        html = pq(firstPage)
        #获取总计有多少页
        tpage = html('.page a')[-2]
        totalnum = pq(tpage).text()
        #获取所有的条目
        items = html('.content ul li')
        for item in items:
            shopname, grade, comment, avg, kouwei, huanjing, fuwu, tags, address, phone, yytime, utags = process(item)
            mysqlconn.insert(mysql_tablename,
                             name=shopname,
                             grade=grade,
                             comment=comment,
                             avg=avg,
                             kouwei=kouwei,
                             huanjing=huanjing,
                             fuwu=fuwu,
                             tags=tags,
                             address=address,
                             phone=phone,
                             yytime=yytime,
                             utags=utags,
                             kword=kword)
            time.sleep(0.5)
        mysqlconn.commit()
        print '%s--page 1--finished' % kword
        #处理剩余的页面
        total = Decimal(totalnum)
        for j in range(2, total + 1):
            nUrl = nextUrl.replace('(*)', str(j))
            page = requests.get(nUrl).text
            nhtml = pq(page)
            nitems = nhtml('.content ul li')
            for nitem in nitems:
                shopname, grade, comment, avg, kouwei, huanjing, fuwu, tags, address, phone, yytime, utags = process(nitem)
                mysqlconn.insert(mysql_tablename,
                                 name=shopname,
                                 grade=grade,
                                 comment=comment,
                                 avg=avg,
                                 kouwei=kouwei,
                                 huanjing=huanjing,
                                 fuwu=fuwu,
                                 tags=tags,
                                 address=address,
                                 phone=phone,
                                 yytime=yytime,
                                 utags=utags,
                                 kword=kword)
                time.sleep(0.5)
            mysqlconn.commit()
            print '%s--page %s--finished' % (kword, str(j))
        print '<---------------->'
    print 'all finished'
    mysqlconn.close()

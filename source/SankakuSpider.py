# Copyright: Copyright(c) 2018
# Created on 2018 - 12 - 7
# Author: HowsonLiu
# Version 1.2
# Title: Sankaku爬虫

import requests
from bs4 import BeautifulSoup
import os           # 路径
import re           # 正则
import pyperclip    # 粘贴板
import traceback    # 异常抛出
import sys          # 参数处理
import getopt
from concurrent.futures import ThreadPoolExecutor, wait   # 线程池

home_url = 'https://chan.sankakucomplex.com'
save_path = 'D:\\SankakuImage'  # 默认保存路径
id_url = 'https://chan.sankakucomplex.com/post/show/'
tag_url = 'https://chan.sankakucomplex.com/?tags='

headers = {
    'Referer': 'https://chan.sankakucomplex.com/post/show/7356020'  # 防盗链
}

crawl_id = ''
crawl_tag = ''
small_mode = False
thread_num = 3                                                  # 默认3个线程

#  只爬取单张图片
#  target_url为string, 如'https://chan.sankakucomplex.com/post/show/7356020'
#  img_id为string, 如'7356020', 用于文件名字
def CrawlSingleImage(target_url, img_id):
    global headers, save_path
    img_name = img_id
    if os.path.exists(os.path.join(save_path, img_name + '_big.jpg')) or \
        os.path.exists(os.path.join(save_path, img_name + '_small.jpg')):
        print(img_id + ' 图片已存在! 跳过')
        return -2

    try:
        target_html = requests.get(target_url, headers=headers)     # 请求图片网页
        target_soup = BeautifulSoup(target_html.text, 'lxml')       # 解析
        elem = target_soup.find('a', attrs={'id': 'image-link'})    # 找到图片所在标签
        src_url = 'https:'
        if not small_mode and 'sample' in elem['class']:            # 图片含有大图而且并非小图模式
            print('正在下载 ' + img_id + ' 大图')
            img_name += '_big.jpg'
            src_url += elem['href']                                 # href的url即为大图
        else:                                                       # 只能拉取小图
            print('正在下载 ' + img_id + ' 小图')
            img_name += '_small.jpg'
            src_url += elem.find('img')['src']                      # img中的src为小图
        src_html = requests.get(src_url, headers=headers)           # 打开图片
    except:
        print(img_id + '下载失败')
        # print(traceback.format_exc())
        return -1

    img_path = os.path.join(save_path, img_name)
    file = open(img_path, 'wb')                                 # 二进制写文件
    for chunk in src_html.iter_content(100000):
        file.write(chunk)
    file.close()
    print(img_id + '保存成功! ')
    return 0

#  遍历网站第一页, 对每张图片进行爬取 1.0
#  target_url为string, 如'https://chan.sankakucomplex.com/?tags=tony'
def ForeachPageAndCrawl(target_url):
    try:
        target_html = requests.get(target_url, headers=headers)             # 请求主网页或搜索后的网页
        home_soup = BeautifulSoup(target_html.text, 'lxml')                 # 解析
        all_picts = home_soup.find_all('span', attrs={'class': 'thumb'})    # <span>中class属性值为'thumb'
    except:
        print(target_url + '加载失败')
        return
    print('一共找到 ' + str(len(all_picts)) + ' 张图片哦! ')
    global home_url, thread_num
    pict_ids = []
    hrefs = []
    for pict in all_picts:                                          # 暂且只爬取第一页
        pict_id = pict['id'].replace('p', '')                       # 去掉标签中的id的p
        href = home_url + pict.find('a')['href']                    # 找出每一张图片的网页url
        pict_ids.append(pict_id)
        hrefs.append(href)
    executor = ThreadPoolExecutor(max_workers=thread_num)
    err_num = skip_num = succ_num = 0
    for res in executor.map(CrawlSingleImage, hrefs, pict_ids):
        if res == -1:
            err_num += 1
        elif res == -2:
            skip_num += 1
        elif res == 0:
            succ_num += 1
    print('爬取完毕! ' + str(succ_num) + '张成功, ' + str(skip_num) + '张跳过, ' + str(err_num) + '张失败')


#  使用粘贴板的url爬取图片
def ClipCrawl():
    input_url = pyperclip.paste()
    print('这是你复制的url “' + input_url + '"')
    if not input_url:
        print('你并没有复制url! ')
        print('要先复制Sankaku的网站, 再运行此脚本哦')
        return
    if re.compile(r'^(https://|http://)?chan.sankakucomplex.com').search(input_url) is None:  # 确认网址是Sankaku
        print('''
你复制的不是Sankaku的网站! 
以下类型地址均可以哦: 
主页: https://chan.sankakucomplex.com
标签搜索: https://chan.sankakucomplex.com/?tags=tony
排名: https://chan.sankakucomplex.com/rankings/show?order=quality&type=artists&page=1
某张图片: https://chan.sankakucomplex.com/post/show/7356020
        ''')
        return
    global save_path
    if not os.path.exists(save_path):               # 确定保存路径存在
        print(save_path + ' 路径不存在，已创建！')
        os.mkdir(save_path)
    if re.compile(r'^(https://|http://)?chan.sankakucomplex.com/post/show/\d+$').search(input_url):   # 网址是图片类型
        img_id = re.compile(r'\d+$').search(input_url).group()    # 根据url解析出id
        CrawlSingleImage(input_url, img_id)
    else:
        ForeachPageAndCrawl(input_url)

def CrawlById():
    target_url = id_url + crawl_id
    CrawlSingleImage(target_url, crawl_id)

def CrawlByTag():
    target_url = tag_url + crawl_tag
    ForeachPageAndCrawl(target_url)

def Help():
    print('''
-h 或 --help 查看使用方法
-s 爬图片时只爬小图
-n <num> 开启<num>个线程爬取
-i <id> 直接爬取<id>的图片
-t <tag> 搜索<tag>标签并爬取图片
    ''')

def ArgsHandle():
    global small_mode, crawl_tag, crawl_id, thread_num
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hsi:t:n:', ["help"])     #短参数为-h -s -i -t -n, 长参数为--help 其中-i -t -n带参数
    except getopt.GetoptError:
        print("你输入的参数有错哦！")
        print('请加入-h查看使用方法吧！')
        return
    try:
        conflict = False                            # id 与 tag 不能同时搜索
        for cmd, arg in opts:                       # 每次循环取出一对命令与参数
            if cmd in ('-h', '--help'):
                Help()
            elif cmd == '-s':
                print('现在是小图模式！')
                small_mode = True
            elif cmd == '-n':
                thread_num = int(arg)
                print('你开启了' + arg + '个线程！')
            elif cmd == '-i':
                if conflict:
                    raise Exception
                conflict = True
                crawl_id = arg
                print('你要寻找的id 是: ' + arg)
            elif cmd == '-t':
                if conflict:
                    raise Exception
                conflict = True
                crawl_tag = arg
                print('你要寻找的tag 是' + arg)
    except Exception:
        print('你不能同时寻找id和tag哦！')
        return
    if crawl_id:                                   # 根据id, tag选定爬取来源
        CrawlById()
    elif crawl_tag:
        CrawlByTag()
    else:
        ClipCrawl()

ArgsHandle()
# os.system('pause')  # 拒绝一闪而过

# Copyright: Copyright(c) 2018
# Created on 2018 - 12 - 7
# Author: HowsonLiu
# Version 1.3
# Title: Sankaku爬虫

import requests
from bs4 import BeautifulSoup
import os           # 路径
import re           # 正则
import pyperclip    # 粘贴板
import traceback    # 异常抛出
import sys          # 参数处理
import getopt
from concurrent.futures import ThreadPoolExecutor   # 线程池
import datetime
import configparser     # ini解析

home_url = 'https://chan.sankakucomplex.com'
save_path = r'D:\SankakuImage'      # 默认保存路径ti
id_url = 'https://chan.sankakucomplex.com/post/show/'
tag_url = 'https://chan.sankakucomplex.com/?tags='
log_path = r'.\SankakuSpiderERROR.log'      # log保存路径
ini_path = r'.\SankakuSpider.ini'           # ini保存路径

err_msg = '''                       
[ERROR] {time}
下载 {url} 的图片失败
{traceback}


'''

default_ini = '''[setting]
;爬取图片的默认保存路径
save_path={save_path}
;默认开启线程数
thread_num={thread_num}
'''

headers = {
    'Referer': 'https://chan.sankakucomplex.com/post/show/7356020'  # 防盗链
}

crawl_id = ''
crawl_tag = ''
small_mode = False
err_num = skip_num = succ_num = 0
thread_num = 3                                                  # 默认3个线程

#  只爬取单张图片
#  target_url为string, 如'https://chan.sankakucomplex.com/post/show/7356020'
#  img_id为string, 如'7356020', 用于文件名字
def CrawlSingleImage(target_url, img_id):
    global headers, save_path, err_msg, skip_num, succ_num, err_num
    img_name = img_id
    if os.path.exists(os.path.join(save_path, img_name + '_big.jpg')) or \
        os.path.exists(os.path.join(save_path, img_name + '_small.jpg')):
        skip_num += 1
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
    except:                                                         # 出错写日志
        print(img_id + '下载失败')
        time_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        msg = err_msg.format(time=time_str, url=target_url, traceback=traceback.format_exc())
        log_file = open(log_path, 'a', encoding='utf-8')
        log_file.write(msg)
        log_file.close()
        err_num += 1
        return -1

    img_path = os.path.join(save_path, img_name)
    file = open(img_path, 'wb')                                 # 二进制写文件
    for chunk in src_html.iter_content(100000):
        file.write(chunk)
    file.close()
    succ_num += 1
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
        return -1
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
    for res in executor.map(CrawlSingleImage, hrefs, pict_ids):
        res     # 等待全部完成
    if succ_num > 0 or skip_num > 0:
        return 0
    else:
        return -1

#  使用粘贴板的url爬取图片
def ClipCrawl():
    input_url = pyperclip.paste()
    print('这是你复制的url “' + input_url + '"')
    if not input_url:
        print('你并没有复制url! ')
        print('要先复制Sankaku的网站, 再运行此脚本哦')
        return -1
    if re.compile(r'^(https://|http://)?chan.sankakucomplex.com').search(input_url) is None:  # 确认网址是Sankaku
        print('''
你复制的不是Sankaku的网站! 
以下类型地址均可以哦: 
主页: https://chan.sankakucomplex.com
标签搜索: https://chan.sankakucomplex.com/?tags=tony
排名: https://chan.sankakucomplex.com/rankings/show?order=quality&type=artists&page=1
某张图片: https://chan.sankakucomplex.com/post/show/7356020
        ''')
        return -1
    if re.compile(r'^(https://|http://)?chan.sankakucomplex.com/post/show/\d+$').search(input_url):   # 网址是图片类型
        img_id = re.compile(r'\d+$').search(input_url).group()    # 根据url解析出id
        return CrawlSingleImage(input_url, img_id)
    else:
        return ForeachPageAndCrawl(input_url)

def CrawlById():
    target_url = id_url + crawl_id
    return CrawlSingleImage(target_url, crawl_id)

def CrawlByTag():
    target_url = tag_url + crawl_tag
    return ForeachPageAndCrawl(target_url)

def Help():
    print('''
-h 或 --help 查看使用方法
-s 爬图片时只爬小图
--thread=<num> 开启<num>个线程爬取
-i <id> 直接爬取<id>的图片
-t <tag> 搜索<tag>标签并爬取图片
    ''')

# 在爬取前显示配置信息
def ShowInfoBeforeCrawl():
    print('图片保存的路径是 ' + save_path)
    print('爬取所用线程数为 ' + str(thread_num))
    if small_mode:
        print('小图模式已启用')
    else:
        print('小图模式已禁用')
    if crawl_id:
        print('你要爬取的图片id是: ' + crawl_id)
    elif crawl_tag:
        print('你要爬取的tag是 ' + crawl_tag)

# 创建默认ini文件
def CreateDefaultIni():
    global ini_path, default_ini, save_path, thread_num
    ini_file = open(ini_path, 'w')
    ini_file.write(default_ini.format(save_path=save_path, thread_num=thread_num))
    ini_file.close()
    if not os.path.exists(save_path):
        os.mkdir(save_path)
    print('已经帮你创建默认的ini文件啦, 可能顺带还有默认的保存路径 ' + save_path + ' 呢')

# 解析ini文件, 当ini文件不存在或是解析出问题, 重写成默认ini
def ParseIni():
    global save_path, thread_num
    if not os.path.exists(ini_path):
        print('ini文件不存在哦')
        CreateDefaultIni()
        return -1
    else:
        try:
            config = configparser.ConfigParser()
            config.read(ini_path)
            get_save_path = config['setting']['save_path']
            if not os.path.exists(get_save_path):
                print('保存路径 ' + get_save_path + ' 不存在')
                raise Exception()
            get_thread_num = int(config['setting']['thread_num'])
        except:                             # 不能读取或者内容出错
            print('ini文件有错误哦')
            CreateDefaultIni()
            return -1
        save_path = get_save_path
        thread_num = get_thread_num
        print('ini文件成功读取了呢')
        return 0

# 爬虫主函数
def StartCrawl():
    if crawl_id:                                   # 根据id, tag选定函数
        return CrawlById()
    elif crawl_tag:
        return CrawlByTag()
    else:
        return ClipCrawl()

def AfterCrawl():
    os.startfile(save_path)             # 打开文件夹

def ArgsHandle():
    global small_mode, crawl_tag, crawl_id, thread_num
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hsi:t:', ["help", "thread="])     #短参数为-h -s -i -t, 长参数为--help --thread= ,其中-i -t -n带参数
    except getopt.GetoptError:
        print("你输入的参数有错哦！")
        print('请加入-h查看使用方法吧！')
        return -1
    try:
        conflict = False                            # id 与 tag 不能同时搜索
        for cmd, arg in opts:                       # 每次循环取出一对命令与参数
            if cmd in ('-h', '--help'):
                Help()
            elif cmd == '-s':
                small_mode = True
            elif cmd == '--thread':
                thread_num = int(arg)
            elif cmd == '-i':
                if conflict:
                    raise Exception
                conflict = True
                crawl_id = arg
            elif cmd == '-t':
                if conflict:
                    raise Exception
                conflict = True
                crawl_tag = arg
    except Exception:
        print('你不能同时寻找id和tag哦！')
        return -1
    return 0

# 保证ini正确
ParseIni()
# 保证命令行正确
if ArgsHandle() == 0:
    ShowInfoBeforeCrawl()
    # 开始爬虫
    res = StartCrawl()
    if res == 0 or res == -2:
        AfterCrawl()    # 确认有新图片或者跳过才打开
os.system('pause')  # 拒绝一闪而过

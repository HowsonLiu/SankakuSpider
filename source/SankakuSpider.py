# Copyright: Copyright(c) 2018
# Created on 2018 - 12 - 7
# Author: HowsonLiu
# Version 1.0
# Title: Sankaku爬虫

import requests
from bs4 import BeautifulSoup
import os           # 路径
import re           # 正则
import pyperclip    # 粘贴板
import traceback    # 异常抛出

home_url = 'https://chan.sankakucomplex.com'

headers = {
    'Referer': 'https://chan.sankakucomplex.com/post/show/7356020'  # 防盗链
}

save_path = 'D:\\SankakuImage'  # 默认保存路径

#  只爬取单张图片
#  target_url为string, 如'https://chan.sankakucomplex.com/post/show/7356020'
#  img_id为string, 如'7356020', 用于文件名字
def DownloadSingleImage(target_url, img_id):
    target_html = requests.get(target_url, headers=headers)     # 请求图片网页
    target_soup = BeautifulSoup(target_html.text, 'lxml')       # 解析
    elem = target_soup.find('a', attrs={'id': 'image-link'})    # 找到图片所在标签
    src_url = 'https:'
    if 'sample' in elem['class']:                               # 图片含有大图
        print('正在下载 ' + img_id + ' 大图')
        src_url += elem['href']                                 # href的url即为大图
    else:                                                       # 只能拉取小图
        print('这张图片没有分辨率高的')
        print('正在下载 ' + img_id + ' 小图')
        src_url += elem.find('img')['src']                      # img中的src为小图
    src_html = requests.get(src_url, headers=headers)           # 打开图片
    img_name = img_id + '.jpg'
    img_path = os.path.join(save_path, img_name)
    file = open(img_path, 'wb')                                 # 二进制写文件
    for chunk in src_html.iter_content(100000):
        file.write(chunk)
    file.close()
    print(img_id + '保存成功! ')

#  遍历网站第一页, 对每张图片进行下载 1.0
#  target_url为string, 如'https://chan.sankakucomplex.com/?tags=tony'
def ForeachPageAndDownload(target_url):
    target_html = requests.get(target_url, headers=headers)             # 请求主网页或搜索后的网页
    home_soup = BeautifulSoup(target_html.text, 'lxml')               # 解析
    all_picts = home_soup.find_all('span', attrs={'class': 'thumb'})  # <span>中class属性值为'thumb'
    print('一共找到 ' + str(len(all_picts)) + ' 张图片哦! ')
    for pict in all_picts:                                          # 暂且只爬取第一页
        pict_id = pict['id'].replace('p', '')       # 去掉标签中的id的p
        href = home_url + pict.find('a')['href']    # 找出每一张图片的网页url
        # print(pict_id, href)
        DownloadSingleImage(href, pict_id)

#  开始函数
def Start():
    input_url = pyperclip.paste()
    print('这是你复制的url “' + input_url + '"')
    if not input_url:
        print('你并没有复制url! ')
        print('要先复制Sankaku的网站, 再运行此脚本哦')
        return
    if re.compile(r'^(https://|http://)?chan.sankakucomplex.com').search(input_url) is None:  # 确认网址是Sankaku
        print('你复制的不是Sankaku的网站! ')
        print('以下类型地址均可以哦: ')
        print('主页: https://chan.sankakucomplex.com')
        print('标签搜索: https://chan.sankakucomplex.com/?tags=tony')
        print('排名: https://chan.sankakucomplex.com/rankings/show?order=quality&type=artists&page=1')
        print('某张图片: https://chan.sankakucomplex.com/post/show/7356020')
        return
    if not os.path.exists(save_path):               # 确定保存路径存在
        print(save_path + ' 路径不存在，已创建！')
        os.mkdir(save_path)
    try:
        if re.compile(r'^(https://|http://)?chan.sankakucomplex.com/post/show/\d+$').search(input_url):   # 网址是图片类型
            img_id = re.compile(r'\d+$').search(input_url).group()    # 根据url解析出id
            DownloadSingleImage(input_url, img_id)
        else:
            ForeachPageAndDownload(input_url)
        print('任务完成! ')
    except:
        print('哎呀，出错了呢! ')
        print('错误是: ' + traceback.format_exc())


Start()
os.system('pause')  # 拒绝一闪而过
#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Created on 2016-09-05 09:06:41
# Project: hospital

from pyspider.libs.base_handler import *
import os
from urllib.parse import urlparse
import re
import requests

# http://www.yezizx.com
# http://www.redream.com/
# shredream.cn

BASE_URL = 'http://sj.haoyunbyby.com/zhuanti/slgby/'


class Handler(BaseHandler):
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/52.0.2743.116 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, sdch',
            'Accept-Language': 'zh-CN,zh;q=0.8'
        }
        self.deal = Deal(BASE_URL)

    @every(minutes=24 * 60)
    def on_start(self):
        self.crawl(self.deal.base_url, callback=self.index_page, headers=self.headers, fetch_type='js')

    def index_page(self, response):
        self.deal = Deal(response.url)
        self.deal.deal_html(response)
        # 获取当前列表下的所有链接
        url_list = []
        for each in response.doc('a').items():
            if each.attr.href and re.match(self.deal.base_url + '/.+', each.attr.href):
                url_list.append(each.attr.href)
        [self.crawl(each, callback=self.child_page, headers=self.headers, fetch_type='js') for each in url_list]

    def child_page(self, response):
        self.deal = Deal(response.url)
        self.deal.deal_html(response)


class Deal:
    def __init__(self, url):
        self.base_url = BASE_URL.strip()
        if self.base_url[len(self.base_url) - 1] == '/':
            self.base_url = self.base_url[0:len(self.base_url) - 1]
        # 要处理的页面url
        self.root_url = url
        # 抓取页面保存的路径
        self.save_root_path = '/home/wwwroot/default/' + urlparse(self.root_url).netloc + urlparse(
            self.root_url).path.replace('/', '-')
        if self.save_root_path[-1] == '-':
            self.save_root_path = self.save_root_path[0:-1]
        if not os.path.exists(self.save_root_path):
            os.mkdir(self.save_root_path)

    def deal_html(self, response):
        img_path = self.mkdir('images')
        for each in response.doc('img').items():
            img_filename = self.rename(each.attr.src)
            if img_filename:
                save_img_path = img_path + '/' + img_filename
                img_content = requests.get(each.attr.src).content
                each.attr.src = 'images/' + img_filename
                self.save_file(img_content, 'wb', save_img_path)

        css_path = self.mkdir('css')
        for each in response.doc('link').items():
            if each.attr.href and urlparse(each.attr.href).path.split('.')[-1] == 'css':
                css_filename = self.rename(each.attr.href)
                self.deal_css(each.attr.href)
                each.attr.href = 'css/' + css_filename


        js_path = self.mkdir('js')
        for each in response.doc('script').items():
            if each.attr.src and urlparse(each.attr.src).path.split('.')[-1] == 'js':
                js_filename = self.rename(each.attr.src)
                save_js_path = js_path + '/' + js_filename
                js_content = requests.get(each.attr.src).text
                self.save_file(js_content, 'w', save_js_path)
                each.attr.src = 'js/' + js_filename

        html_content = str(response.doc('html').html())
        for each in re.findall(r'background:.*?url\(.+?\)', html_content):
            old_img_path = re.search(r'\(("|\')?(.+\.\w+?)("|\')?\)', each).group(2)
            # 去除base64
            if not urlparse(old_img_path).scheme == 'data':
                download_url = self.path_to_url(old_img_path, self.base_url)
                file_content = requests.get(download_url).content
                filename = self.rename(download_url)
                new_img_path = self.save_root_path + '/images/' + filename
                self.save_file(file_content, 'wb', new_img_path)
                html_content = html_content.replace(old_img_path, 'images/' + filename)

        html_content = '<!DOCTYPE html>\n<html>' + html_content + '</html>'
        html_content = html_content.replace('&gt;', '>')
        html_content = html_content.replace('&lt;', '<')
        html_content = html_content.replace('&amp;', '&')

        for each in re.findall(r'<i.*?/>', html_content):
            new_script_tag = each.replace('/>', '></i>')
            html_content = html_content.replace(each, new_script_tag)
        for each in re.findall(r'<script.*?/>', html_content):
            new_script_tag = each.replace('/>', '></script>')
            html_content = html_content.replace(each, new_script_tag)

        self.save_file(html_content, 'w', self.save_root_path + '/index.html')

    def deal_css(self, css_href):
        cssfile_path = urlparse(css_href).scheme + \
                       '://' + \
                       urlparse(css_href).netloc + \
                       self.rm_filename_in_path(urlparse(css_href).path)
        css_content = requests.get(css_href).text
        # 下载css文件中的背景图
        for each in re.findall(r'url\(.+?\)', css_content):
            old_css_img_path = re.search(r'\(("|\')?(.+?)("|\')?\)', each).group(2)
            # base64
            if not urlparse(old_css_img_path).scheme == 'data':
                css_img_url = self.path_to_url(old_css_img_path, cssfile_path)
                css_img_filename = self.rename(css_img_url)
                css_img_content = requests.get(css_img_url).content
                self.save_file(css_img_content, 'wb', self.save_root_path + '/images/' + css_img_filename)
                css_content = re.sub(r'url\(("|\')?' + old_css_img_path + '("|\')?\)',
                                     'url(../images/' + css_img_filename + ')', css_content)
        self.save_file(css_content, 'w', self.save_root_path + '/css/' + self.rename(css_href))

    def mkdir(self, dirname):
        # 创建文件夹
        dirname = dirname.strip()
        if dirname.startswith('/'):
            dirname.lstrip('/')
        dir_path = self.save_root_path + '/' + dirname
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        return dir_path

    def save_file(self, content, mode, path):
        # 保存文件到指定目录
        with open(path, mode=mode) as f:
            f.write(content)
            return 0
        return -1

    def path_to_url(self, path, base_url):
        # 路径转下载url
        if not base_url[len(base_url) - 1] == '/':
            base_url += '/'
        if path[0] == '/':
            path = path[1:]
        if not (urlparse(path).scheme and urlparse(path).netloc):
            return base_url + path
        return path

    def rm_filename_in_path(self, path):
        # 把路径中的文件名删除
        arr = urlparse(path).path.split('/')
        if arr[0] == '':
            arr.pop(0)
        arr.pop()
        arr = ['/' + each for each in arr]
        return ''.join(arr) + '/'

    def rename(self, url):
        # 重命名文件防止重名
        full_filename = urlparse(url).path.split('/')[-1]
        extension = full_filename.split('.')[-1]
        filename = full_filename.replace('.'+extension, '')
        # i = 1

        # if extension == 'jpg' or extension == 'png' or extension == 'gif' or extension == 'bmp' or extension == 'jpeg':
        #     if os.path.exists(self.save_root_path + '/images/' + filename):
        #         while 1:
        #             if os.path.exists(self.save_root_path + '/images/' + filename):
        #                 i += 1
        #             else:
        #                 print(filename + '-' + str(i) + '.' + extension)
        #                 return filename + '-' + str(i) + '.' + extension
        # return urlparse(url).path.split('/')[-1]
        # return (urlparse(url).netloc + urlparse(url).path).replace('/', '_')
        return filename + '.' + extension

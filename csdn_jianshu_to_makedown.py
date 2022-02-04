# coding=utf-8
from glob import glob
import re
from time import time
import requests
import os
# from xml.dom import minidom
from lxml import etree
import base64
import traceback

import html2text as ht #

from selenium.webdriver.chrome.options import Options
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import configparser

## 配置文件名称
configFileName = "config.ini"


res = "res" # 资源目录名称
head={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36 Edg/84.0.522.52"}
base64ImgHead = "data:image/png;base64,"

request_url = ""
bypass_tables = False
chromeDriverName = ""
# 初始化配置信息
def init_config():
    global request_url
    global bypass_tables
    global chromeDriverName
    config = configparser.ConfigParser()
    config.read(configFileName)
    request_url = config['base_config']['url']
    bypass_tables = config['base_config'].getboolean('bypass_tables')
    chromeDriverName = config['base_config']['config_fileName']


## 判断当前协议
def http_protocol(url):
    if url.startswith('https://'):
        return "https:"
    elif url.startswith('http://'):
        return "http:"


def get_image_type(Url,Number):
        if Url.find(base64ImgHead) != -1:
            return ("png_base64", str(Number)+".png")
        else:
            if Url.find(".jpg") != -1:
                return("url", str(Number)+".jpg")
            elif Url.find(".png") != -1:
                return ("url", str(Number)+".png")
            else:
                return ("url", str(Number)+".png")


def init_browser(url):
    chrome_options = webdriver.ChromeOptions()
    # # 禁用浏览器弹窗
    prefs = {"profile.default_content_setting_values.notifications": 2}
    chrome_options.add_experimental_option("prefs", prefs)
    # 设置浏览器不显示
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(os.path.join(os.getcwd(),chromeDriverName) ,chrome_options=chrome_options)
    driver.maximize_window()    
    driver.get(url)
    return driver

# 创建无头浏览器，来处理浏览器执行 跑 n 秒后的页面状态返回回来
def browser_request(url, loadmore = False, waittime = 2):
    browser = init_browser(url)
    time.sleep(waittime)
    if loadmore:
        while True:
            try:
                next_button = browser.find_element_by_class_name("ant-btn")
                next_button.click()
                time.sleep(waittime)
            except Exception as e:
                # traceback.print_exc()
                # info = traceback.format_exc()
                # print(info)
                break
    else:
        time.sleep(waittime)

    html = browser.page_source
    browser.quit()
    return html

def request(url):
    Result=requests.get(url,headers=head)
    Result.encoding = 'utf-8'
    return Result.text

def save_file(fileName, text):
    fileRef = open(fileName, "w+", encoding='utf-8') # win 环境必须指定编码类型，否则默认会使用系统的 gbk编码 
    fileRef.write(text)
    fileRef.close()

def get_csdn_title(root):
    r = root.xpath('//h1[@id="articleContentId"][@class="title-article"]/text()')[0].replace("/","%")
    return r

def get_jianshu_title(root): # //*[@id="__next"]/div[1]/div/div[1]/section[1]/article
    r = root.xpath('//section/h1[@class="_1RuRku"]/text()')[0].replace("/","%")
    
    return r

# 下载资源到本地
def download_res(img_url,srcType,name):
    # print(img_url)
    if srcType == "png_base64" :
        imageBase64Str = img_url.replace(base64ImgHead,"")
        binary_img_data = base64.b64decode(imageBase64Str)
        with open(name,'wb') as fp:
            fp.write(binary_img_data)
        # print(name,'资源下载成功！！！')
    elif srcType == "url":
        img_data = requests.get(url=img_url,headers=head).content
        with open(name,'wb') as fp:
            fp.write(img_data)
            # print(name,'资源下载成功！！！')

# 初始化目录
def init_file(dirName):
    import shutil
    if not os.path.isdir(dirName):
        # shutil.rmtree(titleName)
        os.mkdir(dirName)
    resPath = os.path.join(dirName,res)
    if not os.path.isdir(resPath):
        os.mkdir(resPath)
    return resPath

# 转换为 makedown 并存盘 titleName/titleName.md 文件
def generate_makedown(root, titleName):
    allItem = root.xpath('*')
    need_str = ""
    for p_item in allItem:
        get_str = etree.tostring(p_item,encoding="utf-8")
        need_str += get_str.decode("utf-8")
    text = makedown(need_str)
    save_file(os.path.join(titleName,titleName+".md"), text)

def makedown(need_str):
    text_maker = ht.HTML2Text()
    text_maker.bypass_tables = bypass_tables # 是否使用表格翻译
    text = text_maker.handle(need_str)
    return text

# 处理好 图片的下载逻辑
def downLoadImgMgr(root, resPath):
    imgL = root.xpath('descendant::img')
    record_list = {}
    Number = 0
    for img in imgL:
        DownloadUrl = ""
        if 'data-original-src' in img.attrib and img.attrib['data-original-src'] != "" :
            DownloadUrl = img.attrib['data-original-src']
        elif 'src' in img.attrib and img.attrib['src'] != "" :
            DownloadUrl = img.attrib['src']
        else:
            continue
        if DownloadUrl.startswith('//'):
            DownloadUrl = http_protocol(request_url) + DownloadUrl
        if DownloadUrl in record_list: # 已经下载过了不处理
            img.attrib['src']=record_list[DownloadUrl]
        else:
            srcType,ImageName = get_image_type(DownloadUrl, Number)
            DownloadImgLocalPath = os.path.join(resPath, ImageName)
            ImageNewSrc = os.path.join(res, ImageName)
            download_res(DownloadUrl,srcType, DownloadImgLocalPath)
            img.attrib['src'] = ImageNewSrc
            record_list[DownloadUrl] = ImageNewSrc
            # if srcType == "png_base64":
            Number+=1

# 请求回一个根目录的节点实例
def request_html(url):
    htmlContent = request(url)
    return etree_html(htmlContent)

# 请求回一个根目录的节点实例，通过虚拟一个无头浏览器处理，拿到让js跑完后的结构
def request_html_by_browser(url):
    htmlContent = browser_request(url, True)
    return etree_html(htmlContent)

def etree_html(htmlContent):
    return etree.HTML(htmlContent, parser=etree.HTMLParser(encoding='utf-8'))


def scoll_down(html_page):# 滚轮下拉到最底部
    html_page.send_keys(Keys.END)
    time.sleep(1)


def generate_article(user, content1, content2, AccHtmlContent):
    userHtml = user.get_attribute('outerHTML')
    content1Html = content1.get_attribute('outerHTML')
    content2Html = ""
    if len(content2) != 0 :
        content2Html = content2[0].get_attribute('outerHTML')
    saveHtml = "<div>"+ userHtml + "\n" + content1Html + "\n" + content2Html + "\n" + "</div> \n"
    AccHtmlContent += saveHtml
    return AccHtmlContent


#  csnd 的相关处理
def start_make_csdn():
    tree = request_html(request_url)
    titleName = get_csdn_title(tree)
    resPath = init_file(titleName)
    makeRoot = tree.xpath('//div[@id="content_views"]')[0]
    downLoadImgMgr(makeRoot, resPath)
    generate_makedown(makeRoot, titleName)

# 处理简书
def make_jianshu():
    tree = request_html_by_browser(request_url) # 拿到html结构
    titleName = get_jianshu_title(tree)     # 获取标题
    makeRoot = tree.xpath('//section/article')[0]
    resPath = init_file(titleName)          # 初始化所需目录
    downLoadImgMgr(makeRoot, resPath)       # 处理资源下载
    generate_makedown(makeRoot, titleName)  # 处理makedown转换


def start():
    init_config()
    print(request_url)
    if request_url == "" :
        print("url配置为空")
        return
    if request_url.find("jianshu") != -1:
        make_jianshu()
    elif request_url.find("csdn") != -1:
        start_make_csdn()
    else:
        print("url 错误 不属于csdn也不属于简书")
    
    print("处理 完成")

start()
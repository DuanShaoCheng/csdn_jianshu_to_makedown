# csdn_jianshu_to_makedown
把csdn文章或者简书内容另存为makerdown文件
## 注意事项：
- 需要py 3.x 版本的python
- 只支持有谷歌浏览器的系统
- 需要查看并下载适合对应系统版本的谷歌浏览器的驱动文件，windows为.exe文件
    https://chromedriver.chromium.org/downloads （版本必须与当前系统安装的浏览器版本对应）
- 应用 requirements.txt 中的python库 pip install -r requirements.txt
- 修改配置文件 config.ini base_config 下的 url 配置项
- 执行 python csdn_jianshu_to_makedown.py 启动脚本，执行完毕后当前目录会生成以标题为名的目录，里面就是保存下来的文件

## 原理
### 使用了python 的 selenium 库用来保存简书的内容
### 使用 lxml 对html进行解析定位
### 使用 html2text 完成html到makedown的转换
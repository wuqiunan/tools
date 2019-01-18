## 简介
一个用于Windows平台上的Android截图小工具，并自动复制到剪贴板，方便黏贴~
- 已经打包成exe文件，双击即可运行，需要adb和python环境
- 同时支持多个设备，可自由选择
- 支持查询设备的分辨率、系统版本、设备名等信息，并支持右键复制



 ## 运行效果
- 截图

![image](https://github.com/wuqiunan/tools/blob/master/Images/pic1.png)

- 手机信息

![image](https://github.com/wuqiunan/tools/blob/master/Images/pic2.png)

###打包脚本

pyinstaller -F cap.py
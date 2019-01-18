"""
__author__ =aceiwu
__datetime__ =2018/12/11
"""

import logging
import os
import platform
import subprocess
import time
from io import BytesIO

import win32clipboard as clip
from threading import Thread

import win32con
import wx
from wx.lib.pubsub import pub
from PIL import Image

PATH = os.path.join(os.path.expanduser("~"), 'Desktop')
CAP_FILE_NAME = 'screenshot.bmp'
RECORD_FILE_NAME = 'screenrecord.mp4'
DEVICE_NAME_CMD = 'adb -s {d_id} shell getprop ro.product.model'
SCREENCAP_CMD = r'adb -s {d_id} shell /system/bin/screencap -p /sdcard/{file_name}'
RECORD_CMD = r'adb -s {d_id} shell /system/bin/screenrecord /sdcard/{file_name}'
COPY_CMD = r'adb -s {d_id} pull /sdcard/{file_name} {path}'
RESOLUTION_CMD = 'adb -s {d_id} shell "dumpsys window | grep mUnrestrictedScreen"'
SYS_CMD = 'adb -s {d_id} shell getprop ro.build.version.release'


logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%Y-%H-%d:%M:%S', )
logger = logging.getLogger(__name__)


# 执行命令，返回二进制格式列表
def execute_shell(shell):
    p = subprocess.Popen(shell, shell=True, stdout=subprocess.PIPE)
    out = p.stdout.readlines()
    return out


# 图片保存剪贴板
def set_image(data):
    clip.OpenClipboard()  # 打开剪贴板
    clip.EmptyClipboard()  # 先清空剪贴板
    clip.SetClipboardData(win32con.CF_DIB, data)  # 将图片放入剪贴板
    clip.CloseClipboard()


# 获取设备连接设备列表，返回d_id+设备名
def get_devices_list():
    devices_id_output = execute_shell('adb devices')
    devices_id = [str(i, encoding="utf-8").split('\t')[0] for i in devices_id_output][1:-1]
    devices_list = []
    for d_id in devices_id:
        devices_name = str(execute_shell(DEVICE_NAME_CMD.format(d_id=d_id))[-1], encoding='utf-8')
        devices_list.append('      '.join([d_id, devices_name]))
    return devices_list


# 自定义日志类
class WxTextCtrlHandler(logging.Handler):
    def __init__(self, ctrl):
        logging.Handler.__init__(self)
        self.ctrl = ctrl

    def emit(self, record):
        s = self.format(record) + '\n'
        wx.CallAfter(self.ctrl.WriteText, s)


# 手机信息tab
class PhoneInfo(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.selected = -1
        self.reload_button = wx.Button(parent=self, id=-1, label="重新载入设备", pos=(0, 00), size=(120, 25))
        self.Bind(wx.EVT_BUTTON, self.reload_click, self.reload_button)
        self.phone_info_list = wx.ListCtrl(self, -1, pos=(0, 30), size=(500, 420),
                                           style=wx.LC_REPORT | wx.LC_HRULES | wx.LC_VRULES)
        self.phone_info_list.InsertColumn(1, '序号', format=wx.LIST_FORMAT_LEFT, width=40)
        self.phone_info_list.InsertColumn(2, '设备ID', format=wx.LIST_FORMAT_LEFT, width=155)
        self.phone_info_list.InsertColumn(3, '设备名', format=wx.LIST_FORMAT_LEFT, width=145)
        self.phone_info_list.InsertColumn(4, '分辨率', format=wx.LIST_FORMAT_LEFT, width=80)
        self.phone_info_list.InsertColumn(5, '系统版本', format=wx.LIST_FORMAT_LEFT, width=70)
        self.show_info()

        self.right_click_menu = wx.Menu()
        self.copy_item_1 = self.right_click_menu.Append(-1, '复制设备ID')
        self.copy_item_2 = self.right_click_menu.Append(-1, '复制设备名')
        self.copy_item_3 = self.right_click_menu.Append(-1, '复制分辨率')
        self.copy_item_4 = self.right_click_menu.Append(-1, '复制系统版本')
        self.copy_item_5 = self.right_click_menu.Append(-1, '复制所有信息')
        self.Bind(wx.EVT_MENU, self.copy_device_id, self.copy_item_1)
        self.Bind(wx.EVT_MENU, self.copy_device_name, self.copy_item_2)
        self.Bind(wx.EVT_MENU, self.copy_resolution, self.copy_item_3)
        self.Bind(wx.EVT_MENU, self.copy_sys_code, self.copy_item_4)
        self.Bind(wx.EVT_MENU, self.copy_all, self.copy_item_5)
        self.Bind(wx.EVT_CONTEXT_MENU, self.right_click)

    def show_info(self):
        d_list = get_devices_list()
        for index, d in enumerate(d_list):
            info_list = []
            d_id = d.split(' ')[0]
            info_list.append(d_id.strip())
            info_list.append(' '.join(d.split(' ')[1:]).strip())
            info_list.append(str(execute_shell(RESOLUTION_CMD.format(d_id=d_id))[-1], encoding='utf-8')
                             .strip().split(' ')[-1])
            info_list.append(str(execute_shell(SYS_CMD.format(d_id=d_id))[-1], encoding='utf-8').strip())
            self.phone_info_list.InsertItem(index, index)
            self.phone_info_list.SetItem(index, 0, str(index+1))
            for i, info in enumerate(info_list):
                self.phone_info_list.SetItem(index, i+1, info)

    def reload_click(self, event):
        self.phone_info_list.DeleteAllItems()
        reload_devices_list = get_devices_list()
        if not reload_devices_list:
            wx.MessageBox('没有设备连接！')
            return
        self.show_info()

    def right_click(self, event):
        self.selected = self.phone_info_list.GetFirstSelected()
        if self.selected != -1:
            pos = event.GetPosition()
            pos = self.phone_info_list.ScreenToClient(pos)
            wx.Panel(self).PopupMenu(self.right_click_menu, pos)

    # 右键菜单-复制设备ID
    def copy_device_id(self, event):
        data = self.phone_info_list.GetItem(self.selected, 1).GetText()
        clip.OpenClipboard()
        clip.EmptyClipboard()
        clip.SetClipboardText(data)
        clip.CloseClipboard()

    # 右键菜单-复制设备名
    def copy_device_name(self, event):
        data = self.phone_info_list.GetItem(self.selected, 2).GetText()
        clip.OpenClipboard()
        clip.EmptyClipboard()
        clip.SetClipboardText(data)
        clip.CloseClipboard()

    # 右键菜单-复制分辨率
    def copy_resolution(self, event):
        data = self.phone_info_list.GetItem(self.selected, 3).GetText()
        clip.OpenClipboard()
        clip.EmptyClipboard()
        clip.SetClipboardText(data)
        clip.CloseClipboard()

    # 右键菜单-复制系统版本
    def copy_sys_code(self, event):
        data = self.phone_info_list.GetItem(self.selected, 4).GetText()
        clip.OpenClipboard()
        clip.EmptyClipboard()
        clip.SetClipboardText(data)
        clip.CloseClipboard()

    # 右键菜单-复制所有信息
    def copy_all(self, event):
        data = '设备ID：{}\n设备名：{}\n分辨率：{}\n系统版本：{}'.format(
            self.phone_info_list.GetItem(self.selected, 1).GetText(),
            self.phone_info_list.GetItem(self.selected, 2).GetText(),
            self.phone_info_list.GetItem(self.selected, 3).GetText(),
            self.phone_info_list.GetItem(self.selected, 4).GetText(),
        )
        clip.OpenClipboard()
        clip.EmptyClipboard()
        clip.SetClipboardText(data)
        clip.CloseClipboard()


# 截屏/录屏tab
class Cap(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.d_list = get_devices_list()
        self.devices_info = self.d_list[0].split("\t")[0] if self.d_list else ' '
        wx.StaticText(self, -1, "选择设备:", pos=(15, 7))
        self.devices_combobox = wx.ComboBox(self, -1, self.devices_info, pos=(15, 30),
                                            size=(320, 45), choices=self.d_list, style=wx.CB_READONLY)
        self.capture_button = wx.Button(parent=self, id=-1, label="截屏并复制到剪贴板", pos=(350, 15), size=(120, 25))
        self.record_button = wx.Button(parent=self, id=-1, label="开始录屏", pos=(350, 45), size=(120, 25))
        # self.stop_record_button = wx.Button()
        self.is_save_rb = wx.RadioBox(parent=self, id=-1, label='是否保存文件', pos=(363, 75),
                                      choices=['是', '否'], majorDimension=1, style=wx.RA_SPECIFY_ROWS)
        self.is_save_rb.SetSelection(0)  # 默认保存选是
        self.reload_button = wx.Button(parent=self, id=-1, label="重新载入设备", pos=(15, 77), size=(120, 25))
        self.clear_button = wx.Button(parent=self, id=-1, label="清除日志", pos=(100, 110), size=(100, 25))
        wx.StaticText(self, -1, '日志', pos=(15, 110))
        self.log = wx.TextCtrl(self, -1, '', pos=(15, 140), size=(460, 230),
                               style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_LEFT)

        self.Bind(wx.EVT_BUTTON, self.capture_click, self.capture_button)
        self.Bind(wx.EVT_BUTTON, self.record_click, self.record_button)
        # self.Bind(wx.EVT_BUTTON, self.stop_record_click, self.stop_record_button)
        self.Bind(wx.EVT_BUTTON, self.reload_click, self.reload_button)
        self.Bind(wx.EVT_BUTTON, self.clear_click, self.clear_button)

        pub.subscribe(self.update_display, "update")

        handler = WxTextCtrlHandler(self.log)
        logger.addHandler(handler)
        fmt = "%(asctime)s %(levelname)s %(message)s"
        handler.setFormatter(logging.Formatter(fmt))
        logger.setLevel(logging.DEBUG)

    def capture_click(self, event):
        print('test')
        if not self.devices_combobox.GetValue():
            logger.warning('没有设备可以截图\n')
            return

        self.capture_android(self.devices_combobox.GetValue().split(' ')[0])
        # 是否展示图片
        if "Windows" in platform.platform():
            os.startfile(filepath=os.path.join(PATH, CAP_FILE_NAME))

    def record_click(self, event):
        if not self.devices_combobox.GetValue():
            logger.warning('没有设备可以录屏\n')
            return
        self.record_button = wx.Button(pos=(350, 45), size=(55, 25))
        # self.stop_record_button = wx.Button(parent=self, id=-1, label="结束录屏", pos=(415, 45), size=(55, 25))
        self.record_android(self.devices_combobox.GetValue().split(' ')[0])

    def reload_click(self, event):
        self.devices_combobox.Clear()
        reload_devices_list = get_devices_list()
        if not reload_devices_list:
            logger.warning('没有检测到设备\n')
            return
        for i in reload_devices_list:
            self.devices_combobox.Append(i.split("\t")[0])
        self.devices_combobox.SetValue(reload_devices_list[0].split("\t")[0])
        logger.debug('重新载入设备完成\n')

    def clear_click(self, event):
        self.log.Clear()

    # def msg_click(self, event):
    #     wx.MessageBox(self.get_device_info(self.devices_combobox.GetValue().split(' ')[0]))

    def capture_android(self, device_id):
        logger.debug('开始截图...')
        execute_shell(SCREENCAP_CMD.format(d_id=device_id, file_name=CAP_FILE_NAME))
        execute_shell(COPY_CMD.format(d_id=device_id, file_name=CAP_FILE_NAME, path=PATH))
        picture_path = os.path.join(PATH, CAP_FILE_NAME)
        img = Image.open(picture_path)
        output = BytesIO()
        img.convert("RGB").save(output, "BMP")
        data = output.getvalue()[14:]
        output.close()
        set_image(data)
        logger.debug('已经复制到剪贴板\n')
        if self.is_save_rb.GetStringSelection() == '否':
            os.remove(picture_path)

    def record_android(self, device_id):

        RecordThread(device_id)

        # execute_shell(RECORD_CMD.format(d_id=device_id, file_name=RECORD_FILE_NAME))
        # execute_shell(COPY_CMD.format(d_id=device_id, file_name=RECORD_FILE_NAME, path=PATH))
        # video_path = os.path.join(PATH, CAP_FILE_NAME)

    def update_display(self, msg):
        self.record_button.SetLabel("{}s".format(msg.data))
        # if isinstance(t, int):  # 如果是数字，说明线程正在执行，显示数字
        #     pass
        # else:  # 否则线程未执行，将按钮重新开启
        #     self.record_button.

    def stop_record_click(self, event):
        execute_shell(COPY_CMD.format(d_id=self.devices_combobox.GetValue().split(' ')[0],
                                      file_name=RECORD_FILE_NAME, path=PATH))


class RecordThread(Thread):

    def __init__(self, device_id):
        Thread.__init__(self)
        self.device_id = device_id
        self.start()

    def run(self):
        execute_shell(RECORD_CMD.format(d_id=self.device_id, file_name=RECORD_FILE_NAME))
        for i in range(10):
            time.sleep(1)
            wx.CallAfter(pub.sendMessage, 'update', i)
        wx.CallAfter(pub.sendMessage, 'update', )


class AndroidApp(wx.Frame):

    def __init__(self):
        wx.Frame.__init__(self, None, -1, 'Android工具', size=(500, 440))
        # icon = wx.Icon()
        # icon.CopyFromBitmap(wx.Bitmap("icon.ico", wx.BITMAP_TYPE_ANY))
        # self.SetIcon(icon)

        self.notebook = wx.Notebook(self)
        self.notebook.AddPage(Cap(self.notebook), '截图')
        self.notebook.AddPage(PhoneInfo(self.notebook), '手机信息')
        # self.notebook.AddPage(Record(self.notebook), '录视频')


class MyApp(wx.App):

    def __init__(self):
        wx.App.__init__(self, redirect=False, filename=PATH)

    def OnInit(self):
        frame = AndroidApp()
        frame.Show()
        return True


if __name__ == '__main__':
    # app = wx.PySimpleApp()
    # AutyFrame().Show()
    app = MyApp()
    logging.basicConfig(stream=app)
    app.MainLoop()

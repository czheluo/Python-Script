#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@time    : 2020/3/10 9:33
@file    : TIC_linux.py
@author  : yitong.feng
@contact: yitong.feng@majorbio.com
"""

import os
import socket
import time

import tkinter
from tkinter import StringVar, Label, Entry, Button, ttk
from tkinter.filedialog import askopenfilenames
from tkinter.filedialog import askdirectory


root = tkinter.Tk()
up_or_down = StringVar()
up_files_path = StringVar()
up_files = None
down_dir = StringVar()
linux_port = StringVar()
linux_port.set('12000')

def selectFiles():
    path_ = askopenfilenames()
    path_ = root.tk.splitlist(path_)
    global up_files
    up_files_path.set(path_)
    up_files = path_

def selectPath():
    path_ = askdirectory()
    global down_dir
    down_dir.set(path_)


def be_sure():
    global up_or_down, up_files_path, down_dir, linux_port
    linux_port = int(linux_port.get())
    if not up_or_down == 'upload':
        down_dir = down_dir.get()
    root.destroy()
    # print((up_or_down, up_files, down_dir, linux_port))

def selected(pos):
    global root, up_or_down, up_files_path, down_dir, linux_port, up_files
    up_or_down = up_or_down.get()
    if up_or_down == 'upload':
        root.destroy()
        root = tkinter.Tk()
        up_files_path = StringVar()
        down_dir = StringVar()
        linux_port = StringVar()
        linux_port.set('12000')
        Label(root, text="upload_files:").grid(row=0, column=0)
        Entry(root, textvariable=up_files_path).grid(row=0, column=1)
        Button(root, text="choose files", command=selectFiles).grid(row=0, column=2)
        Label(root, text="linux_port:").grid(row=1, column=0)
        Entry(root, textvariable=linux_port).grid(row=1, column=1)
        Button(root, text="let us go", command=be_sure).grid(row=3, column=2)
        root.mainloop()
    else:
        root.destroy()
        root = tkinter.Tk()
        up_files_path = StringVar()
        down_dir = StringVar()
        linux_port = StringVar()
        linux_port.set('12000')
        Label(root, text="down to where:").grid(row=0, column=0)
        Entry(root, textvariable=down_dir).grid(row=0, column=1)
        Button(root, text="choose a dir", command=selectPath).grid(row=0, column=2)
        Label(root, text="linux_port:").grid(row=1, column=0)
        Entry(root, textvariable=linux_port).grid(row=1, column=1)
        Button(root, text="let us go", command=be_sure).grid(row=3, column=2)
        root.mainloop()


comboxlist = ttk.Combobox(root, textvariable=up_or_down)
comboxlist['value'] = ['upload', 'download']
comboxlist.current(0)
comboxlist.grid(row=0, column=0)
comboxlist.bind("<<ComboboxSelected>>", selected)


root.mainloop()




# 可能是由于windows系统为虚拟机的原因，linux直接往windows传信号根本传不过去，只能先用windows连linux一下，linux借此搞到windows的具体地址，已方便之后的通信
# linux_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
linux_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # 尝试用udp连接过，虽然udp简单方便，但是传的文件有丢包现象
linux_socket.bind(('', linux_port))
linux_socket.listen(5)
print('linux服务器的TCP套接字已经启动，准备接收windows的请求信号')
linux_socket, wind_address = linux_socket.accept()
first_message, _ = linux_socket.recvfrom(2048) # 接收信号，确立通信
# print(wind_address)
# print(first_message)
print("接收到%s的信号%s,已经建立通信" % (str(wind_address[0]), first_message))


# 这个在linux系统上运行的脚本功能不多，就是上传和下载

def file_read(file):
    if not os.path.exists(file):
        exit('%s not exist' % file)
    with open(file, 'rb') as fr:
        for line in fr:
            yield line


def get_file_size(file):
    # size = 0
    # if not os.path.exists(file):
    #     exit('%s not exist' % file)
    # with open(file, 'rb') as fr:
    #     for line in fr:
    #         # size += sys.getsizeof(line)
    #         size += len(line)
    with open(file, 'rb') as fr:
        fr.seek(0, os.SEEK_END)
        size = fr.tell()
    return size

def upload_one_file(file):
    if not os.path.exists(file):
        print('can not find %s' % file)
        return
    global wind_address
    linux_socket.sendto(os.path.basename(file).encode(), wind_address)
    time.sleep(2)
    back_message, _ = linux_socket.recvfrom(2048)
    time.sleep(3)
    if back_message.decode() == 'may transfromed':
        file_size = get_file_size(file)
        linux_socket.sendto(str(file_size).encode(), wind_address)
        back_message, _ = linux_socket.recvfrom(2048)
        if back_message.decode() == 'transfromed':
            return
    if back_message.decode() == 'ok':
        file_size = get_file_size(file)
        linux_socket.sendto(str(file_size).encode(), wind_address)
        print('start transform %s' % file)
        for info in file_read(file):
            linux_socket.sendto(info, wind_address)
        # linux_socket.sendto('}}'.encode('utf-8'), wind_address)
        time.sleep(3)
        print('transform %s over' % file)


def download_one_file(file):
    print('start receive %s' % file)
    file = os.path.join(down_dir, file)
    if os.path.exists(file):
        linux_socket.sendto('may transfromed'.encode(), wind_address)
        file_size, _ = linux_socket.recvfrom(2048)
        file_size = int(file_size.decode())
        check_file_size = get_file_size(file)
        if check_file_size == file_size:
            linux_socket.sendto('transfromed'.encode(), wind_address)
            return
    fw = open(file, 'wb')
    linux_socket.sendto('ok'.encode(), wind_address)
    file_size, _ = linux_socket.recvfrom(2048)
    file_size = int(file_size.decode())
    tmp_size = 0
    while True:
        info, _ = linux_socket.recvfrom(2048)
        fw.write(info)
        # tmp_size += sys.getsizeof(info)
        tmp_size += len(info)
        if tmp_size >= file_size:
            print('%s received' % file)
            break


print("开始传输文件")
if up_or_down == 'upload':
    print('本次服务器为上传文件')
    for file in up_files:
        upload_one_file(file)
    linux_socket.sendto('all files transformed'.encode(), wind_address)

    print("所有文件上传完成，感谢使用")
else:
    print('本次服务器为接收文件')
    while True:
        info, _ = linux_socket.recvfrom(2048)
        info = info.decode()
        if info == 'all files transformed':
            print("所有文件已经接收，感谢使用")
            linux_socket.close()
            break
        download_one_file(info)

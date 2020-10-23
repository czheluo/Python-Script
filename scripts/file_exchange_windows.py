#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@time    : 2020/3/10 9:33
@file    : TIC_windows.py
@author  : yitong.feng
@contact: yitong.feng@majorbio.com
"""

# 本脚本致力于从linux服务器（192.169.10.58）上接收文件，用msconvert处理后再传回服务器，蛋疼的地方在于边跑边下载和边跑边上传

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


# 开始准备跟linux通信并暴露自己的信息，以便建立连接
# linux_name = '192.168.10.58'
linux_name ="10.100.203.40"
# wind_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
wind_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
wind_socket.connect((linux_name, linux_port))
wind_socket.sendto('hi linux'.encode('utf-8'), (linux_name, linux_port))
time.sleep(2)
wind_socket.sendto('tttttttttttttask_id'.encode('utf-8'), (linux_name, linux_port))
time.sleep(2)

# 跟linux一样，也要建立一些上传下载的函数
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
    wind_socket.sendto(os.path.basename(file).encode(), (linux_name, linux_port))
    time.sleep(1)
    back_message, _ = wind_socket.recvfrom(2048)
    time.sleep(1)
    if back_message.decode() == 'may transfromed':
        file_size = get_file_size(file)
        wind_socket.sendto(str(file_size).encode(), (linux_name, linux_port))
        back_message, _ = wind_socket.recvfrom(2048)
        if back_message.decode() == 'transfromed':
            return
    if back_message.decode() == 'ok':
        print('start transform %s' % file)
        file_size = get_file_size(file)
        wind_socket.sendto(str(file_size).encode(), (linux_name, linux_port))
        for info in file_read(file):
            wind_socket.sendto(info, (linux_name, linux_port))
        # wind_socket.sendto('}}'.encode('utf-8'), (linux_name, linux_port))
        time.sleep(3)
        print('transform %s over' % file)


def download_one_file(file):
    print('start receive %s' % file)
    file = os.path.join(down_dir, file)
    if os.path.exists(file):
        wind_socket.sendto('may transfromed'.encode(), (linux_name, linux_port))
        file_size, _ = wind_socket.recvfrom(2048)
        file_size = int(file_size.decode())
        check_file_size = get_file_size(file)
        if check_file_size == file_size:
            wind_socket.sendto('transfromed'.encode(), (linux_name, linux_port))
            return
    fw = open(file, 'bw')
    wind_socket.sendto('ok'.encode(), (linux_name, linux_port))
    file_size, _ = wind_socket.recvfrom(2048)
    file_size = int(file_size.decode())
    tmp_size = 0
    while True:
        info, _ = wind_socket.recvfrom(2048)
        fw.write(info)
        # tmp_size += sys.getsizeof(info)
        tmp_size += len(info)
        if tmp_size >= file_size:
            print('%s received' % file)
            break


print("开始传输文件")

if up_or_down == 'download':
    print('本次本机为接收文件')
    while True:
        info, _ = wind_socket.recvfrom(2048)
        info = info.decode()
        if info == 'all files transformed':
            print("所有文件下载完成，感谢使用")
            break
        download_one_file(info)
else:
    print('本次本机为上传文件')
    for file in up_files:
        upload_one_file(file)
    wind_socket.sendto('all files transformed'.encode(), (linux_name, linux_port))
    print("所有文件上传完成，感谢使用")

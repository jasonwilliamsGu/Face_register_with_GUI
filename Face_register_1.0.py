# Copyright (C) 2018-2021
# SPDX-License-Identifier: SCAU
# -*- coding:utf-8 -*-
# !/usr/bin/env python
# coding:utf8
# encoding=gbk
# 开发者：古卓恒   日期：2021/7/14

# 进行人脸录入 / Face register

from tkinter import *
from tkinter import messagebox
from PIL import Image, ImageTk
import numpy as np
import cv2
import os
import time
import logging
import dlib
import shutil
import subprocess

"""需要安装tkinter，dlib，shutil等库"""

# Dlib 正向人脸检测器 / Use frontal face detector of Dlib
detector = dlib.get_frontal_face_detector()


class FaceID:

    def __init__(self, master=None, name="0", num="0", sex="0", app=None):
        # 定义一个根窗口
        self.master = master
        self.root = Tk()
        self.root.title("信息录入系统")
        self.root.geometry("980x600+200+50")  # 定义窗口大小和位置
        # 调用摄像头
        self.camera = None
        # 设计文件名
        self.name = name
        self.num = num
        self.sex = sex
        self.app = app

        self.time_now = time.strftime("%Y%m%d", time.localtime())
        self.path_photos_from_camera = "data/data_faces_from_camera/"  # 文件名
        self.font = cv2.FONT_ITALIC
        self.existing_faces_cnt = self.num  # 已录入的人脸计数器(以编号命名) / cnt for counting saved faces
        self.ss_cnt = 0  # 录入 personX(编号) 人脸时图片计数器 / cnt for screen shots
        self.current_frame_faces_cnt = 0  # 录入人脸计数器 / cnt for counting faces in current frame

        self.save_flag = 1  # 之后用来控制是否保存图像的 flag / The flag to control if save
        self.press_n_flag = 0  # 之后用来检查是否先按 'n' 再按 's' / The flag to check if press 'n' before 's'

        # FPS
        self.frame_time = 0
        self.frame_start_time = 0
        self.fps = 0

        # 总布局画面
        self.createWeight()  # 设置一个上面的菜单（帮助）
        self.createWeidget_Right()
        self.createWeidget_Left()  # 设计左侧摄影画面

        mainloop()

    def createWeight(self):
        """大体思路就是:我们先新建一个菜单，然后向菜单项中 添加各种功能，
        最后我们监听鼠标右键消息，如果是鼠标 右键被单击，
        此时可以根据需要判断下鼠标位置来确定是 哪个弹出菜单被弹出，
        然后使用 Menu 类的 pop 方法来弹出 菜单。"""
        # https://www.cnblogs.com/jerryspace/p/9836689.html
        menubar = Menu(self.root)  # 创建主菜单栏
        menuhelp = Menu(menubar)  # 创建子菜单
        install = Menu(menubar)
        for item in ['更改文件存储路径']:
            install.add_command(label=item, command=self.change)
        for item in ['关于']:
            menuhelp.add_command(label=item)
        amenu = Menu(menubar)
        amenu.add_command(label='版权信息', command=self.openfile1)
        amenu.add_command(label='其他说明', command=self.openfile2)
        menubar.add_cascade(label="设置(I)", menu=install)
        menubar.add_cascade(label="帮助(H)", menu=menuhelp)
        # menuhelp.add_command(label='使用帮助', command=self.openfilehelp)  # , command=self.openfilehelp
        menubar.add_cascade(label="关于(A)", menu=amenu)
        self.root["menu"] = menubar  # 将主菜单栏添加到根窗口

    def createWeidget_Left(self):
        """信息录入界面组件"""
        print("%s %s %s" % (self.name, self.num, self.sex))
        self.label01 = Label(self.root, text="人脸识别个人信息采集系统", font=('粗体', 20))
        self.label01.grid(row=0, column=0, sticky=N + S, padx=5, pady=5)
        """此时，需接入摄像头接口，并pack（）"""
        self.canvas = Canvas(self.root, width=640, height=480, bg='white')
        self.canvas.grid(row=1, column=0, sticky=S, rowspan=12)

        self.cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
        self.button01 = Button(self.root, text="开始采集(N)")  # 开始录像
        self.button01.grid(row=13, column=0, sticky=SW, ipadx=50, ipady=5)

        self.button02 = Button(self.root, text="拍照(S)")  # """抓拍，并保存"""
        self.button02.grid(row=13, sticky=SE, ipadx=50, ipady=5)
        self.startsee(self.cap)
        rect = self.canvas.create_rectangle(50, 50, 100, 100)

    def change(self):
        # 更改文件存储路径
        pass

    def openfile1(self):
        # '版权信息'
        file1 = Tk()
        file1.title("版权信息")
        file1.geometry("400x100+220+100")  # 定义窗口大小和位置 x * y、
        label01 = Label(file1, text="开发者(排名不分先后)：古卓恒  连佩仪  谢函", font=('微软雅黑', 10))
        label01.grid(row=0, column=0, sticky=N + S, padx=5, pady=5)
        file1.mainloop()

    def openfile2(self):
        # '其他说明'
        file2 = Tk()
        file2.title("其他说明")
        file2.geometry("400x100+220+100")  # 定义窗口大小和位置
        label01 = Label(file2, text="文件存储路径" + str(self.path_photos_from_camera),
                        font=('微软雅黑', 10))
        label01.grid(row=0, column=0, sticky=N + S, padx=5, pady=5)
        file2.mainloop()

    # def openfilehelp(self):

        # try:
        #     helproot = Tk()
        #     helproot.title("使用帮助")
        #     helproot.geometry("880x600+220+70")  # 定义窗口大小和位置
        #     if os.path.exists("introduction.txt"):
        #         path_features_known_txt = "introduction.txt"
        #         with open(path_features_known_txt, "r",encoding = 'utf-8') as f:  # 打开文件
        #             """strip函数原型
        #
        #             声明：s为字符串，rm为要删除的字符序列. 只能删除开头或是结尾的字符或是字符串。不能删除中间的字符或是字符串。
        #
        #             s.strip(rm)        删除s字符串中开头、结尾处，位于 rm删除序列的字符
        #
        #             s.lstrip(rm)       删除s字符串中开头处，位于 rm删除序列的字符
        #
        #             s.rstrip(rm)      删除s字符串中结尾处，位于 rm删除序列的字符"""
        #
        #             line = f.readline()
        #             while line:
        #                 a=line.rstrip()
        #                 i=0
        #                 helproot.Label(text =a, font = ('微软雅黑', 12)).grid(column=2, row=i, sticky=W)
        #                 i+=1
        #                 line = f.readline()
        #             f.close()
        #             helproot.mainloop()
        # except PyEval_RestoreThread:
        #     pass
        # try:
        #     pathtxt=os.path.abspath('introduction.txt')
        #     os.system(r'notepad '+pathtxt)
        # except pymysql.err.ProgrammingError:
        #     pass

    # fil3 = Tk()
    # file2.title("使用帮助")
    # file2.geometry("400x100+220+100")  # 定义窗口大小和位置
    # label01 = Label(file2, text="文件存储路径" + str(self.path_photos_from_camera),
    #                 font=('微软雅黑', 10))
    # label01.grid(row=0, column=0, sticky=N + S, padx=5, pady=5)

    # 新建保存人脸图像文件和数据 CSV 文件夹 / Mkdir for saving photos and csv
    def pre_work_mkdir(self):
        # 新建文件夹 / Create folders to save faces images and csv
        if os.path.isdir(self.path_photos_from_camera):
            pass
        else:
            os.mkdir(self.path_photos_from_camera)

    # 删除之前存的人脸数据文件夹 / Delete old face folders
    def pre_work_del_old_face_folders(self):
        # 删除之前存的人脸数据文件夹, 删除 "/data_faces_from_camera/person_x/"...
        folders_rd = os.listdir(self.path_photos_from_camera)
        for i in range(len(folders_rd)):
            shutil.rmtree(self.path_photos_from_camera + folders_rd[i])
        if os.path.isfile("data/features_all.csv"):
            os.remove("data/features_all.csv")

    # 获取处理之后 stream 的帧数 / Update FPS of video stream
    def update_fps(self):
        now = time.time()
        self.frame_time = now - self.frame_start_time
        self.fps = 1.0 / self.frame_time
        self.frame_start_time = now

    # 抓拍逻辑
    def startsee(self, stream):
        # 1. 新建储存人脸图像文件目录 / Create folders to save photos
        self.pre_work_mkdir()

        # # 3. 检查 "/data/data_faces_from_camera" 中已有人脸文件
        # self.check_existing_faces_cnt()

        while stream.isOpened():
            ref, frame = stream.read()
            img_rd = cv2.flip(frame, 1)  # 摄像头翻转
            kk = cv2.waitKey(1)
            faces = detector(img_rd, 0)  # Use Dlib face detector

            # 4. 按下 'n' 新建存储人脸的文件夹 / Press 'n' to create the folders for saving faces
            if (kk == ord('n')) | int(self.button01['state'] == ACTIVE):
                if self.num == self.existing_faces_cnt:
                    logging.warning("该人脸文件夹已存在，请录入新的信息！！")
                    messagebox.showwarning(title='error', message='该人脸文件夹已存在，请录入新的信息！')
                else:
                    self.existing_faces_cnt = self.num
                    current_face_dir = self.path_photos_from_camera + str(self.existing_faces_cnt)
                    os.makedirs(current_face_dir)
                    logging.info("\n%-40s %s", "新建的人脸文件夹 / Create folders:", current_face_dir)
                    messagebox.showinfo(title='Create folders success', message='新建的人脸文件夹' + str(self.num) + '成功！')

                    self.ss_cnt = 0  # 将人脸计数器清零 / Clear the cnt of screen shots
                    self.press_n_flag = 1  # 已经按下 'n' / Pressed 'n' already

            # 5. 检测到人脸 / Face detected
            if len(faces) != 0:
                # 矩形框 / Show the ROI of faces
                for k, d in enumerate(faces):
                    # 计算矩形框大小 / Compute the size of rectangle box
                    height = (d.bottom() - d.top())
                    width = (d.right() - d.left())
                    hh = int(height / 2)
                    ww = int(width / 2)

                    # 6. 判断人脸矩形框是否超出 480x640 / If the size of ROI > 480x640
                    if (d.right() + ww) > 640 or (d.bottom() + hh > 480) or (d.left() - ww < 0) or (d.top() - hh < 0):
                        cv2.putText(img_rd, "OUT OF RANGE", (20, 300), self.font, 0.8, (0, 0, 255), 1, cv2.LINE_AA)
                        color_rectangle = (0, 0, 255)
                        save_flag = 0
                        if (kk == ord('s')) | int(self.button02['state'] == ACTIVE):
                            logging.warning("请调整位置 / Please adjust your position")
                            messagebox.showwarning(title='error', message='请调整位置 / Please adjust your position')
                    else:
                        color_rectangle = (255, 255, 255)
                        save_flag = 1

                    cv2.rectangle(img_rd,
                                  tuple([d.left() - ww, d.top() - hh]),
                                  tuple([d.right() + ww, d.bottom() + hh]),
                                  color_rectangle, 2)

                    # 7. 根据人脸大小生成空的图像 / Create blank image according to the size of face detected
                    img_blank = np.zeros((int(height * 2), width * 2, 3), np.uint8)

                    # self.active.config(state=ACTIVE)
                    if save_flag:
                        # 8. 按下 's' 保存摄像头中的人脸到本地 / Press 's' to save faces into local images
                        if (kk == ord('s')) | int(self.button02['state'] == ACTIVE):  #
                            # 检查有没有先按'n'新建文件夹 / Check if you have pressed 'n'
                            if self.press_n_flag:
                                self.ss_cnt += 1
                                for ii in range(height * 2):
                                    for jj in range(width * 2):
                                        img_blank[ii][jj] = img_rd[d.top() - hh + ii][d.left() - ww + jj]
                                cv2.imwrite(current_face_dir + "/img_face_" + str(self.ss_cnt) + ".jpg", img_blank)
                                logging.info("%-40s %s/img_face_%s.jpg", "写入本地 / Save into：", str(current_face_dir),
                                             str(self.ss_cnt))
                                messagebox.showinfo(title='success',
                                                    message=(str(self.name) + '的照片' + str(self.ss_cnt) + "写入本地成功！"))
                            else:
                                logging.warning("请先点击开始采集(N)来建文件夹, 按 'S' / Please press 'N' and press 'S'")
                                messagebox.showwarning(title='error', message="请先点击开始采集(N)来建文件夹")

                self.current_frame_faces_cnt = len(faces)

            cvimage = cv2.cvtColor(img_rd, cv2.COLOR_BGR2RGBA)
            pilImage = Image.fromarray(cvimage)
            pilImage = pilImage.resize((640, 480), Image.ANTIALIAS)
            tkImage = ImageTk.PhotoImage(image=pilImage)
            self.img = tkImage
            self.canvas.create_image(0, 0, anchor='nw', image=self.img)
            self.canvas.grid()
            self.root.update()
            self.root.after(100)

            # cv2.namedWindow("camera", 1)
            # cv2.imshow("camera", img_rd)
        stream.release()

    def createWeidget_Right(self):
        """测试单元格
        grid_win =self.root
        for row in range(20):
            for col in range(20):
                text_ = "row=%d,col=%d" % (row, col)
                Button(grid_win, text=text_).grid(row=row, column=col)
            """
        self.label03 = Label(self.root, text="请输入姓名：")
        self.label03.grid(row=5, column=1, padx=5, pady=5, sticky=W)  # ？
        # StringVar变量绑定到指定组件
        # StringVar变量的值发生变化，组件内容也变化，反之亦然。
        v1 = StringVar()
        self.entry01 = Entry(self.root, textvariable=v1)
        self.entry01.grid(row=5, column=2)

        self.label02 = Label(self.root, text="请输入编号：")
        self.label02.grid(row=6, column=1, padx=5, pady=5, sticky=W)  #
        v2 = StringVar()
        self.entry02 = Entry(self.root, textvariable=v2)
        self.entry02.grid(row=6, column=2)
        # self.root.bind("<Enter>", v2)

        self.label04 = Label(self.root, text="请输入性别：")
        self.label04.grid(row=7, column=1, padx=5, pady=5, sticky=W)  #
        v3 = StringVar()
        self.entry03 = Entry(self.root, textvariable=v3)
        self.entry03.grid(row=7, column=2)

        self.button03 = Button(self.root, text="录入", font=('微软雅黑', 12), command=self.login)
        self.button03.grid(row=8, column=2, sticky=EW, rowspan=2)  # columnspan:跨行，横向占两格，rowspan：跨列，纵向占x格

        self.button04 = Button(self.root, text="实时人脸识别", font=('微软雅黑', 12), command=self.linkothers)
        self.button04.grid(row=10, column=2, sticky=EW)
        # self.button04 = Button(self.root,text="查询个人信息",font=('微软雅黑', 12),command=self.search)
        # self.button04.grid(row=10, column=2, sticky=EW)

    def login(self):
        one = self.entry01.get()
        two = self.entry02.get()
        three = self.entry03.get()
        if not one or not two or not three:
            messagebox.showwarning(title='error', message='信息未填写完整！')

        else:
            try:
                print("姓名：" + self.entry01.get())
                print("编号：" + self.entry02.get())
                print("性别：" + self.entry03.get())
            except pymysql.err.ProgrammingError:
                messagebox.showwarning(title='error', message='带有特殊字符！')

            datafile = open(r'data.txt', 'a')
            datafile.write(self.entry01.get() + '\r')
            datafile.write(self.entry02.get() + '\r')
            datafile.write(self.entry03.get() + '\r')
            datafile.close()

            self.name = self.entry01.get()
            self.num = self.entry02.get()
            self.sex = self.entry03.get()

            messagebox.showinfo(title='success', message='信息录入成功！')

            self.entry01.delete(0, 'end')
            self.entry02.delete(0, 'end')
            self.entry03.delete(0, 'end')

    def linkothers(self):
        messagebox.showinfo(title='请等待', message='按确认后界面将关闭，稍作等待后人脸识别界面将弹出！')
        self.root.destroy()
        self.cap.release()
        os.system("python features_extraction_to_csv.py")
        os.system("python face_reco_from_camera.py")

    def search(self):
        pass


if __name__ == '__main__':
    App = FaceID()

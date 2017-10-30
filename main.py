#-------------------------------------------------------------------------------
# Name:        Three Point Rectangle
# Purpose:     Label boxes and metadata
# Author:      YuHsuan Yen
# Created:     2016/12/30
# Demo Video: https://youtu.be/dZGoISfAJmI
#-------------------------------------------------------------------------------
from __future__ import print_function
from __future__ import division
import sys

if sys.version_info[:2] < (3, 0):
    # for Python2
    from Tkinter import *   ## notice capitalized T in Tkinter
    import tkSimpleDialog as simpledialog
else: 
    # for Python3
    from tkinter import *   ## notice lowercase 't' in tkinter here
    import tkinter.simpledialog as simpledialog

from PIL import Image, ImageTk
import os
import glob
import random
import math as m
import cmath as cm
import numpy as np
# colors for the bboxes
COLORS = ['red', 'blue', 'gold', 'pink', 'cyan', 'green', 'black','orange','maroon','seashell3','plum1','dark green','tomato','blanched almond']
# image sizes for the examples
SIZE = 480, 640

class LabelTool():
    def __init__(self, master):
        # set up the main frame
        self.parent = master
        self.parent.title("Domino Label Tool")
        self.frame = Frame(self.parent)
        self.frame.pack(fill=BOTH, expand=1)
        self.parent.resizable(width = FALSE, height = FALSE)

        # initialize global state
        self.imageDir = ''
        self.imageList= []
        self.egDir = ''
        self.egList = []
        self.outDir = ''
        self.cur = 0
        self.total = 0
        self.category = 0
        self.imagename = ''
        self.labelfilename = ''
        self.tkimg = None

        # initialize mouse state
        self.STATE = {}
        self.STATE['click'] = 0
        self.STATE['p1'] = [0, 0]
        self.STATE['p2'] = [0, 0]
        self.STATE['p3'] = [0, 0]
        self.STATE['p4'] = [0, 0]
        self.STATE['angle'] = 0
        # reference to bbox
        self.bboxIdList = []
        self.bboxId = None
        self.bboxList = []
        self.hl = None
        self.vl = None
        # scale image size down
        self.invscale = 2

        # ----------------- GUI stuff ---------------------
        # dir entry & load
        #self.label = Label(self.frame, text = "Image Dir:")
        #self.label.grid(row = 0, column = 0, sticky = E)
        #self.entry = Entry(self.frame)
        #self.entry.grid(row = 0, column = 1, sticky = W+E)
        #self.entry.delete(0, END)
        #self.entry.insert(0, "Image Dir:")
        self.ldBtn = Button(self.frame, text = "Load", command = self.loadDir)
        self.ldBtn.grid(row = 0, column = 2, sticky = W+E)

        # main panel for labeling
        self.mainPanel = Canvas(self.frame, cursor='tcross')
        self.mainPanel.bind("<Button-1>", self.mouseClick)
        self.mainPanel.bind("<Motion>", self.mouseMove) 
        self.parent.bind("<Escape>", self.cancelBBox)   # press <Espace> to cancel current bbox
        self.parent.bind("<Delete>", self.delBBox)      # press <Delete> to cancel the selection
        self.parent.bind("<Prior>", self.prevImage)        # press <up> to go backforward
        self.parent.bind("<Next>", self.nextImage)      # press <down> to go forward
        # self.parent.bind("<Home>",self.loadDir)        # press <Enter> to load dir
        self.mainPanel.grid(row = 1, column = 1, rowspan = 4, sticky = W+N)

        # showing bbox info & delete bbox
        self.help = Label(self.frame, wraplength = 200, justify=LEFT, text = '\
- Press the load button to start.\n\
- Then for each Domino click on three of its corners.\n\
- A dialog box will appear after third point.\n\
- In this box enter the two numbers associated with the domino, no dots mean 0.\n\
- Example input for this box would look like "1,3" without quotes.\n\
- To remove a bad box, click on the associated line below and then click delete to delete that box and try again \n\
- Press Next to save labels to "Labels" folder and load next image')
        self.help.grid(row = 1, column = 2,  sticky = W+N)
        self.listbox = Listbox(self.frame, width = 28, height = 12)
        self.listbox.grid(row = 2, column = 2, sticky = N)
        self.btnDel = Button(self.frame, text = 'Delete', command = self.delBBox)
        self.btnDel.grid(row = 3, column = 2, sticky = W+E+N)
        self.btnClear = Button(self.frame, text = 'ClearAll', command = self.clearBBox)
        self.btnClear.grid(row = 4, column = 2, sticky = W+E+N)


        # control panel for image navigation
        self.ctrPanel = Frame(self.frame)
        self.ctrPanel.grid(row = 5, column = 1, columnspan = 2, sticky = W+E)
        self.prevBtn = Button(self.ctrPanel, text='<< Prev', width = 10, command = self.prevImage)
        self.prevBtn.pack(side = LEFT, padx = 5, pady = 3)
        self.nextBtn = Button(self.ctrPanel, text='Next >>', width = 10, command = self.nextImage)
        self.nextBtn.pack(side = LEFT, padx = 5, pady = 3)
        self.progLabel = Label(self.ctrPanel, text = "Progress:     /    ")
        self.progLabel.pack(side = LEFT, padx = 5)
        self.tmpLabel = Label(self.ctrPanel, text = "Go to Image No.")
        self.tmpLabel.pack(side = LEFT, padx = 5)
        self.idxEntry = Entry(self.ctrPanel, width = 5)
        self.idxEntry.pack(side = LEFT)
        self.goBtn = Button(self.ctrPanel, text = 'Go', command = self.gotoImage)
        self.goBtn.pack(side = LEFT)

        # example pannel for illustration
        self.egPanel = Frame(self.frame, border = 10)
        self.egPanel.grid(row = 1, column = 0, rowspan = 5, sticky = N)
        self.tmpLabel2 = Label(self.egPanel, text = "")
        self.tmpLabel2.pack(side = TOP, pady = 5)
        self.egLabels = []
        for i in range(3):
            self.egLabels.append(Label(self.egPanel))
            self.egLabels[-1].pack(side = TOP)

        # display mouse position
        self.disp = Label(self.ctrPanel, text='')
        self.disp.pack(side = RIGHT)

        self.frame.columnconfigure(1, weight = 1)
        self.frame.rowconfigure(4, weight = 1)

    def vsub(self,a,b):
        return (a[0]-b[0],a[1]-b[1])

    def vdot(self,a,b):
        return a[0]*b[0]+a[1]*b[1]

    def loadDir(self, dbg = False):
        # if not dbg:
        #     s = self.entry.get()
        #     self.parent.focus()
        #     self.category = str(s)
        # else:
        #     s = r'D:\workspace\python\labelGUI'

        # get image list
        self.imageDir = os.path.join(r'./Images','')
        self.imageList = glob.glob(os.path.join(self.imageDir, '*.jpg'))
        if len(self.imageList) == 0:
            print ('No .jpg images found in the specified dir!')
            return
        # default to the 1st image in the collection
        self.cur = 1
        self.total = len(self.imageList)

         # set up output dir
        self.outDir = os.path.join(r'./Labels', '')
        if not os.path.exists(self.outDir):
            os.mkdir(self.outDir)
        self.loadImage()
        print('%d images loaded from %s' %(self.total, self.imageDir))
    
    def loadImage(self):
        # load image
        imagepath = self.imageList[self.cur - 1]
        self.img = Image.open(imagepath)
        #print(self.img.size)
        self.img =self.img.resize((int(self.img.size[0]/self.invscale), int(self.img.size[1]/self.invscale)), Image.ANTIALIAS)
        #print(self.img.size)
        self.tkimg = ImageTk.PhotoImage(self.img)
        self.mainPanel.config(width = max(self.tkimg.width(), 400), height = max(self.tkimg.height(), 400))
        self.mainPanel.create_image(0, 0, image = self.tkimg, anchor=NW)
        self.progLabel.config(text = "%04d/%04d" %(self.cur, self.total))

        # load labels
        self.clearBBox()
        self.imagename = os.path.split(imagepath)[-1].split('.')[0]
        labelname = self.imagename + '.txt'
        self.labelfilename = os.path.join(self.outDir, labelname)
        bbox_cnt = 0
        if os.path.exists(self.labelfilename):
            with open(self.labelfilename) as f:
                for (i, line) in enumerate(f):
                    if i == 0:
                        bbox_cnt = int(line.strip())
                        print ("Loaded", bbox_cnt)
                        continue
                    tmp = [t.strip() for t in line.split()]
                    #print (tmp)
                    P = [float(tmp[0])/self.invscale, float(tmp[1])/self.invscale,\
                         float(tmp[2])/self.invscale, float(tmp[3])/self.invscale,\
                         float(tmp[4])/self.invscale, float(tmp[5])/self.invscale,\
                         float(tmp[6])/self.invscale, float(tmp[7])/self.invscale]
                    #print(P)
                    self.bboxList.append([
                        int(tmp[0]), int(tmp[1]),
                        int(tmp[2]), int(tmp[3]),
                        int(tmp[4]), int(tmp[5]),
                        int(tmp[6]), int(tmp[7]),
                        float(tmp[8]), tmp[9]])
                    
                    tmpId = self.mainPanel.create_polygon(P, \
                                                            width = 2, \
                                                            outline = COLORS[(len(self.bboxList)-1) % len(COLORS)],\
                                                            fill='')
                    self.bboxIdList.append(tmpId)
                    self.listbox.insert(END, '[%s], deg:%.2f' %(tmp[9],float(tmp[8])))
                    self.listbox.itemconfig(len(self.bboxIdList) - 1, fg = COLORS[(len(self.bboxIdList) - 1) % len(COLORS)])

    def saveImage(self):
        with open(self.labelfilename, 'w') as f:
            f.write('%d\n' %len(self.bboxList))
            for bbox in self.bboxList:
                f.write(' '.join(map(str, bbox)) + '\n')
        print (self.cur)

    def mouseClick(self, event):
        print ("click state:{}".format(self.STATE['click']) )
        
        if self.STATE['click'] == 0:    
            self.STATE['p1']= [event.x, event.y]
        
        elif self.STATE['click']==1:
            self.STATE['p2']= [event.x, event.y]
        elif self.STATE['click']==2:
            #self.STATE['p3'] = [event.x, event.y]
            var = simpledialog.askstring("Domino Labels", "Enter Data")
            if var=="":
                var=NONE
            #self.popup_bonus()
            #self.frame.wait_window(self.popup)
            self.bboxList.append([
                int(self.STATE['p1'][0]* self.invscale), int(self.STATE['p1'][1]* self.invscale),
                int(self.STATE['p2'][0]* self.invscale), int(self.STATE['p2'][1]* self.invscale),
                int(self.STATE['p3'][0]* self.invscale), int(self.STATE['p3'][1]* self.invscale),
                int(self.STATE['p4'][0]* self.invscale), int(self.STATE['p4'][1]* self.invscale),
                self.STATE['angle'], var])
            self.bboxIdList.append(self.bboxId)
            self.bboxId = None
            self.listbox.insert(END, '[%s], deg:%.2f' %(var,self.STATE['angle']))
            self.listbox.itemconfig(len(self.bboxIdList) - 1, fg = COLORS[(len(self.bboxIdList) - 1) % len(COLORS)])
            

            self.STATE['click'] = -1
        
        self.STATE['click'] = 1 + self.STATE['click']
    def proj(self, start, angle, point):
        v = [100*np.cos(np.deg2rad(angle))+ start[0], 100*np.sin(np.deg2rad(angle))+ start[1]]

        p1 = self.vsub(v,start)
        p2 = self.vsub(point,start)
        dp = self.vdot(p1,p2)
        lp1 = np.sqrt(self.vdot(p1,p1))
        lp2 = np.sqrt(self.vdot(p2,p2))
        c = dp/(lp1*lp2)
        dpl = c * lp2
        return [start[0] + (dpl * p1[0])/ lp1, start[1] + (dpl * p1[1])/ lp1]

    def mouseMove(self, event):
        self.disp.config(text = 'x: %d, y: %d' %(event.x*self.invscale, event.y*self.invscale))
        if self.tkimg: #mouse tracking
            if self.hl:
                self.mainPanel.delete(self.hl)
            self.hl = self.mainPanel.create_line(0, event.y, self.tkimg.width(), event.y, width = 2)
            if self.vl:
                self.mainPanel.delete(self.vl)
            self.vl = self.mainPanel.create_line(event.x, 0, event.x, self.tkimg.height(), width = 2)
        
        if 1 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
            P = [self.STATE['p1'][0], self.STATE['p1'][1],event.x,event.y]
            self.STATE['angle'] = np.rad2deg(np.arctan2(P[3]-P[1], P[2] - P[0]))
            #print(self.STATE['angle'])
            self.bboxId = self.mainPanel.create_polygon(P, width = 2, outline = COLORS[len(self.bboxList) % len(COLORS)],fill='')
        if 2 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
            self.STATE['p3'] = self.proj(self.STATE['p2'],self.STATE['angle'] + 90,  [event.x,event.y])
            self.STATE['p4'] = self.proj(self.STATE['p1'],self.STATE['angle'] + 90,  [event.x,event.y])
            P = [self.STATE['p1'][0], self.STATE['p1'][1],\
                 self.STATE['p2'][0], self.STATE['p2'][1],\
                 self.STATE['p3'][0], self.STATE['p3'][1],\
                 self.STATE['p4'][0], self.STATE['p4'][1]]
            self.bboxId = self.mainPanel.create_polygon(P, width = 2, outline = COLORS[len(self.bboxList) % len(COLORS)],fill='')

    def cancelBBox(self, event):
        if 1 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
                self.bboxId = None
                self.STATE['click'] = -1

    def delBBox(self):
        sel = self.listbox.curselection()
        if len(sel) != 1 :
            return
        idx = int(sel[0])
        self.mainPanel.delete(self.bboxIdList[idx])
        self.bboxIdList.pop(idx)
        self.bboxList.pop(idx)
        self.listbox.delete(idx)
        self.STATE['click'] = 0

    def clearBBox(self):
        for idx in range(len(self.bboxIdList)):
            self.mainPanel.delete(self.bboxIdList[idx])
        self.listbox.delete(0, len(self.bboxList))
        self.bboxIdList = []
        self.bboxList = []
        self.STATE['click'] = 0

    def prevImage(self, event = None):
        self.saveImage()
        if self.cur > 1:
            self.cur -= 1
            self.loadImage()

    def nextImage(self, event = None):
        self.saveImage()
        if self.cur < self.total:
            self.cur += 1
            self.loadImage()

    def gotoImage(self):
        idx = int(self.idxEntry.get())
        if 1 <= idx and idx <= self.total:
            self.saveImage()
            self.cur = idx
            self.loadImage()

if __name__ == '__main__':
    root = Tk()
    tool = LabelTool(root)
    root.mainloop()

from .dependencies import *

class ImageCutter(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.__name__ = 'ImageCutter'
        self.controller = controller
        self.img_info = None

        # title
        label = tk.Label(self, text="Image Cutter", font=controller.title_font)
        label.pack(side="top", fill="x", pady=10)

        # recenter crosshairs
        rbx,rby = 200,340
        tk.Button(self,text="Recenter",command=self.recenter).place(x=rbx,y=rby)

        # choose cutter
        tk.Label(self,text='Choose cutter:').place(x=20,y=220)
        cbx,cby = 20,240
        tk.Button(self,text="Cross",command=lambda:self.set_cutter('cross')).place(x=cbx,y=cby)
        tk.Button(self,text="Up T",command=lambda:self.set_cutter('up_T')).place(x=cbx,y=cby+30)
        tk.Button(self,text="Down T",command=lambda:self.set_cutter('down_T')).place(x=cbx,y=cby+60)
        tk.Button(self,text="Horizontal",command=lambda:self.set_cutter('horizontal')).place(x=cbx,y=cby+90)
        tk.Button(self,text="Vertical",command=lambda:self.set_cutter('vertical')).place(x=cbx,y=cby+120)

        # exposure scale
        self.escale_label = None
        self.escale_apply = None
        self.escaler = None
        self.controller.init_escaler(self)

        # back, next
        nbbx,nbby = 135,400
        tk.Button(self, text="Back",command=self.back).place(x=nbbx,y=nbby)
        tk.Button(self,text="Cut Image",command=self.do_cut).place(x=nbbx+180,y=nbby)
        

        self.controller.init_img_info(self)
        self.controller.view_ax = 'z'
        self.controller.init_escaler(self)
        traceback.print_stack()
        print("stack size: {}".format(len(traceback.extract_stack())))
        gc.collect()
        self.init_ani()


    def recenter(self):
        self.controller.cx, self.controller.cy = self.controller.cx_def, self.controller.cy_def
        self.controller.show_frame(self.__name__)


    def back(self):
        self.controller.show_frame('ImageRotator')

    def init_ani(self):
        self.start_cutter()

    def start_cutter(self):
        self.controller.animated_cutter(view_ax=self.controller.view_ax)

    def change_ax(self,ax):
        self.controller.view_ax = ax
        self.start_cutter()

    def set_cutter(self,cutter):
        self.controller.cutter=cutter
        self.show_frame(self.__name__)

    def do_cut(self):
        self.controller.cut_image()
        self.controller.show_frame('CutViewer')
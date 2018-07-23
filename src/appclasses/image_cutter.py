from .dependencies import *

class ImageCutter(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.__name__ = 'ImageCutter'
        self.controller = controller
        self.img_info = None
        
        # title
        title = tk.Label(self, text="Image Cutter", font=controller.title_font, justify='center')


        # controls frame
        controls_frame = tk.Frame(self)

        # add next and back buttons
        nbframe = tk.Frame(controls_frame)
        nxt = tk.Button(nbframe,text='Next',command=self.next)
        back = tk.Button(nbframe,text='Back',command=self.back)
        nxt.pack(side=tk.RIGHT,padx=(100,30),pady=(30,30))
        back.pack(side=tk.LEFT,padx=(30,100),pady=(30,30))
        nbframe.grid(row=4,column=0,columnspan=4,pady=(40,0))
       
        # add cut to queued cuts
        cut_controls = tk.Frame(controls_frame)
        add_cut = tk.Button(cut_controls,text='Add cut',command=self.add_cut)
        add_cut.pack(side=tk.RIGHT,padx=(30,0))
        undo_click = tk.Button(cut_controls,text='Undo click',command=self.undo_click)
        undo_click.pack(side=tk.LEFT)
        cut_controls.grid(row=3,column=2)

        # rm cut frame
        ncuts = len(self.controller.image.cuts)
        rm_button_frame = None
        if ncuts:
            rm_button_frame = tk.Frame(controls_frame)
            for ix in range(ncuts):
                rmbutton = tk.Button(rm_button_frame,text='Remove cut {}'.format(ix+1),command=lambda ix=ix:self.remove_cut(ix))
                rmbutton.pack(side="top")
            rm_button_frame.grid(row=1,column=0,rowspan=ncuts,padx=(30,30))

        # img info
        img_info = controller.get_img_info(controls_frame)
        img_info.grid(row=0,column=0,pady=(0,50))

        # exposure scale
        self.escaler, self.escale_label, self.escale_apply = self.controller.init_escaler(controls_frame)
        ec,er = 3,0
        epx = (50,50)
        self.escale_label.grid(column=ec,row=er,padx=epx)
        self.escaler.grid(column=ec,row=er+1,padx=epx)
        self.escale_apply.grid(column=ec,row=er+2,padx=epx)

        # make figure
        self.make_figure()

        # grid to master frame
        title.pack(side="top", fill="x", pady=10,expand=False)
        controls_frame.pack(side="right",fill='y',expand=False,pady=30)#.grid(row=1,column=2,padx=100)
        self.figframe.pack(side="left",fill='both',expand=True,padx=(30,30),pady=30)#.grid(row=1,column=0,padx=10)

        

    def make_figure(self):
        # make figure in tkinter
        self.figframe = tk.Frame(self)
        self.figure = Figure()
        self.canvas = FigureCanvasTkAgg(self.figure, self.figframe)

        self.controller.static_cutter(figure=self.figure)

        self.controller.static_cutter_controls(canvas=self.canvas)
        self.canvas.show()
        self.canvas_widget = self.canvas.get_tk_widget()
        
        self.canvas_widget.pack(side="top",fill='both',expand=True) # self.canvas_widget.place(x=fx,y=fy)  # self.canvas_widget.pack(anchor=tk.W, side="left",padx=10) #

        tbframe = tk.Frame(self.figframe)
        toolbar = NavigationToolbar2TkAgg(self.canvas, tbframe)
        toolbar.update()
        self.canvas._tkcanvas.pack()  # toolbar # self.canvas._tkcanvas.place(x=fx,y=fy)
        tbframe.pack(side="top",expand=False)


    def reset(self):
        self.controller.show_frame(self.__name__)

    def back(self):
        self.controller.show_frame('ImageRotator')

    def add_cut(self):
        self.controller.add_cut()
        self.reset()

    def remove_cut(self,ix):
        self.controller.remove_cut(ix)
        self.reset()

    def undo_click(self):
        if self.controller.current_cut:
            self.controller.current_cut.pop(-1)
            self.reset()

    def next(self):
        if self.controller.image.cuts:
            self.controller.show_frame('HeaderUI')
        else:
            print('No cuts made yet')
        # self.controller.cut_image()
        # if self.controller.image.cuts:
        #     self.controller.show_frame('HeaderUI')

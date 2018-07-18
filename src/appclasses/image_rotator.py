from .dependencies import *

class ImageRotator(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.__name__ = 'ImageRotator'
        self.controller = controller
        self.img_info = None
        
        # title
        label = tk.Label(self, text="Image Rotator", font=controller.title_font)
        label.pack(side="top", fill="x", pady=10)
        
        # reminder to specify nmice
        self.nmice_msg = None

        # rotator instructions
        tk.Label(self, 
            text="\n".join([
                'Notes on rotation:',
                'x-axis: belly should be up, head to right',
                'y-axis: head should be up, heart on right']), 
            font=tkfont.Font(family='Helvetica', size=9),
            justify=tk.LEFT
            ).place(x=20,y=320)

        # next, back
        nbbx,nbby = 135,400
        tk.Button(self, text="Back",command=self.back).place(x=nbbx,y=nbby)
        tk.Button(self,text="Next",command=self.next_page).place(x=nbbx+180,y=nbby)
       
        # exposure scale
        self.escale_label = None
        self.escale_apply = None
        self.escaler = None
        self.controller.init_escaler(self)

 
        rotbx,rotby = 200,220
        tk.Button(self, text="Rotate on x axis", command=lambda : self.rotate_on_axis('x')).place(x=rotbx,y=rotby)
        tk.Button(self, text="Rotate on y axis", command=lambda : self.rotate_on_axis('y')).place(x=rotbx,y=rotby+30)
        tk.Button(self, text="Rotate on z axis", command=lambda : self.rotate_on_axis('z')).place(x=rotbx,y=rotby+60)
        
        # init some stuff
        self.controller.init_img_info(self)
        self.controller.init_escaler(self)
        self.escaler.place(self.controller.escaler_x)
        self.img_info.place()

        # make figure in tkinter
        fx,fy = 600,100
        self.figure = Figure(figsize=(5,5), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, self)

        self.controller.view_each_axis(figure=self.figure)

        self.controller.connect_controls(canvas=self.canvas)
        self.canvas.show()
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.place(x=fx,y=fy)

        toolbar = NavigationToolbar2TkAgg(self.canvas, self)
        toolbar.update()
        self.canvas._tkcanvas.place(x=fx,y=fy)


    def back(self):
        self.controller.show_frame('ImageSelector')

    def animate_axes(self):
        self.controller.animate_axes()

    def rotate_on_axis(self,ax):
        self.controller.image.rotate_on_axis(ax)
        self.animate_axes()

    def next_page(self):
        if self.controller.nmice is not None:
            if self.controller.nmice == 1:
                self.controller.view_ax = 'x'
                im = self.controller.image
                fpcs = im.filename.split('.')
                if not fpcs[0].endswith('_s1'):
                    fpcs[0]+='_s1'
                self.controller.image.filename = '.'.join(fpcs)
                self.controller.image.cuts = [self.controller.image] #[SubImage(parent_image=im,img_data=im.img_data,filename='.'.join(fpcs))]
                self.controller.show_frame('CutViewer')
            else:
                self.controller.show_frame('ImageCutter')
        else:
            self.nmice_warn()
            print('Specify number of mice before continuing.')

    def set_nmice(self):
        nmice = self.tknmice.get()
        if nmice is not None:
            self.controller.nmice = self.tknmice.get()


    def nmice_warn(self):
        if self.nmice_msg:
            self.nmice_msg.destroy()
        color = np.random.choice(["blue","red","green","purple","orange","maroon","cyan","indigo","yellow","violet","pink","turquoise"])
        self.nmice_msg = tk.Label(self, 
            text="Number of mice must be indicated before continuing.", 
            font=tkfont.Font(family='Helvetica', size=12, weight="bold"),
            fg=color)
        self.nmice_msg.pack(side="top",fill="x",pady=15)

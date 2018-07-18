from .dependencies import *

class ImageSelector(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)


        self.__name__ = 'ImageSelector'
        self.controller = controller
        self.controller.remove_temp_dirs()
        label = tk.Label(self, text="Select Image", font=controller.title_font)
        label.grid(row=0,column=1,columnspan=2,padx=(30,0),pady=(0,20))
        
        self.petcol = 1
        self.ctcol = 2

        # pad space
        tk.Label(self,text=' '*25).grid(column=0)

        # browse for file
        tk.Button(self, text='Browse', command=self.browse_file).grid(row=1,column=1,columnspan=1,padx=(30,0),pady=(0,20))
        tk.Button(self, text='Quit', command=lambda app=self.controller:exit_fn(app)).grid(row=1,column=2,columnspan=1,padx=(30,0),pady=(0,20))

        self.make_buttons()

        self.controller.remove_temp_dirs() # do this when we select new file
        self.controller.nmice=None
        for b in self.buttons:
            b.destroy()
        self.make_buttons()
        gc.collect()


    def make_buttons(self):
        img_pairs = self.controller.get_files()

        self.buttons = []
        for i,pair in enumerate(img_pairs):
            try:
                im1,im2 = pair
            except:
                im1,im2 = pair[0],None
            for im in [im1,im2]:
                if im is not None:
                    column = self.petcol if im.type == 'pet' else self.ctcol
                    b = tk.Button(self,
                        text=im.filename,
                        command = lambda im=im: self.controller.start_img(im))
                    b.grid(row=i+3,column=column)
                    self.buttons.append(b)


    def browse_file(self):

        p = os.path.join('C:\\Users\\jmusko01\\Desktop\\For Jack\\F220\\4bed\\dynamic\\flipped','mpet3691b_em1_v1.img')
        i = PETImage(p)
        self.controller.start_img(i)


        # Tk().withdraw()
        # fpath = askopenfilename()
        # if fpath:
        #     if fpath.endswith('.hdr'):
        #         fpath = '.'.join(fpath.split('.')[:-1])
        #     fname = ntpath.basename(fpath)
        #     if is_pet(fname):
        #         img = PETImage(fpath)
        #     else:
        #         img = CTImage(fpath)
        #     self.controller.start_img(img)
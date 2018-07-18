from .dependencies import *

class HeaderUI(tk.Frame):

    def __init__(self, parent, controller):

        self.__name__ = 'HeaderUI'
        
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.controller = controller
        self.img_info = None

        # local image editor for controlling animation of each cut
        self.ie = None
        self.cut = None
        self.title = None

        # pad space
        tk.Label(self,text=' '*30).grid(column=0)  

        # exposure scale
        self.escale_label = None
        self.escale_apply = None
        self.escaler = None

        self.additional_init()

        


    def additional_init(self):
        self.reset_attrs()
        self.cut_ix = 0 if self.controller.last_frame == 'CutViewer' else len(self.controller.image.cuts)-1
        
        # coords for placing entry boxes and labels
        self.er,self.ec = 1,1
        self.hdr_attrs = ['filename','animal_number','subject_weight']

        # input file info
        if self.controller.image.type == 'ct':
            pass
        elif self.controller.image.type == 'pet':
            self.hdr_attrs += ['dose','injection_time']
        else:
            raise ValueError('Unexpected image type: {}'.format(self.controller.image.type))


        try:
            self.destroy_buttons()
        except AttributeError:
            pass

        self.controller.init_img_info(self,coords=(30,self.controller.escaler_y))
        self.controller.init_escaler(self)

        er,ec = self.er,self.ec
        for i,attr in enumerate(self.hdr_attrs):
            setattr(self,attr,tk.StringVar(value=''))
            entry = tk.Entry(self,textvariable=getattr(self,attr),width=40)
            entry_attr = attr+'_entry'
            setattr(self,entry_attr,entry)
            getattr(self,entry_attr).grid(row=er+i,column=ec+1)
            label_attr = attr+'_label'
            setattr(self,label_attr,tk.Label(self,text=get_label(attr)))
            getattr(self,label_attr).grid(row=er+i,column=ec)

        # add title
        self.update_title()

        # back, next
        nbbx,nbby = 135,400
        self.back_button = tk.Button(self, text="Back",command=self.back)
        self.back_button.place(x=nbbx,y=nbby)
        self.next_button = tk.Button(self, text="Next",command=self.increment_cut)
        self.next_button.place(x=nbbx+180,y=nbby)

        self.cut = self.controller.image.cuts[0]
        self.init_cut()


    def update_title(self):
        if self.title is not None:
            self.title.destroy()
        self.title = tk.Label(self, text="Cut {} Header Information".format(self.cut_ix+1), font=self.controller.title_font, justify=tk.LEFT)
        self.title.grid(row=0,column=1,columnspan=2,padx=(0,0),pady=(10,20))



    def increment_cut(self):
        self.update_cut()
        self.cut_ix += 1
        if self.cut_ix < len(self.controller.image.cuts):
            self.update_title()
            self.cut = self.controller.image.cuts[self.cut_ix]
            self.init_cut()
        else:
            self.destroy_buttons()
            self.reset_attrs()
            self.controller.show_frame('ConfirmSave')


    def decrement_cut(self):
        self.cut_ix -= 1
        self.update_title()
        self.cut = self.controller.image.cuts[self.cut_ix]
        self.init_cut()


    def init_cut(self):
        self.init_entries()
        self.init_ani()

    def init_ani(self):
        self.ie = ImageEditor(self.cut, escale=self.controller.escale)
        self.ie.animate_axes()

    def init_entries(self):
        for attr in self.hdr_attrs:
            if (not attr=='filename'):
                _ = getattr(self.cut.params,attr)
                if _ is not None:
                    getattr(self,attr).set(_)
                else:
                    getattr(self,attr).set('')

        self.filename.set(self.cut.filename)

    def update_cut(self):
        for attr in self.hdr_attrs:
            entry_attr = attr+'_entry'
            entry = getattr(self,entry_attr)
            val = entry.get().strip()
            if attr=='filename':
                self.cut.filename = val
            else:
                setattr(self.cut.params, attr, val)

    def destroy_buttons(self):
        
        for attr in self.hdr_attrs:
            entry_attr = attr+'_entry'
            label_attr = attr+'_label'
            getattr(self,entry_attr).destroy()
            getattr(self,label_attr).destroy()
        self.next_button.destroy()
        self.back_button.destroy()

    def reset_attrs(self):
        self.ie = None
        self.cut = None
        gc.collect()


    def back(self):
        self.update_cut()
        if self.cut_ix > 0:
            self.decrement_cut()
        else:
            self.destroy_buttons()
            self.reset_attrs()
            self.controller.show_frame('CutViewer')
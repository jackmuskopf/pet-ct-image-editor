from .dependencies import *
from .smallscreens import YesNoPopup

class ConfirmSave(tk.Frame):

    def __init__(self, parent, controller):

        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.__name__ = 'ConfirmSave'
        self.additional_init()


    def additional_init(self):
        # pad space
        tk.Label(self,text=' '*30).grid(column=0)
        
        # title
        label = tk.Label(self, text="Confirm", font=self.controller.title_font)
        label.grid(row=0,column=0,columnspan=2,padx=(30,0),pady=(0,20))        

        params_to_display = ['animal_number','injection_time','dose','subject_weight','filename']
        for i,cut in enumerate(self.controller.image.cuts):
            for j,param in enumerate(params_to_display):
                jx=j+1
                if param == 'filename':
                    val = cut.filename
                else:
                    try:
                        val = getattr(cut.params,param)
                    except AttributeError:
                        val = None
                if val is not None:
                    r,c = jx+(i//2)*len(params_to_display),i%2
                    r = r+1 if i>1 else r
                    px = c*10+5
                    tk.Label(self,text='{0} : {1}'.format(get_label(param),val)).grid(row=r,column=c,padx=(px,0))
        
        # space
        tk.Label(self,text=' '*50).grid(row=6,column=0,columnspan=2)
        tk.Label(self,text=' '*50).grid(row=12,column=0,columnspan=2)

        brow = len(params_to_display)*2+3
        self.back_button = tk.Button(self, text="Back",command=self.back)
        self.back_button.grid(column=0,row=brow)
        self.save_button = tk.Button(self, text="Save",command=self.save_cuts)
        self.save_button.grid(column=1,row=brow)
        self.init_ani()

    def init_ani(self):
        self.controller.animate_cuts()


    def clear_widgets(self):
        for widget in self.winfo_children():
            widget.destroy()

    def back(self):
        self.controller.show_frame('HeaderUI')

    def check_path(self, path):
        overwrite = [tf for tf in (path,path+'.hdr') if os.path.exists(tf)]
        if overwrite:
            ow_msg = '\n'.join(['The following files will be overwritten:']+overwrite+['Do you want to continue?'])
            ynpopup = self.controller.make_splash(SplashObj=YesNoPopup,text=ow_msg)
            yes_no = ynpopup.get_ans()
            self.controller.stop_splash(ynpopup)
            print('Returning {}'.format(yes_no))
            return yes_no
        else:
            return True




    def save_cuts(self):
        Tk().withdraw()
        save_path = askdirectory()
        if save_path:
            '''
            I think order should be preserved here.  
            That is important for the ok_save check to match which file we are saving
            '''
            not_saved = []
            new_files = [os.path.join(save_path,cut.filename) for cut in self.controller.image.cuts]
            for i,filepath in enumerate(new_files):
                ok_save = self.check_path(filepath)
                if ok_save:
                    savescreen = self.controller.make_splash(SplashObj=SplashScreen,text='Saving image...')
                    self.controller.image.save_cut(index=i,path=save_path)
                    self.controller.stop_splash(savescreen)
                else:
                    not_saved.append(1)

            # if any not saved, might need to revise filepath, don't reset.
            if not_saved:
                pass
            else:
                self.controller.remove_temp_dirs()
                self.controller.show_frame('ImageSelector')
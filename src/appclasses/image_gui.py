from .dependencies import *
from .confirm_save import ConfirmSave
from .header_ui import HeaderUI
from .image_cutter import ImageCutter
from .image_rotator import ImageRotator
from .image_selector import ImageSelector
from .smallscreens import YesNoPopup, SplashScreen


class ImageGUI(tk.Tk,ImageEditor):

    def __init__(self, folder='data'):
        ImageEditor.__init__(self)
        tk.Tk.__init__(self)
        self.__name__ = 'ImageGUI'
        self.title("Image Preprocessing")

        self.make_size()

        self.img_type = None
        self.filepath = None
        self.nmice = None
        self.folder = folder.strip('/').strip('\\').strip()
        self.tempdirs = []

        # default exposure scale
        self.escale = 1.0
        self.str_scale = tk.StringVar()

        # escaler coords
        self.escaler_x,self.escaler_y = 960,245
        
        # view axis
        self.view_ax = 'z'
        
        # image info coords
        self.iicoords = (620,140)

        # next and back button coords
        self.bbx, self.bby = 735, 400
        self.nbx, self.nby = self.bbx+180, self.bby

        # attribute to hold splash screen
        self.splash = None

        # attribute to hold which frame is raised
        self.raised_frame = None

        # attribute to hold which frame was raised last
        self.last_frame = None

        # keep track of which cut we are on (HeaderUI)
        self.cutix = 0

        # title font var
        self.title_font = tkfont.Font(family='Helvetica', size=18, weight="bold", slant="italic")

        # the container is where we'll stack a bunch of frames
        # on top of each other, then the one we want visible
        # will be raised above the others
        self.container = tk.Frame(self)
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (ImageSelector, ImageRotator, ImageCutter, HeaderUI, ConfirmSave):
            page_name = F.__name__
            self.frames[page_name] = F

        self.show_frame("ImageSelector")

    def make_size(self,small=False):
        if small:
            w = 500
            h = 500
        else:
            w = 1200 # width for the Tk root
            h = 650 # height for the Tk root

        # get screen width and height
        ws = self.winfo_screenwidth() # width of the screen
        hs = self.winfo_screenheight() # height of the screen

        # calculate x and y coordinates for the Tk root window
        x = (ws/2) - (w/2)
        y = (hs/2) - (h/2)

        # set the dimensions of the screen 
        # and where it is placed
        self.geometry('%dx%d+%d+%d' % (w, h, x, y))


    def get_files(self):
        
        fnames = [os.path.join(dp, f) for dp, dn, filenames in os.walk(self.folder) for f in filenames]
        pet_files =  [PETImage(f) for f in fnames if is_pet(f)]
        ct_files = [CTImage(f) for f in fnames if f.endswith('.ct.img')]
        all_files = pet_files+ct_files
        all_files.sort(key=lambda x: x.subject_id)
        groups = defaultdict(list)
        for img in all_files:
            groups[img.subject_id].append(img)
        img_pairs = groups.values()
        return img_pairs
        


    def show_frame(self, page_name):
        if self.raised_frame is not None:
            self.last_frame = self.raised_frame.__name__
            self.raised_frame.destroy()

        stack_report(page_name)
        
        '''Show a frame for the given page name'''
        FrameObj = self.frames[page_name]
        self.raised_frame = FrameObj(parent=self.container, controller=self)
        self.raised_frame.grid(row=0, column=0, sticky="nsew")
        self.raised_frame.tkraise()




    def make_splash(self,SplashObj=SplashScreen,text='Loading...'):
        self.withdraw()
        return SplashObj(self,text=text)

    def stop_splash(self,SplashObj):
        SplashObj.destroy()
        self.deiconify()

    def load_image(self):
        tdir = tempfile.mkdtemp()
        log_temp_dir(tdir)
        self.image.tempdir = tdir
        self.image.load_image()
        
        # calc crossx len for static cutter
        maxdim = max(self.image.params.x_dimension,self.image.params.y_dimension)
        self.cxlen = math.ceil(maxdim/100)


    def start_img(self,img):
        # self.make_size()
        loadscreen = self.make_splash(SplashObj=SplashScreen,text='Loading...')       
        self.image = img
        self.load_image()
        self.tempdirs.append(self.image.tempdir)
        self.stop_splash(loadscreen)
        self.show_frame("ImageRotator")



    def init_escaler(self, frame):

        escaler = self.make_escale(frame)
        escale_label = tk.Label(frame, text="Exposure Scale:",justify=tk.LEFT)
        escale_apply = tk.Button(frame, text="Apply",command=self.adjust_escale)
        
        return (escaler,escale_label,escale_apply)
        # self.place_escale(frame)

    def make_escale(self, frame):
        self.str_scale.set(str(self.escale))
        escaler = tk.Entry(frame,textvariable=self.str_scale)
        return escaler


    def adjust_escale(self):
        try:
            self.escale = float(self.str_scale.get())
        except ValueError:
            print('Cannot interpret input {} exposure scale as a float.'.format(self.str_scale.get()))
            return
        self.show_frame(self.raised_frame.__name__)


    def place_escale(self,frame):
        frame.escale_label.place(x=self.escaler_x,y=self.escaler_y-30)
        frame.escaler.place(x=self.escaler_x,y=self.escaler_y)
        frame.escale_apply.place(x=self.escaler_x+30,y=self.escaler_y+30)




    def get_img_info(self,frame):
        fname = self.image.filename
        z,y,x,frames = self.image.img_data.shape
        text = '\n'.join(['File : {}'.format(fname),
                        'Number of frames : {}'.format(frames),
                        'Frame dimensions : ({0}, {1}, {2})'.format(x,y,z)
            ])
        label = tk.Label(frame,text=text,font=tkfont.Font(family='Helvetica', size=9),justify=tk.LEFT)
        return label

    def init_img_info(self,frame,coords=None):
        if frame.img_info is not None:
            frame.img_info.destroy()
        frame.img_info = self.get_img_info(frame)
        if coords is None:
            coords = self.iicoords
        frame.img_info.place(x=coords[0],y=coords[1])



    def static_cutter_controls(self,canvas):

        def onClick(event):
            if event.xdata is not None and event.ydata is not None:
                self.cx,self.cy = (int(round(event.xdata)),int(round(event.ydata)))
                if len(self.current_cut) > 4:
                    raise ValueError('Error in onClick event; self.current_cut too large.')
                elif len(self.current_cut) == 4:
                    self.current_cut.pop(-1)
                self.current_cut.append((self.cx,self.cy))

                message = 'Cutter coords: (x={0},y={1})'.format(self.cx,self.cy)
                print(message)
                self.show_frame(self.raised_frame.__name__)

        canvas.mpl_connect('button_press_event', onClick)





    def remove_temp_dirs(self):
        self.clean_memmaps()
        for directory in self.tempdirs:
            try:
                shutil.rmtree(directory)
                print('Removed tempdir: {}'.format(directory))
                self.tempdirs.remove(directory)
            except Exception as e:
                print('Failed to remove tempdir: {0}\n{1}'.format(directory,e))
        
    def clean_memmaps(self):
        if self.image is not None:
            self.image.clean_cuts()
            try:
                delattr(self.image,'img_data')
            except AttributeError:
                pass
            fn = '{}.dat'.format(self.image.filename.split('.')[0])
            fp = os.path.join(self.image.tempdir,fn)
            if os.path.exists(fp):
                os.remove(fp)
            self.image = None
        gc.collect()


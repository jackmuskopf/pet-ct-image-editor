from src.appclasses.image_gui import *
from src.imgclasses.imageviewer import normalize, not_zero
import matplotlib.pyplot as plt
import time


### ALGO PARAMS

# bottom x percent of pixels are used for finding gaussian params for no mice
intensity_cutoff = .9

# allow x percent of image dimensions gap between pixels still same mouse
gap_percent = .05

# minimum number of pixels to count as mice (as percentage of total pixels)
min_mouse_percent = .02

# hypothesis test threshold
gamma = .1



def rmdir(mydir):
	try:
		shutil.rmtree(mydir)
		print('removing tempdir {}'.format(mydir))
	except Exception as e:
		print(e)
		print('error when removing: \n{}'.format(mydir))


def do_plot(mat,title=''):
	fig = plt.figure()
	ax = fig.add_subplot(111)
	ax.imshow(mat,cmap="gray",clim=(0,1))
	ax.set_title(title)
	ax.set_xlim(0,mat.shape[1])
	ax.set_ylim(0,mat.shape[0])
	return ax


def add_lines(ax,lines):
	'''
	lines is list of tuples, each containing 2 tuples x1,y1; x2,y2
	'''
	for line in lines:
		p1,p2 = line
		x1,y1 = p1
		x2,y2 = p2
		ax.plot([x1,x2],[y1,y2],'r-')



def get_files(folder):
    
    fnames = [os.path.join(dp, f) for dp, dn, filenames in os.walk(folder) for f in filenames]
    print(len(fnames))
    pet_files =  [PETImage(f) for f in fnames if is_pet(f)]
    ct_files = [CTImage(f) for f in fnames if f.endswith('.ct.img')]
    all_files = pet_files+ct_files
    all_files.sort(key=lambda x: x.subject_id)
    groups = defaultdict(list)
    for img in all_files:
        groups[img.subject_id].append(img)
    img_pairs = groups.values()
    return (ct_files,pet_files)





def likelihood_point(xp,h1,h0):
	

	# hypothesis vars
	mu0,var0 = h0
	mu1,var1 = h1
	# var0 = .0015
	# var1 = .014
	# mu0 = .01
	# mu1 = .29

	like = (var0/var1)*np.exp( (-.5/var1)*(xp-mu1)**2 + (.5/var0)*(xp-mu0)**2 )

	return like




def find_mice(binary_mat):


	### WIP #########
	
	def add_pts(p):
		# print('len open_list: {}; len mouse_open: {}; nmice: {}'.format(len(open_list),len(mouse_open_list),len(mouses)))
		y,x=p
		pts = []
		[pts.append(hkp) for j in range(adj_max) for hkp in [
																(y+j,x),
																(y-j,x),
																(y,x+j),
																(y,x-j)
															]]

		pts = [k for k in pts if k in open_list]

		for k in pts:
			open_list.remove(k)

		for k in pts:
			ty,tx = k
			if bmat[ty,tx]:
				mouse_open_list.append(k)


	bmat = binary_mat
	s= bmat.shape
	avgdim = (s[0]+s[1])/2
	adj_max = max([1,math.floor(gap_percent*avgdim)])
	open_list = [(y,x) for x in range(s[1]) for y in range(s[0])]
	cur_mouse = []
	mouses = []

	while open_list:
		tp = open_list.pop(0)
		y,x = tp
		
		mouse_open_list = [tp,] if bmat[tp[0],tp[1]] else []
		
		while mouse_open_list:
			# print('mol: {}'.format(len(mouse_open_list)))
			mp = mouse_open_list.pop(0)
			cur_mouse.append(mp)
			add_pts(mp)


		min_mouse_size = math.floor(s[0]*s[1]*min_mouse_percent)
		if len(cur_mouse) > min_mouse_size:
			mouses.append(cur_mouse)
		cur_mouse = []

	return mouses




def analyze_image(img):

	try:

		print('Analyzing image: {}'.format(img.filepath))
		time.sleep(1)


		# image
		img.tempdir = tempfile.mkdtemp()
		print(img.tempdir)
		img.load_image()

		# sum over time axis
		show_method = 'max' if "\\CT\\" in img.filepath else 'sum'
		frame = img.collapse_over_frames(method='sum')
		show_frame = img.collapse_over_frames(method=show_method)


		# collapse on z axis
		axis = img.get_axis('z')
		mat = getattr(frame, 'sum')(axis=axis)
		mat = normalize(mat)
		show_mat = getattr(show_frame, show_method)(axis=axis)
		show_mat = normalize(show_mat)
		
		# get hypothesis vars
		# assume mice compose top 10 %
		h0 = mat.mean(),mat.std()**2
		
		flt = mat.flatten()
		cutoff = np.percentile(flt,intensity_cutoff*100)

		mouse_pix = np.array([k for k in flt if k > cutoff])
		nothing_pix = np.array([k for k in flt if k < cutoff])

		h0 = nothing_pix.mean(), nothing_pix.std()**2
		h1 = mouse_pix.mean(), mouse_pix.std()**2


		rmdir(img.tempdir)
		del img.img_data
		gc.collect()		

		gammas = [gamma,]
		for g in gammas:
			s = mat.shape
			res = mat.copy()
			coords = [(x,y) for x in range(s[1]) for y in range(s[0])]

			for x,y in coords:
				p = mat[y,x]
				# res[y,x] = 1 if (likelihood_point(p,h1=h1,h0=h0)>g) else 0

			tf1 = lambda x: int(likelihood_point(x,h1=h1,h0=h0)>g)
			tf2 = lambda x: int(x>cutoff)
			
			vf1 = np.vectorize(tf1)
			vf2 = np.vectorize(tf2)

			testmat1 = vf1(mat)
			testmat2 = vf2(mat)

			tflt1 = testmat1.flatten()
			tflt2 = testmat2.flatten()

			tr = [tflt1[i]==tflt2[i] for i in range(len(tflt1))]
			print('\n'*5,'percent same: {}'.format(len(tr)/float(len(tflt1))),'\n'*5)

			res = vf1(mat)


			myres = res.copy()
			
			# downsample to size ok for cluster finding algo
			ds = 1
			while myres.size > 15000:
				ds = ds*2
				myres = myres[::2,::2]

			mouses = find_mice(myres)
			mouses = [np.matrix(m)*ds for m in mouses]
			coords = [m.mean(axis=0) for m in mouses]
			for c in coords:
				print('mouse at {}'.format(c))
			print('Found {} mice'.format(len(mouses)))




			ax = do_plot(show_mat*10,title='original')

			# # plot dots over mouse
			# for m in mouses:
			# 	for k in range(m.shape[0]):
			# 		y,x = m[k,:][0,0],m[k,:][0,1]
			# 		ax.plot(y,x,'r')

			lines = []
			for m in mouses:
				my,mx = m.max(axis=0)[0,0],m.max(axis=0)[0,1]
				miy,mix = m.min(axis=0)[0,0],m.min(axis=0)[0,1]
				lines += [[(mix,miy),(mix,my)],[(mix,miy),(mx,miy)],[(mx,my),(mix,my)],[(mx,my),(mx,miy)]]

			add_lines(ax,lines)

			block = (g is gammas[-1])
			# do_plot(res,title='gamma = {}'.format(g),block=block)
			# plt.show(block=False)


	except Exception as e:
		rmdir(img.tempdir)
		print(e)







# make tempdir management in BaseImage methods


# ## path
# p = os.path.join('C:\\Users\\Jack\\Downloads\\Dynamic\\Dynamic\\PET','mpet3721a_em1_v1.pet.img')
# pet1 = PETImage(filepath=p)

# p2 = r"D:\image_data\Pre-Clinical_Data_Samples\Pre-Clinical_Data_Samples\Seimens Inveon Scanner\2 Bed\Dynamic\PET\mpet3741a_em1_v1.pet.img"
# pet2 = PETImage(filepath=p2)

# ctp = r'C:\Users\Jack\Downloads\Dynamic\Dynamic\CT\mpet3721a_ct1_v1.ct.img'
# ct1 = CTImage(filepath = ctp)

# ctp2 = r"D:\image_data\Pre-Clinical_Data_Samples\Pre-Clinical_Data_Samples\Seimens Inveon Scanner\2 Bed\Dynamic\CT\mpet3741a_ct1_v1.ct.img"
# ct2 = CTImage(filepath = ctp2)

# img = pet1

# rmdir(r'C:\Users\Jack\AppData\Local\Temp\tmps86lzbt_')



folder = r"D:\image_data\Pre-Clinical_Data_Samples\Pre-Clinical_Data_Samples"
ct_imgs, pet_imgs = get_files(folder)

for im in pet_imgs:
	analyze_image(im)


for im in ct_imgs:
	analyze_image(im)


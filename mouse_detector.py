from src.appclasses.image_gui import *
from src.imgclasses.imageviewer import normalize, not_zero
import matplotlib.pyplot as plt
import time


### ALGO PARAMS

# bottom x percent of pixels are used for finding gaussian params for no mice
default_cutoff = .9
get_intensity_cutoff = lambda nmice: 1-.035*nmice  # assume mice takes up 3.5% of image

# allow x percent of image dimensions gap between pixels still same mouse
gap_percent = .05

# minimum number of pixels to count as mice (as percentage of total pixels)
min_mouse_percent = .02

# hypothesis test threshold
gamma = .1

# expected mouse percent of image
mouse_percent = .035



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
			mp = mouse_open_list.pop(0)
			cur_mouse.append(mp)
			add_pts(mp)


		min_mouse_size = math.floor(s[0]*s[1]*min_mouse_percent)
		if len(cur_mouse) > min_mouse_size:
			mouses.append(cur_mouse)
		cur_mouse = []

	return mouses




def analyze_image(img, nmice=0):


	if nmice == 0:
		intensity_cutoff = default_cutoff
	else:
		intensity_cutoff = get_intensity_cutoff(nmice)

	try:

		print('Analyzing image: {}'.format(img.filepath))
		time.sleep(1)


		# image
		img.tempdir = tempfile.mkdtemp()
		print(img.tempdir)
		if img.img_data is None:
			img.load_image()

		# sum over time axis
		show_method = 'sum' if  is_pet(img.filepath) else 'max'
		frame = img.collapse_over_frames(method='sum')
		show_frame = img.collapse_over_frames(method=show_method)


		# collapse on z axis
		axis = img.get_axis('z')
		mat = getattr(frame, show_method)(axis=axis)
		mat = normalize(mat)
		show_mat = getattr(show_frame, show_method)(axis=axis)
		show_mat = normalize(show_mat)
		
		# get hypothesis vars
		# assume mice compose top 10 %
		
		flt = mat.flatten()
		cutoff = np.percentile(flt,intensity_cutoff*100)

		mouse_pix = np.array([k for k in flt if k > cutoff])
		nothing_pix = np.array([k for k in flt if k < cutoff])

		h0 = nothing_pix.mean(), nothing_pix.std()**2
		h1 = mouse_pix.mean(), mouse_pix.std()**2


	

		gammas = [gamma,]
		for g in gammas:

			# hypothesis test each point is it a mouse?
			tf1 = lambda x: int(likelihood_point(x,h1=h1,h0=h0)>g)
			vf1 = np.vectorize(tf1)
			testmat1 = vf1(mat)
			res = vf1(mat)

			
			### quicker and possibly equivalent way of doing this but I like the proper hypothesis test			
			# tf2 = lambda x: int(x>cutoff)
			# vf2 = np.vectorize(tf2)
			# testmat2 = vf2(mat)
			# tflt1 = testmat1.flatten()
			# tflt2 = testmat2.flatten()
			# tr = [tflt1[i]==tflt2[i] for i in range(len(tflt1))]
			# print('\n'*5,'percent same: {}'.format(len(tr)/float(len(tflt1))),'\n'*5)

			
			# downsample to size ok for group finding algo
			dsres = res.copy()
			ds = 1
			while dsres.size > 15000:
				ds = ds*2
				dsres = dsres[::2,::2]

			mouses = find_mice(dsres)
			mouses = [np.matrix(m)*ds for m in mouses]
			coords = [m.mean(axis=0) for m in mouses]
			for c in coords:
				print('mouse at {}'.format(c))
			print('Found {} mice'.format(len(mouses)))


			if not (nmice == len(mouses)):
				return analyze_image(img,nmice=len(mouses))


			ax = do_plot(show_mat*10,title='original')

			# plot dots over mouse
			for m in mouses:
				for k in range(m.shape[0]):
					y,x = m[k,:][0,0],m[k,:][0,1]
					ax.plot(x,y,'r.')

			lines = []
			for m in mouses:
				my,mx = m.max(axis=0)[0,0],m.max(axis=0)[0,1]
				miy,mix = m.min(axis=0)[0,0],m.min(axis=0)[0,1]
				lines += [[(mix,miy),(mix,my)],[(mix,miy),(mx,miy)],[(mx,my),(mix,my)],[(mx,my),(mx,miy)]]

			add_lines(ax,lines)

			block = (g is gammas[-1])
			# do_plot(res,title='gamma = {}'.format(g),block=block)
			plt.show()
			# plt.draw()

			clean_up_img(img)

			return mouses



	except Exception as e:
		clean_up_img(img)
		print(e)



def clean_up_img(img):
	img.img_data = None
	gc.collect()	
	rmdir(img.tempdir)




def get_radius(x,y):
	return np.sqrt(mouse_percent*x*y/np.pi)

def get_circle_points(p,r):
	x,y = p
	if r>x or r>y:
		raise ValueError('Radius too big in get_circle_points')
	xmi,xma = x-r,x+r
	ymi,yma = y-r,y+r
	square = [(xi,yi) for xi in range(xmi,xma+1) for yi in range(ymi,yma+1)]
	circle = [k for k in square if np.sqrt( (x-k[0])**2 + (y-k[1])**2 ) < r]
	return circle




# folder = r"D:\image_data\Pre-Clinical_Data_Samples\Pre-Clinical_Data_Samples"
# folder = r"C:\Users\jmusko01\Desktop\For Jack"	#\Inveon\4bed\dynamic\flipped"
folder = r"C:\Users\jmusko01\Documents\mycode\old_preproc_work\data"

ct_imgs, pet_imgs = get_files(folder)

if __name__ == "__main__":

	for im in pet_imgs:
		analyze_image(im, nmice=0)


	for im in ct_imgs:
		analyze_image(im, nmice=0)

# plt.show()
# -*- coding: utf-8 -*-

import string, math, itertools, random, os
from PIL import Image, ImageFont, ImageDraw


class TextGenerator(object):

	def __init__(self, letters=string.ascii_lowercase, length=6, rnd=None):
		self.letters = letters
		self.length = length
		if rnd is None:
			rnd = random.Random()
		self.rnd = rnd

	def __call__(self):
		return ''.join(self.rnd.sample(self.letters, self.length))


class Captcha(object):

	mode = 'L'
	bg_color = 254
	color = 0
	
	linesn = 10
	linescolor_range = (0, 255)
	dotspercent = 5
	dotscolor_range = (0, 255)
	
	def __init__(self, size, rnd=None, **kwargs):
		self.size = size
		if rnd is None:
			rnd = random.Random()
		self.rnd = rnd
		self.__dict__.update(kwargs)

	def _period(self):
		return self.rnd.uniform(0.075, 0.12)

	def _phase(self):
		return self.rnd.uniform(0, math.pi)

	def _amplitude(self):
		return self.rnd.uniform(3, 3.8)

	def _wave(self, img):
		dst_img = Image.new(self.mode, img.size, self.bg_color)
		src_data = img.getdata()
		width, height = img.size
		dx_period_x = self._period()
		dx_period_y = self._period()
		dy_period_x = self._period()
		dy_period_y = self._period()
		dx_phase_x = self._phase()
		dx_phase_y = self._phase()
		dy_phase_x = self._phase()
		dy_phase_y = self._phase()
		dx_amplitude = self._amplitude()
		dy_amplitude = self._amplitude()
		# Variable lookup optimization
		sin = math.sin
		bg_color = self.bg_color
		dst_data = [self.bg_color] * (height*width)
		for x, y in itertools.product(xrange(width), xrange(height)):
			color_diff = src_data[x + width*y] - bg_color
			if not color_diff:
				continue
			# source x (float)
			dx_x = sin(x * dx_period_x + dx_phase_x)
			dx_y = sin(y * dx_period_y + dx_phase_y)
			sx = x + (dx_x + dx_y) * dx_amplitude
			if not 0 <= sx < width-1:
				continue
			# source y (float)
			dy_x = sin(x * dy_period_x + dy_phase_x)
			dy_y = sin(y * dy_period_y + dy_phase_y)
			sy = y + (dy_x + dy_y) * dy_amplitude
			if not 0 <= sy < height-1:
				continue
			sx_i = int(sx)
			sy_i = int(sy)
			frx = sx - sx_i
			fry = sy - sy_i
			idx1 = sx_i + width*sy_i
			idx2 = idx1 + width
			dst_data[idx1] += int(color_diff * (1-frx) * (1-fry))
			dst_data[idx1+1] += int(color_diff * frx * (1-fry))
			dst_data[idx2] += int(color_diff * (1-frx) * fry)
			dst_data[idx2+1] += int(color_diff * frx * fry)
		dst_img.putdata(dst_data)
		return dst_img

	def _noise(self, img):
		im = img.copy()
		draw = ImageDraw.Draw(im)
		#add random lines
		for i in xrange(self.linesn):
			coordinates = (self.rnd.randint(0, im.size[0]), self.rnd.randint(0,im.size[1]),
							self.rnd.randint(0, im.size[0]), self.rnd.randint(0,im.size[1]))
			linecolor = self.rnd.randint(self.linescolor_range[0], self.linescolor_range[1])
			draw.line(coordinates, fill=linecolor)
		#add random dots
		pixeln = int(((im.size[0] * im.size[1]) / 100) * self.dotspercent)
		for i in xrange(pixeln):
			ptxy = (self.rnd.randint(0, im.size[0]), self.rnd.randint(0,im.size[1]))
			dotcolor = self.rnd.randint(self.dotscolor_range[0], self.dotscolor_range[1])
			draw.point(ptxy, fill=dotcolor)
		return im

	def create_simple(self, text, font):
		img = Image.new(self.mode, self.size, self.bg_color)
		draw = ImageDraw.Draw(img)
		text_size = draw.textsize(text, font=font)
		left = int((self.size[0]-text_size[0])/2)
		top = int((self.size[1]-text_size[1])/2)
		draw.text((left, top), text, fill=self.color, font=font)
		return self._wave(img)
	
	def create(self, text, font):
		simple_img = self.create_simple(text, font)
		return self._noise(simple_img)

class FontLoad(object):
	
	def __init__(self, path, rnd=None):
		self.fonts = []
		if rnd is None:
			rnd = random.Random()
		self.rnd = rnd
		
		for f in os.listdir(path):
			fullpath = os.path.join(path, f)
			if os.path.isfile(fullpath) and os.path.splitext(f)[1] == '.ttf':
				newfont = ImageFont.truetype(fullpath, 32)
				self.fonts.append(newfont)
	
	def randomfont(self):
		return self.rnd.choice(self.fonts)
	
	def fontlist(self):
		return self.fonts
	
if __name__=='__main__':
	font = ImageFont.truetype('fonts/Times_New_Roman.ttf', 32)
	get_text = TextGenerator()
	captcha = Captcha(size=(120, 50))#, mode='RGB', color='#033')
	from time import time
	start = time()
	count = 20
	for i in range(count):
		text = get_text()
		print text
		img = captcha.create(text, font)
		img.save('tmp/captcha%i.png' % i)
	print '%.4f' % ((time()-start)/count, )
	

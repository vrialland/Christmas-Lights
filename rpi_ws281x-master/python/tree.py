
from random import random
from random import shuffle
from threading import Thread
import sys
from time import sleep
from time import time
import signal

from neopixel import *
from websocket_server import WebsocketServer


def wheel(pos, bri = 1):
	"""Generate rainbow colors across 0-255 positions."""
	if pos < 85:
		return Color(int((pos * 3)*bri), int((255 - pos * 3) * bri), 0)
	elif pos < 170:
		pos -= 85
		return Color(int((255 - pos * 3) * bri), 0, int(pos * 3 * bri))
	else:
		pos -= 170
		return Color(0, int(pos * 3 * bri), int((255 - pos * 3) * bri))


#================================================
#
#    PATTERNS
#
#------------------------------------------------
class PatternBase(object):
	def __init__(self, numPixels):
		self.numPx = numPixels
		self.state = 0
		self.loopCount = 0
		self.strip_order = range(numPixels)
		shuffle(self.strip_order)
		self.clear()

	def clear(self):
		pass

	def step(self, strip):
		self.loopCount += 1
		self.state = self._step(self.state, strip)



class Twinkle(PatternBase):
	def __init__(self, numPixels):
		super(Twinkle, self).__init__(numPixels)

	def clear(self):
		self.stars = []

	def _step(self, state, strip):
		for i,x in enumerate(self.stars):
			if x[1] == 0:
				# dimming
				if x[2] == [0,0,0]:
					if state == 3:
						self.stars.remove(x)
						if len(self.stars) == 0:
							print("---twinkle done")
							return 0
						break
					else:
						while True:
							idx = int(random() * 900) % self.numPx
							for st in self.stars:
								if idx == st[0]:
									continue
							break
						self.stars[i][0] = idx
						self.stars[i][1] = 1
				else:
					self.stars[i][2] = [max(0, c*9/10) for c in x[2]]
			else:
				# brightening
				if x[2] == [255,255,255]:
					self.stars[i][1] = 0
				else:
					self.stars[i][2] = [min(255, int(c + (random()**3)*25)) for c in x[2]]
			strip.setPixelColor(x[0], Color(*x[2]))
		if state == 1:
			if len(self.stars) < 50:
				if self.loopCount % 4 == 0:
					self.stars.append([int(random() * self.numPx), 1, [0,0,0]])
			else:
				print("---twinkle full")
				return 2
		return state



class Classic(PatternBase):
	def __init__(self, numPixels):
		numPixels = numPixels - (numPixels % 4)   # makes sure that numPixels can be divided by 4, e.g, numPixels = 150 wouldn't work 
		super(Classic, self).__init__(numPixels)
		self.strip_order = range(0, numPixels, 4)
		shuffle(self.strip_order)

	def clear(self):
		self.dots = []

	def newDot(self, strip, idx):
		x = self.strip_order[idx] + (int(random() * 100) % 4)
		if random() > 0.05 and idx < len(self.dots):
			x = self.dots[idx][0]
		strip.setPixelColor(x, Color(220,180,50))
		return [x, int(random() * 100)]

	def _step(self, state, strip):
		for i in range(len(self.dots)):
			if self.dots[i][1] == 0:
				strip.setPixelColor(self.dots[i][0], 0x0)
				if state != 3:
					self.dots[i] = self.newDot(strip, i)
				else:
					del self.dots[i]
					if len(self.dots) == 0:
						shuffle(self.strip_order)
						print("---classic done")
						return 0
					break
			else:
				self.dots[i][1] -= 1
		if state == 1:
			if len(self.dots) < 75:
				self.dots.append(self.newDot(strip, len(self.dots)))
			else:
				print("---classic full")
				return 2
		return state



class Candycane(PatternBase):
	def __init__(self, numPixels):
		super(Candycane, self).__init__(numPixels)

	def clear(self):
		self.stripes = []

	def newStripe(self):
		r = int(random() * 5)+2 # stripe radius
		return [-r, r, int(random()*2+0.5)+1,    Color(255,0,0) if random() < 0.5 else Color(255,255,255)]

	def _step(self, state, strip):
		for i in range(len(self.stripes)):
			if self.stripes[i][0] - self.stripes[i][1] > self.numPx:
				if state != 3:
					self.stripes[i] = self.newStripe()
				else:
					del self.stripes[i]
					if len(self.stripes) == 0:
						print("---candycane done")
						return 0
					break
			else:
				for speed in range(self.stripes[i][2] + (2 if state == 3 else 0)):
					strip.setPixelColor(min(self.numPx, self.stripes[i][0]+self.stripes[i][1]), self.stripes[i][3])
					strip.setPixelColor(max(0,self.stripes[i][0]-self.stripes[i][1]), 0x0)
					self.stripes[i][0] += 1

		if state == 1:
			if len(self.stripes) < 20:
				if self.loopCount % 5 == 0:
					self.stripes.append(self.newStripe())
			else:
				print("---candycane full")
				return 2

		return state



class Wind(PatternBase):
	def __init__(self, numPixels):
		super(Wind, self).__init__(numPixels)

	def clear(self):
		self.wisp = []

	def newWisp(self):
		e = int(random() * 30)+10
		s = int(random() * (self.numPx-e))
		return [s, e+s, s, min(1.0, random()+0.5)]

	def _step(self, state, strip):
		for i in range(len(self.wisp)):
			if self.wisp[i][0] > self.wisp[i][1] + 1:
				strip._led_data[self.wisp[i][0]] = 0x0
				strip._led_data[self.wisp[i][0]+1] = 0x0
				if state != 3:
					self.wisp[i] = self.newWisp()
				else:
					del self.wisp[i]
					if len(self.wisp) == 0:
						print("---wind done")
						return 0
					break
			else:
				c = max(0,int(255.0 *  ((0.5 - abs( ((1.0 * self.wisp[i][1]-self.wisp[i][0])/(1.0 * self.wisp[i][1] - self.wisp[i][2])) - 0.5))*2.0)**4.0))
				strip._led_data[self.wisp[i][0] - 1] = 0x0
				strip._led_data[self.wisp[i][0]] = Color(int(c * self.wisp[i][3]/4),int(c * self.wisp[i][3]/4),c/4)
				self.wisp[i][0] += 1
				strip._led_data[self.wisp[i][0]] = Color(int(c * self.wisp[i][3]),int(c * self.wisp[i][3]),c)
				strip._led_data[self.wisp[i][0]+1] = Color(int(c * self.wisp[i][3]/4),int(c * self.wisp[i][3]/4),c/4)

		if state == 1:
			if len(self.wisp) < 20:
				if self.loopCount % 6 == 0:
					self.wisp.append(self.newWisp())
			else:
				print("---wind full")
				return 2
		return state



class Rainbow(PatternBase):
	def __init__(self, numPixels):
		super(Rainbow, self).__init__(numPixels)
		self.buff = [0] * numPixels

	def clear(self):
		self.i = 0
		self.cleared = 0
		shuffle(self.strip_order)

	def _step(self, state, strip):
		for t in range(10):
			if self.i >= len(self.strip_order):
				self.i = 0
				if state == 1:
					self.buff = strip._led_data
					print("---rainbow full")
					return 2
			if self.i == 0 and state == 3:
				if self.cleared == 2:
					self.cleared = 0
					print("---rainbow done")
					return 0
				self.cleared += 1
			pos = self.strip_order[self.i]
			color = wheel((pos + int(time()*30)) % 256) if state != 3 else 0x0
			self.buff[pos] = color
			self.i += 1

		return state



class Blur(PatternBase):
	def __init__(self, numPixels):
		super(Blur, self).__init__(numPixels)
		self.strip_order = range(numPixels)
		shuffle(self.strip_order)
		self.buff = [0] * numPixels

	def clear(self):
		self.i = 0
		self.cleared = 0
		self.baseC = int(random()*1024)%256
		self.dots = []#[self.newDot() for x in range(15)]

	def newDot(self):
		return [int(random()*900)%self.numPx, wheel((self.baseC + int(random() * 40))%256, random()**2)]

	def _step(self, state, strip):
		if state == 1:
			self.buff = strip._led_data
			print("---blur full")
			return 2
		for t in range(40):
			if self.i >= len(self.strip_order):
				self.i = 0
				shuffle(self.strip_order)
			if self.i == 0 and state == 3:
				if self.cleared == 2:
					self.cleared = 0
					print("---blur done")
					return 0
				self.cleared += 1
			pos = self.strip_order[self.i]
			if state != 3:
				c0 = self.buff[pos-1]
				# c1 = self.buff[pos]
				c2 = self.buff[(pos+1)%self.numPx]
				# c = ((((c0&0xff0000)+(c1&0xff0000)+(c2&0xff0000))/3)&0xff0000) |\
				#     ((((c0&  0xff00)+(c1&  0xff00)+(c2&  0xff00))/3)&0xff00) |\
				#     ((((c0&    0xff)+(c1&    0xff)+(c2&    0xff))/3)&0xff)
				c = ((((c0&0xff0000)+(c2&0xff0000))>>1)&0xff0000) |\
				    ((((c0&  0xff00)+(c2&  0xff00))>>1)&0xff00) |\
				    ((((c0&    0xff)+(c2&    0xff))>>1)&0xff)
				self.buff[pos] = c
			else:
				self.buff[pos] = 0
			self.i += 1
		if state != 3:
			# update base dots
			for t in self.dots:
				self.buff[t[0]] = t[1]
			# add dots
			if len(self.dots) < 10 and self.loopCount % 10 == 0:
				self.dots.append(self.newDot())
			# base color
			if self.loopCount % 10 == 0:
				i = int(random()*1000)%len(self.dots)
				self.dots[i] = self.newDot()
			# color burst
			if self.loopCount % 30 == 0:
				c = wheel(int(random()*1024)%256)
				i = int(random()*900)%(self.numPx-4)
				self.buff[i:i+4] = [c]*4
			# change base color
			if self.loopCount % 100 == 0 and random() < 0.1:
				self.baseC = int(random()*1024)%256
				print("---blur base color change %d"%self.baseC)
		return state


class Fairy(PatternBase):
	def __init__(self, numPx):
		super(Fairy, self).__init__(numPx)
		self.strip_b = [random() ** 2 for x in range(numPx)]
		self.strip_c = [int(random() * 40) for x in range(numPx)]

	def clear(self):
		self.wisp = []
		self.spawn = 0

	def newWisp(self, i = -1):
		d = (int(random()*100)%2) * 2 - 1
		length = int(random() * 15 + 8)
		px = range(1, length)
		c = int(random() * 1024)%256
		return [0 if d > 0 else self.numPx - 1, d, c, length, px]

	def _step(self, state, strip):
		for i in range(len(self.wisp)):
			shuffle(self.wisp[i][4])
			if state == 3:
				if self.wisp[i][1] > 0 and self.wisp[i][0] < self.numPx / 2 or self.wisp[i][1] < 0 and self.wisp[i][0] > self.numPx / 2:
					self.wisp[i][1] = -self.wisp[i][1]
			if self.wisp[i][0] > self.numPx + self.wisp[i][3] or self.wisp[i][0] < -self.wisp[i][3]:
				if state != 3:
					if random() < 0.02 and self.spawn > 50:
						self.wisp[i] = self.newWisp(i)
						self.spawn = 0
					self.spawn += 1
				else:
					del self.wisp[i]
					if len(self.wisp) == 0:
						shuffle(self.strip_b)
						shuffle(self.strip_c)
						print("---fairy done")
						return 0
					break
			else:
				if self.wisp[i][0] - self.wisp[i][3] * self.wisp[i][1] >= 0 and self.wisp[i][0] - self.wisp[i][3] * self.wisp[i][1] < self.numPx:
					strip._led_data[self.wisp[i][0] - self.wisp[i][3] * self.wisp[i][1]] = 0x0
				if self.wisp[i][0] >= 0 and self.wisp[i][0] < self.numPx:
					strip._led_data[self.wisp[i][0]] = Color(255,255,255)
				for x in self.wisp[i][4][0:self.wisp[i][3]/3]:
					x = x * self.wisp[i][1]
					if self.wisp[i][0] - x >= 0 and self.wisp[i][0] - x < self.numPx:
						b = (((self.wisp[i][3]+1)-abs(x))/float(self.wisp[i][3]-1))**3 * self.strip_b[(self.wisp[i][0] + x)%self.numPx]
						c = wheel((self.wisp[i][2] + self.strip_c[(self.wisp[i][0] + x)%self.numPx]) % 256, b)
						strip._led_data[self.wisp[i][0] - x] = c
				self.wisp[i][0] += self.wisp[i][1]
		if state == 1:
			if len(self.wisp) < 6:
				if (self.spawn > 50 and random() < 0.1) or len(self.wisp) == 0:
					self.wisp.append(self.newWisp())
					self.spawn = 0
				self.spawn += 1
			else:
				print("---fairy full")
				return 2
		return state




class Off(PatternBase):
	def __init__(self, numPixels):
		super(Off, self).__init__(numPixels)

	def clear(self):
		self.i = 0

	def _step(self, state, strip):
		if self.i >= len(self.strip_order):
			self.i = 0
			shuffle(self.strip_order)
			if state == 1:
				return 2
			elif state == 3:
				return 0
		strip.setPixelColor(self.strip_order[self.i], 0)
		self.i += 1

		return state




#================================================
#
#    STATES / CONTROLS
#
#------------------------------------------------


#--------------------------------------
# available catalog
patterns = [
	# event , func           , full stop ,
	[-1     , Off(300)       , 0] ,
	[-1     , Rainbow(300)   , 1] ,
	[-1     , Candycane(300) , 0] ,
	[-1     , Classic(300)   , 0] ,
	[-1     , Wind(300)      , 0] ,
	[-1     , Twinkle(300)   , 0] ,
	[-1     , Fairy(300)     , 0] ,
	[-1     , Blur(300)      , 1] ,
]

allPats = [
	"off",
	"rainbow",
	"candycane",
	"classic",
	"wind",
	"twinkle",
	"fairy",
	"blur",
]


#================================================
#
#    SERVER
#
#------------------------------------------------
def start(name):
	if name in allPats:
		if patterns[allPats.index(name)][1].state != 2:
			patterns[allPats.index(name)][0] = 1

def stop(name, offMode):
	if name in allPats:
		if patterns[allPats.index(name)][1].state != 0:
			patterns[allPats.index(name)][0] = 4 if offMode else 3

def solo(name):
	offMode = patterns[allPats.index(name)][2]
	for key in allPats:
		if key == name:
			start(key)
		else:
			stop(key, offMode)

def serv_recvParser(cli, serv, msg):
	print(msg)
	solo(msg)

def signal_handler(signal, frame):
	global serv_thread
	global server
	print("Exiting...")
	server.server_close()
	serv_thread.join()
	sys.exit(0)



#================================================
#
#    MAIN / INIT
#
#------------------------------------------------


signal.signal(signal.SIGINT, signal_handler)
print('Press Ctrl+C to exit')

server = WebsocketServer(12000, host="0.0.0.0")
server.set_fn_message_received(serv_recvParser)
serv_thread = Thread(target=server.run_forever, args=())
serv_thread.start()

strip = Adafruit_NeoPixel(300, 12, strip_type = ws.WS2811_STRIP_GRB)
strip.begin()
strip_order = range(strip.numPixels())
shuffle(strip_order)

while True:
	looptime = time()
	for idx in range(len(patterns)):
		if patterns[idx][1].state > 0:
			patterns[idx][1].step(strip)
		if patterns[idx][0] >= 0:
			if patterns[idx][0] == 1: # turn on
				patterns[idx][1].state = 1
			elif patterns[idx][0] == 3: # turn off (gentle)
				patterns[idx][1].state = 3
			elif patterns[idx][0] == 4: # turn off (hard stop)
				patterns[idx][1].state = 0
				patterns[idx][1].clear()
			patterns[idx][0] = -1
	strip.show()

	delta = time() - looptime
	# print("%.4f"%(delta*40))
	if delta < 1.0/40:
		sleep(1.0/40 - delta)




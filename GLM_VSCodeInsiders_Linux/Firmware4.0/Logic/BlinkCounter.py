import Logic
import pickle
import imutils
import numpy as np
import cv2
import time


class BlinkCounter(object):

	def make_lut_u(self):
		return np.array([[[i, 255 - i, 0] for i in range(256)]], dtype=np.uint8)

	def make_lut_v(self):
		return np.array([[[0, 255 - i, i] for i in range(256)]], dtype=np.uint8)

	def whoami(self):
		"""
		returns the class name as string
		"""
		return type(self).__name__

	__instance__ = None

	@staticmethod
	def Instance():
		""" Static method to fetch the current instance.
		"""
		return BlinkCounter.__instance__

	def __init__(self, LedLocationFilePath, configs):
		try:
			self.logger = Logic.GetLogger().SetAPIName(self.whoami())
			self.SetPreviousLedLocations(LedLocationFilePath)
			self.__TOTAL_NUMBER_OF_LEDS__ = 3
			self.__LedsCentrePointList__ = list()
			self.__LastStateofLedAtPos__ = dict()
			self.__LedLocation__ = []
			self.__LedBlinkCounter__ = []
			self.__VerdictTimer__ = Logic.PeriodicTimer(10, self.GenerateVerdict)

			self.__FoundLED__ = [False, False, False]
			self.__LedBlinkCounter__ = []
			self.__LedBlinkCounter__.append([0, [False, 0]])
			self.__LedBlinkCounter__.append([1, [False, 0]])
			self.__LedBlinkCounter__.append([2, [False, 0]])

			# Setting Static Object
			if BlinkCounter.__instance__ is None:
				BlinkCounter.__instance__ = self
		except:
			self.logger.log(self.logger.ERROR, 'Failed to Init ' + self.whoami())
			raise ValueError()
		pass

	def GetYUVImage(self, image):
		yuvImage = cv2.cvtColor(image, cv2.COLOR_BGR2YUV)
		yuvImage = cv2.GaussianBlur(yuvImage, (5, 5), 0)
		# Separating the y, cb and cr channels
		y, u, v = cv2.split(yuvImage)
		del yuvImage

		lut_u, lut_v = self.make_lut_u(), self.make_lut_v()
		u = cv2.cvtColor(u, cv2.COLOR_GRAY2BGR)
		v = cv2.cvtColor(v, cv2.COLOR_GRAY2BGR)

		v_mapped = cv2.LUT(v, lut_v)
		u_mapped = cv2.LUT(u, lut_u)
		del lut_u
		del lut_v
		del u
		del v
		# Convert back to BGR so we can apply the LUT and stack the images
		y = cv2.cvtColor(y, cv2.COLOR_GRAY2BGR)

		return y, u_mapped, v_mapped

	def Adjust_VMap(self, vmap, adjustment=205):
		y, x, _ = vmap.shape

		# Adjustment of fisrt half of image
		avg1 = np.mean(vmap[:, :, 2][0:int(y / 2), int(0):int(x)], axis=(0, 1))
		avg2 = np.mean(vmap[:, :, 2][int(y / 2):int(y), int(0):int(x)], axis=(0, 1))
		newavg = int((avg1 / adjustment) * 100)

		if avg1 >= 120 and avg1 < 130:
			newavg += (newavg / 1.2)
		elif avg1 >= 130:
			newavg += (avg1 - 100)
		vmap[:, :, 2][0:int(y / 2), int(0):int(x)] += int(newavg)

		# Adjustment of second half of image
		newavg = int((avg2 / adjustment) * 100)
		if avg2 >= 120 and avg2 < 130:
			newavg /= 3
		elif avg2 >= 130:
			newavg = newavg - (newavg / 4)
		vmap[:, :, 2][int(y / 2):int(y), int(0):int(x)] += int(newavg)
		return vmap

	def VMAP_LightDetection(self, vmapImage, i, isRedMask):

		kernel_1 = np.ones((1, 1), np.uint8)
		kernel_2 = np.ones((2, 2), np.uint8)
		kernel_3 = np.ones((3, 3), np.uint8)
		currentLedState = False
		if not isRedMask:
			vmapImage = cv2.bitwise_not(vmapImage)

		ret, thresh1 = cv2.threshold(vmapImage, 200, 255, cv2.THRESH_BINARY)  # Let red color range pass bw 200-255
		if ret:
			thresh1 = cv2.morphologyEx(thresh1, cv2.MORPH_CLOSE, kernel_1)  # Remove Dots  (1x1 Kernel)
			thresh1 = cv2.morphologyEx(thresh1, cv2.MORPH_OPEN, kernel_2)  # Fill Connected Dots (2x2 Kernel)
			thresh1 = cv2.dilate(thresh1, kernel_3, iterations=6)  # Expand remaining Pixels (3x3 Kernel)

			cv2.imshow("Thresh" + str(i), thresh1)

			if cv2.countNonZero(thresh1) > 0:
				currentLedState = True  # Light is on

			del kernel_1, kernel_2, kernel_3, vmapImage, thresh1
		return currentLedState

	def GetLastLedBlinkState(self, image):
		ret = False
		if len(self.__LedLocations__) < 1:
			del image
			return ret, self.__LedLocations__

		img_hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

		## Gen lower mask (0-5) and upper mask (175-180) of RED
		mask1 = cv2.inRange(img_hsv, (0, 50, 20), (5, 255, 255))
		mask2 = cv2.inRange(img_hsv, (175, 50, 20), (180, 255, 255))

		## Merge the mask and crop the red regions
		mask = cv2.bitwise_or(mask1, mask2)
		red_mask = cv2.bitwise_and(image, image, mask=mask)

		del mask, mask1, mask2, img_hsv

		_, _, v_mapped = self.GetYUVImage(image)
		v_mapped = self.Adjust_VMap(v_mapped)

		for i in range(len(self.__LedLocations__)):
			(rectX, rectY), radius = self.__LedLocations__[i][0], self.__LedLocations__[i][1]

			col_start = rectY
			row_start = rectX

			if col_start > 20:
				col_start = rectY - 20
			else:
				col_start = 0

			if row_start > 20:
				row_start = rectX - 20
			else:
				row_start = 0

			col_end = int(rectY + (2 * radius))
			row_end = int(rectX + (2 * radius))
			cropR_VMAP = v_mapped[:, :, 2][col_start:col_end, row_start:row_end]
			redMaskCropped = red_mask[:, :, 2][col_start:col_end, row_start:row_end]
			if not self.__FoundLED__[i]:
				self.__LedLocations__[i][3] = cropR_VMAP
				self.__FoundLED__[i] = True
				continue

			prev = self.__LedLocations__[i][3]

			err = np.sum((cropR_VMAP.astype("float") - prev.astype("float")) ** 2)
			err /= float(prev.shape[0] * prev.shape[1])
			self.__LedLocations__[i][3] = []
			self.__LedLocations__[i][3] = cropR_VMAP

			currentLedState = False
			if err > 20:  # Change is greater
				if not self.VMAP_LightDetection(redMaskCropped, i, True):
					currentLedState = self.VMAP_LightDetection(cropR_VMAP, i, False)
				else:
					currentLedState = True
				self.__LedLocations__[i][2] = currentLedState

			del prev

		del image, red_mask, cropR_VMAP

		return ret, self.__LedLocations__

	def SetPreviousLedLocations(self, filepath):
		f = open(filepath, 'rb')
		obj = pickle.load(f)
		f.close()
		self.__LedLocations__ = obj
		for i in range(len(self.__LedLocations__)):
			self.__LedLocations__[i][2] = False
			if len(self.__LedLocations__[i]) == 3:
				self.__LedLocations__[i].append([])  # set previous light state later on for change comparison
			else:
				self.__LedLocations__[i][3] = []

	def IncrementLightCounter(self, lightId, isLightOn):
		count = 0
		for i in range(len(self.__LedBlinkCounter__)):
			id = self.__LedBlinkCounter__[i][0]
			if id == lightId:
				prevcounterArr = self.__LedBlinkCounter__[i][1]
				prevLightState = prevcounterArr[0]
				count = prevcounterArr[1]
				if prevLightState != isLightOn:
					if prevLightState == False:
						if id != 0:
							self.__LedBlinkCounter__[i][1][1] += 1
						else:
							self.__LedBlinkCounter__[i][1][1] = 1
					self.__LedBlinkCounter__[i][1][0] = isLightOn
				else:
					pass
			else:
				pass
		return count

	def SetLedsCentreLocations(self, ledLocation):
		locUpdated = False
		addToArray = False
		if len(self.__LedLocation__) == 0:
			self.__LedLocation__.append([ledLocation].copy())
		else:
			x1, y1, w, h, c = ledLocation
			for i in range(len(self.__LedLocation__)):
				x2, y2, w, h, c = (self.__LedLocation__[i][0].copy())
				dx2 = (x2 - x1) ** 2
				dy2 = (y2 - y1) ** 2
				distance = math.sqrt(dx2 + dy2)
				print('Distance from Led  = ' + str(i) + '  ' + str(distance))

				if int(distance) <= 2:
					addToArray = False
					break
				if int(distance) > 2 and int(distance) <= 50:
					print('Updating LED Location')
					self.__LedLocation__[i] = [ledLocation]
					addToArray = False
					locUpdated = True
					break

				if int(distance) > 30:
					addToArray = True

		if addToArray == True:
			if ledLocation[3] > self.__LedLocation__[0][0][3]:
				if len(self.__LedLocation__) > 1:
					if ledLocation[3] > self.__LedLocation__[1][0][3]:
						self.__LedLocation__.append([ledLocation].copy())
					else:
						self.__LedLocation__.insert(1, [ledLocation].copy())
				else:
					self.__LedLocation__.append([ledLocation].copy())
			else:
				self.__LedLocation__.insert(0, [ledLocation].copy())

		xyr = {}

		for i in range(len(self.__LedLocation__)):
			((x, y), radius), b = cv2.minEnclosingCircle(self.__LedLocation__[i][0][4]), False
			if i > 0:
				swapped = False
				for j in range(len(xyr)):
					y2 = xyr[j][0][1]
					if y < y2:
						temp = xyr[j]
						xyr[j] = [(int(x), int(y)), int(radius), b]
						xyr[len(xyr)] = temp
						swapped = True

			if i == 0 or swapped == False:
				xyr[len(xyr)] = [(int(x), int(y)), int(radius), b]

		self.__LedLocations__.clear()
		self.__LedLocations__ = xyr
		if len(self.__LedLocations__) == 3:
			self.StoreLedLocations()
		else:
			pass

	def StoreLedLocations(self):
		if len(self.__LedLocations__) == 3:
			with open("GLM2.pckl", 'wb') as f:
				pickle.dump(self.__LedLocations__, f)
				f.close()
		else:
			pass

	def FindCountoursInMaskedImage(self, image, cntSize):
		# perform a connected component analysis on the thresholded
		# image, then initialize a mask to store only the "large"
		# components
		labels = measure.label(image, connectivity=2, background=0)
		mask = np.zeros(image.shape, dtype="uint8")

		# loop over the unique components
		for label in np.unique(labels):
			# if this is the background label, ignore it
			if label == 0:
				continue
			# otherwise, construct the label mask and count the
			# number of pixels
			labelMask = np.zeros(image.shape, dtype="uint8")
			labelMask[labels == label] = 255
			numPixels = cv2.countNonZero(labelMask)

			# if the number of pixels in the component is sufficiently
			# large, then add it to our mask of "large blobs"

			if numPixels > cntSize:  # Chnage this accordingly
				mask = cv2.add(mask, labelMask)
		# find the contours in the mask, then sort them from left to
		# right
		cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
		cnts = imutils.grab_contours(cnts)
		return cnts

	def ResetBlinkcounters(self):
		self.__LedBlinkCounter__.clear()
		self.__FoundLED__ = [False, False, False]
		self.__LedBlinkCounter__.append([0, [False, 0]])
		self.__LedBlinkCounter__.append([1, [False, 0]])
		self.__LedBlinkCounter__.append([2, [False, 0]])

	def GetBlinkCounters(self):
		return self.__LedBlinkCounter__

	def GenerateVerdict(self):
		for i in range(len(self.__LedBlinkCounter__)):
			print('Blink Count of Led => ' + str(i) + ' : ' + str(self.__LedBlinkCounter__[i][1][1]))
		self.__LedBlinkCounter__.clear()
		self.__LedBlinkCounter__.append([0, [False, 0]])
		self.__LedBlinkCounter__.append([1, [False, 0]])
		self.__LedBlinkCounter__.append([2, [False, 0]])

		self._sameValue = 0
		self.__VerdictTimer__.stop()

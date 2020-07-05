
import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import cv2
import colorsys

LEN_MIN = 610
LEN_MAX = 740
LEN_STEP = 1
X = [
    0.000160, 0.000662, 0.002362, 0.007242, 0.019110, 0.043400, 0.084736, 0.140638, 0.204492, 0.264737,
    0.314679, 0.357719, 0.383734, 0.386726, 0.370702, 0.342957, 0.302273, 0.254085, 0.195618, 0.132349,
    0.080507, 0.041072, 0.016172, 0.005132, 0.003816, 0.015444, 0.037465, 0.071358, 0.117749, 0.172953,
    0.236491, 0.304213, 0.376772, 0.451584, 0.529826, 0.616053, 0.705224, 0.793832, 0.878655, 0.951162,
    1.014160, 1.074300, 1.118520, 1.134300, 1.123990, 1.089100, 1.030480, 0.950740, 0.856297, 0.754930,
    0.647467, 0.535110, 0.431567, 0.343690, 0.268329, 0.204300, 0.152568, 0.112210, 0.081261, 0.057930,
    0.040851, 0.028623, 0.019941, 0.013842, 0.009577, 0.006605, 0.004553, 0.003145, 0.002175, 0.001506,
    0.001045, 0.000727, 0.000508, 0.000356, 0.000251, 0.000178, 0.000126, 0.000090, 0.000065, 0.000046,
    0.000033]

Y = [
    0.000017, 0.000072, 0.000253, 0.000769, 0.002004, 0.004509, 0.008756, 0.014456, 0.021391, 0.029497,
    0.038676, 0.049602, 0.062077, 0.074704, 0.089456, 0.106256, 0.128201, 0.152761, 0.185190, 0.219940,
    0.253589, 0.297665, 0.339133, 0.395379, 0.460777, 0.531360, 0.606741, 0.685660, 0.761757, 0.823330,
    0.875211, 0.923810, 0.961988, 0.982200, 0.991761, 0.999110, 0.997340, 0.982380, 0.955552, 0.915175,
    0.868934, 0.825623, 0.777405, 0.720353, 0.658341, 0.593878, 0.527963, 0.461834, 0.398057, 0.339554,
    0.283493, 0.228254, 0.179828, 0.140211, 0.107633, 0.081187, 0.060281, 0.044096, 0.031800, 0.022602,
    0.015905, 0.011130, 0.007749, 0.005375, 0.003718, 0.002565, 0.001768, 0.001222, 0.000846, 0.000586,
    0.000407, 0.000284, 0.000199, 0.000140, 0.000098, 0.000070, 0.000050, 0.000036, 0.000025, 0.000018,
    0.000013]

Z = [
    0.000705, 0.002928, 0.010482, 0.032344, 0.086011, 0.197120, 0.389366, 0.656760, 0.972542, 1.282500,
    1.553480, 1.798500, 1.967280, 2.027300, 1.994800, 1.900700, 1.745370, 1.554900, 1.317560, 1.030200,
    0.772125, 0.570060, 0.415254, 0.302356, 0.218502, 0.159249, 0.112044, 0.082248, 0.060709, 0.043050,
    0.030451, 0.020584, 0.013676, 0.007918, 0.003988, 0.001091, 0.000000, 0.000000, 0.000000, 0.000000,
    0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000,
    0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000,
    0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000,
    0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000,
    0.000000]

MATRIX_SRGB_D65 = [
    3.2404542, -1.5371385, -0.4985314,
    -0.9692660,  1.8760108,  0.0415560,
    0.0556434, -0.2040259,  1.0572252]

class RgbCalculator:
    def calWave(self, wave, x,y, z):
        if wave < x:
            return y
        else:
            return z



    def rgb_to_hsv(self,r, g, b):
        r, g, b = r/255.0, g/255.0, b/255.0
        mx = max(r, g, b)
        mn = min(r, g, b)
        df = mx-mn
        if mx == mn:
            h = 0
        elif mx == r:
            h = (60 * ((g-b)/df) + 360) % 360
        elif mx == g:
            h = (60 * ((b-r)/df) + 120) % 360
        elif mx == b:
            h = (60 * ((r-g)/df) + 240) % 360
        if mx == 0:
            s = 0
        else:
            s = (df/mx)*100
        v = mx*100
        return h, s, v
    def hue2wavelength(self, hue):
        # There is nothing corresponding to magenta in the light spectrum, 
        # So let's assume that we only use hue values between 0 and 270
        if hue >= 0 and hue <= 270:
            # Estimating that the usable part of the visible spectrum is 450-620nm, 
            # with wavelength (in nm) and hue value (in degrees), you can improvise this:
            wavelength = 620 - 170 / 270 * hue;

    def rgb2hsv(self, r,g,b):
        #hsv = self.rgb_to_hsv(r,g,b)
        #[h,s,v] = rgb2hsv(r, g, b)

        MAX_PIXEL_VALUE = 255.0;

        r = r / MAX_PIXEL_VALUE;
        g = g / MAX_PIXEL_VALUE;
        b = b / MAX_PIXEL_VALUE;

        max_val = max(r, g, b);
        min_val = min(r, g, b);

        v = max_val;

        if max_val == 0.0:
            s = 0;
            h = 0;
        elif (max_val - min_val) == 0.0:
            s = 0;
            h = 0;
        else:
            s = (max_val - min_val) / max_val

            if max_val == r:
                h = 60 * ((g - b) / (max_val - min_val)) + 0
            elif max_val == g:
                h = 60 * ((b - r) / (max_val - min_val)) + 120
            else:
                h = 60 * ((r - g) / (max_val - min_val)) + 240

        if h < 0:
            h = h + 360.0

        h = h / 2
        s = s * MAX_PIXEL_VALUE
        v = v * MAX_PIXEL_VALUE

        return [h, s, v]


    def WaveLenghtToXYZFit(self,wavelength):
        wave = wavelength
        t1 = (wave - 442.0) * (self.calWave(wave, 442.0, 0.0624, 0.0374))
        t2 = (wave - 599.8) * (self.calWave(wave,  599.8, 0.0264 , 0.0323))
        t3 = (wave - 501.1) * (self.calWave(wave,  501.1, 0.0490 , 0.0382))

        x = 0.362 * math.exp(-0.5 * t1 * t1) + 1.056 * math.exp(-0.5 * t2 * t2) - 0.065 * math.exp(-0.5 * t3 * t3);

        t1 = (wave - 568.8) * (self.calWave(wave, 568.8, 0.0213, 0.0247))
        t2 = (wave - 530.9) * (self.calWave(wave, 530.9, 0.0613 , 0.0322))

        y = 0.821 * math.exp(-0.5 * t1 * t1) + 0.286 * math.exp(-0.5 * t2 * t2)

        t1 = (wave - 437.0) * (self.calWave(wave, 437.0, 0.0845, 0.0278))
        t2 = (wave - 459.0) * (self.calWave(wave, 459.0, 0.0385, 0.0725))

        z = 1.217 * math.exp(-0.5 * t1 * t1) + 0.681 * math.exp(-0.5 * t2 * t2);

        return x,y,z

    def wavelengthToRGB(self, len):
        #len = len * (700 - 400) + 400
        if len < LEN_MIN or len > LEN_MAX:
            return [3]

        len -= LEN_MIN
        index = int(math.floor(len/LEN_STEP))
        offset = len - LEN_STEP * index
        x,y,z = self.WaveLenghtToXYZFit(len)

        x = self.Interpolate(X, index, offset)
        y = self.Interpolate(Y, index, offset)
        z = self.Interpolate(Z, index, offset)

        m = MATRIX_SRGB_D65

        r = m[0] * x + m[1] * y + m[2] * z;
        g = m[3] * x + m[4] * y + m[5] * z
        b = m[6] * x + m[7] * y + m[8] * z

        r = self.GammaCorrect_sRGB(r)
        g = self.GammaCorrect_sRGB(g)
        b = self.GammaCorrect_sRGB(b)

        return [(255 * r),(255 * g),(255 * b)];
    
    def Interpolate(self, values, index, offset):
        if offset == 0:
            return values[index]

        x0 = index * LEN_STEP
        x1 = x0 + LEN_STEP
        y0 = values[index]
        y1 = values[1 + index]

        return y0 + offset * (y1 - y0) / (x1 - x0)
    
    def GammaCorrect_sRGB(self, c):
         return (1 + a) * math.pow(c, 1 / 2.4) - a

    def Clip(self, c): 
        if(c < 0):
            return 0
        if(c > 1):
            return 1
        return c

    def Generate(self):
        for x in range(LEN_MIN, LEN_MAX):

           #out = self.wavelengthToRGB(x)
           img = cv2.imread("Test.png")
           b,g,r=cv2.split(img)
           #whiteFrame[:] = (out[0], out[1], out[2])
           blue   = img[:, :, 0]
           green  = img[:, :, 1]
           red    = img[:, :, 2]

           cv2.imshow("Red", r)
           cv2.imshow("green", b)
           cv2.imshow("blue", g)

           imgWhite = 0 * np.ones([img.shape[0],img.shape[1]],dtype=np.uint8)
           red[red < 253] = 0

           cv2.imshow("whiteFrame", img)
           cv2.imshow("mask", red)
           

           result = cv2.bitwise_and(img, img , mask= red)
           cv2.imshow("result", result)
           cv2.waitKey(0)
           [h,s,v] = self.rgb2hsv(red, blue, green)
           [h1,s1,v1] = self.rgb_to_hsv(red, blue, green)
           v1 = self.hue2wavelength(h)
           v2 = self.hue2wavelength(h1)
           cv2.imshow("Frame", whiteFrame)
           cv2.waitKey(1)

    def __init__(self):
        self.Generate()

if __name__ == '__main__':

    obj = RgbCalculator()
    pass
import sys
import os
import cv2 as cv

# ---- Useful functions ----

def init_video(video_file):
    """
    Given the name of the video, prepares the stream and checks that everything works as attended
    """
    capture = cv.VideoCapture(video_file)
    if(capture.isOpened()):
        nFrames = int(capture.get(cv.CAP_PROP_FRAME_COUNT))
        fps = capture.get(cv.CAP_PROP_FPS )
        if fps != 0:
            waitPerFrameInMillisec = int( 1/fps * 1000/1 )

            print ('Num. Frames = '+ str(nFrames))
            print ('Frame Rate = '+ str(fps) + ' frames per sec')
            print ('----')
        
            return capture
        else:
            return None

    return None

def display_img(img, delay=1000):
    """
    One liner that displays the given image on screen
    """
    cv.namedWindow("Vid", cv.WINDOW_AUTOSIZE)
    cv.imshow("Vid", img)
    cv.waitKey(0)

def display_video(my_video, frame_inc=100, delay=100):
    """
    Displays frames of the video in a dumb way.
    Used to see if everything is working fine
    my_video = cvCapture object
    frame_inc = Nmber of increments between each frame displayed
    delay = time delay between each image 
    """
    cpt = 0    
    ret, img = my_video.read()

    nFrames = int(  cv.VideoCapture.get( my_video, cv.CAP_PROP_FRAME_COUNT ) )
    while cpt < nFrames:
        for ii in range(frame_inc):
            ret, img = my_video.read()
            cpt + 1
            
        cv.imshow("Vid", img)
        cv.waitKey(delay)

def grab_images(video_file, frame_inc=100, delay = 100):
    """
    Walks through the entire video and save image for each increment
    """
    my_video = init_video(video_file)
    if my_video != None:
        # Display the video and save evry increment frames
        cpt = 0  
        ret, img = my_video.read()
    
        if ret == True:
           cv.namedWindow("Vid", cv.WINDOW_AUTOSIZE)
        else:
            return None
    
        nFrames = int(my_video.get(cv.CAP_PROP_FRAME_COUNT ) )
        while cpt < nFrames:
            for ii in range(frame_inc):
                ret, img = my_video.read()
                cpt += 1
            if ret == True:    
                cv.imshow("Vid", img)
                out_name = "./data/output/" + str(cpt) + ".jpg"
                cv.imwrite(out_name, img)
                print (out_name + ' ' + str(nFrames))
                cv.waitKey(delay)
    else: 
        return None

def to_gray(img):
    """
    Converts the input in grey levels
    Returns a one channel image
    """
    grey_img = cv.CreateImage(cv.GetSize(img), img.depth, 1)
    cv.CvtColor(img, grey_img, cv.CV_RGB2GRAY )
    
    return grey_img   
    
def grey_histogram(img, nBins=64):
    """
    Returns a one dimension histogram for the given image
    The image is expected to have one channel, 8 bits depth
    nBins can be defined between 1 and 255 
    """
    hist_size = [nBins]
    h_ranges = [0, 255]
   
    #hist = cv.CreateHist(hist_size , cv.HIST_ARRAY, [[0, 255]], 1)

    hist = cv.calcHist([img], [0], None, hist_size, h_ranges,1)

    return hist

def extract_bright(grey_img, histogram=False):
    """
    Extracts brightest part of the image.
    Expected to be the LEDs (provided that there is a dark background)
    Returns a Thresholded image
    histgram defines if we use the hist calculation to find the best margin
    """
    ## Searches for image maximum (brightest pixel)
    # We expect the LEDs to be brighter than the rest of the image
    [minVal, maxVal, minLoc, maxLoc] = cv.minMaxLoc(grey_img)
    print ("Brightest pixel val is %d" %(maxVal))
    
    #We retrieve only the brightest part of the image
    # Here is use a fixed margin (80%), but you can use hist to enhance this one    
    if False:
        ## Histogram may be used to wisely define the margin
        # We expect a huge spike corresponding to the mean of the background
        # and another smaller spike of bright values (the LEDs)
        hist = grey_histogram(grey_img, nBins=64)
        
        [hminValue, hmaxValue, hminIdx, hmaxIdx] = cv.minMaxLoc(hist) 
        margin = 0# statistics to be calculated using hist data    
    else:  
        margin = 0.8
        
    thresh = int( maxVal * margin) # in pix value to be extracted
    print ("Threshold is defined as %d" %(thresh))
    
    #thresh_img = cv.CreateImage(cv.GetSize(img), img.depth, 1)
    ret, thresh_img = cv.threshold(grey_img, thresh, 255, cv.THRESH_BINARY)
    
    return thresh_img

def find_leds(thresh_img):

    roi_copy = thresh_img.copy()
    cnts, hierarchy = cv.findContours(thresh_img.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    cnts = sorted(cnts, key = cv.contourArea, reverse = True)[:6] # get largest five contour area
    rects = []
    for c in cnts:
        peri = cv.arcLength(c, True)
        approx = cv.approxPolyDP(c, 0.02 * peri, True)
        x, y, w, h = cv.boundingRect(approx)
        #if h >= 15:
            # if height is enough
            # create rectangle for bounding
        rect = (x, y, w, h)
        rects.append(rect)
        cv.rectangle(roi_copy, (x, y), (x+w, y+h), (0, 255, 0), 1);

    return (roi_copy, rects) 


  #  """
  #  Given a binary image showing the brightest pixels in an image, 
  #  returns a result image, displaying found leds in a rectangle
  #  """
  #  contours,_ = cv.findContours(thresh_img.copy(),
  #                             mode=cv.RETR_EXTERNAL , 
  #                             method=cv.CHAIN_APPROX_NONE , 
  #                             offset=(0, 0))
  #  # Cycle through contours and add area to array
  #  areas = []
  #  for c in contours:
  #      areas.append(cv.contourArea(c))
    
  #  sorted_areas = sorted(zip(areas, contours), key=lambda x: x[0], reverse=True)
    
  #  if sorted_areas and len(sorted_areas) >= 2:
		## Find nth largest using data[n-1][1]
  #      return sorted_areas[n - 1][1]
  #  else:
  #      return None 

  #  regions = []
  #  while contours:
  #      pts = [ pt for pt in contours ]
  #      zipped = list(zip(*pts) )
  #      x = zipped[0]
  #      y = zipped[1]
  #      min_x, min_y = min(x), min(y)
  #      width, height = max(x) - min_x + 1, max(y) - min_y + 1
  #      regions.append((min_x, min_y, width, height))
  #      contours = contours.h_next()

  #      out_img = cv.CreateImage(cv.GetSize(grey_img), 8, 3)
  #  for x,y,width,height in regions:
  #      pt1 = x,y
  #      pt2 = x+width,y+height
  #      color = (0,0,255,0)
  #      cv.Rectangle(out_img, pt1, pt2, color, 2)

  #  return out_img, regions

def leds_positions(regions):
    """
    Function using the regions in input to calculate the position of found leds
    """
    centers = []
    for x, y, width, height in regions:
        centers.append( [x+ (width / 2),y + (height / 2)])

    return centers


if __name__ == '__main__':
    video_file =  "./data/MusicLEDBox.mp4"
    print (cv.__version__)
    
    # do once once, create some images out of the video
  #  grab_images(video_file, frame_inc=100, delay = 100)
        
    
    img = cv.imread("./data/output/600.jpg")
    if img.size > 0:
        # Displays the image I ll be working with
        display_img(img, delay = 1000)
    else:
        print ("IMG not found !")
        sys.exit(0)

    ####
    # Starts image processing here 
    ####
    # Turns to one channel image
    #grey_img = to_gray(img)
    path = './data/output/'
    for f in os.listdir(path):
        print (f)
        if f.endswith('.jpg') or f.endswith('.JPG'):
            grey_img = cv.imread(path + f, 0)
            #display_img(grey_img, 1) 
            # Detect brightest point in image :
            thresh_img = extract_bright(grey_img)
            display_img(thresh_img, delay = 1000)

            # We want to extract the elements left, and count their number
            led_img, regions = find_leds(thresh_img)
            display_img(led_img, delay=1000)

            centers = leds_positions(regions)

            print ("Total number of Leds found : %d !" %(len(centers)))
            print ("###")
            print ("Led positions :")
            for c in centers:
                print ("x : %d; y : %d" %(c[0], c[1]))
            print ("###")
    

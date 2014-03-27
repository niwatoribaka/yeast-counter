'''
prepare_dp.py contains methods necessary to automatically prepare
a data point for use with yeast.py.  A simple GUI for selecting 
the data point directory is included.

The strategy for preparing a data point is as follows:
    store a backup
    remove EXIF metadata
    crop the images
    rotate the images
'''

import cv2
import os
import wx
import shutil
import numpy as np
from matplotlib import pyplot as plt  # @UnusedImport
from gi.repository import GExiv2  # @UnresolvedImport
from GUI.prepare_dp_wizard import wizard as prepare_dp_wizard

class PrepareWizard(prepare_dp_wizard):
    '''
    Overrides the methods from the FormBuilder generated file.
    '''
    def user_exit(self, event):
        exit()
    def set_dir(self, event):
        global RAW_DP_FOLDER
        RAW_DP_FOLDER = self.dir_picker.GetPath()

def rotate_image(image, angle):
    '''
    returns image rotated by angle degrees.
    '''
    image_center = tuple(np.array(image.shape) / 2)
    if len(image_center) > 2:
        image_center = image_center[:2]
    rot_mat = cv2.getRotationMatrix2D(image_center, angle, 1.)
    result = cv2.warpAffine(image, rot_mat, image.shape[:2], flags=cv2.INTER_LINEAR)
    return result

def auto_crop(image, sig_brightness):
    '''
    Pans across image from each direction until significant 
    brightness is detected (i.e. light from the lens of the microscope).
    Crops at the location of significant brigtness detected.
    check_ratio determines how much of the image to pan over.
    The inverse of check_ratio is the fraction of the image
    that is panned in each direction.
    '''
    img_HSV = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    BIG_NUMBER = 2 ** 32 - 1
    left = BIG_NUMBER
    right = BIG_NUMBER
    top = BIG_NUMBER
    bottom = BIG_NUMBER
    
    check_ratio = 2

    for y in range(len(img_HSV)):
        for x in range(len(img_HSV[y]))[:len(img_HSV[y]) / check_ratio]:
            if img_HSV[y, x][-1] > sig_brightness:
                if x < left:
                    left = x
                break
    img_HSV = img_HSV[:, left:]
    image = image[:, left:]
    
    for y in range(len(img_HSV)):
        for x in range(len(img_HSV[y]))[:len(img_HSV[y]) / check_ratio]:
            if img_HSV[y, len(img_HSV[y]) - 1 - x][-1] > sig_brightness:
                if x < right:
                    right = x
                break
    right = len(img_HSV[0]) - 1 - right
    img_HSV = img_HSV[:, :right]
    image = image[:, :right]
    
    for y in range(len(img_HSV))[:len(img_HSV) / check_ratio]:
        for x in range(len(img_HSV[y])):
            if img_HSV[y, x][-1] > sig_brightness:
                if y < top:
                    top = y 
                break
    img_HSV = img_HSV[top:, :]
    image = image[top:, :]
    
    for y in range(len(img_HSV))[:len(img_HSV) / check_ratio]:
        for x in range(len(img_HSV[y])):
            if img_HSV[len(img_HSV) - 1 - y, x][-1] > sig_brightness:
                if y < bottom:
                    bottom = y 
                break
    bottom = len(img_HSV) - 1 - bottom
    img_HSV = img_HSV[:bottom, :]
    image = image[:bottom, :]
    return image

def auto_rotate(image, sampling_factor=1.):
    '''
    Performs Canny edge detection on the image and then 
    shrinks the edge mask.  The edge mask is then rotated
    sampling_factor * 180 times.  After each rotation,
    A vector containing the sum of each row of the image is
    stored.  The ideology is that the angle that produces
    a maximum value in this vector must be the horizontal
    channel orientation, because when the channel is
    oriented horizontally, the sum of the rows in the edge
    mask will be maximized.  image is then rotated by
    the calculated angle and returned.
    '''
    edges = cv2.Canny(image, 50, 150)
    small = cv2.resize(edges, (0, 0), fx=0.2, fy=0.2)
    small = cv2.medianBlur(small, 5)
    
    pushed_max = []
    for i in range(0, int(180 * sampling_factor)):
        rot_edges = rotate_image(small, i / sampling_factor)
        pushed = [sum(y) for y in rot_edges]
        pushed_max.append(max(pushed))
    
    pushed_max = smooth(pushed_max, 2)
    
    angle = pushed_max.index(max(pushed_max)) / sampling_factor
    image = rotate_image(image, angle)
    return image
    
def smooth(data, iterations=1, _side=-1):
    '''
    Novel recursive algorithm for smoothing peaks from noisy data.
    
    data[i] trends to data[j] as iterations -> inf. ; i,j in [0,len(data)]
    '''
    if iterations == 0:
        return data
    for i in range(len(data)):
        if not (i == 0 or i == len(data) - 1):
            if data[i] > data[i - 1] and data[i] < data[i + 1]:
                pass
            elif data[i] < data[i - 1] and data[i] > data[i + 1]:
                pass
            else:
                data[i] = data[i + _side]
    return smooth(data, iterations - 1, _side * -1)

def auto_prepare(RAW_DP_FOLDER):
    '''
    Takes a data point and backs its images up to a 'bak' folder.
    Removes EXIF metadata and performs auto_crop and
    auto_rotate on all of the images.
    '''
    try:
        os.mkdir('{0}/bak'.format(RAW_DP_FOLDER))
    except:
        pass
    for fname in sorted([f for f in os.listdir(RAW_DP_FOLDER) if os.path.isfile('{0}/{1}'.format(RAW_DP_FOLDER,f))]):
        try:
            shutil.copy2('{0}/{1}'.format(RAW_DP_FOLDER,fname),
                     '{0}/bak/{1}'.format(RAW_DP_FOLDER,fname))
        except:
            pass
        
        print '{0} :'.format(fname)
        
        path = '{0}/{1}'.format(RAW_DP_FOLDER, fname)
        
        print '\tClearing EXIF metadata'
        exif = GExiv2.Metadata(path)
        exif.clear_exif()
        exif.clear_xmp()
        exif.save_file()
        
        img = cv2.imread(path)
        
        print '\tCropping'
        img = auto_crop(img, 60)
        print '\tRotating'
        img = auto_rotate(img, 2.)
        
#         cv2.namedWindow('rotated', cv2.WINDOW_NORMAL)
#         cv2.resizeWindow('rotated', 800, 600)
#         cv2.startWindowThread()
#         cv2.imshow('rotated', img)
#         cv2.waitKey()
#         cv2.destroyAllWindows()

        cv2.imwrite(path, img)

'''
prepare_dp.py is typically called by yeast.py, but a simple
GUI for selecting an unprepared data point will open if
prepare_dp.py is called directly.
'''
if __name__ == '__main__':
    RAW_DP_FOLDER = None
    
    app = wx.App(False)
    wiz = PrepareWizard(None)
    wiz.RunWizard(wiz.m_pages[0])
    wiz.Destroy()
    app.MainLoop()
    
    auto_prepare(RAW_DP_FOLDER)

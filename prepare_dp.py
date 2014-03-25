import cv2
import os
import wx
import numpy as np
from matplotlib import pyplot as plt
from gi.repository import GExiv2
from GUI.prepare_dp_wizard import wizard as prepare_dp_wizard

class PrepareWizard(prepare_dp_wizard):
    def user_exit(self, event):
        exit()
    def set_dir(self, event):
        global RAW_DP_FOLDER
        RAW_DP_FOLDER = self.dir_picker.GetPath()

def rotate_image(image, angle):
    image_center = tuple(np.array(image.shape) / 2)
    if len(image_center) > 2:
        image_center = image_center[:2]
    rot_mat = cv2.getRotationMatrix2D(image_center, angle, 1.)
    result = cv2.warpAffine(image, rot_mat, image.shape[:2], flags=cv2.INTER_LINEAR)
    return result

def auto_crop(image, sig_brightness):
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
    for fname in sorted(os.listdir(RAW_DP_FOLDER)):
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
        
if __name__ == '__main__':
    RAW_DP_FOLDER = None
    
    app = wx.App(False)
    wiz = PrepareWizard(None)
    wiz.RunWizard(wiz.m_pages[0])
    wiz.Destroy()
    app.MainLoop()
    
    auto_prepare(RAW_DP_FOLDER)

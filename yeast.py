import cv2
import wx
import os
import sys
import commands
from matplotlib import pyplot as plt
from pylab import *
from GUI.settings_wizard import wizard as settings_wizard
from prepare_dp import auto_prepare

# Testing mode should be used with data points generated by
# generate_test.py
TESTING = None

# MODE list
# 0 -> custom normalized value method
# 1 -> harris corner detection
MODE = None

UNITS = 'cm'
HEIGHTS = [20, 30, 40, 50]  # from lab 3 (low-flush + 3 heights)
# HEIGHTS = [20, 35, 40, 45, 50] #experiment (low-flush + 4 heights)

DP_FOLDER = None
PREPARE_FIRST = None

class SettingsWizard(settings_wizard):
    def user_exit(self, event):
        exit()
    def start_processing(self, event):
        global TESTING, MODE, DP_FOLDER, PREPARE_FIRST
        TESTING = self.select_testing.GetValue()
        mode = self.select_mode.GetStringSelection()
        if mode.__contains__('HSV'):
            MODE = 0
        elif mode.__contains__('Harris'):
            MODE = 1
        DP_FOLDER = self.dp_picker.GetPath()
        PREPARE_FIRST = self.select_prepare.GetValue()


class DataPoint():
    def __init__(self, dp_path):
        global TESTING, MODE
        if TESTING:
            print 'TESTING MODE IS ON'
        print 'MODE IS {0}'.format(MODE)

        self.dp_path = dp_path
        self.img_names = sort([f for f in os.listdir(dp_path) if os.path.isfile('{0}/{1}'.format(dp_path,f))])

        if not TESTING:
            assert len(HEIGHTS) == len(self.img_names)

        self.imgs = [cv2.imread('{0}/{1}'.format(dp_path, fname)) for fname in self.img_names]
        self.user_params = {i:
                {
                    'testing_region':['ix', 'iy', 'x', 'y'],
                    }
                for i in range(len(self.imgs))
                }
        if MODE == 0:
            self.working_imgs = [cv2.cvtColor(img, cv2.COLOR_BGR2HSV) \
                    for img in self.imgs]
        elif MODE == 1:
            self.working_imgs = [cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype('float32') \
                                 for img in self.imgs]
        self.average_value = [0. for img in range(len(self.img_names))]
        self.yeast_count = [0. for img in range(len(self.img_names))]
        print 'Setting params'
        self.set_user_params()
        print 'Cropping'
        self.crop_working(0, 200)

        if MODE == 0:
            self.pixel_method()
        elif MODE == 1:
            self.harris_method()
    def pixel_method(self):
        print 'Filtering borders'
        self.filter()
        print 'Normalizing'
        self.normalize_V()
        print 'Calculating averages'
        self.average_V()
        print 'Plotting'
        self.plot()
    def harris_method(self):
        print 'Setting thresholds'
        self.set_threshold()
        print 'Counting yeast'
        self.count_yeast()
        print 'Plotting'
        self.plot()


    def normalize_V(self):
        '''Normalizes each HSV image against its particular background.
        The background is whatever was within the crop buffer but outside
        the testing region.

        Modifies self.working_imgs'''
        for i in range(len(self.working_imgs)):
            region = self.user_params[i]['testing_region']
            self.working_imgs[i] = self.working_imgs[i].astype(float)
            top_background_values = self.working_imgs[i][:, :, 2][0:region[1], :].flatten()
            bottom_background_values = self.working_imgs[i][:, :, 2][region[3]:-1, :].flatten()
            left_background_values = self.working_imgs[i][:, :, 2][:, 0:region[0]].flatten()
            right_background_values = self.working_imgs[i][:, :, 2][:, region[2]:-1].flatten()
            flat_background = concatenate((
                          top_background_values,
                          bottom_background_values,
                          left_background_values,
                          right_background_values,
                          ))
            repr_background = average(flat_background)
            self.working_imgs[i][:, :, 2] /= repr_background
    def suggest_lowpass_threshold(self):
        pass
    def filter(self):
        '''Filters out very dark regions of the cropped HSVs.

        The target of this filter is to remove the effect of the channel
        border and miscellaneous garbage in between the chip top and bottom
        when calculating the average value for the testing region.'''
        # TODO -> set darkness_threshold to value suggested by
        # self.suggest_lowpass_threshold()
        # perhaps each image should have a separate darkness_threshold?
        darkness_threshold = .8 * 255
        print 'Low-pass filter set at: {0}'.format(darkness_threshold)
        for i in range(len(self.working_imgs)):
            print 'Min Intensity for image {0}:   {1}'.format(i, min([min(col) for col in self.working_imgs[i][:, :, 2]]))
            for x in range(len(self.working_imgs[i][:, :, 2])):
                for y in range(len(self.working_imgs[i][:, :, 2][x])):
                    if self.working_imgs[i][:, :, 2][x][y] < darkness_threshold:
                        self.working_imgs[i][:, :, 2][x][y] = 1.
    def average_V(self):
        '''Stores the average value in the testing region in self.average_value'''
        for i in range(len(self.img_names)):
            region = self.user_params[i]['testing_region']
            cropped = self.working_imgs[i][region[1]:region[3], region[0]:region[2]]
            cropped = cropped[:, :, 2]
            self.average_value[i] = sum([sum(row) for row in cropped]) / float(cropped.size)


    def set_threshold(self):
        global TESTING

        self.threshold = [0. for i in range(len(self.imgs))]
        self.dst = [cv2.cornerHarris(img, 2, 1, .04) for img in self.working_imgs]
        self.dst = [cv2.dilate(img, None) for img in self.dst]

        if sys.platform.startswith('win'):
            import ctypes
            user32 = ctypes.windll.user32
            screen_res = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
        else:
            status, output = commands.getstatusoutput("xrandr | grep '*'")
            if not status:
                screen_res = tuple(
                                   [int(dim) for dim in \
                                   [
                                    part for part in output.split('\n')[-1].split(' ') if part][0].split('x')
                                    ]
                                   )
            else:
                screen_res = 800, 600
        
        scale_width = screen_res[0] / float(img.shape[1])
        scale_height = screen_res[1] / float(img.shape[0])
        scale = min(scale_width, scale_height)
        window_width = int(img.shape[1] * scale)
        window_height = int(img.shape[0] * scale)

        for i in range(len(self.working_imgs)):
            if TESTING and i != 0:
                self.threshold[i] = self.threshold[i - 1]
                continue
            cv2.namedWindow(self.img_names[i], cv2.WINDOW_NORMAL)
            cv2.resizeWindow(self.img_names[i], window_width, window_height)
            cv2.createTrackbar('threshold', self.img_names[i], 0, 260, lambda new: None)
            cv2.startWindowThread()

            while True:
                drawn_over = self.imgs[i].__copy__()
                drawn_over[self.dst[i] > cv2.getTrackbarPos('threshold', self.img_names[i]) \
                            * self.dst[i].max() / 1000.] = [0, 0, 255]
                cv2.imshow(self.img_names[i], drawn_over)
                k = cv2.waitKey(40)
                if k == 27:
                    print 'User Interrupt: exiting'
                    exit()
                elif k != -1:
                    self.threshold[i] = cv2.getTrackbarPos('threshold', self.img_names[i]) \
                                        * self.dst[i].max() / 1000.
                    break
            cv2.destroyWindow(self.img_names[i])
            cv2.waitKey(1)
    def count_yeast(self):
        for i in range(len(self.imgs)):
            mask = self.dst[i] > self.threshold[i]
            self.yeast_count[i] = float(sum(mask)) / len(mask)


    def printdir(self):
        '''Prints the content of the data point folder'''
        print '{0}:'.format(self.dp_path)
        for fname in self.img_names:
            print '\t{0}'.format(fname)
    def set_user_params(self):
        '''Is responsible for displaying each image of the data point folder.

        Works with self.paramsUI to gather input from the user'''
        self.stage = 0
        global TESTING
        for i in range(len(self.imgs)):
            if TESTING and i != 0:
                self.user_params[i]['testing_region'] = self.user_params[0]['testing_region']
            else:
                self.i = i
                self.drawing_overlay = self.imgs[i].__copy__()

                if sys.platform.startswith('win'):
                    import ctypes
                    user32 = ctypes.windll.user32
                    screen_res = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
                else:
                    status, output = commands.getstatusoutput("xrandr | grep '*'")
                    if not status:
                        screen_res = tuple(
                                           [int(dim) for dim in \
                                           [
                                            part for part in output.split('\n')[-1].split(' ') if part][0].split('x')
                                            ]
                                           )
                    else:
                        screen_res = 800, 600

                scale_width = screen_res[0] / float(self.imgs[i].shape[1])
                scale_height = screen_res[1] / float(self.imgs[i].shape[0])
                scale = min(scale_width, scale_height)
                window_width = int(self.imgs[i].shape[1] * scale)
                window_height = int(self.imgs[i].shape[0] * scale)

                cv2.namedWindow(self.img_names[i], cv2.WINDOW_NORMAL)
                cv2.startWindowThread()
                cv2.resizeWindow(self.img_names[i], window_width, window_height)

                self.ix, self.iy = -1, -1
                if i == 0:
                    cv2.putText(self.drawing_overlay, 'Select testing region', (20, 100), \
                            cv2.FONT_HERSHEY_COMPLEX, 2, (255, 255, 0), 5)
                else:
                    cv2.putText(self.drawing_overlay, 'Place testing region', (20, 100), \
                            cv2.FONT_HERSHEY_COMPLEX, 2, (255, 255, 0), 5)
                cv2.setMouseCallback(self.img_names[i], self.paramsUI)
                cv2.imshow(self.img_names[i], self.drawing_overlay)
                while True:
                    k = cv2.waitKey(5)
                    if k == 27:
                        print 'User Interrupt: exiting'
                        exit()
                    elif k == ord('n'):
                        self.stage = 0
                        cv2.destroyWindow(self.img_names[i])
                        cv2.waitKey(1)
                        break
    def paramsUI(self, event, x, y, flags, param):
        '''Modifies self.drawing_overlay in response to user input

        Sets the testing region with respect to the unaltered image'''
        if not self.stage and not self.i:
            if event == cv2.EVENT_LBUTTONDOWN:
                self.ix, self.iy = x, y
            elif event == cv2.EVENT_LBUTTONUP:
                self.user_params[self.i]['testing_region'] = [self.ix, self.iy, x, y]
                cv2.rectangle(self.drawing_overlay, (self.ix, self.iy), (x, y), (0, 255, 0), 3)
                cv2.putText(self.drawing_overlay, "Press 'n' to continue", (20, 190), \
                        cv2.FONT_HERSHEY_COMPLEX, 2, (255, 255, 0), 5)
                self.stage = 1
                cv2.imshow(self.img_names[self.i], self.drawing_overlay)
        elif not self.stage:
            if event == cv2.EVENT_LBUTTONDOWN:
                testing_region = self.user_params[0]['testing_region']
                w = testing_region[2] - testing_region[0]
                h = testing_region[3] - testing_region[1]
                self.user_params[self.i]['testing_region'] = [x, y, x + w, y + h]
                cv2.rectangle(self.drawing_overlay,
                        (x, y), (x + w, y + h),
                        (0, 255, 0), 3)
                cv2.putText(self.drawing_overlay, "Press 'n' to continue", (20, 190), \
                        cv2.FONT_HERSHEY_COMPLEX, 2, (255, 255, 0), 5)
                self.stage = 1
                cv2.imshow(self.img_names[self.i], self.drawing_overlay)
    def crop_working(self, x_cropbuff, y_cropbuff):
        '''Crops the working images to the testing region.

        The x and y crop buffers allow for other functions in self
        to have a background region to normalize to.

        Modifies self.working_imgs and self.user_params -> 'testing_region'.'''
        for i in range(len(self.working_imgs)):
            region = self.user_params[i]['testing_region']
            self.working_imgs[i] = self.working_imgs[i][region[1] - y_cropbuff:region[3] + y_cropbuff,
                    region[0] - x_cropbuff:region[2] + x_cropbuff]
            self.imgs[i] = self.imgs[i][region[1] - y_cropbuff:region[3] + y_cropbuff,
                    region[0] - x_cropbuff:region[2] + x_cropbuff]
            self.user_params[i]['testing_region'] = [x_cropbuff, y_cropbuff,
                    x_cropbuff + region[2] - region[0], y_cropbuff + region[3] - region[1]]
    def prepare_data(self):
        '''Uses self.average_value to construct self.coverage
        Also calculates self.significant_shear_height and self.x_significant_shear

        self.coverage[0] = 1, self.coverage[-1] = 0'''
        if MODE == 0:
            self.data = self.average_value
        elif MODE == 1:
            self.data = self.yeast_count
        norm = self.data[-1]
        self.data = [entry / norm for entry in self.data]
        self.data = [1 - v for v in self.data]
        norm = self.data[0]
        self.data = [entry / norm for entry in self.data]

        left_bound = 0
        for i in range(len(self.data)):
            if self.data[i] < .25:
                break
            left_bound = i
        self.x_significant_shear = (.25 - self.data[left_bound]) * \
                                (1. / (self.data[left_bound + 1] - self.data[left_bound])) + left_bound
        global HEIGHTS
        self.significant_shear_height = HEIGHTS[0] + (HEIGHTS[-1] - HEIGHTS[0]) \
                                        * (self.x_significant_shear + 1) / \
                                        (((HEIGHTS[-1] - HEIGHTS[0]) / (HEIGHTS[-1] - HEIGHTS[-2])) + 1)
    def plot(self):
        global TESTING, UNITS
        '''Prepares the data using self.prepare_data and then
        graphs the data on a plot.'''
        self.prepare_data()

        plt.plot(range(len(self.data)), self.data)
        plt.hlines(.25, 0, len(self.data))
        plt.vlines(self.x_significant_shear, -1, 2)
        print 'Significant shear at image {0}'.format(self.x_significant_shear)
        if not TESTING:
            print 'Theoretical significant shear at height {0} {1}'.format(self.significant_shear_height, UNITS)

        plt.ylim([-1, 2])
        plt.xlabel('Image')
        plt.ylabel('Coverage')
        plt.title(self.dp_path.split('/')[-1])
        plt.show()

app = wx.App(False)
wiz = SettingsWizard(None)
wiz.RunWizard(wiz.m_pages[0])
wiz.Destroy()
app.MainLoop()

if PREPARE_FIRST:
    auto_prepare(DP_FOLDER)
dp = DataPoint(DP_FOLDER)


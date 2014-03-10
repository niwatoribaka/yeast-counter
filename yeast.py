import cv2
import os
import sys
import commands
from matplotlib import pyplot as plt
from pylab import *

#TODO -> Add new mode that operates on SURF feature (corner) detection
#     -> Threshold can be adjusted with slider (until corners in testing
#     -> region disappear).
#TODO -> Auto-rotation
#TODO -> Auto-crop to lens view after rotation
#TODO -> Location of significant shear calculation
#TODO -> Seperation of DataPoint.__init__ from calculation
#TODO -> Concurrent (threaded) image processing

#Testing mode should be used with data points generated by
#generate_test.py
TESTING = True
MODE = 1 #1 for pixel, 0 for SURF

class DataPoint():
    def __init__(self, dp_path):
        global TESTING, MODE
        if TESTING:
            print 'TESTING MODE IS ON'
        self.dp_path = dp_path
        self.img_names = sort(os.listdir(dp_path))
        self.imgs = [cv2.imread('{0}/{1}'.format(dp_path, fname)) \
                for fname in self.img_names]
        self.user_params = {i:
                {
                    'testing_region':['ix', 'iy', 'x', 'y'],
                    }
                for i in range(len(self.imgs))
                }
        self.HSVs = [cv2.cvtColor(img, cv2.COLOR_BGR2HSV) \
                for img in self.imgs]
        self.average_value = [0. for img in range(len(self.img_names))]
        print 'Setting params'
        self.set_user_params()
        print 'Cropping'
        self.crop_HSVs(0, 200)
        if MODE:
            self.pixel_method()
        else:
            pass
    def pixel_method(self):
        print 'Filtering borders'
        self.filter()
        print 'Normalizing'
        self.normalize_V()
        print 'Calculating averages'
        self.average_V()
        print 'Plotting'
        self.plot()
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
                                            part for part in output.split(' ') if part][0].split('x')
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
                        cv2.destroyAllWindows()
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
    def crop_HSVs(self, x_cropbuff, y_cropbuff):
        '''Crops the HSV images to the testing region.

        The x and y crop buffers allow for other functions in self
        to have a background region to normalize to.

        Modifies self.HSVs and self.user_params -> 'testing_region'.'''
        for i in range(len(self.HSVs)):
            region = self.user_params[i]['testing_region']
            self.HSVs[i] = self.HSVs[i][region[1] - y_cropbuff:region[3] + y_cropbuff,
                    region[0] - x_cropbuff:region[2] + x_cropbuff]
            self.user_params[i]['testing_region'] = [x_cropbuff, y_cropbuff,
                    x_cropbuff + region[2] - region[0], y_cropbuff + region[3] - region[1]]
    def normalize_V(self):
        '''Normalizes each HSV image against its particular background.
        The background is whatever was within the crop buffer but outside
        the testing region.

        Modifies self.HSVs'''
        for i in range(len(self.HSVs)):
            region = self.user_params[i]['testing_region']
            self.HSVs[i] = self.HSVs[i].astype(float)
            top_background_values = self.HSVs[i][:, :, 2][0:region[1], :].flatten()
            bottom_background_values = self.HSVs[i][:, :, 2][region[3]:-1, :].flatten()
            left_background_values = self.HSVs[i][:, :, 2][:, 0:region[0]].flatten()
            right_background_values = self.HSVs[i][:, :, 2][:, region[2]:-1].flatten()
            flat_background = concatenate((
                          top_background_values,
                          bottom_background_values,
                          left_background_values,
                          right_background_values,
                          ))
            repr_background = average(flat_background)
            self.HSVs[i][:, :, 2] /= repr_background
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
        for i in range(len(self.HSVs)):
            print 'Min Intensity for image {0}:   {1}'.format(i, min([min(col) for col in self.HSVs[i][:, :, 2]]))
            for x in range(len(self.HSVs[i][:, :, 2])):
                for y in range(len(self.HSVs[i][:, :, 2][x])):
                    if self.HSVs[i][:, :, 2][x][y] < darkness_threshold:
                        self.HSVs[i][:, :, 2][x][y] = 1.
    def average_V(self):
        '''Stores the average value in the testing region in self.average_value'''
        for i in range(len(self.img_names)):
            region = self.user_params[i]['testing_region']
            cropped = self.HSVs[i][region[1]:region[3], region[0]:region[2]]
            cropped = cropped[:, :, 2]
            self.average_value[i] = sum([sum(row) for row in cropped]) / float(cropped.size)
    def prepare_data(self):
        '''Uses self.average_value to construct self.coverage

        self.coverage[0] = 1, self.coverage[-1] = 0'''
        norm = self.average_value[-1]
        self.average_value = [entry / norm for entry in self.average_value]
        self.coverage = [1 - v for v in self.average_value]
        norm = self.coverage[0]
        self.coverage = [entry / norm for entry in self.coverage]
    def plot(self):
        '''Prepares the data using self.prepare_data and then
        graphs the data on a plot.'''
        self.prepare_data()

        fig = plt.figure(figsize=figaspect(1.))

        p = fig.add_subplot(111)
        p.grid(True)
        p.plot(range(len(self.coverage)), self.coverage)
        # p.set_ylim(-1,2)
        p.set_xlabel('Image')
        p.set_ylabel('Coverage')

        plt.show()

dp_folders = sort([thing for thing in os.listdir(os.getcwd()) \
        if os.path.isdir(thing)])

if len(dp_folders) == 0:
    print 'There are no data points in the working directory'
    print 'Exiting'
    exit()

print 'Select a data point folder'
for i in range(len(dp_folders)):
    print '({0})   {1}'.format(i, dp_folders[i])

choice = -1
while choice < 0 or choice >= len(dp_folders):
    try:
        choice = int(raw_input('\nChoice? '))
    except:
        pass

print '\n'

dp = DataPoint(dp_folders[choice])

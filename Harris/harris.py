import cv2
from numpy import array, float32

img = cv2.imread('haystack.jpg')
img = cv2.imread('../dp2/02.JPG')
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype('float32')

dst = cv2.cornerHarris(gray, 2, 1, .04)

dst = cv2.dilate(dst, None)

screen_res = 800, 600
scale_width = screen_res[0] / float(img.shape[1])
scale_height = screen_res[1] / float(img.shape[0])
scale = min(scale_width, scale_height)
window_width = int(img.shape[1] * scale)
window_height = int(img.shape[0] * scale)
cv2.namedWindow('dst', cv2.WINDOW_NORMAL)
cv2.resizeWindow('dst', window_width, window_height)
cv2.createTrackbar('threshold', 'dst', 0, 260, lambda new: None)

while True:
    drawn_over = img.__copy__()
    drawn_over[dst > cv2.getTrackbarPos('threshold', 'dst') \
                * dst.max() / 1000.] = [0, 0, 255]
    cv2.imshow('dst', drawn_over)
    k = cv2.waitKey(2)
    if k != -1: break
cv2.destroyAllWindows()

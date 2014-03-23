import cv2
import numpy as np
from matplotlib import pyplot as plt

MAX_INT = 2 ** 32 - 1

def rotate_image(image, angle):
    image_center = tuple(np.array(image.shape) / 2)
    rot_mat = cv2.getRotationMatrix2D(image_center[:-1], angle, 1.)
    result = cv2.warpAffine(image, rot_mat, image.shape[:-1], flags=cv2.INTER_LINEAR)
    return result

def auto_crop(image, sig_brightness):
    img_HSV = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    left = MAX_INT
    right = MAX_INT
    top = MAX_INT
    bottom = MAX_INT

    for y in range(len(img_HSV)):
        for x in range(len(img_HSV[y])):
            if img_HSV[y, x][-1] > sig_brightness:
                if x < left:
                    left = x
                break
    img_HSV = img_HSV[:, left:]
    image = image[:, left:]
    
    for y in range(len(img_HSV)):
        for x in range(len(img_HSV[y])):
            if img_HSV[y, len(img_HSV[y]) - 1 - x][-1] > sig_brightness:
                if x < right:
                    right = x
                break
    right = len(img_HSV[0]) - 1 - right
    img_HSV = img_HSV[:, :right]
    image = image[:, :right]
    
    for y in range(len(img_HSV)):
        for x in range(len(img_HSV[y])):
            if img_HSV[y, x][-1] > sig_brightness:
                if y < top:
                    top = y 
                break
    img_HSV = img_HSV[top:, :]
    image = image[top:, :]
    
    for y in range(len(img_HSV)):
        for x in range(len(img_HSV[y])):
            if img_HSV[len(img_HSV) - 1 - y, x][-1] > sig_brightness:
                if y < bottom:
                    bottom = y 
                break
    bottom = len(img_HSV) - 1 - bottom
    img_HSV = img_HSV[:bottom, :]
    image = image[:bottom, :]
    return image

def angle_slice(image,angle):
    image_center = tuple(np.array(image.shape)/2)[:-1]

img = cv2.imread('DPs/raw dp3/photo 1.JPG')
img = auto_crop(img, 60)

edges = cv2.Canny(img, 400, 100)

# plt.subplot(121),plt.imshow(img,cmap='gray')
# plt.title('Original'),plt.xticks([]),plt.yticks([])
plt.subplot(111), plt.imshow(edges, cmap='gray')
plt.title('Edges'), plt.xticks([]), plt.yticks([])

plt.show()

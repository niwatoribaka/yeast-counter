import cv2
import numpy as np

def rotateImage(image, angle):
    image_center = tuple(np.array(image.shape) / 2)
    rot_mat = cv2.getRotationMatrix2D(image_center[:-1], angle, 1.)
    result = cv2.warpAffine(image, rot_mat, image.shape[:-1], flags=cv2.INTER_LINEAR)
    return result
import cv2
import os
from pylab import *
from random import randrange

dir = raw_input('Name of data point? ')
if dir in os.listdir(os.getcwd()):
    print 'A datapoint with that name already exists.'
    print 'Will not overwrite'
    print '\nExiting'
    exit()
else:
    os.mkdir(dir)

number_of_slides = int(raw_input('Number of non-empty slides? '))
initial_coverage = int(raw_input('Initial Number of yeast cells? '))

yeast_count = range(
                    initial_coverage,
                    - 1,
                    int((-1) * (float(initial_coverage) / float(number_of_slides)))
                    )
def coverage(domain):
    return [x**3/domain[0]**2 for x in domain]

yeast_count = coverage(yeast_count)
# ordered = True if raw_input('Ordered? (y) ') == 'y' else False

for i in range(len(yeast_count)):
    img = zeros((800, 800, 3))
    # circle(img, center, radius, color[, thickness[, lineType[, shift]]])
    cv2.circle(img, (400, 400), 400, (255, 255, 255), -1)
    # rectangle(img, pt1, pt2, color[, thickness[, lineType[, shift]]])
    cv2.rectangle(img, (0, 350), (800, 350), (0, 0, 0), 5)
    cv2.rectangle(img, (0, 450), (800, 450), (0, 0, 0), 5)

    for j in range(yeast_count[i]):
        x, y = randrange(5, 796), randrange(355, 446)
        cv2.circle(img, (x, y), 5, (255, 0, 0), -1)

    cv2.imwrite('{0}/{1}{2}.jpg'.format(dir,
                                    '0' * (3 - len(str(i))),
                                    i),
                img)

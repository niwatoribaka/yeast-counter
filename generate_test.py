'''
generate_test.py presents a simple dialog that will allow the user
to generate a 'perfect data point'.  The data points generated by this
script can be used with the testing mode of yeast.py in order to easily
ascertain the functionality of novel yeast counting methods.
'''

import cv2
import os
from pylab import zeros
from random import randrange

test_name = raw_input('Name of data point? ')
if test_name in os.listdir(os.getcwd()):
    print 'A datapoint with that name already exists.'
    print 'Will not overwrite'
    print '\nExiting'
    exit()
else:
    os.mkdir(test_name)

number_of_slides = int(raw_input('Number of non-empty slides? '))
initial_coverage = int(raw_input('Initial Number of yeast cells? '))

if number_of_slides > initial_coverage:
    print 'Initial Number of yeast cells must be greater than or equal to the number of non-empty slides.'
    os.rmdir(test_name)
    exit()

yeast_count = range(
                    initial_coverage,
                    - 1,
                    int((-1) * (float(initial_coverage) / float(number_of_slides)))
                    )
def coverage(domain):
    return [x**3/domain[0]**2 for x in domain]

yeast_count = coverage(yeast_count)

for i in range(len(yeast_count)):
    img = zeros((800, 800, 3))
    cv2.circle(img, (400, 400), 400, (255, 255, 255), -1)
    cv2.rectangle(img, (0, 350), (800, 350), (0, 0, 0), 5)
    cv2.rectangle(img, (0, 450), (800, 450), (0, 0, 0), 5)

    for j in range(yeast_count[i]):
        x, y = randrange(5, 796), randrange(355, 446)
        cv2.circle(img, (x, y), 5, (255, 0, 0), -1)

    cv2.imwrite('{0}/{1}{2}.jpg'.format(test_name,
                                    '0' * (3 - len(str(i))),
                                    i),
                img)

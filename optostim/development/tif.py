from PIL import Image
import matplotlib.pyplot as plt
import numpy

img = Image.open("C:/Users/Scotty/Desktop/happyface.tif")

imarray = numpy.array(img)

plt.imshow(imarray)
plt.show()
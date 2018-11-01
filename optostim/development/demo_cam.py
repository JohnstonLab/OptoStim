import matplotlib.pyplot as plt

from ThirdParty.mmcorepy import MMCorePy

# mmc = MMCorePy.CMMCore()
# mmc.loadDevice('Camera', 'DemoCamera', 'DCam')
# mmc.initializeAllDevices()
# mmc.setCameraDevice('Camera')
# mmc.snapImage()
# img = mmc.getImage()
# imgplot = plt.imshow(img)

from pylab import *
ion()

mmc = MMCorePy.CMMCore()
mmc.loadDevice("cam","DemoCamera","DCam")
mmc.initializeDevice("cam")


print("Test acquire and display of monochrome images.")

figure()
mmc.setCameraDevice("cam")
mmc.snapImage()
im1 = mmc.getImage()
imshow(im1,cmap = cm.gray)


print("Test acquire and display of RGB images.")
figure()
mmc.setProperty("cam", "PixelType", "32bitRGB")
#mmc.setCameraDevice("rgbcam")
mmc.snapImage()
im2 = mmc.getImage()
imshow(im2)


print("Test MMCore.registerCallback():")

class PyMMEventCallBack(MMCorePy.MMEventCallback):
	def onPropertiesChanged(self):
		print("PyMMEventCallBack onPropertiesChanged() called")

callback = PyMMEventCallBack()
mmc.registerCallback(callback)
mmc.setCameraDevice("cam")
mmc.setProperty("cam","ScanMode","1")

print("Test MMCore.getLastImageMD():")

mmc.startSequenceAcquisition(1,1,False)
while(mmc.isSequenceRunning()):
	pass
md = MMCorePy.Metadata()
img = mmc.getLastImageMD(0,0,md)
imshow(img)
print(img)
print(md.Dump())

import cv2
from PyQt5.QtGui import QImage


class OpenCVQImage(QImage):

    def __init__(self, opencv_bgr_img):
        depth, nChannels = opencv_bgr_img.depth, opencv_bgr_img.nChannels
        if depth != cv2.cv.IPL_DEPTH_8U or nChannels != 3:
            raise ValueError("The input image must be 8-bit, 3-channel.")
        w, h = cv2.cv.GetSize(opencv_bgr_img)
        opencvRgbImg = cv2.cv.CreateImage((w, h), depth, nChannels)
        # it's assumed the image is in BGR format
        cv2.cv.CvtColor(opencv_bgr_img, opencvRgbImg, cv2.cv.CV_BGR2RGB)
        self._imgData = opencvRgbImg.tostring()
        super().__init__(self._imgData, w, h, QImage.Format_RGB888)
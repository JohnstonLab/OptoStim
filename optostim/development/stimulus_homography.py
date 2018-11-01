import sys

import cv2
import numpy as np
import matplotlib.pyplot as plt

cam_width = 1360
cam_height = 1030

stimulus_screen_width = 1920
stimulus_screen_height = 1080

stimulus_points = [(791, 922), (1063, 365), (85, 320), (696, 950)]


def draw_circles(img, points, colour):
    radius = 10
    for i, p in enumerate(points):
        cv2.putText(img, "{}".format(i), (int(p[0]), int(p[1])), cv2.FONT_HERSHEY_SIMPLEX, 4, colour)


cam_screen = np.zeros((cam_height, cam_width, 3), np.uint8)

draw_circles(cam_screen, stimulus_points, (0, 255, 0))

# for p in stimulus_points:
#     cv2.circle(stimulus_selection, p, radius, 255, cv2.FILLED)

#
# plt.imshow(stimulus_selection)
# plt.show()

#cam_image = np.zeros_like(stimulus_selection)
mid = (cam_width / 2, cam_height / 2)

#source = [(1090, 300), (1000, 800), (268, 833), (250, 270)]
source = [(mid[0] + 300, mid[1] - 300), (mid[0] + 300, mid[1] + 300), (mid[0] - 300, mid[1] + 300), (mid[0] - 300, mid[1] - 300)]
draw_circles(cam_screen, source, (255, 0, 0))
# plt.imshow(cam_image)
# plt.show()

stimulus_screen = np.zeros((stimulus_screen_height, stimulus_screen_width, 3), np.uint8)
stimulus_screen_mid = (stimulus_screen_width/2, stimulus_screen_height/2)


destination = [(stimulus_screen_mid[0] - 200, stimulus_screen_mid[1] - 200),
               (stimulus_screen_mid[0] + 200, stimulus_screen_mid[1] - 200),
               (stimulus_screen_mid[0] + 200, stimulus_screen_mid[1] + 200),
               (stimulus_screen_mid[0] - 200, stimulus_screen_mid[1] + 200)]

#draw_circles(stimulus_screen, destination)
#
#
# #destination = [(1200, 600), (2000, 600), (2000, 1200), (1200, 1200)]
#
matrix, _ = cv2.findHomography(np.array(source), np.array(destination))
# # matrix, _ = cv2.findHomography(np.array(destination), np.array(source))
#
print(matrix)
#result = cv2.warpPerspective(stimulus_selection, matrix, (stimulus_selection.shape[0], stimulus_selection.shape[1]))

#
for i, p in enumerate(stimulus_points):
    new_x = matrix[0][0] * p[0] + matrix[0][1] * p[1] + matrix[0][2]
    new_y = matrix[1][0] * p[0] + matrix[1][1] * p[1] + matrix[1][2]
    print("{} goes to ({}, {})".format(p, new_x, new_y))
    #cv2.putText(stimulus_screen, "{}".format(i), (int(p[0]), int(p[1])), cv2.FONT_HERSHEY_SIMPLEX, 1, 255)
    cv2.putText(stimulus_screen, "{}".format(i), (int(new_x), int(new_y)), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0))
    #cv2.putText(stimulus_screen, "{}".format(i), (int(source[i][0]), int(source[i][1])), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255))
    cv2.putText(stimulus_screen, "{}".format(i), (int(destination[i][0]), int(destination[i][1])), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 0))


plt.subplot(211)
plt.imshow(cam_screen)
plt.subplot(212)
plt.imshow(stimulus_screen)
plt.show()





# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#
#     camera_window = [(0, 0), (1360, 0), (1360, 1036), (0, 1036)]
#
#     # pixel_size = 100
#     # squares = [Square(parent=None, position=(0.0, 10), scale=pixel_size),
#     #            Square(parent=None, position=(100, 100), scale=pixel_size)]
#
#     myapp = OpenGLWidget()
#
#     myapp.frameSwapped.connect(lambda: print("Swapped"))
#     sw = StimulusWindow()
#
#     sw.setWindowTitle("Stimulus Window")
#
#     myapp.stimulus_window = sw
#
#     sw.show()
#     myapp.show()
#     try:
#         sys.exit(app.exec_())
#     except Exception as e:
#         print(e)
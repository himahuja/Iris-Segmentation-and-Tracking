import numpy as np
import cv2
import sys
from time import time

import kcftracker

selectingObject = False
initTracking = False
onTracking = False

ix, iy, cx, cy = -1, -1, -1, -1
w, h = 0, 0

inteval = 1
duration = 0.01

# mouse callback function
def draw_boundingbox(event, x, y, flags, param):
	global selectingObject, initTracking, onTracking, ix, iy, cx,cy, w, h

	if event == cv2.EVENT_LBUTTONDOWN:
		selectingObject = True
		onTracking = False
		ix, iy = x, y
		cx, cy = x, y

	elif event == cv2.EVENT_MOUSEMOVE:
		cx, cy = x, y

	elif event == cv2.EVENT_LBUTTONUP:
		selectingObject = False
		if(abs(x-ix)>10 and abs(y-iy)>10):
			w, h = abs(x - ix), abs(y - iy)
			ix, iy = min(x, ix), min(y, iy)
			initTracking = True
		else:
			onTracking = False

	elif event == cv2.EVENT_RBUTTONDOWN:
		onTracking = False
		if(w>0):
			ix, iy = x-w/2, y-h/2
			initTracking = True


if __name__ == '__main__':
	flag = 0

	if(len(sys.argv) == 1):
		cap = cv2.VideoCapture(0)
		flag = 1
	elif(len(sys.argv) == 3):
		## setting external camera
		if (sys.argv[1].isdigit() and sys.argv[2] == 'cam'):
			cap = cv2.VideoCapture(sys.argv[1])
			flag = 1
		elif (sys.argv[2] == 'vid'):
			cap = cv2.VideoCapture(sys.argv[1])
			flag = 2
		elif (sys.argv[2] == 'seq'):
			cap = cv2.VideoCapture(sys.argv[1] + '%04d.jpg', cv2.CAP_IMAGES)
			flag = 2
			inteval = 30
	else:
		assert(0), "Please check help for description"

	tracker = kcftracker.KCFTracker(True, True, True)
	# hog, fixed_window, multiscale

	cv2.namedWindow('Tracking')
	cv2.setMouseCallback('Tracking',draw_boundingbox)

	# Reading the first frame in case of stored video
	# This ensures we can mark the BB with stability.
	ret, frame = cap.read()
	if not ret:
		print('Nothing was returned.')
		exit(0)
	firstFrame = frame.copy() # Copy to restore each frame after BB creation
	while (not initTracking and flag == 2):
		if(selectingObject):
			cv2.rectangle(frame, (ix,iy), (cx,cy), (0,255,255), 1)
		cv2.imshow('Tracking', frame)
		cv2.waitKey(inteval)
		frame = firstFrame.copy() # Duplicate into frame the non BB overlay frame

	# Reading the subsequent frames in case of both camera & stored video
	while(cap.isOpened()):
		ret, frame = cap.read()
		if not ret:
			break
		if flag == 1 and selectingObject:
		 	cv2.rectangle(frame,(ix,iy), (cx,cy), (0,255,255), 1)
		elif(initTracking):
			initbb = [ix, iy, w, h]
			cv2.rectangle(frame,(ix,iy), (ix+w,iy+h), (0,255,255), 2)
			tracker.init([ix,iy,w,h], frame)
			initTracking = False
			onTracking = True
		elif(onTracking):
			t0 = time()
			bb = tracker.update(frame)
			t1 = time()
			bb = map(int, bb)
			amplitude = np.sqrt((initbb[0] + initbb[2]/2 - bb[0] - bb[2]/2)**2 + (initbb[1] + initbb[3]/2 - bb[1] - bb[3]/2)**2)
			cv2.rectangle(frame,(bb[0],bb[1]), (bb[0]+bb[2],bb[1]+bb[3]), (0,255,255), 1)

			duration = 0.8*duration + 0.2*(t1-t0)
			#duration = t1-t0
			cv2.putText(frame, 'FPS: '+str(1/duration)[:4].strip('.'), (8,20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255), 2)
			cv2.putText(frame, 'Amplitude: '+ str(amplitude), (8,40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255), 2)
		cv2.imshow('Tracking', frame)
		# Exit on key 'esc' or 'q'
		c = cv2.waitKey(inteval) & 0xFF
		if c==27 or c==ord('q'):
			break

	cap.release()
	cv2.destroyAllWindows()

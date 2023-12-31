# CÁCH DÙNG
# python detect_mask_image.py --image examples/example_01.jpg

# import các thư viện cần thiết
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.models import load_model
import numpy as np
import argparse
import cv2
import os
from skimage import io
def mask_image():
	# các tham số đầu vào
	ap = argparse.ArgumentParser()
	ap.add_argument("-i", "--image", required=True,
		help="path to input image")
	ap.add_argument("-f", "--face", type=str,
		default="face_detector",
		help="path to face detector model directory")
	ap.add_argument("-m", "--model", type=str,
		default="mask_detector.model",
		help="path to trained face mask detector model")
	ap.add_argument("-c", "--confidence", type=float, default=0.5,
		help="minimum probability to filter weak detections")
	args = vars(ap.parse_args())

	# load face detector model từ thư mục
	print("[INFO] loading face detector model...")
	prototxtPath = os.path.sep.join([args["face"], "deploy.prototxt"])
	weightsPath = os.path.sep.join([args["face"],
		"res10_300x300_ssd_iter_140000.caffemodel"])
	net = cv2.dnn.readNet(prototxtPath, weightsPath)

	# load face mask detector model đã train
	print("[INFO] loading face mask detector model...")
	model = load_model(args["model"])

	# load input image và preprocess
	image = cv2.imread(args["image"])
	orig = image.copy()
	(h, w) = image.shape[:2]

	# chuyển image sang blob
	blob = cv2.dnn.blobFromImage(image, 1.0, (300, 300),
		(104.0, 177.0, 123.0))

	# face detections
	print("[INFO] computing face detections...")
	net.setInput(blob)
	detections = net.forward()

	# lặp qua các detections
	for i in range(0, detections.shape[2]):
		# lấy ra độ tin cậy (xác suất,...) tương ứng của mỗi detection
		confidence = detections[0, 0, i, 2]

		# lọc ra các detections đảm bảo độ tin cậy > ngưỡng tin cậy
		if confidence > args["confidence"]:
			# tính toán (x,y) bounding box
			box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
			(startX, startY, endX, endY) = box.astype("int")

			# đảm bảo bounding box nằm trong kích thước frame
			(startX, startY) = (max(0, startX), max(0, startY))
			(endX, endY) = (min(w - 1, endX), min(h - 1, endY))

			# trích ra face ROI, chuyển image từ BGR sang RGB, resize về 224x224 và preprocess
			face = image[startY:endY, startX:endX]
			face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
			face = cv2.resize(face, (224, 224))
			face = img_to_array(face)
			face = preprocess_input(face)
			face = np.expand_dims(face, axis=0)

			# dùng model đã train để predict mask or no mask
			(mask, withoutMask) = model.predict(face)[0]

			# xác định class label và color để vẽ bounding box và text
			label = "Mask" if mask > withoutMask else "No Mask"
			color = (0, 255, 0) if label == "Mask" else (0, 0, 255)

			# đính thêm thông tin về xác suất(probability) của label
			label = "{}: {:.2f}%".format(label, max(mask, withoutMask) * 100)

			# display label và bounding box hình chữ nhật trên output frame
			cv2.putText(image, label, (startX, startY - 10),
				cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 2)
			cv2.rectangle(image, (startX, startY), (endX, endY), color, 2)

	# show output image
	cv2.imshow("Output", image)
	cv2.waitKey(0)

if __name__ == "__main__":
	mask_image()

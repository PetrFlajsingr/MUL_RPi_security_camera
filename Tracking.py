import cv2
import imutils


class ChangeDetector:
    def __init__(self, reference_img, area_limits: (int, int), resize, thresh=5):
        self.resize = resize
        gray = self.prepare_img(reference_img)
        self.avg_img = gray.copy().astype("float")
        self.area_limits = area_limits
        self.thresh = thresh

    def detect(self, img):
        gray = self.prepare_img(img)
        cv2.accumulateWeighted(gray, self.avg_img, 0.5)
        frame_delta = cv2.absdiff(gray, cv2.convertScaleAbs(self.avg_img))

        thresh = cv2.threshold(frame_delta, self.thresh, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        contours = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = imutils.grab_contours(contours)
        max_area = 0
        bounding_box = None
        for c in contours:
            area = cv2.contourArea(c)
            (x, y, w, h) = cv2.boundingRect(c)
            if self.area_limits[0] < area < self.area_limits[1] and area > max_area and h > w:
                bounding_box = (x, y, w, h)
                max_area = area

        if bounding_box is not None:
            return True, bounding_box

        return False, None

    def prepare_img(self, img):
        img = imutils.resize(img, width=self.resize)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return cv2.GaussianBlur(gray, (21, 21), 0)


class PersonDetector:
    def __init__(self):
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

    def detect(self, img, sub_area=None):
        if sub_area is not None:
            (x, y, w, h) = sub_area
            img = img[y:y + h, x:x + w]
        return self.hog.detectMultiScale(img, winStride=(4, 4),
                                         padding=(8, 8), scale=1.05)


OPENCV_OBJECT_TRACKERS = {
    "csrt": cv2.TrackerCSRT_create,
    "kcf": cv2.TrackerKCF_create,
    "boosting": cv2.TrackerBoosting_create,
    "tld": cv2.TrackerTLD_create,
    "medianflow": cv2.TrackerMedianFlow_create,
    "mosse": cv2.TrackerMOSSE_create
}


class PersonTracker:
    def __init__(self, tracker_name: str, img, init_bb, resize):
        self.tracker = OPENCV_OBJECT_TRACKERS[tracker_name]()
        self.tracker.init(img, init_bb)
        self.resize = resize

    def update(self, img):
        img = imutils.resize(img, width=self.resize)
        return self.tracker.update(img)

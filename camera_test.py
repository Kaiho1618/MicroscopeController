
import cv2

def test_directshow():
    # Try with DirectShow backend
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    
    if cap.isOpened():
        # Set some properties if needed
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        
        ret, frame = cap.read()
        if ret:
            cv2.imwrite('directshow_capture.jpg', frame)
            print("Image captured with DirectShow!")
        else:
            print("Failed to capture with DirectShow")
        
        cap.release()\
    else:
        print("Cannot open camera with DirectShow")

if __name__ == "__main__":
    test_directshow()

import cv2
import os

def add_faces():
    try:
        name = input("Enter your name: ")

        video = cv2.VideoCapture(0)

        if not video.isOpened():
            print("Error: Failed to open camera.")
            return

        facedetect = cv2.CascadeClassifier('C://Users//rohan//OneDrive//Desktop//firebase//haarcascade_frontalface_default.xml')
      

        while True:
            ret, frame = video.read()
            if not ret:
                print("Error: Failed to capture frame")
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = facedetect.detectMultiScale(gray, 1.3, 5)

            # Add text for taking attendance
            cv2.putText(frame, "Press 'C' for taking attendance", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (50, 50, 255), 2)
            
            cv2.imshow("Frame", frame)

            k = cv2.waitKey(1)
            if k == ord('q'):
                break
            elif k == ord('c'):
                if len(faces) == 1:
                    # Add text for attendance taken
                    cv2.putText(frame, "Attendance taken", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                    x, y, w, h = faces[0]
                    crop_img = frame[y:y+h, x:x+w]
                    img_name = os.path.join("C:\\xampp\\htdocs\\FRBAS\\static\\faculty\\", f"{name}.jpg")
                    cv2.imwrite(img_name, crop_img)
                    print(f"Image saved as {img_name}")

                    # Display 'Attendance taken' for 3 seconds
                    cv2.imshow("Frame", frame)
                    cv2.waitKey(2000)

                    break
                else:
                    print("Please make sure only one face is visible before capturing.")

        video.release()
        cv2.destroyAllWindows()

    except Exception as e:
        print("An error occurred:", str(e))

if __name__ == "__main__":
    add_faces()

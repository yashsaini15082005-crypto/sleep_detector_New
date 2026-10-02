import cv2
import pygame
import time
import os
import subprocess
import imageio_ffmpeg
import tkinter as tk
from tkinter import messagebox
from threading import Thread


# =========================================================
# 1. ALARM AUDIO SETUP
# =========================================================

video_file = "alaram.web.mp4"
audio_file = "alarm.wav"

if not os.path.exists(audio_file):
    print("Alarm recording se audio nikala ja raha hai...")

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

    command = [
        ffmpeg,
        "-y",
        "-i", video_file,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "44100",
        "-ac", "2",
        audio_file
    ]

    subprocess.run(command)

    print("Alarm audio ready!")


# =========================================================
# 2. PYGAME
# =========================================================

pygame.init()
pygame.mixer.init()

pygame.mixer.music.load(audio_file)


# =========================================================
# 3. OPENCV CASCADE
# =========================================================

cv2_base_dir = os.path.dirname(cv2.__file__)
haar_dir = os.path.join(cv2_base_dir, "data")

face_cascade_path = os.path.join(haar_dir, "haarcascade_frontalface_default.xml")

eye_cascade_path = os.path.join(
    haar_dir,
    "haarcascade_eye.xml"
)

face_cascade = cv2.CascadeClassifier(face_cascade_path)
eye_cascade = cv2.CascadeClassifier(eye_cascade_path)


if face_cascade.empty():
    print("ERROR: Face cascade XML load nahi hua!")
    exit()

if eye_cascade.empty():
    print("ERROR: Eye cascade XML load nahi hua!")
    exit()


# =========================================================
# 4. SETTINGS
# =========================================================

CLOSED_TIME = 3

running = False
camera = None

eyes_closed_start = None
alarm_on = False

drowsiness_count = 0
alarm_count = 0


# =========================================================
# 5. CAMERA DETECTION
# =========================================================

def camera_detection():

    global running
    global camera
    global eyes_closed_start
    global alarm_on
    global drowsiness_count
    global alarm_count

    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        messagebox.showerror(
            "Camera Error",
            "Camera open nahi ho pa raha!"
        )
        running = False
        return

    while running:

        ret, frame = camera.read()

        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.3,
            minNeighbors=5,
            minSize=(80, 80)
        )

        eyes_detected = False

        for (x, y, w, h) in faces:

            cv2.rectangle(
                frame,
                (x, y),
                (x + w, y + h),
                (0, 255, 0),
                2
            )

            face_gray = gray[y:y+h, x:x+w]

            eyes = eye_cascade.detectMultiScale(
                face_gray,
                scaleFactor=1.2,
                minNeighbors=5,
                minSize=(20, 20)
            )

            if len(eyes) >= 1:
                eyes_detected = True

                for (ex, ey, ew, eh) in eyes:

                    cv2.rectangle(
                        frame,
                        (x + ex, y + ey),
                        (x + ex + ew, y + ey + eh),
                        (255, 255, 0),
                        2
                    )

        # =================================================
        # EYES OPEN
        # =================================================

        if eyes_detected:

            eyes_closed_start = None

            if alarm_on:

                pygame.mixer.music.stop()
                alarm_on = False

            status_label.config(
                text="● AWAKE",
                fg="#00ff88"
            )

            timer_label.config(
                text="Eyes Closed: 0.0 sec"
            )

        # =================================================
        # EYES CLOSED
        # =================================================

        else:

            if eyes_closed_start is None:

                eyes_closed_start = time.time()

            closed_duration = time.time() - eyes_closed_start

            timer_label.config(
                text=f"Eyes Closed: {closed_duration:.1f} sec"
            )

            if closed_duration < CLOSED_TIME:

                status_label.config(
                    text="● EYES CLOSED",
                    fg="#ffaa00"
                )

            else:

                status_label.config(
                    text="🚨 DROWSINESS DETECTED!",
                    fg="#ff3333"
                )

                if not alarm_on:

                    pygame.mixer.music.play(-1)

                    alarm_on = True

                    drowsiness_count += 1
                    alarm_count += 1

                    count_label.config(
                        text=f"Drowsiness Events: {drowsiness_count}"
                    )

        # =================================================
        # CAMERA TEXT
        # =================================================

        cv2.putText(frame,"Time:0.0 second",(20,35),
                    cv2.FONT_HERSHEY_SIMPLEX,0.8,(255,255,255),2)
        
        cv2.imshow(
            "Draw signs  Detection Camera",
            frame)

        # Q KEY ALSO STOPS CAMERA
        if cv2.waitKey(1) & 0xFF == ord("q"):

            running = False
            break

    # =====================================================
    # CLEANUP
    # =====================================================

    if camera is not None:
        camera.release()

    cv2.destroyAllWindows()

    pygame.mixer.music.stop()

    alarm_on = False

    status_label.config(
        text="● SYSTEM STOPPED",
        fg="#ff5555"
    )

    timer_label.config(
        text="Eyes Closed: 0.0 sec"
    )


# =========================================================
# 6. START FUNCTION
# =========================================================

def start_detection():

    global running

    if running:
        return

    running = True

    status_label.config(
        text="● STARTING CAMERA...",
        fg="#00ccff"
    )

    start_button.config(
        state="disabled"
    )

    stop_button.config(
        state="normal"
    )

    thread = Thread(
        target=camera_detection,
        daemon=True
    )

    thread.start()


# =========================================================
# 7. STOP FUNCTION
# =========================================================

def stop_detection():

    global running

    running = False

    pygame.mixer.music.stop()

    status_label.config(
        text="● STOPPED",
        fg="#ff5555"
    )

    start_button.config(
        state="normal"
    )

    stop_button.config(
        state="disabled"
    )


# =========================================================
# 8. MAIN GUI
# =========================================================

root = tk.Tk()

root.title(
    "AI Drowsiness Detection System"
)

root.geometry(
    "700x550"
)

root.configure(
    bg="#101820"
)

root.resizable(
    False,
    False
)


# =========================================================
# TITLE
# =========================================================

title_label = tk.Label(
    root,
    text="AI DROWSINESS DETECTION",
    font=("Arial", 28, "bold"),
    fg="#00e5ff",
    bg="#101820"
)

title_label.pack(
    pady=(30, 5)
)


subtitle_label = tk.Label(
    root,
    text="Computer Vision Based Driver Alert System",
    font=("Arial", 13),
    fg="#bbbbbb",
    bg="#101820"
)

subtitle_label.pack(
    pady=(0, 25)
)


# =========================================================
# STATUS BOX
# =========================================================

status_frame = tk.Frame(
    root,
    bg="#182631",
    highlightbackground="#00e5ff",
    highlightthickness=2
)

status_frame.pack(
    padx=50,
    pady=10,
    fill="x"
)


status_title = tk.Label(
    status_frame,
    text="SYSTEM STATUS",
    font=("Arial", 12, "bold"),
    fg="#aaaaaa",
    bg="#182631"
)

status_title.pack(
    pady=(15, 5)
)


status_label = tk.Label(
    status_frame,
    text="● SYSTEM READY",
    font=("Arial", 24, "bold"),
    fg="#00ff88",
    bg="#182631"
)

status_label.pack(
    pady=(0, 18)
)


# =========================================================
# TIMER
# =========================================================

timer_label = tk.Label(
    root,
    text="Eyes Closed: 0.0 sec",
    font=("Arial", 20, "bold"),
    fg="white",
    bg="#101820"
)

timer_label.pack(
    pady=20
)


# =========================================================
# EVENT COUNTER
# =========================================================

count_label = tk.Label(
    root,
    text="Drowsiness Events: 0",
    font=("Arial", 16),
    fg="#00e5ff",
    bg="#101820"
)

count_label.pack(
    pady=10
)


# =========================================================
# BUTTON FRAME
# =========================================================

button_frame = tk.Frame(
    root,
    bg="#101820"
)

button_frame.pack(
    pady=30
)


# =========================================================
# START BUTTON
# =========================================================

start_button = tk.Button(
    button_frame,
    text="▶️ START DETECTION",
    command=start_detection,
    font=("Arial", 15, "bold"),
    bg="#00a86b",
    fg="white",
    activebackground="#00cc88",
    activeforeground="white",
    width=20,
    height=2,
    relief="flat",
    cursor="hand2"
)

start_button.grid(
    row=0,
    column=0,
    padx=10
)


# =========================================================
# STOP BUTTON
# =========================================================

stop_button = tk.Button(
    button_frame,
    text="■ STOP DETECTION",
    command=stop_detection,
    font=("Arial", 15, "bold"),
    bg="#d32f2f",
    fg="white",
    activebackground="#ff4444",
    activeforeground="white",
    width=20,
    height=2,
    relief="flat",
    cursor="hand2",
    state="disabled"
)

stop_button.grid(
    row=0,
    column=1,
    padx=10
)


# =========================================================
# FOOTER
# =========================================================

footer_label = tk.Label(
    root,
    text="Python • OpenCV • Computer Vision • Real-Time Alert",
    font=("Arial", 10),
    fg="#777777",
    bg="#101820"
)

footer_label.pack(
    pady=20
)


# =========================================================
# CLOSE WINDOW
# =========================================================

def close_application():

    global running

    running = False

    pygame.mixer.music.stop()

    if camera is not None:
        camera.release()

    cv2.destroyAllWindows()

    pygame.quit()

    root.destroy()


root.protocol(
    "WM_DELETE_WINDOW",
    close_application
)


# =========================================================
# RUN GUI
# =========================================================

root.mainloop()
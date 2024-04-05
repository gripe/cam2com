import cv2
import matplotlib.pyplot as plt
import time
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import threading
import numpy as np
import serial
import serial.tools.list_ports
from queue import Queue
from multiprocessing import Process



import matplotlib.pyplot as plt
import matplotlib.animation as animation
from simulation import amp_plot
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import math


# If running on a laptop, make sure it is charging
# Reduced power modes seem to not have fun running the camera feed

# To make this thing thread-safe
update_queue = Queue()

# COM TERMINAL (WHAT MY LAPTOP USES)
try:
    ser = serial.Serial('COM4', 115200, timeout=1)
except:
    ser = 0

# Adjust if text doesn't work:
# alt_font = ('Courier', 13)
alt_font = ('JetBrains Mono NL', 13)

# Global variables for face position
face_X, face_Y, face_Distance, delay = -1, -1, -1, 10
last_X, last_Y, last_Distance, last_Delay = -2, -2, -2, 10
manual_control = False
facetrack_loop = True

theta = np.linspace(-math.pi / 2, math.pi / 2, 1000)


### GUI ### GUI ### GUI ###

# Create the main window
root = tk.Tk()
root.title("PASS: Face Tracking and STM32 Communication Interface")
root.geometry("600x500")

# Toggle use manual control / Face-tracking
def toggle_manual_control():
    global manual_control
    manual_control = not manual_control
    button_toggle_control.config(text="Use Face-Tracker" if manual_control else "Use Sliders")
    toggle_label.config(text="Now using sliders." if manual_control else "Now using face-tracker.")

def toggle_wobble():
    global wobble_mode
    wobble_mode = not wobble_mode
    button_toggle_wobble.config(text="Turn Off Wobble" if wobble_mode else "Turn On Wobble")

# Add a label above the button
toggle_label = tk.Label(root, text="Using face-tracker.", font=alt_font)
toggle_label.pack(pady=10)

# Add the toggle control button
button_toggle_control = tk.Button(root, text="Use Sliders", command=toggle_manual_control, font=alt_font, bg='gray', fg='white')
button_toggle_control.pack(pady=10)

button_toggle_wobble = tk.Button(root, text="Turn on Wobble", command=toggle_wobble, font=alt_font, bg='gray', fg='white')
button_toggle_wobble.pack(pady=10)



# X, Y, Distance Sliders

sliderA = tk.Scale(root, from_=-90, to=90, orient='horizontal', label='Angle', length=500, font=alt_font)
sliderA.pack()
delay = 0
angle = 0
last_Angle = 0
wobble_mode = True

# Function to quit the program
def quit_program():
    global facetrack_loop
    facetrack_loop = False
    time.sleep(1) # Delay so the flag is caught
    # Release the camera
    if cap.isOpened():
        cap.release()
    plt.close('all')
    root.destroy()

# Create and place the buttons
button_quit = ttk.Button(root, text="Quit Program", command=quit_program)
button_quit.pack(pady=25)

# Create a new window
new_window = tk.Toplevel(root)
new_window.title("COM5 Output")

# Create a text widget in the new window
text = tk.Text(new_window)
text.pack()

# Read from the serial port
def read_from_port():
    while facetrack_loop:
        if not ser == 0:
            line = ser.readline()
            if line:
                # Update the text widget with the received line
                text.insert(tk.END, line.decode())
                text.see(tk.END)
        time.sleep(0.1)

# Start a new thread that reads from the serial COM port


counter = 0
def serial_thread():
    global face_X, face_Y, face_Distance, angle
    global last_X, last_Y, last_Distance, last_Angle
    while True:
        if manual_control:
            angle = (int)(sliderA.get()) * math.pi / 180.0 
        time.sleep(.01)
        send_facepos_values()
def send_facepos_values():
    global face_X, face_Y, face_Distance, angle
    global last_X, last_Y, last_Distance, last_Angle
    global delay, delay_us, counter
    
    try:
        if angle != last_Angle or (wobble_mode):
            last_Angle = angle
            delay_us = .015 * math.sin(angle) / 343.3
            delay = delay_us / (208e-7) * 32
            if wobble_mode:
                delay += int(40 * math.sin(2 * math.pi * time.time() * 1000 / 3e3))
            delay = min(delay,80)
            delay = max(delay, -80)
            print(delay)
            command = f'setDelay {int(-delay + 80)}\n'.encode()  # Construct and encode the command
            ser.write(command)  # Send the command
            ser.flush()  # Ensure all data is written to the serial port

    except serial.SerialException as e:
        messagebox.showerror("Error", f"Failed to open the serial port: {e}")

#### FACE #### TRACK #### FACE #### TRACK ####

# Load the face-detection model
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
frame_width = 640
frame_height = 480
# Open the webcam:
# 0 is the default camera
# 1 is the USB camera (takes 3 minutes to load for some reason)
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)  #3840
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)  #2160                 
# cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)
cap.set(cv2.CAP_PROP_FPS, 30)
# For some reason using the plot feature is way faster than just displaying the camera feed
plt.ion()  # Turn on interactive mode for live updates

fig2, ax2 = plt.subplots()  # Create a figure and a set of subplots
ax2.set_xlabel('Theta (Degrees)')
ax2.set_ylabel('Decibels')
# plt.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=0, hspace=0)  # Adjust subplot parameters (basically fullscreen)
frequencies = [100, 500, 800, 1000, 2000, 5000, 10000]
lines = []
for i in frequencies:
    lines += ax2.plot(180 / math.pi * theta, np.sin(theta), label = f'{i} Hz')
plt.legend()
ax2.set_ylim(-100, 100)

fov_horizontal=57
fov_vertical=34.6
angle_per_pixel_horizontal = fov_horizontal / frame_width
angle_per_pixel_vertical = fov_vertical / frame_height
def getFacePositionFromVideo():
    global face_X, face_Y, face_Distance, angle
    if not manual_control: # Face-tracking enabled
        #print('!~!~! Face-Tracking Loop Working !~!~!')
        while True:
            if manual_control:
                time.sleep(.1)
                continue
            ret, frame = cap.read()
            if not ret:
                return False  # Break out of the loop if the frame is not captured properly

            frame = cv2.flip(frame,1)
            # Convert the frame to grayscale for face detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces in the frame
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

            # Iterate over detected faces but break (just using the first face found)
            for (x, y, w, h) in faces:
                # Calculate the center of the face
                face_X = x + w // 2
                face_Y = y + h // 2
                # Calculate the distance based on face size (scaling factor can be adjusted)
                face_Distance = 100 / w

                # Display the center coordinates and distance
                # output_str = f"X: {center_x}, Y: {center_y}, Distance: {center_distance:.2f}"
                # print(output_str, end='\r', flush=True)
                angle = (face_X - frame_width / 2) * angle_per_pixel_horizontal
                angle = angle * math.pi / 180
                update_queue.put((frame, face_X, face_Y, face_Distance))

                # Draw a rectangle around the face
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
            cv2.imshow('Input', frame)
            c = cv2.waitKey(1)
            if c == 27:
                break
            time.sleep(.1)

plot_text = fig2.text(0.50, 0.95, 
'Delay =', horizontalalignment='center', wrap=True ) 

# Thread-safe GUI update addition to getFacePositionFromVideo()
factor = 15 * (208e-7) / 32.0
def update_gui():
    global delay, delay_us
    # delay = math.asin((320.0 - x) / 640.0  * 5000.0 / distance / distance) / math.pi * 1000e-6
    for i, line in enumerate(lines):
        if frequencies[i] <= 1400:
            line.set_ydata(10 * np.log(amp_plot(frequencies[i], .1, .06, 3 * factor * -delay, 12)))
        else:
            line.set_ydata(10 * np.log(amp_plot(frequencies[i], .035, .02, 1 * factor *  -delay , 20)))
    plot_text.set_text(f'Delay = {int(delay * 20.8 / 32)} microseconds')
    plt.pause(0.08)  # This pyplot delay seems to work best
    root.after(1, update_gui)

# Main loop
if __name__ == "__main__":
    threading.Thread(target=read_from_port, daemon=True).start()
    threading.Thread(target=getFacePositionFromVideo, daemon=True).start()
    threading.Thread(target=serial_thread, daemon=True).start()
    root.after(1, update_gui)
    root.mainloop() 
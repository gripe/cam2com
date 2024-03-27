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

# If running on a laptop, make sure it is charging
# Reduced power modes seem to not have fun running the camera feed

# To make this thing thread-safe
update_queue = Queue()

# COM TERMINAL (WHAT MY LAPTOP USES)
ser = serial.Serial('COM5', 115200, timeout=1)

# Adjust if text doesn't work:
# alt_font = ('Courier', 13)
alt_font = ('JetBrains Mono NL', 13)

# Global variables for face position
face_X, face_Y, face_Distance = -1, -1, -1
last_X, last_Y, last_Distance = -2, -2, -2
manual_control = False
facetrack_loop = True

### GUI ### GUI ### GUI ###

# Create the main window
root = tk.Tk()
root.title("PASS: Face Tracking and STM32 Communication Interface")
root.geometry("600x500")

# Test command 'T'
def toggle_led():
    try:
        ser.write(b'T\n')
        # messagebox.showinfo("Success", "The 'T' command has been sent.")
    except serial.SerialException as e:
        messagebox.showerror("Error", f"Failed to open the serial port: {e}")

# Add a button to the window
button = tk.Button(root, text="Toggle blue LED", command=toggle_led, font=alt_font, bg='blue', fg='white')
button.pack(pady=20)

# Toggle use manual control / Face-tracking
def toggle_manual_control():
    global manual_control
    manual_control = not manual_control
    button_toggle_control.config(text="Use Face-Tracker" if manual_control else "Use Sliders")
    toggle_label.config(text="Now using sliders." if manual_control else "Now using face-tracker.")
    # Might add more to the toggler (hide sliders, etc.)
    #if manual_control:
        # Add manual control sliders
    #else:
        # Remove manual control sliders

# Add a label above the button
toggle_label = tk.Label(root, text="Using face-tracker.", font=alt_font)
toggle_label.pack(pady=10)

# Add the toggle control button
button_toggle_control = tk.Button(root, text="Use Sliders", command=toggle_manual_control, font=alt_font, bg='gray', fg='white')
button_toggle_control.pack(pady=10)

# X, Y, Distance Sliders
sliderX = tk.Scale(root, from_=0, to=640, orient='horizontal', label='X: Horizontal', length=500, font=alt_font)
sliderX.pack()
sliderY = tk.Scale(root, from_=0, to=480, orient='horizontal', label='Y: Vertical', length=500, font=alt_font)
sliderY.pack()
sliderD = tk.Scale(root, from_=0, to=100, orient='horizontal', label='Distance', length=500, font=alt_font)
sliderD.pack()

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
        line = ser.readline()
        if line:
            # Update the text widget with the received line
            text.insert(tk.END, line.decode())
        time.sleep(0.1)

# Start a new thread that reads from the serial COM port
threading.Thread(target=read_from_port, daemon=True).start()


def serial_thread():
    global face_X, face_Y, face_Distance
    #global last_X, last_Y, last_Distance
    while facetrack_loop:
        if manual_control:
            face_X = (int) (sliderX.get())
            face_Y = (int) (sliderY.get())
            face_Distance = (int) (sliderD.get())
            #output_str = f"X: {face_X}, Y: {face_Y}, Distance: {face_Distance}"
            #print(output_str, end='\r', flush=True)
        send_facepos_values()
        time.sleep(1)
        
def send_facepos_values():
    global face_X, face_Y, face_Distance
    global last_X, last_Y, last_Distance
    try:
        #X
        if face_X != last_X and face_X >= 0: # Only send the command if the value has changed
            last_X = face_X # Update the last-used/sent value
            command = f'setX {face_X}\n'.encode()  # Construct and encode the command
            ser.write(command)  # Send the command
            ser.flush()  # Ensure all data is written to the serial port
            time.sleep(0.1) # A delay between sending commands to prevent spamming the buffer
        #Y
        if face_Y != last_Y and face_Y >= 0:
            last_Y = face_Y
            command = f'setY {face_Y}\n'.encode()
            ser.write(command)
            ser.flush()
            time.sleep(0.1)
        #Distance
        if face_Distance != last_Distance and face_Distance >= 0:
            last_Distance = face_Distance
            command = f'setDistance {face_Distance}\n'.encode()
            ser.write(command)
            ser.flush()
            time.sleep(0.1)
    except serial.SerialException as e:
        messagebox.showerror("Error", f"Failed to open the serial port: {e}")

#### FACE #### TRACK #### FACE #### TRACK ####

# Load the face-detection model
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Open the webcam:
# 0 is the default camera
# 1 is the USB camera (takes 3 minutes to load for some reason)
cap = cv2.VideoCapture(0)
# For some reason using the plot feature is way faster than just displaying the camera feed
plt.ion()  # Turn on interactive mode for live updates
fig, ax = plt.subplots()  # Create a figure and a set of subplots
plt.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=0, hspace=0)  # Adjust subplot parameters (basically fullscreen)
im = ax.imshow(np.zeros((480, 640, 3)))  # Placeholder for the first frame, adjust the size as necessary
plt.axis('off')
    
def getFacePositionFromVideo():
    global face_X, face_Y, face_Distance
    if not manual_control: # Face-tracking enabled
        #print('!~!~! Face-Tracking Loop Working !~!~!')
        
        ret, frame = cap.read()
        if not ret:
            return False  # Break out of the loop if the frame is not captured properly

        # Convert the frame to grayscale for face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect faces in the frame
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

        # Iterate over detected faces but break (just using the first face found)
        for (x, y, w, h) in faces:
            # Calculate the center of the face
            center_x = x + w // 2
            center_y = y + h // 2

            # Calculate the distance based on face size (scaling factor can be adjusted)
            center_distance = 10000 / w

            # Display the center coordinates and distance
            # output_str = f"X: {center_x}, Y: {center_y}, Distance: {center_distance:.2f}"
            # print(output_str, end='\r', flush=True)
            face_X, face_Y, face_Distance = int(center_x), int(center_y), int(center_distance)
            update_queue.put((frame, face_X, face_Y, face_Distance))

            # Draw a rectangle around the face
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
        
            break; # Only track the first face

        # Left in for reference
        # Avoiding displaying/updating GUI in this function due to it not being thread safe
        # Display the resulting frame using matplotlib
        #im.set_data(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        #plt.pause(0.1)  # Delay to prevent burning a hole in my CPU

        #root.update_idletasks()
        #root.update()
    
        return True

# Start the serial thread for sending face position data
threading.Thread(target=serial_thread, daemon=True).start()

# Main face-tracking function
def face_tracking():
    global facetrack_loop
    while facetrack_loop:
        #print('=== === ===')
        if not manual_control:
            if not getFacePositionFromVideo():
                #print('~!~!~ Face-Tracking Loop Broken ~!~!~')
                break  # Exit if video capture failed
        time.sleep(0.1)  # Delay to prevent burning a hole in my CPU

# Start the face-tracking in a separate thread
threading.Thread(target=face_tracking, daemon=True).start()

# Thread-safe GUI update addition to getFacePositionFromVideo()
def update_gui():
    while not update_queue.empty():
        frame, x, y, distance = update_queue.get()
        im.set_data(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        plt.pause(0.08)  # This is the pyplot delay seems to work best

    if facetrack_loop:
        root.after(50, update_gui)  # Schedule this method to be called again after 50 ms

# Main loop
if __name__ == "__main__":
    root.after(50, update_gui)
    root.mainloop()   
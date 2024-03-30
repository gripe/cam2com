# This is a rough spherical coordinate-based face position tracker
# I calibrated this by standing in different spots in my room and measuring the distance from the camera to my face in centimeters
# It's not precise by any means, but it has been consistent in its estimations

# The Logitech Brio 100 camera records in 1920x1080 resolution
# It is 2MP and has a 58 degree field of view horizontally, and about a 34.6 degree field of view vertically

# for (x, y, w, h) in faces:
#        center_x = x + w // 2
#        center_y = y + h // 2
#        center_distance = 100 / w

# At 100 cm away, center_distance is 0.25
# At 200 cm away, center_distance is 0.5

# FROM THE POV OF THE CAMERA


#                     φ = +17.3°
#          # # # # # # # # # # # # # # # # #
#          # (0, 0)              (1920, 0) #
#          #                               #
#          #                               #
# θ = -29° #         (960, 540)            # θ = +29°
#          #                               #
#          #                               #
#          # (0, 1080)        (1920, 1080) #
#          # # # # # # # # # # # # # # # # #
#                     φ = -17.3°

import cv2
import matplotlib.pyplot as plt
import time
import tkinter as tk
from tkinter import ttk
import threading
import numpy as np


def facepos_to_spherical_coordinates(x, y, w, h, frame_width=1920, frame_height=1080, fov_horizontal=58, fov_vertical=34.6):
    # distance, theta, phi = 0, 0, 0
    
    # I don't have an effective formula for the distance that adjusts per webcam, but this works for the Logitech Brio 100
    distance = (100 / w) * 400 # *approximate* distance in cm

    center_x = x + w // 2
    center_y = y + h // 2
    pixel_offset_x = center_x - (frame_width / 2)
    pixel_offset_y = center_y - (frame_height / 2)
    
    # Convert pixel offsets to angles
    # Angle per pixel = FOV / number of pixels in that direction
    angle_per_pixel_horizontal = fov_horizontal / frame_width
    angle_per_pixel_vertical = fov_vertical / frame_height
    
    # Calculate angles based on pixel offsets
    theta = pixel_offset_x * angle_per_pixel_horizontal
    phi = pixel_offset_y * angle_per_pixel_vertical * -1 # Inverting the vertical angle since Y increases downwards

    #print(f"Spherical Coordinates: Distance: {distance:.2f} cm, Theta: {theta:.2f}°, Phi: {phi:.2f}°")

    return distance, theta, phi

#######################

g_x = -1.0
g_y = -1.0
g_distance = -1.0
lx, ly, lw, lh = 0, 0, 0, 0
pos_simple = ""
additional_info = True
facetrack_loop = True

def setFacePos(nx, ny, nd):
    global g_x, g_y, g_distance
    g_x = nx
    g_y = ny
    g_distance = nd

def get_last_face_position():
    global lx, ly, lw, lh
    print(f"last position-> X: {lx}, Y: {ly}, W: {lw}, H: {lh}")
    print(f"last position (cont.) Center X: {lx+lw//2}, Center Y: {ly+lh//2}")
    print(f"last position (cont.) Distance: {100/lw:.4f}")
    distance, theta, phi = facepos_to_spherical_coordinates(lx, ly, lw, lh)
    print(f"last position (cont.) Spherical Coordinates: Distance: {distance:.2f} cm, Theta: {theta:.2f}°, Phi: {phi:.2f}°")
    button_action.config(state=tk.NORMAL)  # Re-enable the timer button in the main thread

def countdown(seconds):
    if seconds > 0:
        print(f"Starting in {seconds}...               ")
        root.after(1000, countdown, seconds-1)  # Schedule the next countdown step (1 second)
    else:
        get_last_face_position()  # Print out the last-record face position info

def start_countdown():
    button_action.config(state=tk.DISABLED)  # Disable the timer button to prevent multiple presses
    countdown(timer.get())

# Dummy face position summary
def printFacePos(new_x, new_y, new_dist):
    global g_x, g_y, g_distance, pos_simple
    if g_x == -1.0 or g_y == -1.0 or g_distance == -1.0:
        setFacePos(new_x, new_y, new_dist)
    else:
        if abs(new_x - g_x) > 0: g_x = new_x
        if abs(new_y - g_y) > 0: g_y = new_y
        if abs(new_dist - g_distance) > 0: g_distance = new_dist
    
    if additional_info:
        if g_y < 160: pos_simple = "Upper "
        elif g_y >= 160 and g_y < 320: pos_simple = "Middle "
        else: pos_simple = "Lower "
        if g_x < 213: pos_simple += "Left "
        elif g_x >= 213 and g_x < 426: pos_simple += "Center "
        else: pos_simple += "Right "
        if g_distance < .6: pos_simple += "Close"
        else: pos_simple += "Far  "
    else:
        pos_simple = ""
        
    output_str = f"X: {g_x}, Y: {g_y}, Distance: {g_distance:.2f}    {pos_simple}"
    print(output_str, end='\r', flush=True)
        
#### GUI STUFF ####

root = tk.Tk()
root.title("Control Panel")

def quit_program():
    global facetrack_loop
    facetrack_loop = False
    root.quit()
    root.destroy()

button_action = ttk.Button(root, text="Print Position", command=start_countdown)
button_action.pack(pady=5)

timer = tk.Scale(root, from_=0, to=15, orient='horizontal', label='Timer')
timer.pack(pady=5)

button_quit = ttk.Button(root, text="Quit Program", command=quit_program)
button_quit.pack(pady=5)

#### #### #### ####

# Load the face detection model
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Open the webcam:
# 0 is the default camera
# 1 is the USB camera (takes 3 minutes to load for some reason)
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
ret, frame = cap.read()
if ret:
    print(frame.shape)

# For some reason using the plot feature is way faster than just displaying the camera feed
plt.ion()
fig, ax = plt.subplots()
plt.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=0, hspace=0)  # Adjust subplot parameters (basically fullscreen)
im = ax.imshow(np.zeros((1080, 1920, 3)), aspect='equal')  # Set for the webcam resolution
plt.axis('off')

def getFacePositionFromVideo():
    global lx, ly, lw, lh
    ret, frame = cap.read()
    if not ret:
        return False  # Break out of the loop if the frame is not captured properly

    # Convert the frame to grayscale for face detection
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detect faces in the frame
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

    # Iterate over detected faces (just using the first face found)
    for (x, y, w, h) in faces:
        center_x = x + w // 2
        center_y = y + h // 2
        lx, ly, lw, lh = x, y, w, h
        center_distance = 100 / w
        output_str = f"X: {center_x}, Y: {center_y}, Distance: {center_distance:.2f}"
        print(output_str, end='\r', flush=True)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
        break; # Only track the first face

    # Display the resulting frame using matplotlib
    im.set_data(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    plt.pause(0.1)
    root.update_idletasks()
    root.update()
    
    return True

def main():
    try: 
        while facetrack_loop:
            if not getFacePositionFromVideo():
                break

            time.sleep(0.08)  # Delay to prevent burning a hole in my CPU

    except KeyboardInterrupt:
        print("\nInterrupted by user")

    finally:
        # Release the webcam and close the plot window
        cap.release()
        plt.close()
        #cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

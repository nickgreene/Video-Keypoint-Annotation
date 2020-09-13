import argparse
import cv2
import glob
import os
import numpy as np
import json
import copy

# you can configure these variables. Note: there must be at least as many COLORS as MAX_POINTS
MAX_POINTS = 8
POINT_SIZE = 3
STARTING_RESIZE_FACTOR = 5
STARTING_ROI = [(100, 100),(400,400)]
COLORS = [(0, 0, 255),
          (52, 152, 235),
          (52, 201, 235),
          (0, 255, 0),
          (255, 227, 87),
          (255, 0, 0),
          (255, 0, 127),
          (205, 102, 155),
          (235, 152, 225),
          (204, 153, 255),
          (0, 51, 102),
        ]

UI_SIZE = (200,400) # height, width

# Below is program code
resize_factor = STARTING_RESIZE_FACTOR
cropPt = [None, None]
roiPt = STARTING_ROI
refPt = []
resized_resolution = []
current_point = 0
is_point_selected = True
isMouseDown = False
isRMouseDown = False
image = None
read_mode = True
brightness = 0
is_current_image_saved = False
num_quit_attempts = 0
ui_message_length = 20
ui_frames = 0


output_file_name = "output.json"
backup_file_name = "backup.json"

def render_image():
    global image, refPt, isRMouseDown
    clone = image.copy()
 
    if brightness > 0:
        clone = np.minimum(255 - brightness, clone)
        clone += brightness
    
    if brightness < 0:
        clone = np.maximum(clone, -brightness)
        clone -= -brightness    
   
    for i in range(len(refPt)):
        if refPt[i] is not None:
            cv2.circle(clone, refPt[i], 3, COLORS[i], -1)
    
    if isRMouseDown:
        cv2.rectangle(clone, cropPt[0], cropPt[1], (0, 255, 0), 1)
        
    cv2.imshow("image", clone)


def render_roi():
    global image, roiPt, refPt
    roi = image[roiPt[0][1]:roiPt[1][1], roiPt[0][0]:roiPt[1][0]]
    resized_resolution = (round(roi.shape[1]*resize_factor), round(roi.shape[0]*resize_factor))
    roi = cv2.resize(roi, (resized_resolution[0], resized_resolution[1]))
    
    if brightness > 0:
        roi = np.minimum(255 - brightness, roi)
        roi += brightness
    
    if brightness < 0:
        roi = np.maximum(roi, -brightness)
        roi -= -brightness
    
    
    for i in range(len(refPt)):
        if refPt[i] is not None:
            x1, y1 = refPt[i]
            x2, y2 = roiPt[0]
            cv2.circle(roi, (round((x1 - x2) * resize_factor), round((y1 - y2) * resize_factor)), 3, COLORS[i], -1)
            
    cv2.imshow("ROI", roi)
    
    
def render_UI(current_image, total_images):
    global is_current_image_saved, image_index, glob_results, ui_frames  
    ui = np.zeros((UI_SIZE[0], UI_SIZE[1], 3), np.uint8)
    ui.fill(255)
    
    cv2.putText(ui, f"image {image_index}/{len(glob_results)}", ( (UI_SIZE[1]-250)//2, UI_SIZE[0]//5), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 1)
    
    if is_current_image_saved:
        saved_text = "frame saved"
    else:
        saved_text = "frame not saved"
        
    cv2.putText(ui, saved_text, ( (UI_SIZE[1]-250)//2, UI_SIZE[0]*2//5), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 1)
    
    current_point_for_UI = current_point + 1 - int(not is_point_selected) 
    if current_point >= MAX_POINTS:
        current_point_for_UI = MAX_POINTS
    
    if is_point_selected:
        current_point_text = f"current point: {current_point_for_UI}"
    else:
        current_point_text = f"current point: {current_point_for_UI}+"
        
    cv2.putText(ui, current_point_text, ( (UI_SIZE[1]-280)//2, UI_SIZE[0]*3//5), cv2.FONT_HERSHEY_SIMPLEX, 1, COLORS[current_point_for_UI-1], 2, cv2.LINE_AA)

    if ui_frames > 0:
        color = 0
        if ui_frames < ui_message_length // 3:        
            color = (255*((ui_message_length//3)-ui_frames))//(ui_message_length//3)
        cv2.putText(ui, "saved to output file", ( (UI_SIZE[1]-300)//2, UI_SIZE[0]*4//5), cv2.FONT_HERSHEY_SIMPLEX, 1, (color, color, color), 1, cv2.LINE_AA)
        ui_frames -= 1
            
    cv2.imshow("ui", ui)

    
def handle_mouse_event_image(event, x, y, flags, param):
    click_and_crop(event, x, y, flags, param, "image")

    
def handle_mouse_event_roi(event, x, y, flags, param):
    click_and_crop(event, x, y, flags, param, "ROI")


def click_and_crop(event, x, y, flags, param, window):
    global refPt, cropPt, roiPt, isMouseDown, isRMouseDown, image, current_point, is_point_selected, is_current_image_saved
    
    if event == cv2.EVENT_LBUTTONDOWN:
        if current_point > MAX_POINTS - 1:
            current_point = MAX_POINTS - 1
            
        isMouseDown = True
        
        if window == "image":
            refPt[current_point] = (x,y)
        
        if window == "ROI":
            x2, y2 = roiPt[0]
            refPt[current_point] = (round(x / resize_factor) + x2, round(y / resize_factor) + y2)
        
        is_current_image_saved = False
            
    elif event == cv2.EVENT_LBUTTONUP:
        isMouseDown = False
        is_point_selected = False
           
        if window == "image":
            refPt[current_point] = (x,y)
        
        if window == "ROI":
            x2, y2 = roiPt[0]
            refPt[current_point] = (round(x / resize_factor) + x2, round(y / resize_factor) + y2)
            
        current_point += 1
        if current_point > MAX_POINTS - 1:
            current_point = MAX_POINTS - 1
            is_point_selected = True
            
    elif event == cv2.EVENT_MOUSEMOVE:
        if isMouseDown:           
            if window == "image":
                refPt[current_point] = (x,y)
        
            if window == "ROI":
                x2, y2 = roiPt[0]
                refPt[current_point] = (round(x / resize_factor) + x2, round(y / resize_factor) + y2)
        
        elif isRMouseDown:
            if window == "image":
                cropPt[1] = (x, y)                       
            
    elif event == cv2.EVENT_RBUTTONDOWN:
        if window == "image":
            isRMouseDown = True
            cropPt = [(x, y), (x, y)]

    elif event == cv2.EVENT_RBUTTONUP:
        if window == "image":
            isRMouseDown = False                    
            
            x1 = cropPt[0][0]
            x2 = x
            y1 = cropPt[0][1]
            y2 = y
            
            if x < cropPt[0][0]:
                x1 = x
                x2 = cropPt[0][0]
                
            if y < cropPt[0][1]:
                y1 = y
                y2 = cropPt[0][1]
            
            
            if x1 < 0:
                x1 = 0
            
            if y1 < 0:
                y1 = 0
                
            roiPt = [(x1, y1), (x2, y2)]


def add_output_line(filename, file_contents, image_index, backup_file_object):
    global refPt, is_current_image_saved
    output_line = {"index": image_index}                
    
    for i in range(len(refPt)):
        if refPt[i] is not None:
            output_line[f"{i}"] = (refPt[i][0], refPt[i][1])
        else:
            output_line[f"{i}"] = None

    
    file_contents["data"][os.path.basename(filename)] = output_line
    
    backup_file_object.seek(0)
    json.dump(file_contents, backup_file_object, indent=2)
    backup_file_object.truncate()
    is_current_image_saved = True        

def write_output_file(output_filepath, contents):
    output_file = open(output_filepath, "w", 1)      
    json.dump(contents, output_file, indent=2, sort_keys=True)
    output_file.close()
    
def read_points(filename, file_contents, image_index):
    # not using image_index right now

    filename_without_path = os.path.basename(filename)
    
    if filename_without_path in file_contents['data']:        
        global refPt, is_current_image_saved
        line_contents = file_contents["data"][filename_without_path]
        is_current_image_saved = True
        
        for i in range(0, len(refPt)):
            refPt[i] = None
            if (f"{i}" in line_contents) and (line_contents[f"{i}"] is not None):
                refPt[i] = tuple(line_contents[f"{i}"])

                
        
if __name__ == "__main__":    
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--image_folder", required=True, help="Path to the image folder")
    ap.add_argument("-e", "--image_extension", required=True, help=".ppm, .pgm, .png")
    ap.add_argument("-f", "--starting_frame", required=False)
    
    args = vars(ap.parse_args())
    
    glob_results = glob.glob(os.path.join( args["image_folder"], f'*{args["image_extension"]}'))
    
    if len(glob_results) == 0:
        raise FileNotFoundError(f'No {args["image_extension"]} files found in {args["image_folder"]}')
    
    glob_results.sort()   

    output_filepath = os.path.join(args["image_folder"], output_file_name)
    backup_filepath = os.path.join(args["image_folder"], backup_file_name)    
   
    filename_index = 0
 
    if os.path.exists(output_filepath):
        f = open(output_filepath, "r")
        file_contents = json.load(f)
        f.close()
        
        filename_index = min(max(file_contents["current_index"] - 1, 0), len(glob_results) - 1)
        roiPt = file_contents["roi"]
        resize_factor = file_contents["scale"]
        brightness = file_contents["brightness"]

    else:
        file_contents = { "data":{} }
        
    original_file_contents = copy.deepcopy(file_contents)
    
    backup_file_object = open(backup_filepath, "w")
        
    refPt = []
    for i in range(MAX_POINTS):
        refPt.append(None)
        
    if args["starting_frame"] is not None:
        filename_index = min(max(int(args["starting_frame"]) - 1, 0), len(glob_results) - 1)
           
    while True:
        image_index = filename_index + 1
        filename = glob_results[filename_index]
        
        print(os.path.basename(filename))
        
        # note image index starts from 1 for first image, also header
        if read_mode:
            read_points(filename, file_contents, image_index)
        else:
            is_current_image_saved = False

        read_mode = True
        image = cv2.imread(filename)
        cv2.namedWindow("image")
        cv2.setMouseCallback("image", handle_mouse_event_image)
        cv2.namedWindow("ROI")
        cv2.setMouseCallback("ROI", handle_mouse_event_roi)
        next_image = False

        # keep looping until the 'ESC' key is pressed
        while not next_image:
            # display the image and wait for a keypress
            render_image()
            render_roi()
            render_UI(image_index, len(glob_results))
                
            key = cv2.waitKey(1) & 0xFF

            if not isMouseDown:
                if key == ord("q"):
                    num_quit_attempts += 1 # press q 10 times to quit without saving
                    print(f"quitting after {10 - num_quit_attempts} more q presses")
                    if num_quit_attempts > 9:
                        backup_file_object.close()
                        cv2.destroyAllWindows()
                        exit()
                        
                elif key != 255:
                    num_quit_attempts = 0
                        
                if key == ord(" ") or key == ord("]"):
                    next_image = True
                    add_output_line(filename, file_contents, image_index, backup_file_object)
        
                    filename_index += 1
                    if filename_index > len(glob_results) - 1:
                        filename_index = len(glob_results) - 1
                        
                    current_point = 0
                    is_point_selected = True
                    
                    if key == ord("]"):
                        read_mode = False
                        is_current_image_saved = False
                    
                elif key == ord("b") or key == ord("["):
                    next_image = True
                    add_output_line(filename, file_contents, image_index, backup_file_object)
                    
                    filename_index -= 1
                    if filename_index < 0:
                        filename_index = 0
                        
                    current_point = 0
                    is_point_selected = True
                    
                    if key == ord("["):
                        read_mode = False
                        is_current_image_saved = False
                
                elif key == ord("f"):
                    next_image = True

                    filename_index -= 1
                    if filename_index < 0:
                        filename_index = 0
                        
                    current_point = 0
                    is_point_selected = True
                    
                    for i in range(0, len(refPt)):
                        refPt[i] = None
                    
                
                elif key == ord("g"):
                    next_image = True
        
                    filename_index += 1
                    if filename_index > len(glob_results) - 1:
                        filename_index = len(glob_results) - 1
                        
                    current_point = 0
                    is_point_selected = True
                    
                    for i in range(0, len(refPt)):
                        refPt[i] = None
                    
                elif key == ord("v"):
                    add_output_line(filename, file_contents, image_index, backup_file_object)
                    
                    file_contents["current_index"] = image_index
                    file_contents["roi"] = roiPt
                    file_contents["scale"] = resize_factor
                    file_contents["brightness"] = brightness

                    write_output_file(output_filepath, file_contents)
                    ui_frames = ui_message_length
                    print("Saved and wrote to output file")

                elif key == ord("c"):
                    read_points(filename, original_file_contents, image_index)
                    is_current_image_saved = False

                elif key == 27:  # ESC key
                    file_contents["current_index"] = image_index
                    file_contents["roi"] = roiPt
                    file_contents["scale"] = resize_factor
                    file_contents["brightness"] = brightness

                    write_output_file(output_filepath, file_contents)
                    backup_file_object.close()
                    cv2.destroyAllWindows()
                    exit()
                    
                elif key == ord("r"):
                    is_current_image_saved = False

                    if is_point_selected:
                        refPt[current_point] = None
                        
                        if current_point > 0:
                            is_point_selected = False
                                        
                    else:
                        refPt[current_point - 1] = None
                        current_point -= 1
                        if current_point < 1:
                            current_point = 0
                            is_point_selected = True
                            
                elif key == ord("t"):
                    for i in range(0, len(refPt)):
                        refPt[i] = None
                
                    current_point = 0
                    is_point_selected = True
                    is_current_image_saved = False
                
                elif key == ord("="):
                    resize_factor += 0.2
                    
                elif key == ord("-"):
                    resize_factor -= 0.2
                    
                    if resize_factor < 0.6:
                        resize_factor = 0.4

                elif key == ord("1"):
                    current_point = 0
                    if current_point > MAX_POINTS - 1:
                        current_point = MAX_POINTS - 1
    
                    is_point_selected = True
                    
                elif key == ord("2"):
                    current_point = 1
                    if current_point > MAX_POINTS - 1:
                        current_point = MAX_POINTS - 1

                    is_point_selected = True
    
                elif key == ord("3"):
                    current_point = 2
                    if current_point > MAX_POINTS - 1:
                        current_point = MAX_POINTS - 1

                    is_point_selected = True
    
                elif key == ord("4"):
                    current_point = 3
                    if current_point > MAX_POINTS - 1:
                        current_point = MAX_POINTS - 1

                    is_point_selected = True
    
                elif key == ord("5"):
                    current_point = 4
                    if current_point > MAX_POINTS - 1:
                        current_point = MAX_POINTS - 1

                    is_point_selected = True
    
                elif key == ord("6"):
                    current_point = 5
                    if current_point > MAX_POINTS - 1:
                        current_point = MAX_POINTS - 1

                    is_point_selected = True
    
                elif key == ord("7"):
                    current_point = 6
                    if current_point > MAX_POINTS - 1:
                        current_point = MAX_POINTS - 1

                    is_point_selected = True
    
                elif key == ord("8"):
                    current_point = 7
                    if current_point > MAX_POINTS - 1:
                        current_point = MAX_POINTS - 1

                    is_point_selected = True
    
                elif key == ord("9"):
                    current_point = 8
                    if current_point > MAX_POINTS - 1:
                        current_point = MAX_POINTS - 1

                    is_point_selected = True
                    
                elif key == ord("w") or key == ord("i"):
                    index = current_point
                    if not is_point_selected:
                        index = current_point - 1
                        if index < 0:
                            index = 0
                                            
                    if refPt[index] is not None:
                        x, y = refPt[index]
                        refPt[index] = (x, y - 1)
                        
                    is_current_image_saved = False
                        
                elif key == ord("a") or key == ord("j"):
                    index = current_point
                    if not is_point_selected:
                        index = current_point - 1
                        if index < 0:
                            index = 0

                    if refPt[index] is not None:
                        x, y = refPt[index]
                        refPt[index] = (x - 1, y)
    
                    is_current_image_saved = False

                elif key == ord("s") or key == ord("k"):
                    index = current_point
                    if not is_point_selected:
                        index = current_point - 1
                        if index < 0:
                            index = 0

                    if refPt[index] is not None:                    
                        x, y = refPt[index]
                        refPt[index] = (x, y + 1)

                    is_current_image_saved = False
                        
                elif key == ord("d") or key == ord("l"):
                    index = current_point
                    if not is_point_selected:
                        index = current_point - 1
                        if index < 0:
                            index = 0
                        
                    if refPt[index] is not None:
                        x, y = refPt[index]
                        refPt[index] = (x + 1, y)

                    is_current_image_saved = False
    
                elif key == ord("z") or key == ord(","):
                    if is_point_selected:
                        current_point -= 1
                    else:
                        current_point -= 2
                    
                    if current_point < 0:
                        current_point = 0
                                        
                    is_point_selected = True
                                        
                elif key == ord("x") or key == ord("."):
                    if is_point_selected:
                        current_point += 1
                    
                    if current_point > MAX_POINTS - 1:
                        current_point = MAX_POINTS - 1
                        
                    is_point_selected = True
                    
                elif key == ord("y"):
                    brightness += 5
                    
                elif key == ord("h"):
                    brightness -= 5                
                
                elif key == ord("n"):
                    brightness = 0
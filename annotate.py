import argparse
import cv2
import glob
import os
import numpy as np
import json
import copy

# you can configure these variables. Note: there must be at least as many COLORS as MAX_POINTS
NUMBER_OF_ROIS = 3
MAX_POINTS = 27
SHAFT_POINT_1 = 19
SHAFT_POINT_2 = 20
POINT_SIZE = 3
STARTING_RESIZE_FACTOR = 5
STARTING_ROI = [(100, 100),(400,400)]
COLORS = [(75, 25, 230),
          (48, 130, 245),
          (25, 226, 255),
          (60, 245, 210),
          (75, 180, 60),
          (240, 240, 70),
          (200, 130, 0),
          (180, 30, 145),
          (230, 50, 240),
          (0, 0, 128),
          (40, 110, 170),
          (0, 128, 128),
          (128, 128, 0),
          (128, 0, 0),
          (212, 190, 250),
          (180, 215, 255),
          (200, 250, 255),
          (195, 255, 170),
          (255, 190, 220),
          (120, 120, 120),
          (220, 220, 220),
          (0, 137, 250),
          (0, 230, 162),
          (190, 250, 0),
          (230, 2, 35),
          (17, 3, 255),
          (227, 11, 222),
          (11, 160, 227)
        ]

################################################
UI_WINDOW_NAME = "ui"
IMAGE_WINDOW_NAME = "image"
ROI_WINDOW_NAME = "ROI"

UI_SIZE = (200,400) # height, width

default_selected_point = 0

# Below is program code
cropPt = [None, None]

roiPts = []
resize_factors = []
for i in range(NUMBER_OF_ROIS + 1):
    roiPts.append(STARTING_ROI)
    resize_factors.append(STARTING_RESIZE_FACTOR)
    
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
ui_saved_message_frames = 0

previous_point = 0
highlight_selected_point_frames = 0
highlight_point_length = 24

roi_selection = 1

undo_roi_pts = None

output_file_name = "output.json"
backup_file_name = "backup.json"

def render_image():
    global image, refPt, isRMouseDown, highlight_selected_point_frames
    clone = image.copy()
 
    resize_factor = resize_factors[0]
    resized_resolution = (round(clone.shape[1]*resize_factor), round(clone.shape[0]*resize_factor))
    clone = cv2.resize(clone, (resized_resolution[0], resized_resolution[1]))
 
    if brightness > 0:
        clone = np.minimum(255 - brightness, clone)
        clone += brightness
    
    if brightness < 0:
        clone = np.maximum(clone, -brightness)
        clone -= -brightness    
   
    if refPt[SHAFT_POINT_1] is not None and refPt[SHAFT_POINT_2] is not None:
        pt1 = (round(refPt[SHAFT_POINT_1][0]*resize_factor), round(refPt[SHAFT_POINT_1][1]*resize_factor))
        pt2 = (round(refPt[SHAFT_POINT_2][0]*resize_factor), round(refPt[SHAFT_POINT_2][1]*resize_factor))
        cv2.line(clone, pt1, pt2, COLORS[SHAFT_POINT_2], 3)
   
    for i in range(len(refPt)):
        if refPt[i] is not None:
            pt = (round(refPt[i][0]*resize_factor), round(refPt[i][1]*resize_factor))
            cv2.circle(clone, pt, 3, COLORS[i], -1)
            cv2.circle(clone, pt, 1, (0,0,0), -1)
            
    if highlight_selected_point_frames > 0:
        if refPt[current_point] is not None:
            color = 0
            if highlight_selected_point_frames < highlight_point_length // 3:        
                color = (255*((highlight_point_length//3)-highlight_selected_point_frames))//(highlight_point_length//3)
            
            pt = (round(refPt[current_point][0]*resize_factor), round(refPt[current_point][1]*resize_factor))
            cv2.circle(clone, pt, 15, (color, color, 255 - color), 4)
            highlight_selected_point_frames -= 1
    
    if isRMouseDown:
        pt1 = cropPt[0]
        pt2 = cropPt[1]
             
        cv2.rectangle(clone, pt1, pt2, (0, 255, 0), 1)
        
    cv2.imshow(IMAGE_WINDOW_NAME, clone)


def render_roi():
    global image, roiPt, refPt, highlight_selected_point_frames
    
    for idx in range(1, len(roiPts)):
        roiPt = roiPts[idx]
        resize_factor = resize_factors[idx]
        roi = image[roiPt[0][1]:roiPt[1][1], roiPt[0][0]:roiPt[1][0]]
        resized_resolution = (round(roi.shape[1]*resize_factor), round(roi.shape[0]*resize_factor))
 
        roi = cv2.resize(roi, (resized_resolution[0], resized_resolution[1]))
        
        if brightness > 0:
            roi = np.minimum(255 - brightness, roi)
            roi += brightness
        
        if brightness < 0:
            roi = np.maximum(roi, -brightness)
            roi -= -brightness
        
        if refPt[SHAFT_POINT_1] is not None and refPt[SHAFT_POINT_2] is not None:
            x0, y0 = refPt[SHAFT_POINT_1]
            x1, y1 = refPt[SHAFT_POINT_2]
            x2, y2 = roiPt[0]

            point_in_roi1 = (round((x0 - x2) * resize_factor), round((y0 - y2) * resize_factor))
            point_in_roi2 = (round((x1 - x2) * resize_factor), round((y1 - y2) * resize_factor))
            
            cv2.line(roi, point_in_roi1, point_in_roi2, COLORS[SHAFT_POINT_2], 3)
        
        for i in range(len(refPt)):
            if refPt[i] is not None:
                x1, y1 = refPt[i]
                x2, y2 = roiPt[0]
                
                point_in_roi = (round((x1 - x2) * resize_factor), round((y1 - y2) * resize_factor))
                cv2.circle(roi, point_in_roi, 3, COLORS[i], -1)
                cv2.circle(roi, point_in_roi, 1, (0,0,0), -1)
                
        if highlight_selected_point_frames > 0:
            if refPt[current_point] is not None:
                color = 0
                if highlight_selected_point_frames < highlight_point_length // 3:        
                    color = (255*((highlight_point_length//3)-highlight_selected_point_frames))//(highlight_point_length//3)
                
                x1, y1 = refPt[current_point]
                x2, y2 = roiPt[0]
                point_in_roi = (round((x1 - x2) * resize_factor), round((y1 - y2) * resize_factor))

                cv2.circle(roi, point_in_roi, 15, (color, color, 255 - color), 4)
                highlight_selected_point_frames -= 1
                
        cv2.imshow(f"{ROI_WINDOW_NAME}_{idx}", roi)
        
    
def render_UI(current_image, total_images):
    global is_current_image_saved, image_index, glob_results, ui_saved_message_frames  
    ui = np.zeros((UI_SIZE[0], UI_SIZE[1], 3), np.uint8)
    ui.fill(255)
    
    cv2.putText(ui, f"image {image_index}/{len(glob_results)}", ( (UI_SIZE[1]-250)//2, UI_SIZE[0]//6), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 1)
    
    if is_current_image_saved:
        saved_text = "frame saved"
    else:
        saved_text = "frame not saved"
        
    cv2.putText(ui, saved_text, ( (UI_SIZE[1]-250)//2, UI_SIZE[0]*2//6), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 1)
    
    current_point_for_UI = current_point + 1 - int(not is_point_selected) 
    if current_point >= MAX_POINTS:
        current_point_for_UI = MAX_POINTS
    
    if is_point_selected:
        current_point_text = f"current point: {current_point_for_UI}"
    else:
        current_point_text = f"current point: {current_point_for_UI}+"
        
    cv2.putText(ui, current_point_text, ( (UI_SIZE[1]-280)//2, UI_SIZE[0]*3//6), cv2.FONT_HERSHEY_SIMPLEX, 1, COLORS[current_point_for_UI-1], 2, cv2.LINE_AA)


    window_selected_text = "current Window: "
    if roi_selection == 0:
        window_selected_text += IMAGE_WINDOW_NAME
    else:
        window_selected_text += f"{ROI_WINDOW_NAME}_{roi_selection}"
    cv2.putText(ui, window_selected_text, ( (UI_SIZE[1]-360)//2, UI_SIZE[0]*4//6), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 1)


    if ui_saved_message_frames > 0:
        color = 0
        if ui_saved_message_frames < ui_message_length // 3:        
            color = (255*((ui_message_length//3)-ui_saved_message_frames))//(ui_message_length//3)
        cv2.putText(ui, "saved to output file", ( (UI_SIZE[1]-300)//2, UI_SIZE[0]*5//6), cv2.FONT_HERSHEY_SIMPLEX, 1, (color, color, color), 1, cv2.LINE_AA)
        ui_saved_message_frames -= 1
            
    cv2.imshow(UI_WINDOW_NAME, ui)

    
def handle_mouse_event_image(event, x, y, flags, param):
    click_and_crop(event, x, y, flags, IMAGE_WINDOW_NAME)

    
def handle_mouse_event_roi(event, x, y, flags, param):
    click_and_crop(event, x, y, flags, param)


def click_and_crop(event, x, y, flags, window):
    global refPt, cropPt, roiPts, linePt, isMouseDown, isRMouseDown, image, current_point, is_point_selected, is_current_image_saved
      
    if event == cv2.EVENT_LBUTTONDOWN:
        if current_point > MAX_POINTS - 1:
            current_point = MAX_POINTS - 1
            
        isMouseDown = True
        
        if window == IMAGE_WINDOW_NAME:
            refPt[current_point] = (round(x / resize_factors[0]), round(y / resize_factors[0]))
        
        if window[0:3] == "ROI":
            window_number = int(window[4:])
            resize_factor = resize_factors[window_number]
            
            x2, y2 = roiPts[window_number][0]
            refPt[current_point] = (round(x / resize_factor) + x2, round(y / resize_factor) + y2)
        
        is_current_image_saved = False
            
    elif event == cv2.EVENT_LBUTTONUP:
        isMouseDown = False
        is_point_selected = False
           
        if window == IMAGE_WINDOW_NAME:
            refPt[current_point] = (round(x / resize_factors[0]), round(y / resize_factors[0]))
        
        if window[0:3] == "ROI":
            window_number = int(window[4:])
            resize_factor = resize_factors[window_number]
            
            x2, y2 = roiPts[window_number][0]
            refPt[current_point] = (round(x / resize_factor) + x2, round(y / resize_factor) + y2)
            
        current_point += 1
        if current_point > MAX_POINTS - 1:
            current_point = MAX_POINTS - 1
            is_point_selected = True


    elif event == cv2.EVENT_RBUTTONDOWN:
        print(window, x, y)
        
        if window == IMAGE_WINDOW_NAME:
            x_pos = round(x / resize_factors[0])
            y_pos = round(y / resize_factors[0])
        
        if window[0:3] == "ROI":
            window_number = int(window[4:])
            resize_factor = resize_factors[window_number]
            
            x2, y2 = roiPts[window_number][0]
            
            x_pos = round(x / resize_factor) + x2
            y_pos = round(y / resize_factor) + y2

        print(x_pos, y_pos)

        min_dist = float('inf')

        if refPt is not None:
            for i, pt in enumerate(refPt):
                if pt is None:
                    continue

                x_pt, y_pt = pt
                dist = (x_pos - x_pt)**2 + (y_pos - y_pt)**2

                if dist < min_dist:
                    current_point = i
                    min_dist = dist
            
                print(current_point, min_dist, dist)

            is_point_selected = True


            
    elif event == cv2.EVENT_MOUSEMOVE:
        if isMouseDown:           
            if window == IMAGE_WINDOW_NAME:
                refPt[current_point] = (round(x / resize_factors[0]), round(y / resize_factors[0]))
        
            if window[0:3] == "ROI":
                window_number = int(window[4:])
                resize_factor = resize_factors[window_number]
                
                x2, y2 = roiPts[window_number][0]
                refPt[current_point] = (round(x / resize_factor) + x2, round(y / resize_factor) + y2)
        
        elif isRMouseDown:
            if window == IMAGE_WINDOW_NAME:
                cropPt[1] = (x,y)
            
    elif event == cv2.EVENT_MBUTTONDOWN:
        if window == IMAGE_WINDOW_NAME:
            isRMouseDown = True
            cropPt = [(x,y), (x,y)]

    elif event == cv2.EVENT_MBUTTONUP:
        if window == IMAGE_WINDOW_NAME:
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
                
                        
            x1 = round(x1 / resize_factors[0])
            x2 = round(x2 / resize_factors[0])
            y1 = round(y1 / resize_factors[0])
            y2 = round(y2 / resize_factors[0])
 
             
            if x1 != x2 and y1 != y2:
                roiPts[roi_selection] = [(x1, y1), (x2, y2)]


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
    ap.add_argument("-f", "--starting_frame", required=False, help="start on frame index (ignores save data for last frame)")
    ap.add_argument("-p", "--default_selected_point", required=False, type=int, help="Set the default starting point when ch")

    
    args = vars(ap.parse_args())

    if args["default_selected_point"] is not None:
        default_selected_point = args["default_selected_point"] - 1
    
    current_point = default_selected_point
    
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
        
        file_resize_factors = file_contents["scale"]
        for i in range(len(file_resize_factors)):
            resize_factors[i] = file_resize_factors[i] 
        
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
        
        cv2.namedWindow(UI_WINDOW_NAME, cv2.WINDOW_GUI_NORMAL  )

        cv2.namedWindow(IMAGE_WINDOW_NAME, cv2.WINDOW_GUI_NORMAL  )
        cv2.setMouseCallback(IMAGE_WINDOW_NAME, handle_mouse_event_image)
        

        for i in range(1, NUMBER_OF_ROIS+1):
            cv2.namedWindow(f"{ROI_WINDOW_NAME}_{i}", cv2.WINDOW_GUI_NORMAL  )
            cv2.setMouseCallback(f"{ROI_WINDOW_NAME}_{i}", handle_mouse_event_roi, f"{ROI_WINDOW_NAME}_{i}")

        next_image = False

        # keep looping until the 'ESC' key is pressed
        while not next_image:
            if current_point != previous_point:
                previous_point = current_point
                highlight_selected_point_frames = highlight_point_length
            
            # display the image and wait for a keypress
            render_image()
            render_roi()
            render_UI(image_index, len(glob_results))
                
            key = cv2.waitKey(1) & 0xFF

            if not isMouseDown:
                if key == ord("l"):
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
                        
                    current_point = default_selected_point
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
                        
                    current_point = default_selected_point
                    is_point_selected = True
                    
                    if key == ord("["):
                        read_mode = False
                        is_current_image_saved = False
                
                elif key == ord(","):
                    next_image = True

                    filename_index -= 1
                    if filename_index < 0:
                        filename_index = 0
                        
                    current_point = default_selected_point
                    is_point_selected = True
                    
                    for i in range(0, len(refPt)):
                        refPt[i] = None
                    
                
                elif key == ord("."):
                    next_image = True
        
                    filename_index += 1
                    if filename_index > len(glob_results) - 1:
                        filename_index = len(glob_results) - 1
                        
                    current_point = default_selected_point
                    is_point_selected = True
                    
                    for i in range(0, len(refPt)):
                        refPt[i] = None
                    

                elif key == ord("v"):
                    add_output_line(filename, file_contents, image_index, backup_file_object)
                    
                    file_contents["current_index"] = image_index
                    file_contents["roi"] = roiPt
                    file_contents["scale"] = resize_factors
                    file_contents["brightness"] = brightness

                    write_output_file(output_filepath, file_contents)
                    ui_saved_message_frames = ui_message_length
                    print("Saved and wrote to output file")

                elif key == ord("u"):
                    read_points(filename, original_file_contents, image_index)
                    is_current_image_saved = False

                elif key == ord("y"):
                    read_points(filename, file_contents, image_index)
                    is_current_image_saved = False

                elif key == 27:  # ESC key
                    add_output_line(filename, file_contents, image_index, backup_file_object)

                    file_contents["current_index"] = image_index
                    file_contents["roi"] = roiPt
                    file_contents["scale"] = resize_factors
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
                            
                # elif key == ord("t"):
                #     for i in range(0, len(refPt)):
                #         refPt[i] = None
                
                #     current_point = 0
                #     is_point_selected = True
                #     is_current_image_saved = False
                
                elif key == ord("="):
                    resize_factors[roi_selection] += 0.1
                    
                elif key == ord("-"):
                    resize_factors[roi_selection] -= 0.1
                    
                    if resize_factors[roi_selection] < 0.2:
                        resize_factors[roi_selection] = 0.1

                elif key == ord("1"):
                    roi_selection = 0
                    
                elif key == ord("2"):
                    roi_selection = 1
                
                elif key == ord("3"):
                    roi_selection = 2
    
                elif key == ord("4"):
                    roi_selection = 3
                                    
                elif key == ord("w"):
                    index = current_point
                    if not is_point_selected:
                        index = current_point - 1
                        if index < 0:
                            index = 0
                                            
                    if refPt[index] is not None:
                        x, y = refPt[index]
                        refPt[index] = (x, y - 1)
                        
                    is_current_image_saved = False
                        
                elif key == ord("a"):
                    index = current_point
                    if not is_point_selected:
                        index = current_point - 1
                        if index < 0:
                            index = 0

                    if refPt[index] is not None:
                        x, y = refPt[index]
                        refPt[index] = (x - 1, y)
    
                    is_current_image_saved = False

                elif key == ord("s"):
                    index = current_point
                    if not is_point_selected:
                        index = current_point - 1
                        if index < 0:
                            index = 0

                    if refPt[index] is not None:                    
                        x, y = refPt[index]
                        refPt[index] = (x, y + 1)

                    is_current_image_saved = False
                        
                elif key == ord("d"):
                    index = current_point
                    if not is_point_selected:
                        index = current_point - 1
                        if index < 0:
                            index = 0
                        
                    if refPt[index] is not None:
                        x, y = refPt[index]
                        refPt[index] = (x + 1, y)

                    is_current_image_saved = False
    
                elif key == ord("q"):
                    if is_point_selected:
                        current_point -= 1
                    else:
                        current_point -= 2
                    
                    if current_point < 0:
                        current_point = 0
                                        
                    is_point_selected = True
                                        
                elif key == ord("e"):
                    if is_point_selected:
                        current_point += 1
                    
                    if current_point > MAX_POINTS - 1:
                        current_point = MAX_POINTS - 1
                        
                    is_point_selected = True
                    
                elif key == ord("x"):
                    brightness += 5
                    
                elif key == ord("z"):
                    brightness -= 5                
                
                elif key == ord("c"):
                    brightness = 0

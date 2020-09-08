import argparse
import cv2
import glob
import os
from pprint import pprint
import numpy as np

# you can configure these variables. Note: there must be at least as many COLORS as MAX_POINTS
MAX_POINTS = 10
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

UI_SIZE = (200,300) # height, width

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
    global current_point, is_point_selected
    
    ui = np.zeros((UI_SIZE[0], UI_SIZE[1], 3), np.uint8)
    ui.fill(255)
    
    cv2.putText(ui, f"image {image_index}/{len(glob_results)}", ( (UI_SIZE[1]-250)//2, UI_SIZE[0]//4), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 1)
    
    
    current_point_for_UI = current_point + 1 - int(not is_point_selected) 
    if current_point >= MAX_POINTS:
        current_point_for_UI = MAX_POINTS
    
    if is_point_selected:
        current_point_text = f"current point: {current_point_for_UI}"
    else:
        current_point_text = f"current point: {current_point_for_UI}+"
        
    cv2.putText(ui, current_point_text, ( (UI_SIZE[1]-280)//2, UI_SIZE[0]*3//4), cv2.FONT_HERSHEY_SIMPLEX, 1, COLORS[current_point_for_UI-1], 2, cv2.LINE_AA)

    cv2.imshow("ui", ui)
    

    
def handle_mouse_event_image(event, x, y, flags, param):
    click_and_crop(event, x, y, flags, param, "image")

    
def handle_mouse_event_roi(event, x, y, flags, param):
    click_and_crop(event, x, y, flags, param, "ROI")


def click_and_crop(event, x, y, flags, param, window):
    global refPt, cropPt, roiPt, isMouseDown, isRMouseDown, image, current_point, is_point_selected
    
    if event == cv2.EVENT_LBUTTONDOWN:
        if current_point > MAX_POINTS - 1:
            current_point = MAX_POINTS - 1
            
        isMouseDown = True
        
        if window == "image":
            refPt[current_point] = (x,y)
        
        if window == "ROI":
            x2, y2 = roiPt[0]
            refPt[current_point] = (round(x / resize_factor) + x2, round(y / resize_factor) + y2)
            
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


def add_output_line(filename, file_contents, image_index):
    global refPt
    output_line = f"{filename},{image_index}"
                
    for i in range(len(refPt)):
        if refPt[i] is not None:
            output_line = f"{output_line},{refPt[i][0]},{refPt[i][1]}"
        else:
            output_line = f"{output_line},{None},{None}"

    output_line = f"{output_line}\n"
    # output_file.write(output_line)
    
    if image_index < len(file_contents):  # note image index starts from 1 for first image
        file_contents[image_index] = output_line           
    else:
        file_contents.append(output_line)
            

def write_output_file(output_filepath, contents):
    output_file = open(output_filepath, "w", 1)      
    output_file.writelines(contents)
    output_file.close()
    
    
def read_points(filename, file_contents, image_index):
    global refPt
       
    line_contents = file_contents[image_index][:-1].split(',')

    assert(filename == line_contents[0])
    assert(image_index == int(line_contents[1]))
           
    for i in range(0, len(refPt)):
        print(len(line_contents) - 1, i, 2*i + 2  )
        if (2*i + 2 < (len(line_contents) - 1)):
            if (line_contents[2*i + 2] == "None"):
                refPt[i] = None
            else:
                refPt[i] = (int(line_contents[2*i + 2]), int(line_contents[2*i + 3]))
                
        
if __name__ == "__main__":    
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--image_folder", required=True, help="Path to the image folder")
    ap.add_argument("-e", "--image_extension", required=True, help=".ppm, .pgm, .png")
    ap.add_argument("-r", "--read_points", required=False, action="store_true", help="Path to csv file corresponding to the image folder")   
    ap.add_argument("-f", "--starting_frame", required=False)
    
    args = vars(ap.parse_args())
    
    glob_results = glob.glob(os.path.join( args["image_folder"], f'*{args["image_extension"]}'))
    
    if len(glob_results) == 0:
        raise FileNotFoundError(f'No {args["image_extension"]} files found in {args["image_folder"]}')
    
    glob_results.sort()   

    output_filepath = os.path.join(args["image_folder"], "output.csv")    
    
    csv_header = "filename, image_index"
    for i in range(MAX_POINTS):
        csv_header = f"{csv_header}, x{i}, y{i}"
    csv_header = f"{csv_header}\n"
    
    file_contents = [csv_header]
    if os.path.exists(output_filepath):
        f = open(output_filepath, "r")
        file_contents = f.readlines()
        f.close()
        
    original_file_contents = file_contents.copy()
        
    refPt = []
    for i in range(MAX_POINTS):
        refPt.append(None)
        
    filename_index = 0
    
    if args["starting_frame"] is not None:
        filename_index = int(args["starting_frame"]) - 1
        
    while True:
        image_index = filename_index + 1
        
        filename = glob_results[filename_index]

        print(f"current image: {image_index} / {len(glob_results)}")

        if image_index < (len(file_contents)):  # note image index starts from 1 for first image, also header
            if read_mode:
                read_points(filename, file_contents, image_index)

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
                if key == ord(" ") or key == ord("]"):
                    next_image = True
                    add_output_line(filename, file_contents, image_index)
        
                    filename_index += 1
                    current_point = 0
                    is_point_selected = True
                    
                    if key == ord("]"):
                        read_mode = False
                    
                elif key == ord("b") or key == ord("["):
                    next_image = True
                    add_output_line(filename, file_contents, image_index)
                    
                    filename_index -= 1
                    if filename_index < 0:
                        filename_index = 0
                        
                    current_point = 0
                    is_point_selected = True
                    
                    if key == ord("["):
                        read_mode = False
                    
                elif key == ord("v"):
                    print(f"Saved Current Points for image {image_index} / {len(glob_results)}")
                    add_output_line(filename, file_contents, image_index)

                elif key == ord("c"):
                    print(f"loading originally saved points for image {image_index} / {len(glob_results)}")
                    if image_index < (len(file_contents)):  # note image index starts from 1 for first image, also header
                        read_points(filename, original_file_contents, image_index)

                elif key == 27:  # ESC key
                    write_output_file(output_filepath, file_contents)
                    # output_file.close()
                    cv2.destroyAllWindows()
                    exit()
                    
                elif key == ord("r"):
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
                        
                elif key == ord("a") or key == ord("j"):
                    index = current_point
                    if not is_point_selected:
                        index = current_point - 1
                        if index < 0:
                            index = 0

                    if refPt[index] is not None:
                        x, y = refPt[index]
                        refPt[index] = (x - 1, y)
    
                elif key == ord("s") or key == ord("k"):
                    index = current_point
                    if not is_point_selected:
                        index = current_point - 1
                        if index < 0:
                            index = 0

                    if refPt[index] is not None:                    
                        x, y = refPt[index]
                        refPt[index] = (x, y + 1)
                        
                elif key == ord("d") or key == ord("l"):
                    index = current_point
                    if not is_point_selected:
                        index = current_point - 1
                        if index < 0:
                            index = 0
                        
                    if refPt[index] is not None:
                        x, y = refPt[index]
                        refPt[index] = (x + 1, y)
                        
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
# video-annotation
 

Usage:

```
python annotate.py --image_folder PATH_TO_FOLDER_OF_IMAGES --image_extension FILE_EXTENSION_OF_IMAGES
```

additional options are:
-  ```--starting_frame```  - forces the program to start on frame index (ignoring the save data for last opened frame)
-  ```--default_selected_point```  - Set the default selected point to something other than 0 when moving to a new image


### Mouse Actions
- ```Left click```: left click on either the image window or the ROI window to move or create a keypoint
- ```Middle click``` middle click and drag on the main image window to select the ROI (Region of Interest). Note that you must first chose which ROI window you want using the ```1-9```. Nothing happens if you select a ROI when the main image window is selected (with ```1```). The default selected ROI_window is ```ROI_1``` (keypress ```2```)
- ```Right click```: right click selects the closest keypoint which is currently on the image


### Keyboard Shortcuts
- ```wasd```: move the selected point by one pixel
- ```1-9```: select a window (window 1 is the main image window)
- ```q/e```: increment/decrement the keypoint selection
- ```Spacebar``` | ```b```: save the current image and move to the next/previous image. Load saved keypoints for the new image if they already exist.
- ```[``` | ```]```: save the current image and move to the next/previous image. Copy over the keypoints from the previous image.
- ```<``` | ```>```: don't save the current image and move to the next/previous image. Load saved keypoints for the new image if they already exist.
- ```r```: delete the selected keypoint
- ```=``` | ```-```: enlarge/shrink the current window (Depends on the OpenCV window type)
- ```z``` | ```x```: increase/decrease image brightness
- ```c```: reset image brightness
- ```v```: force save the keypoints in the current image and write the output file
- ```u```: reload originally saved keypoints undoing any modifications if they existed in the save file upon startup
- ```y```: reset the keypoints to how they were when the current frame was loaded
- ```ESC```: quit and save changes (will save the current frame even if it says "unsaved")
- ```l```: press and hold to quit without saving any changes at all (quits after 10 uninterrupted 'l' presses)


### Intented Workflow
- Adjust image by first selecting the image window with ```1``` and then adjust the window size with ```+-``` (first run only)
- Set up ROIS by selecting the roi to edit with ```2-4``` and then dragging with the middle mouse button on the image window
- Insert keypoints in order by left clicking at the rough position and then nudging with ```wasd```. Once the keypoint is in the right spot you can left click to insert the next keypoint (when the UI window shows "current point: i+" a left click will insert/move the next point instead of moving the current point)
- Use ```q/e``` to skip keypoints or to go back and fix previous keypoints
- After the first frame is done, copy over the keypoints from the previous frame with `]`. Then use the mouse ```right click``` to select a point to edit. Move it to the new poisition with ```left click``` or ```wasd```. Repeat for all of the points. If needed, use ```q/e``` and ```left click``` to insert more points, or press ```r``` to delete a point.


### Saving
The output is automatically saved to ```output.json``` upon exiting with ```ESC```. Other information is also saved and recalled upon resuming including the current frame, window sizes, etc... 
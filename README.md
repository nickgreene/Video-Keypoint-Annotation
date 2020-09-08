# video-annotation
 

Usage:

```
python annotate.py --image_folder PATH_TO_FOLDER_OF_IMAGES --image_extension FILE_EXTENSION_OF_IMAGES
```

additional non-required option is ```--starting_frame ``` which forces the program to open that frame


### Mouse Actions
- Left click on either the image window or the ROI window to move or create a keypoint
- Right click and drag on the image window to select the ROI (Region of Interest)


### Keyboard Shortcuts
- ```wasd``` | ```ijkl```: move the selected point by one pixel
- ```1-9```: select a keypoint to edit
- ```z/x``` | ```,/.```: increment/decrement the keypoint selection
- ```Spacebar``` | ```b```: save the current image and move to the next/previous image. Load saved keypoints for the new image if they already exist.
- ```[``` | ```]```: save the current image and move to the next/previous image. Carry over the keypoints from the previous image.
- ```f``` | ```g```: don't save the current image and move to the next/previous image. Load saved keypoints for the new image if they already exist.
- ```r```: delete the selected keypoint
- ```t```: delete all of the keypoints in the current image
- ```=``` | ```-```: enlarge/shrink the ROI window
- ```y``` | ```h```: increase/decrease image brightness
- ```n```: reset image brightness
- ```v```: force save the keypoints in the current image and write the output file
- ```c```: reload originally saved keypoints undoing any modifications if they existed in the save file upon startup
- ```ESC```: quit and save changes (will not save current frame if it says "unsaved")
- ```q```: press and hold to quit without saving (quits after 10 uninterrupted 'q' presses)

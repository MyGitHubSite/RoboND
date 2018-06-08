## Project: Search and Sample Return


**The goals / steps of this project are the following:**  

**Training / Calibration**  

* Download the simulator and take data in "Training Mode"
* Test out the functions in the Jupyter Notebook provided
* Add functions to detect obstacles and samples of interest (golden rocks)
* Fill in the `process_image()` function with the appropriate image processing steps (perspective transform, color threshold etc.) to get from raw images to a map.  The `output_image` you create in this step should demonstrate that your mapping pipeline works.
* Use `moviepy` to process the images in your saved dataset with the `process_image()` function.  Include the video you produce as part of your submission.

**Autonomous Navigation / Mapping**

* Fill in the `perception_step()` function within the `perception.py` script with the appropriate image processing functions to create a map and update `Rover()` data (similar to what you did with `process_image()` in the notebook). 
* Fill in the `decision_step()` function within the `decision.py` script with conditional statements that take into consideration the outputs of the `perception_step()` in deciding how to issue throttle, brake and steering commands. 
* Iterate on your perception and decision function until your rover does a reasonable (need to define metric) job of navigating and mapping.  
---

### Writeup / README

### Notebook Analysis
#### 1. Run the functions provided in the notebook on test images (first with the test data provided, next on data you have recorded). Add/modify functions to allow for color selection of obstacles and rock samples.

I modified the color_thresh function (color_thresh2) to take in a range of rbg values. In order to have more control over detection. However, I left the rgb vales pretty much as used in the sample jupyter project and lectures as they were doing a decent job.

navigable terrain [[160,255],[160,255],[160,255]])
obstacles [[0,160],[0,160],[0,160]])
rocks [[100,255],[100,255],[0,50]])

Describe in your writeup (and identify where in your code) how you modified or added functions to add obstacle and rock sample identification. 

#### 1. Populate the `process_image()` function with the appropriate analysis steps to map pixels identifying navigable terrain, obstacles and rock samples into a worldmap.  Run `process_image()` on your test data using the `moviepy` functions provided to create video output of your result. 

Describe in your writeup how you modified the process_image() to demonstrate your analysis and how you created a worldmap. Include your video output with your submission.

[Boulder]: ./calibration_images/Boulders.jpg


![alt text][image2]
### Autonomous Navigation and Mapping

#### 1. Fill in the `perception_step()` (at the bottom of the `perception.py` script) and `decision_step()` (in `decision.py`) functions in the autonomous mapping scripts and an explanation is provided in the writeup of how and why these functions were modified as they were.

#### Perception

(1) The source and destination points were added to create a perspective from the camera image.

(2) The forward perspective was then warped to a top-down view.

(3) The color thresholds were run through the color_thresh2 function to identify navigable terrain and obstacles.

Modified the color_thresh function (color_thresh2) to take in a range of rbg values. In order to have more control over detection.  However, I left the rgb vales pretty much as used in the sample jupyter project and lectures as they were doing a decent job.
 - navigable terrain [[160,255],[160,255],[160,255]])
 - rocks [[100,255],[100,255],[0,50]])

(4) A rover vision was created so that the warped navigable terrain showed up as blue channel in an image and obstacles showed up in red in the image.  The warped and rover vision image are overlayed onto the simulator in order to visualize what the camera sees.
rover coordinates were calculated from the warped image.

(5) The rover coordinates were combined with the rover positions translate the rover vision image onto the world map.

(6) The navigable terrain from the rover image were converted to world coordinates.

(7) the navigable and obstacles in world coordinated were overlayed onto the world map in blue and the obstacles were overlayed onto the worldmap in red.  

Pitch and roll thresholds were used to control when to mpa navigable terrain and obstacles in order to increase the accuracy of the mapping.

(8) Navigable pixel angles and their distances were calcuated for use in the decision steps.

(9) A rock finding routine was added to find gold rocks in the rover camera image.

If any rock was found it was mapped onto the worldmap using the steps above.

The angles and distances to the rocks was calculated for use in the rock collecting routine.

Finally the Rover.seesrock property was set to true if a rock was found in the image.

#### Decision
 
This is where I spent the most time trying to improve the mapping%, fideilty%, and rock collection.  I wound up rewriting most of the code although many of the principles from the sample project were kept.
 
Notable additions/modifications:
 
Instead of using all navigable angles for calculating the steering angle while moving forward I used only angles beyond a certain distance (15).  This had the effect of focusing on longer angles for steering rather than short angles which the rover wouldn't be of much use to the rover while the rover is moving.  This allowed the rover to navigate the entire map in most cases with the added help of the stop and stuck routine to get out of jams from the dark boulders and while collecting rocks.

I changed the stop_forward and go_forward thresholds to longer distances to avoid getting too close to walls in dead ends and also to have a more clean pathway after a turn to avoid the walls.

I also changed the max velocity to 1.8 instead of 2.  Because I only used longer angles there was no need to go too fast.  I added a throttle calculator based on the ratio for narrow navigable angles to all longer navigable angles.  he higher the ratio the faster I allowed the rover to go.  The principle here was that when the pathway was more certain I cranked up the throttle.  When the pathway became more uncertain I slowed down.

I added a rock collecting routine.  When the rover sees the rock it uses the angles to the rock to steer instead of the navigable angles.  Also, I slowed way down as soon as it sees the rock and starts sterring towards it.  I modified the stop forward threshold for collecting a rock to 1 so that the rover stopped right in fron of the rock for collection.

I modified the stop routine so that when the rover comes to a halt it will search for a larger number of long angles to get a better restart out trouble.  Also, I added a calculation to be able to turn in a direction that helps move the rover toward unnavigated terrain when jammed up against a wall.

Within the forward, stop, and rock collection routines I added some code to allow for a stuck condition.  The stuck mode will cause the rover to move backwards and turn at an angle that will help create enough navigable angles to move forward successfully.

 - Forward: sees enough navigable angles but is jammed up and not moving forward.
 - Stop: turning not enough to get out of a jam.
 - Rock collecting: sees a rock but has an obstacle in the pathway.
 
 In drive_rover.py I added 4 new rover properties for use in the decision step
  - self.stuck_count   # keeps track of time spent in a stuck mode
  - self.stuck_time    # time to perform action while in stuck mode
  - self.seesrock      # does the rover see a rock?
  - self.throttle_collect = 0.04 # Throttle setting for slow 
  
#### 2. Launching in autonomous mode your rover can navigate and map autonomously.  Explain your results and how you might improve them in your writeup.  

My rover usually gets to > 75% mapped and > 75% fidelity quite easily though some problem areas pop up depending upon how the simulator was initialized. 

 Sometimes in certains parts of the map where it's a coin toss between going left or right my rover may need a few passes to eventually make the correct turn and continue on mapping unexplored regions.  I didn't want to over specify the decisions knowing what the map looks like so I avoided writing any kind of handling for the trouble spots.  If I had more time I would dive deeper into how the pixels, pitch, and roll are controlling the randomness and then fix so that the rover can traverse the map more quickly.  Right now the rover does a decent job with what I already implemented.
 
 The dark boulders are not getting picked up well enough in perception for the rover to avoid at times.  However, my stop and stuck routines and velocity control help the rover wiggle out of trouble eventually.  The boulders are 3D and the rover right now just isn't capable of avoiding getting jammed into them at times.
 
 My velocity and steering parameters as well as error handling parameters were determined by trial and error.  It would be fun to try and let the rover learn the best parameters through some deep learning.
 
 My rock collecting routine is working very well.  It was not difficult to implement.  The only trouble that popped up is sometimes the rover would get jammed into the sides of the mountain and get stuck for a while.  The stop and stuck routines fixed that problem.  If the rover can get to the whole map the rover will pick up all the rocks.
 
I did not have time to try and write a routine to return the rover back to the center of the map once all the rocks were collected.  I'm assuming this would be some sort of A* routine.  I would like to come back to this once I have more skills with building something like that.

By running drive_rover.py and launching the simulator in autonomous mode, your rover does a reasonably good job at mapping the environment. 

The rover must map at least 40% of the environment with 60% fidelity (accuracy) against the ground truth. You must also find (map) the location of at least one rock sample. They don't need to pick any rocks up, just have them appear in the map (should happen automatically if their map pixels in Rover.worldmap[:,:,1] overlap with sample locations.)

**Note: running the simulator with different choices of resolution and graphics quality may produce different results, particularly on different machines!  Make a note of your simulator settings (resolution and graphics quality set on launch) and frames per second (FPS output to terminal by `drive_rover.py`) in your writeup when you submit the project so your reviewer can reproduce your results.**

Here I'll talk about the approach I took, what techniques I used, what worked and why, where the pipeline might fail and how I might improve it if I were going to pursue this project further.  








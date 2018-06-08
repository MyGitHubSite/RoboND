import numpy as np
import cv2

# Identify pixels above the threshold
# Threshold of RGB > 160 does a nice job of identifying ground pixels only
def color_thresh(img, rgb_thresh=(160, 160, 160)):
    # Create an array of zeros same xy size as img, but single channel
    color_select = np.zeros_like(img[:,:,0])
    # Require that each pixel be above all three threshold values in RGB
    # above_thresh will now contain a boolean array with "True"
    # where threshold was met
    above_thresh = (img[:,:,0] > rgb_thresh[0]) \
                & (img[:,:,1] > rgb_thresh[1]) \
                & (img[:,:,2] > rgb_thresh[2])
    # Index the array of zeros with the boolean array and set to 1
    color_select[above_thresh] = 1
    # Return the binary image
    return color_select

def find_rocks(img, levels=(100,100,50)):
    # Create an array of zeros same xy size as img, but single channel    
    color_select = np.zeros_like(img[:,:,0])
    # Require that each pixel be within all three threshold values in RGB
    # within_thresh will now contain a boolean array with "True"
    # where threshold was met
    within_thresh = ((img[:,:,0] > levels[0]) \
             & (img[:,:,1] > levels[1]) \
             & (img[:,:,2] < levels[2]))
    # Index the array of zeros with the boolean array and set to 1
    color_select[within_thresh] = 1
    # Return the binary image
    return color_select

def color_thresh2(img, rgb_thresh):
    color_select = np.zeros_like(img[:,:,0])
    within_thresh = (np.greater_equal(img[:,:,0], rgb_thresh[0,0])) \
                  & (np.less_equal(   img[:,:,0], rgb_thresh[0,1])) \
                  & (np.greater_equal(img[:,:,1], rgb_thresh[1,0])) \
                  & (np.less_equal(   img[:,:,1], rgb_thresh[1,1])) \
                  & (np.greater_equal(img[:,:,2], rgb_thresh[2,0])) \
                  & (np.less_equal(   img[:,:,2], rgb_thresh[2,1]))   
    color_select[within_thresh] = 1
    return color_select

# Define a function to convert from image coords to rover coords
def rover_coords(binary_img):
    # Identify nonzero pixels
    ypos, xpos = binary_img.nonzero()
    # Calculate pixel positions with reference to the rover position being at the 
    # center bottom of the image.  
    x_pixel = -(ypos - binary_img.shape[0]).astype(np.float)
    y_pixel = -(xpos - binary_img.shape[1]/2 ).astype(np.float)
    return x_pixel, y_pixel


# Define a function to convert to radial coords in rover space
def to_polar_coords(x_pixel, y_pixel):
    # Convert (x_pixel, y_pixel) to (distance, angle) 
    # in polar coordinates in rover space
    # Calculate distance to each pixel
    dist = np.sqrt(x_pixel**2 + y_pixel**2)
    # Calculate angle away from vertical for each pixel
    angles = np.arctan2(y_pixel, x_pixel)
    return dist, angles

# Define a function to map rover space pixels to world space
def rotate_pix(xpix, ypix, yaw):
    # Convert yaw to radians
    yaw_rad = yaw * np.pi / 180
    xpix_rotated = (xpix * np.cos(yaw_rad)) - (ypix * np.sin(yaw_rad))
                            
    ypix_rotated = (xpix * np.sin(yaw_rad)) + (ypix * np.cos(yaw_rad))
    # Return the result  
    return xpix_rotated, ypix_rotated

def translate_pix(xpix_rot, ypix_rot, xpos, ypos, scale): 
    # Apply a scaling and a translation
    xpix_translated = (xpix_rot / scale) + xpos
    ypix_translated = (ypix_rot / scale) + ypos
    # Return the result  
    return xpix_translated, ypix_translated

# Define a function to apply rotation and translation (and clipping)
# Once you define the two functions above this function should work
def pix_to_world(xpix, ypix, xpos, ypos, yaw, world_size, scale):
    # Apply rotation
    xpix_rot, ypix_rot = rotate_pix(xpix, ypix, yaw)
    # Apply translation
    xpix_tran, ypix_tran = translate_pix(xpix_rot, ypix_rot, xpos, ypos, scale)
    # Perform rotation, translation and clipping all at once
    x_pix_world = np.clip(np.int_(xpix_tran), 0, world_size - 1)
    y_pix_world = np.clip(np.int_(ypix_tran), 0, world_size - 1)
    # Return the result
    return x_pix_world, y_pix_world

# Define a function to perform a perspective transform
def perspect_transform(img, src, dst):
           
    M = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(img, M, (img.shape[1], img.shape[0]))                        # keep same size as input image
    mask =   cv2.warpPerspective(np.ones_like(img[:,:,0]), M, (img.shape[1], img.shape[0]))
    return warped, mask

# Apply the above functions in succession and update the Rover state accordingly
def perception_step(Rover):
    # Perform perception steps to update Rover()
    # TODO: 
    # NOTE: camera image is coming to you in Rover.img
    
    # 1) Define source and destination points for perspective transform

    dst_size = 5 
        # Set a bottom offset to account for the fact that the bottom of the image 
        # is not the position of the rover but a bit in front of it
        # this is just a rough guess, feel free to change it!
    bottom_offset = 6
    image=Rover.img
    source = np.float32([[14, 140], [301 ,140],[200, 96], [118, 96]])
    destination = np.float32([[image.shape[1]/2 - dst_size, image.shape[0] - bottom_offset],
                  [image.shape[1]/2 + dst_size, image.shape[0] - bottom_offset],
                  [image.shape[1]/2 + dst_size, image.shape[0] - 2*dst_size - bottom_offset], 
                  [image.shape[1]/2 - dst_size, image.shape[0] - 2*dst_size - bottom_offset],
                  ])
    
    # 2) Apply perspective transform
    
    warped, mask = perspect_transform(image, source, destination)

    # 3) Apply color threshold to identify navigable terrain/obstacles samples

    rgb_nav = np.float32([[160,255],[160,255],[160,255]])           #navigible_rgb
    navigable = color_thresh2(warped, rgb_nav)                      #navigable

    #rgb_obs = np.float32([[0,160],[0,160],[0,160]])           #navigible_rgb    
    #obstacles = color_thresh2(warped, rgb_obs) * mask         #obstacles
    obstacles = np.absolute(np.float32(navigable)-1) * mask         #obstacles
    
    # 4) Update Rover.vision_image (this will be displayed on the left side of the screen)
    
    Rover.vision_image[:,:,2] = navigable * 255   #blue channel
    Rover.vision_image[:,:,0] = obstacles * 255   #red channel
                 
    # 5) Convert map image pixel values to rover-centric coords

    navigable_x, navigable_y = rover_coords(navigable)
    obstacles_x, obstacles_y = rover_coords(obstacles)

    # 6) Convert rover-centric pixel values to world coordinates

    world_size = Rover.worldmap.shape[0]
    scale = 2 * dst_size

    navigable_x_world, navigable_y_world = pix_to_world(navigable_x, navigable_y, Rover.pos[0], Rover.pos[1], Rover.yaw, world_size, scale)
    obstacles_x_world, obstacles_y_world = pix_to_world(obstacles_x, obstacles_y, Rover.pos[0], Rover.pos[1], Rover.yaw, world_size, scale)

    # 7) Update Rover worldmap (to be displayed on right side of screen)
    pitch = np.absolute(np.absolute(Rover.pitch-180)-180)
    roll = np.absolute(np.absolute(Rover.roll-180)-180)
    if pitch < 0.25 and roll < 0.25:    # reduce fideility loss from too much roll and pitch
        Rover.worldmap[navigable_y_world, navigable_x_world, 2] += 1   #blue channel
        Rover.worldmap[obstacles_y_world, obstacles_x_world, 0] += 1    #red channel

    # 8) Convert rover-centric pixel positions to polar coordinates

    dist, angles = to_polar_coords(navigable_x, navigable_y)
    
    Rover.nav_dists = dist
    Rover.nav_angles = angles

    #9) Find rocks
                 
    rgb_rock = np.float32([[100,255], [100,255], [0,50]])          #rocks_rgb
    rock = color_thresh2(warped, rgb_rock)                         #rocks
                 
    if rock.any():
        rock_x, rock_y = rover_coords(rock)        
        rock_x_world, rock_y_world = pix_to_world(rock_x, rock_y, Rover.pos[0], Rover.pos[1], Rover.yaw, world_size, scale)
       
        rock_dist, rock_angles = to_polar_coords(rock_x, rock_y)          

        Rover.rock_dists = rock_dist
        Rover.rock_angles = rock_angles

        rock_idx = np.argmin(rock_dist)
        rock_xcen = rock_x_world[rock_idx]
        rock_ycen = rock_y_world[rock_idx]         
                 
        Rover.worldmap[rock_ycen, rock_xcen, 1] = 255
        Rover.vision_image[:,:,1] = rock * 255        #green channel
        Rover.seesrock = True
    else:
        Rover.vision_image[:,:,1] = 0                  #green channel                 
        Rover.seesrock = False
    return Rover
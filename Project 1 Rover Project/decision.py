import numpy as np


# This is where you can build a decision tree for determining throttle, brake and steer 
# commands based on the output of the perception_step() function
def decision_step(Rover):

    # Implement conditionals to decide what to do given perception data
    # Here you're all set up with some basic functionality but you'll need to
    # improve on this decision tree to do a good job of navigating autonomously!

    ########################################################################################
    # capture states before going through all conditions
    mode = Rover.mode
    velocity = Rover.vel
    throttle = Rover.throttle
    nav_angles = Rover.nav_angles*180/np.pi
    nav_dists = Rover.nav_dists
    Rock_angles = Rover.rock_angles
    picking_up = Rover.picking_up
    # calculate key metrics in code
    long_nav_angles = nav_angles[nav_dists > 15]
    narrow_nav_angles = long_nav_angles[np.absolute(long_nav_angles)<15]
    ratio = len(narrow_nav_angles) / (len(long_nav_angles)+0.001)
    nav_steer = np.clip(np.mean(long_nav_angles), -15, 15)
    ########################################################################################
    # calculate go forward and stop forward conditions
    if len(long_nav_angles) > Rover.go_forward:
        go_forward = True
    else:
        go_forward = False

    if len(long_nav_angles) < Rover.stop_forward:
        stop_forward = True
    else:
        stop_forward = False
    #calculate the longest angle in a go forward condition
    if len(nav_angles) > 0 and go_forward == True:
        longest_steer = np.clip(nav_angles[np.argmax(nav_dists)],-15,15)
    else:
        longest_steer = -15 # default when no navigable angles or go foward condition not met
    ########################################################################################

    if mode == 'forward': 
        Rover.brake = 0  #release brake and let's go

        if stop_forward == True: # end of navigable terrain.  Stop and assess
            Rover.mode = 'stop'
            Rover.throttle = 0
            Rover.brake = Rover.brake_set

        else:
            Rover.steer = nav_steer  # plenty of navigable terrain so set a favorable steering angle
            
            if velocity < 0.01:
                Rover.steer = longest_steer  # if moving very slow search out for the longest angle to get going in a favorable direction

            if velocity >= 0.1:
                Rover.stuck_count=0  #if moving forward at a good velocity, reset the stuck count

            # calculate throttle based on ratio of narrow angles to all navigable angles
            if velocity < Rover.max_vel:
                if ratio > 0.7:
                    Rover.throttle = Rover.throttle_set
                elif ratio > 0.5:
                    Rover.throttle = Rover.throttle_set*0.7                                        
                elif ratio > 0.3:
                    Rover.throttle = Rover.throttle_set*0.5                                                            
                elif ratio > 0.1:
                    Rover.throttle = Rover.throttle_set*0.3                                                            
                else:
                    Rover.throttle = Rover.throttle_set*0.1                                                            
            
            if velocity >= Rover.max_vel: # if max velocity then come off throttle
                Rover.throttle=0

            # Is Rover Stuck?
            if (velocity > -0.02 and velocity < 0.02) and throttle != 0:
                Rover.stuck_count +=1
                if Rover.stuck_count >= 40:
                    Rover.mode='stuck'
                    Rover.stuck_count = Rover.stuck_time

    # If stuck then back up
    elif mode == 'stuck':
        Rover.throttle = -0.2   # reverse
        Rover.steer = -longest_steer  # when going backwards turn in the opposite direction of the longest angle.
        Rover.brake = 0
        Rover.stuck_count -= 1

        # go to Stop mode and assess
        if (Rover.stuck_count <= 0) and go_forward == True:
            Rover.mode = 'stop'
            Rover.throttle = 0
            Rover.brake = Rover.brake_set  #stop the rover

    elif mode == 'stop' and not Rover.picking_up:  #if in stop mode but still moving then stop
        if velocity != 0:
            Rover.throttle=0
            Rover.brake=Rover.brake_set

        else:
            if go_forward == False:
                Rover.throttle = 0
                Rover.brake =  0
                Rover.steer = longest_steer #turn in the direction that has the longest navigable angle.
                Rover.stuck_count +=1

                #is Rover stuck?
                if Rover.stuck_count >= 400:
                    Rover.mode='stuck'  # yes, go to stuck mode
                    Rover.stuck_count = Rover.stuck_time
            else:
                Rover.mode = 'forward'
                Rover.stuck_count = 0
        
    if Rover.seesrock == True and mode != 'Stuck':

        Rover.throttle =  Rover.throttle_collect   # slow down
        Rover.steer = np.clip(np.mean(Rover.rock_angles*180/np.pi),-15,15)

        # If Rover near rock sample, set throttle to 0 and apply brake to stop
        if Rover.near_sample and velocity != 0:
            Rover.throttle = 0
            Rover.brake = Rover.brake_set

        # If in a state where want to pickup a rock send pickup command
        if Rover.near_sample and velocity == 0 and not picking_up:
            Rover.send_pickup = True
            Rover.mode='stop'  #go to stop mode and assess nav angles
            Rover.stuck_count = 0

        if velocity == 0 and not picking_up:  #rover is not moving and not collecting rock is rover stuck?
            Rover.stuck_count += 1
            if Rover.stuck_count > 100:
                Rover.mode='stuck'
                Rover.stuck_count = 100
 
    return Rover


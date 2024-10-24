import math

class Reward:
    def __init__(self):
        self.prev_speed = 0
        self.prev_progress = 0.0
        self.prev_steps = 0
        self.prev_steering_angle = 0
        self.prev_x = 0.0
        self.prev_y = 0.0
        self.cumulative_episode_distance = 0
        self.pre_progress2 = 0
        self.pre_progress = 0

        # Define constants
        self.ZERO_REWARD = 0.0
        self.MIN_ZERO_REWARD = 0.001
        self.MIN_LOW_REWARD = 0.1
        self.AVERAGE_STEPS_PER_LAP = 260
        self.MAX_TOLERANCE_ANGLE = 60.0
        self.RADIUS_RATIO_WAYPOINT_LOOKUP = 0.6 # Rishee : Change to 0.65 ??


    def class_reward_function(self, params):
        # Read Parameters
        is_offtrack = params['is_offtrack']
        is_crashed = params['is_crashed']
        speed = params['speed']
        steps = params['steps']
        progress = params['progress']
        steering_angle = params['steering_angle']
        closest_waypoints = params['closest_waypoints']
        x = params['x']
        y = params['y']

        # Putting a blank link for clarity in logs
        print("")
        print("Current Step     : ", steps, " -- Current Progress : ", progress, " -- Previous Progress : ", self.prev_progress)
        print("Closest Waypoint : ", closest_waypoints[1], " -- x : ", x, " -- y : ", y)
        self.resetPreviousValuesOnFirstStep(params)


        rewardForCurrentProgress = self.calcRewardOnCurrentProgress(params)
        weighted_rewardForCurrentProgress = (1 * rewardForCurrentProgress)

        rewardForCurrentPosition = self.calcRewardOnCurrentPosition(params)
        weighted_rewardForCurrentPosition = (0 * rewardForCurrentPosition)

        rewardForOptimumSteering = self.calcRewardOnOptimumSteering(params)
        weighted_rewardForOptimumSteering = (0 * rewardForOptimumSteering)

        rewardForSmoothSteering = self.calcRewardOnSmoothSteering(params)
        weighted_rewardForSmoothSteering = (0 * rewardForSmoothSteering)

        rewardForDistanceExpVsActual = self.calcRewardOnDistanceExpVsActual(params)
        weighted_rewardForDistanceExpVsActual = (0 * rewardForDistanceExpVsActual)

        rewardForCompletedLap = self.calcRewardOnCompletedLap(params)
        weighted_rewardForCompletedLap = (0 * rewardForCompletedLap)

        reward = weighted_rewardForCurrentProgress + weighted_rewardForCurrentPosition + weighted_rewardForOptimumSteering + weighted_rewardForSmoothSteering + weighted_rewardForDistanceExpVsActual + weighted_rewardForCompletedLap

        print("")
        print("Reward Name      : Actual Value   --   Weighted Value   --   % Contribution of Total Reward")
        print("Current Progress : ", rewardForCurrentProgress, " -- ", weighted_rewardForCurrentProgress, " -- ", f"{weighted_rewardForCurrentProgress/reward:.3%}")
        print("Wheels on Track  : ", rewardForCurrentPosition, " -- ", weighted_rewardForCurrentPosition, " -- ", f"{weighted_rewardForCurrentPosition/reward:.3%}")
        print("Optimum Steering : ", rewardForOptimumSteering, " -- ", weighted_rewardForOptimumSteering, " -- ", f"{weighted_rewardForOptimumSteering/reward:.3%}")
        print("Smooth Steering  : ", rewardForSmoothSteering, " -- ", weighted_rewardForSmoothSteering, " -- ", f"{weighted_rewardForSmoothSteering/reward:.3%}")
        print("Optimum Distance : ", rewardForDistanceExpVsActual, " -- ", weighted_rewardForDistanceExpVsActual, " -- ", f"{weighted_rewardForDistanceExpVsActual/reward:.3%}")
        print("Completed Lap    : ", rewardForCompletedLap, " -- ", weighted_rewardForCompletedLap, " -- ", f"{weighted_rewardForCompletedLap/reward:.3%}")

        # Assign previous values
        self.prev_speed = speed
        self.prev_progress = progress
        self.prev_steps = steps
        self.prev_steering_angle = steering_angle
        self.prev_x = x
        self.prev_y = y

        # If crashed don't consider any other rewards
        if is_offtrack or is_crashed:
            print("ZERO Reward for OffTrack : ", self.MIN_ZERO_REWARD)
            reward = self.MIN_ZERO_REWARD

        print("FINAL Reward     : ", reward)
        return max(reward, self.MIN_ZERO_REWARD)

    ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### #####
    # Force resetting on step 2 as direct instantiation reset is having issues
    def resetPreviousValuesOnFirstStep(self, params):
        steps = params['steps']
        waypoints = params['waypoints']
        closest_waypoints = params['closest_waypoints']


        if steps == 2:
            self.prev_speed = 0
            self.prev_progress = 0.0
            self.prev_steps = 0
            self.prev_steering_angle = 0

            prev_waypoint = waypoints[closest_waypoints[0]]
            self.prev_x = prev_waypoint[0]
            self.prev_y = prev_waypoint[1]
            self.cumulative_episode_distance = 0

            print("**** **** PREVIOUS VALUES RESET **** ****")
            print("Cumulative Distance : ", self.cumulative_episode_distance, " -- X : ", self.prev_x, " -- Y : ", self.prev_y)


  
    
    ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### #####
    # Level : Each Step - Calculate reward on progress
    def calcRewardOnCurrentProgress(self, params):    
        this_reward = 0
        steps = params['steps']
        speed = params['speed']
        progress = params['progress']
        MINIMUM_SPEEDING_STEPS = 6
        if((steps <= MINIMUM_SPEEDING_STEPS) and (speed >= 3.75)):
            this_reward = 1
        else:
            this_reward = self.MIN_ZERO_REWARD
    
 
        if (steps > MINIMUM_SPEEDING_STEPS):
            this_reward = ((progress- self.pre_progress)*2)**2 + ((progress- self.pre_progress2))**2
            

        if ((progress - self.pre_progress)>=5) or ((progress - self.pre_progress2)>=5):
            this_reward = self.MIN_ZERO_REWARD
      
        
        self.pre_progress2 = self.pre_progress
        self.pre_progress = progress
        return max(this_reward, self.MIN_ZERO_REWARD)

    ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### #####
    # Calculate the reward for current position
    # Supporting rewards, try to keep overall value less than (0.5 or 0.75 of main rewards)
    def calcRewardOnCurrentPosition(self, params):
        all_wheels_on_track = params['all_wheels_on_track']
        steps = params['steps']
        distance_from_center = params['distance_from_center']
        track_width = params['track_width']

        if steps <= self.AVERAGE_STEPS_PER_LAP:
            if all_wheels_on_track and (0.5*track_width - distance_from_center) >= 0.05:
                this_reward = 1
            else:
                this_reward = self.MIN_LOW_REWARD
        else:
            this_reward = self.MIN_ZERO_REWARD

        return this_reward
    ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### #####
    # Level : Each Step - Reward if actual distance covered is less than expected distance
    # This will encourage it to take shorter routes
    def calcRewardOnDistanceExpVsActual(self, params):
        progress = params['progress']
        track_length = params['track_length']

        self.cumulative_episode_distance += self.calcCurrentStepCarDistance(params)
        expectedDistance = (progress * track_length)/100

        this_reward = 2 * (expectedDistance - self.cumulative_episode_distance)
        print("Distance. Expected : ", expectedDistance, " -- Actual : ", self.cumulative_episode_distance, " -- Current Diff : ", (expectedDistance - self.cumulative_episode_distance))

        return max(this_reward, self.MIN_ZERO_REWARD)

    ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### #####
    # Calculate the reward for completed lap
    def calcRewardOnCompletedLap(self, params):
        progress = params['progress']
        steps = params['steps']
        track_length = params['track_length']

        distance_reward = 0.0
        steps_reward = 0.0

        if math.isclose(progress, 100.0):
            #Logic for distance reward
            distanceDiff = track_length - self.cumulative_episode_distance
            if distanceDiff > 0:
                distance_reward = 50 * distanceDiff
            else:
                distance_reward = self.ZERO_REWARD

            #Logic for step reward
            steps_diff = self.AVERAGE_STEPS_PER_LAP - steps
            if steps_diff > 0:
                steps_reward = 0.1 * (steps_diff ** 2)
            else:
                steps_reward = self.ZERO_REWARD

            print("Final. Distance Diff : ", distanceDiff, " -- Distance Reward : ", distance_reward)
            print("Final. Steps Diff : ", steps_diff, " -- Steps Reward : ", steps_reward)

        this_reward = steps_reward + distance_reward
        return this_reward

    ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### #####
    def calcCurrentStepCarDistance(self, params):
        steps = params['steps']
        carDistance = 0.0

        if steps >= 2:
            currentCarPosition = [params['x'], params['y']]
            previousCarPosition = [self.prev_x, self.prev_y]
            carDistance = self.calcDistance(currentCarPosition, previousCarPosition)

        return carDistance
    ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### #####
    # Calculate the reward for optimum steering
    # Supporting rewards, try to keep overall value less than (0.5 or 0.75 of main rewards)
    def calcRewardOnSmoothSteering(self, params):
        steering_angle = params['steering_angle']
        steeringDiff = abs(steering_angle - self.prev_steering_angle)

        print("Steering. Curr : ", steering_angle, " -- Prev : ", self.prev_steering_angle, " -- Diff : ", steeringDiff)
        this_reward = math.exp(-0.15 * steeringDiff)

        # Checking if steering direction is changing
        if (steering_angle * self.prev_steering_angle) >= 0:
            this_reward = 1.5 * this_reward
        else:
            this_reward = 0.75 * this_reward

        return max(this_reward, self.ZERO_REWARD)

    ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### #####
    # Calculate the reward for optimum steering
    def calcRewardOnOptimumSteering(self, params):
        heading = params['heading']
        steering_angle = params['steering_angle']

        best_steering_angle = self.getBestSteeringAngleDegrees(params)
        error = (steering_angle - best_steering_angle) / self.MAX_TOLERANCE_ANGLE
        this_reward = 1.0 - abs(error)
        print(" -- Heading : ", heading, " -- Target Angle : ", (heading + best_steering_angle), " -- Best Str : ", best_steering_angle)

        return max(this_reward, self.MIN_ZERO_REWARD)
    ##### ##### #####   HELPER FUNCTIONS - START    ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### #####
    # Calculates the best Steering angle in degrees
    def getBestSteeringAngleDegrees(self, params):
        heading = params['heading']

        target_angle = self.get_target_angle(params)
        best_steering_angle = target_angle - heading

        return self.angle_mod_360(best_steering_angle)

    def get_target_angle(self,params):
        car_x = params['x']
        car_y = params['y']

        tx, ty = self.get_target_point(params)
        dx = tx-car_x
        dy = ty-car_y

        _, target_angle = self.polar(dx, dy)
        return target_angle

    def get_target_point(self,params):
        waypoints = params['waypoints']
        waypoints = self.up_sample(waypoints, 20)
        car = [params['x'], params['y']]

        distances = [self.calcDistance(p, car) for p in waypoints]
        min_dist = min(distances)
        i_closest = distances.index(min_dist)
        n = len(waypoints)

        waypoints_starting_with_closest = [waypoints[(i+i_closest) % n] for i in range(n)]
        r = params['track_width'] * self.RADIUS_RATIO_WAYPOINT_LOOKUP
        is_inside = [self.calcDistance(p, car) < r for p in waypoints_starting_with_closest]
        i_first_outside = is_inside.index(False)

        if i_first_outside < 0:  # this can only happen if we choose r as big as the entire track
            return waypoints[i_closest]

        return waypoints_starting_with_closest[i_first_outside]

    def calcDistance(self, point1, point2):
        return ((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2) ** 0.5

    # Adds extra waypoints in between provided waypoints
    # param factor: integer. E.g. 3 means that the resulting list has 3 times as many points
    def up_sample(self, waypoints, factor):
        p = waypoints
        n = len(p)

        return [[i / factor * p[(j+1) % n][0] + (1 - i / factor) * p[j][0],
                 i / factor * p[(j+1) % n][1] + (1 - i / factor) * p[j][1]] for j in range(n) for i in range(factor)]

    # Calculates radius and angle in degrees
    def polar(self, x, y):

        r = (x ** 2 + y ** 2) ** .5
        theta = math.degrees(math.atan2(y,x))
        return r, theta

    # Maps an angle to the interval -180, +180
    # angle_mod_360(362) == 2
    # angle_mod_360(270) == -90
    #
    # return: angle in degree. Between -180 and +180
    def angle_mod_360(self, angle):
        n = math.floor(angle/360.0)
        angle_between_0_and_360 = angle - n*360.0

        if angle_between_0_and_360 <= 180.0:
            return angle_between_0_and_360
        else:
            return angle_between_0_and_360 - 360

    ##### ##### #####   HELPER FUNCTIONS -  END     ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### #####
    ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### ##### #####

reward_object = Reward()

def reward_function(params):
    # Reward function for Team MUDR24-279 for RModel

    final_reward = reward_object.class_reward_function(params)
    return float(final_reward)

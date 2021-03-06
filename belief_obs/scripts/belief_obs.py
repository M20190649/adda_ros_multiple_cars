#! /usr/bin/env python


import rospy

import math
import numpy as np
# import matplotlib.pyplot as plt

from std_msgs.msg import Bool
from scipy.stats import multivariate_normal

import tf
import time

class BeliefObs:

    def __init__(self):
        print "Starting Observation"
        self.x = []
        self.pos_car2 = []
        self.listener = tf.TransformListener()
        time.sleep(0.5)

        # setup publisher
        self._examplePublisher = rospy.Publisher('/belief_obs/exampletopic', Bool, queue_size=10)
        self.timer = rospy.Timer(rospy.Duration(0.1), self.my_callback)

        self.belief = []
        self.belief.append(0.5) # prob that goal is 1
        self.belief.append(0.5) # prob that goal is 2
        #[0.5 , 0.5]

        self.goals = []
        self.goals.append([38.0, 3.0, 1.0]) # random goal
        self.goals.append([30.0, 32.0, 1.0]) # target goal

    def observation_probability(self, current_position, mues, sigma):
        # Gaussian Probability distribution
        # Dimentionality: n = 2 (x, y)
        # x => cuttent observation
        # mue => calculated possition from mue function (using position from the last step)
        # sigma - noise of prob. from sigma function
        # T - transpose of the vector/matrix

        observation_probability = []


          # last observed possition

        for i in range(len(mues)):
            # mue=np.array(mue)
            # mue=mues[i]
            # mue=np.array( mue)
            # sigma=sigmas[i]
            # print mue
            # print (mues[i].shape)
            # print sigma
            # print (sigma.shape)

            observation_probability.append(multivariate_normal.pdf(current_position, mues[i], sigma))

            # print ("step prob: ", observation_probability)


        return observation_probability

    def mue(self, last_observed_pos):
        # mue - car2 movement function. Will calculate new position from:
        # last observed position (x,y) ; velocity (v) and goal (g) after delta_t

        mue_array = []
        for goal in self.goals:
            vel_car2 = 1 # I need to get it from somewhere
            # (maybe calculate from distance speed = distance / time )
            delta_t = 0.2 # also need to calculate

            last_observed_pos = np.array(last_observed_pos, dtype='f')
            goals = np.array(goal, dtype='f')

            normalized_unit_vector_counter = goals - last_observed_pos  # (x, y, z)
            normalized_unit_vector_denominator = math.sqrt((goals[0] - self.pos_car2[0]) ** 2 + (goals[1] - self.pos_car2[1]) ** 2 + (goals[2] - self.pos_car2[2]) ** 2)  # euclidean distance

            mue = ((normalized_unit_vector_counter / normalized_unit_vector_denominator) * vel_car2 * delta_t) + last_observed_pos  # should be (x, y, z)
            mue_array.append(mue)


      #  print("mue_array", mue_array)

        return mue_array


    def sigma(self):
        # How noisy prediction is? Identity martix multiplied by small factor.
        # Dimentionality of the matrix depends on dimensionality of vectors.
        # The formula will compute the likelihood of the observation (so needs info also about noise).
        # With low noise, the likelihood will be close to the mean.

        identitymatrix = np.eye(3)
        factor = 0.1
        sigma = identitymatrix * factor
        return sigma

    def belief_update(self, observation_probability):
        # Belief update for goals (for two goals together)
        belief_array = []
        numerator_array = []
        denominator_array = []

        i = 0
        for op in observation_probability:
            numerator = op * self.belief[i]
            numerator_array.append(numerator)
            denominator_array.append(numerator)

            #belief = (op * self.belief[i]) / (self.observation_probability[0] * self.belief[0] + self.observation_probability[1] * self.belief[1])
            #belief_array.append(belief)
            i = i + 1

        for value in numerator_array:
            sumassion = sum(denominator_array[0:len(denominator_array)])
            belief = value / sumassion
            belief_array.append(belief)

        return belief_array



    def my_callback(self, event):

        #print 'Timer called at ' + str(event.current_real)
        #lop = self.mue()
        #noise = self.sigma()
        #probaility = self.probability(x, lop, noise)

        time_now = rospy.Time(0)
        r = rospy.Rate(5) # frequency
        probability_history = []
        belief_history = []

        step_observation = []


        while not rospy.is_shutdown():
            (trans2, rot2) = self.listener.lookupTransform('/map', '/car2/base_link', time_now)
            self.pos_car2 = trans2

            if len(step_observation) == 0:
                step_observation.append(self.pos_car2)


            print ("Current car2 possition: ", self.pos_car2)
            now = rospy.get_rostime()
            r.sleep()

            # print ("Delta_t: ", rospy.get_rostime() - now) # delta t

            muetes = self.mue(step_observation[0])

            # print("muetes", muetes)

            step_observation_probability = self.observation_probability(self.pos_car2, muetes, self.sigma())
            # print ("step_observation_probability", step_observation_probability)

            # store current observation for next step
            step_observation[0] = self.pos_car2

            step_belief = self.belief_update(step_observation_probability)
            print("step belief", step_belief)
            self.belief = step_belief
            print ("")
            # probability_history.append(step_observation_probability)
            # step_belief = self.belief_update(step_observation_probability, probability_history)
            # belief_history.append(step_belief)

        print probability_history
        print belief_history





   

if __name__ == '__main__':
    rospy.init_node("belief_obs")
    belief_update = BeliefObs()
    rospy.spin()

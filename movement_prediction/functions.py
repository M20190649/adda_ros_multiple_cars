import cv2
from scipy.stats import multivariate_normal
from scipy.interpolate import NearestNDInterpolator
import numpy as np
import pandas as pd
import glob
import matplotlib.pyplot as plt
import math
import random
import sys
from matplotlib.collections import PatchCollection

# Sets plot style to given theme
plt.style.use("seaborn")

def replace_zeros_in_list(list):
    """
    Takes in a list, replaces zero with really small values to avoid divide by zero or cascade effect
    :param list:
    :return: list
    """
    for (i, item) in enumerate(list):
        if item == 0:
            list[i] = 0.00001
    return list

def read_csv_fast(file):
    """
    Faster way to read csv files using Pandas since numpy's csv reading functions (genfromtxt and loadtxt) are very slow especially when number of
    files is larger
    """
    return pd.read_csv(file, skiprows=1).values

def recognize_map(map_file):
    """
    Given a type of map file, try to recognize using geometric operations which
    type of map it is.
    """

    img1 = cv2.imread('maps/testmap5.png')
    img2 = cv2.imread('maps/testmap6_0_.png')
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    ret1, thresh1 = cv2.threshold(gray1, 127, 255, 1)
    ret2, thresh2 = cv2.threshold(gray2, 127, 255, 1)
    img1, contours1, h1 = cv2.findContours(thresh1, 1, 2)
    img2, contours2, h2 = cv2.findContours(thresh2, 1, 2)
    x = 0
    y = 0

    for cnt1 in contours1:
        approx1 = cv2.approxPolyDP(cnt1, 0.01 * cv2.arcLength(cnt1, True), True)

        if len(approx1) == 4:
            x = x + 1
            cv2.drawContours(img1, [cnt1], 0, (0, 0, 255), -1)

    for cnt2 in contours2:
        approx2 = cv2.approxPolyDP(cnt2, 0.01 * cv2.arcLength(cnt2, True), True)

        if len(approx2) == 4:
            y = y + 1
            cv2.drawContours(img2, [cnt2], 0, (0, 0, 255), -1)

    print("x = ", x)
    print("y = ", y)

    if x > y:
        cv2.waitKey(0)
        cv2.imwrite('output/X.png', img1)
        cv2.imwrite('output/T.png', img2)
        cv2.destroyAllWindows()
    elif x < y:
        cv2.waitKey(0)
        cv2.imwrite('output/T.png', img1)
        cv2.imwrite('output/X.png', img2)
        cv2.destroyAllWindows()

    img1 = cv2.imread(map_file)
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    ret1, thresh1 = cv2.threshold(gray1, 127, 255, 1)
    im1, contours1, h1 = cv2.findContours(thresh1, 1, 2)
    x = 0

    for cnt1 in contours1:
        approx1 = cv2.approxPolyDP(cnt1, 0.01 * cv2.arcLength(cnt1, True), True)

        if len(approx1) == 4:
            x = x + 1
            cv2.drawContours(img1, [cnt1], 0, (0, 0, 255), -1)

    if x == 8:
        print("This Image is X-intersection")

    elif x == 4:
        print("This Image is T-intersection")

def clear_plot():
    """
    Clears the graph plot after each interval
    """
    plt.title('Movement Classification f = y(x)')
    plt.xlabel('x [m]')
    plt.ylabel('y [m]')

def interpolate_dist(x, y, len_des):
    """
    Takes in a trajectory and interpolates it to specified number of points.
    For example 1000 point to 100 or 10.
    """

    xd = np.diff(x)
    yd = np.diff(y)

    dist = np.sqrt(xd ** 2 + yd ** 2)
    u = np.cumsum(dist)
    u = np.hstack([[0], u])

    t = np.linspace(0, u.max(), len_des)

    xn = np.interp(t, u, x)
    yn = np.interp(t, u, y)

    return xn, yn

# calculated using the last formula on the formulas paper
def calculate_covariance_for_class(trajectories_in_class, number_points):
    """
    Given all trajectories in a class, this function calculates
    covariance against all trajectories in each class
    """
    cov_for_all_timesteps = []
    for point in range(number_points):
        calculate_cov_on = []
        for trajectory in range(len(trajectories_in_class)):
            calculate_cov_on.append(trajectories_in_class[trajectory][point])

        cov_for_this_timestep = np.cov(calculate_cov_on, rowvar=False)
        cov_for_all_timesteps.append(cov_for_this_timestep)
    return cov_for_all_timesteps

# simple probability formula for one point instead of full trajectory like
def simple_probability(point, mean, covariance):
    return multivariate_normal.pdf(point, mean, covariance)

# calculated using the pdf formula, 2) equation on the formulas paper
def probability(test_trajectory, mean_of_all_classes, covariance):
    """
    Given a test trajectory, this function calculates probability density across
    different classes (right, left or straight) for each point based on mean and covariance
    of the trajectory
    """
    # array to collect probabilities for each point
    observation_probability = []

    # loop over each point and calculate PDF
    for point_in_test_trajectory in range(len(test_trajectory)):
        # calculate pdf for single time step
        pdf_for_this_timestamp = multivariate_normal.pdf(test_trajectory[point_in_test_trajectory],
                                                         mean_of_all_classes[point_in_test_trajectory],
                                                         covariance[point_in_test_trajectory])
        # append calculated pdf to the master array defined above
        observation_probability.append(pdf_for_this_timestamp)
    return observation_probability

def probability_with_power(test_trajectory, mean_of_all_classes, covariance, power):
    """
    Clone of above function for testing purposes, simply applies power on each PDF.

    Given a test trajectory, this function calculates probability density across
    different classes (right, left or straight) for each point based on mean and covariance
    of the trajectory
    """
    # array to collect probabilities for each point
    observation_probability = []

    # loop over each point and calculate PDF
    for point_in_test_trajectory in range(len(test_trajectory)):
        # calculate pdf for single time step
        pdf_for_this_timestamp = multivariate_normal.pdf(test_trajectory[point_in_test_trajectory],
                                                         mean_of_all_classes[point_in_test_trajectory],
                                                         covariance[point_in_test_trajectory])
        # skip power for first step
        if point_in_test_trajectory == 0:
            observation_probability.append(pdf_for_this_timestamp)
        elif point_in_test_trajectory > 0:
            # append calculated pdf to the master array defined above
            observation_probability.append(math.pow(pdf_for_this_timestamp, power))
    return observation_probability

def sigma():
    """
    This function signifies noise in PDF function. Previously used for
    calculating covariance
    """
    identitymatrix = np.eye(2)
    factor = 1
    sigma = identitymatrix * factor
    return sigma

# calculated using the 1) quation on the formulas paper
def simple_belief_update(belief_input, observation_probability):

    # Belief update for goals (for two goals together)
    belief_local_copy = belief_input
    numerator_array = []
    denominator_array = []

    for class_counter in range(len(observation_probability)):
        numerator = observation_probability[class_counter] * belief_local_copy[class_counter]
        numerator_array.append(numerator)
        denominator_array.append(numerator)

    for belief_counter in range(len(numerator_array)):
        # belief_local_copy[belief_counter] = float("{0:.2f}".format(value / sum(denominator_array)))
        belief_local_copy[belief_counter] = 0.00001 if (numerator_array[belief_counter] / sum(denominator_array)) == 0 else numerator_array[belief_counter] / sum(denominator_array)

    return belief_local_copy



# calculated using the 1) quation on the formulas paper
def belief_update(belief_input, observation_probability, number_points):
    """
    This function returns the newly calculated belief given inputs of
    - Previous belief
    - Observation probability for each class i.e left, right and straight
    - Number of points
    """
    # Belief update for goals (for two goals together)
    belief_local_copy = belief_input

    # print('belief local copy', belief_local_copy)

    belief_array = []
    # comment if you only want seeding beleif to be 0.3, 0.3, 0.3 not the updated for step 0
    # belief_array.append(list(belief_local_copy))

    for points in range(0, number_points):

        numerator_array = []
        denominator_array = []

        for class_counter in range(3):
            numerator = observation_probability[class_counter][points] * belief_local_copy[class_counter]
            numerator_array.append(numerator)
            denominator_array.append(numerator)

        for belief_counter in range(len(numerator_array)):
            # belief_local_copy[belief_counter] = float("{0:.2f}".format(value / sum(denominator_array)))
            belief_local_copy[belief_counter] = 0.00001 if (numerator_array[belief_counter] / sum(denominator_array)) == 0 else numerator_array[belief_counter] / sum(denominator_array)

        belief_array.append(list(belief_local_copy))

    return belief_array

# package all prediction processing in a function so that it can be called multiple times without duplication
def all_prediction_processing(number_point, apply_power=False, power=0):
    print("++++++++++++++++++++++++++++++++++++++++++++++")
    print("++++++++++++++++++++++++++++++++++++++++++++++")
    print("Running prediction for {} points".format(number_point))
    print("++++++++++++++++++++++++++++++++++++++++++++++")
    print("++++++++++++++++++++++++++++++++++++++++++++++")

    """
    Step 1:
    - Define number of point for interpolation purposes throughout this program
    - Load all trajectory files in file dictionary
    - Select a test trajectory and interpolate it
    """

    # set number of points
    NUMBER_POINTS = number_point

    # fill files directionary with file paths of all csv files
    files_dictionary = {
        # return all files starting with left_ in the folder
        'left': glob.glob('trajectories/left_*.csv'),
        # return all files starting with right in the folder
        'right': glob.glob('trajectories/right_*.csv'),
        # return all files starting with straight in the folder
        'straight': glob.glob('trajectories/straight_*.csv'),
    }

    if sys.argv[1] == 'straight':
        file = 'trajectories/test_straight.csv'
        random_trajectory = read_csv_fast(file)
    elif sys.argv[1] == 'left':
        file = 'trajectories/test_left.csv'
        random_trajectory = read_csv_fast(file)
    elif sys.argv[1] == 'right':
        file = 'trajectories/test_right.csv'
        random_trajectory = read_csv_fast(file)
    else:
        # Select any random trajectory
        sample_trajectory_categories = ['straight', 'left', 'right']
        file = files_dictionary[random.choice(sample_trajectory_categories)][np.random.randint(0, 9)]
        random_trajectory = read_csv_fast(file)

    print('Chosen random trajectory path: {}'.format(file))

    interpolated_random_trajectory = interpolate_dist(random_trajectory[:, 1], random_trajectory[:, 2], NUMBER_POINTS)

    random_trajectory = np.asarray(random_trajectory)
    [xn, yn] = interpolate_dist(random_trajectory[:, 1], random_trajectory[:, 2], NUMBER_POINTS)
    random_trajectory = np.vstack((xn, yn)).T

    """
    Step 2: Recognize type of the map
    """
    # to be able to run the program without testmap, uncomment following line
    recognize_map('maps/testmap.png')
    # recognize_map('/home/linjuk/adda_ros/src/code_lina/simple_sim_car/pomdp_car_launch/maps/testmap.png')

    """
    Step 3: Accumulate and plot all trajectories
    """
    # container dictionary for ploting graphs
    trajectory_csv_data = {}

    # container dictionary for averaging
    trajectory_csv_file_wise_data = {}

    # big array container for all points from all trajectories
    all_points_from_files = []

    # color map for graph
    color_map = {
        'left': 'green',
        'right': 'blue',
        'straight': 'magenta'
    }

    # plot graph
    fig, ax = plt.subplots()
    plt.figure(1)
    plt.title('Movement Classification f = y(x)')
    plt.xlabel('x [m]')
    plt.ylabel('y [m]')

    # labels
    plt.plot(0, 0, color='green', label='Left-Side Parking', alpha=0.4)
    plt.plot(0, 0, color='blue', label='Right-Side Parking', alpha=0.4)
    plt.plot(0, 0, color='magenta', label='Straight-Side Parking', alpha=0.4)

    # loop over trajectories i.e. left, right, straight
    for key in files_dictionary:
        trajectory_csv_file_wise_data[key] = {}
        # loop over files in each trajectory
        for index, file in enumerate(files_dictionary[key]):
            file_raw_data = read_csv_fast(file)
            all_points_from_files.append(file_raw_data)
            # read file
            trajectory_csv_data[key] = (file_raw_data)
            # aggregate data in container for averaging
            trajectory_csv_file_wise_data[key][index] = []
            trajectory_csv_file_wise_data[key][index].append(trajectory_csv_data[key])
            # segregate x and y for plotting
            x, y = trajectory_csv_data[key][:, 1], trajectory_csv_data[key][:, 2]
            p = plt.plot(x, y, color=color_map[key], alpha=0.3)

    """
    Step 4: Interpolate the accumulated trajectories in the previous step to NUMBER_POINTS defined in STEP 1
    """
    all_points_from_files = np.asarray(all_points_from_files)
    count_straight_files = len(files_dictionary['straight'])
    count_left_files = len(files_dictionary['left'])
    count_right_files = len(files_dictionary['right'])

    all_straight = []
    for i in range(count_straight_files):
        [xn, yn] = interpolate_dist(all_points_from_files[i][:, 1], all_points_from_files[i][:, 2], NUMBER_POINTS)
        points = np.vstack((xn, yn)).T
        all_straight.append(points)

    all_rights = []
    for i in range(count_straight_files, count_straight_files + count_right_files):
        [xn, yn] = interpolate_dist(all_points_from_files[i][:, 1], all_points_from_files[i][:, 2], NUMBER_POINTS)
        points = np.vstack((xn, yn)).T
        all_rights.append(points)

    all_lefts = []
    for i in range(count_straight_files + count_right_files,
                   count_straight_files + count_right_files + count_left_files):
        [xn, yn] = interpolate_dist(all_points_from_files[i][:, 1], all_points_from_files[i][:, 2], NUMBER_POINTS)
        points = np.vstack((xn, yn)).T
        all_lefts.append(points)

    all_rights = np.asarray(all_rights)
    all_straight = np.asarray(all_straight)
    all_lefts = np.asarray(all_lefts)

    """
    Step 5: Calculate and plot mean for each class i.e. all trajectories for that class
    """
    means_straight = np.mean(all_straight, axis=0)
    means_right = np.mean(all_rights, axis=0)
    means_left = np.mean(all_lefts, axis=0)

    plt.plot(means_straight[:, 0], means_straight[:, 1], color="black")
    plt.plot(means_right[:, 0], means_right[:, 1], color="black")
    plt.plot(means_left[:, 0], means_left[:, 1], color="black")

    """
    Step 6: Calculate and plot standard deviation for each class i.e. all trajectories for that classes
    """
    std_right = np.std(all_rights, axis=0)
    std_straight = np.std(all_straight, axis=0)
    std_left = np.std(all_lefts, axis=0)

    circles_right = []
    circles_straight = []
    circles_left = []
    for i in range(NUMBER_POINTS):
        circle_right = plt.Circle((means_right[i][0], means_right[i][1]), radius=2 * np.linalg.norm(std_right[i]))
        radius = np.linalg.norm(std_right[i])
        circle_straight = plt.Circle((means_straight[i][0], means_straight[i][1]),
                                     radius=2 * np.linalg.norm(std_straight[i]))
        circle_left = plt.Circle((means_left[i][0], means_left[i][1]), radius=2 * np.linalg.norm(std_left[i]))

        # circle_right = Ellipse((means_right[i][0], means_right[i][1]), width=2*std_right[i][0], height=2*std_right[i][1])
        # circle_straight = Ellipse((means_straight[i][0], means_straight[i][1]), width=2*std_straight[i][0], height=2*std_straight[i][1])
        # circle_left = Ellipse((means_left[i][0], means_left[i][1]), width=2*std_left[i][0], height=2*std_left[i][1])

        # 1*std --> 68.27%, 2*std --> 95.45%, 3*std --> 99.73%.

        circles_right.append(circle_right)
        circles_straight.append(circle_straight)
        circles_left.append(circle_left)

    p = PatchCollection(circles_right, alpha=0.3, color="red")
    p1 = PatchCollection(circles_straight, alpha=0.3, color="green")
    p2 = PatchCollection(circles_left, alpha=0.2, color="blue")
    ax.add_collection(p)
    ax.add_collection(p1)
    ax.add_collection(p2)

    """
    Step 7: Calculate covariance for trajectories in each class
    """
    covariance_right = calculate_covariance_for_class(all_rights, NUMBER_POINTS)
    covariance_straight = calculate_covariance_for_class(all_straight, NUMBER_POINTS)
    covariance_left = calculate_covariance_for_class(all_lefts, NUMBER_POINTS)

    """
    Step 8: Calculate likelihood of random test trajectory to belong to which class
    """
    # probability calculation without power
    if apply_power == False:
        left_probability = probability(random_trajectory, means_left, covariance_left)
        right_probability = probability(random_trajectory, means_right, covariance_right)
        straight_probability = probability(random_trajectory, means_straight, covariance_straight)
    # probability calculation with power
    elif apply_power == True:
        straight_probability_with_power = probability_with_power(random_trajectory, means_straight, covariance_straight,
                                                                 power)
        left_probability_with_power = probability_with_power(random_trajectory, means_left, covariance_left, power)
        right_probability_with_power = probability_with_power(random_trajectory, means_right, covariance_right, power)

    """
    Step 9: Do belief calculation based on initial belief, class probabilities and NUMBER_POINTS
    """
    # belief calculation without power
    if apply_power == False:
        belief = []
        belief.append(0.33333)  # prob that class1
        belief.append(0.33333)  # prob that class2
        belief.append(0.33333)  # prob that class3

        trajectory_beliefs = belief_update(belief[:], [left_probability, right_probability, straight_probability],
                                           NUMBER_POINTS)
    # belief calculation with power
    elif apply_power == True:
        belief_with_power = []
        belief_with_power.append(0.33333)  # prob that class1
        belief_with_power.append(0.33333)  # prob that class2
        belief_with_power.append(0.33333)  # prob that class3
        trajectory_beliefs_with_power = belief_update(belief_with_power[:],
                                                      [left_probability_with_power, right_probability_with_power,
                                                       straight_probability_with_power], NUMBER_POINTS)

    """
    Step 10: Plot results of belief calculation on the graph for each timestep
    """
    INTERVAL = 0.001  # in seconds

    if apply_power == False:
        for point in range(0, NUMBER_POINTS):

            belief_sum = trajectory_beliefs[point][0] + trajectory_beliefs[point][1] + trajectory_beliefs[point][2]

            print("----------")
            print("Step: ", point)
            print("Coordinates: ", random_trajectory[point][0], random_trajectory[point][1])

            # Imagine step -1 is 0.3, 0.3, 0.3 so print that first and then all belief updates.
            # Since last one will be missed because of this logic, print it explicitiy
            if point == 0:
                print("Initial step belief", str([0.33333, 0.33333, 0.33333]))
            else:
                print("Last step belief [left, right, straight]: ", str(trajectory_beliefs[point - 1]))

            if point == NUMBER_POINTS:
                print("Last step belief [left, right, straight]: ", str(trajectory_beliefs[point]))

            print(
            "PDF [left, right, straight]: ", left_probability[point], right_probability[point], straight_probability[point])
            print("Updated belief [left, right, straight]: ", str(trajectory_beliefs[point]))
            plt.suptitle('[Left, Right, Straight] = ' + str(np.round(trajectory_beliefs[point], 3)) + '   [Sum] = ' + str(
                belief_sum) + '   [Step] = ' + str(point), fontsize=12, ha='left', x=0.05, y=0.98)
            plt.scatter(x=interpolated_random_trajectory[0][point], y=interpolated_random_trajectory[1][point], c="red",
                        s=7,
                        zorder=10)

            # commented for time being to avoid animation and get faster
            # plt.pause(INTERVAL)

            # Now clear the plot
            clear_plot()

    elif apply_power == True:
        for point in range(0, NUMBER_POINTS):

            belief_sum = trajectory_beliefs_with_power[point][0] + trajectory_beliefs_with_power[point][1] + trajectory_beliefs_with_power[point][2]

            print("----------")
            print("Step: ", point)
            print("Coordinates: ", random_trajectory[point][0], random_trajectory[point][1])

            # Imagine step -1 is 0.3, 0.3, 0.3 so print that first and then all belief updates.
            # Since last one will be missed because of this logic, print it explicitiy
            if point == 0:
                print("Initial step belief", str([0.33333, 0.33333, 0.33333]))
            else:
                print("Last step belief [left, right, straight]: ", str(trajectory_beliefs_with_power[point - 1]))

            if point == NUMBER_POINTS:
                print("Last step belief [left, right, straight]: ", str(trajectory_beliefs_with_power[point]))

            print(
                "PDF [left, right, straight]: ", left_probability_with_power[point], right_probability_with_power[point],
                straight_probability_with_power[point])
            print("Updated belief [left, right, straight]: ", str(trajectory_beliefs_with_power[point]))
            plt.suptitle(
                '[Left, Right, Straight] = ' + str(np.round(trajectory_beliefs_with_power[point], 3)) + '   [Sum] = ' + str(
                    belief_sum) + '   [Step] = ' + str(point), fontsize=12, ha='left', x=0.05, y=0.98)
            plt.scatter(x=interpolated_random_trajectory[0][point], y=interpolated_random_trajectory[1][point], c="red",
                        s=7,
                        zorder=10)

            # commented for time being to avoid animation and get faster
            # plt.pause(INTERVAL)

            # Now clear the plot
            clear_plot()

    plt.legend(loc='lower right')
    plt.show()

    """
    Step 11: Scaling calculation
    """
    print("-------------------------")
    print("-------------------------")
    # print("Calculations for scaling")
    # print("-------------------------")
    # print("-------------------------")
    # print("Number of steps: ", NUMBER_POINTS)
    # print("")

    capital_pi_left = []
    capital_pi_right = []
    capital_pi_straight = []

    capital_pi_left_with_power = []
    capital_pi_right_with_power = []
    capital_pi_straight_with_power = []

    result = []
    # left_probability = replace_zeros_in_list(left_probability)
    # right_probability = replace_zeros_in_list(right_probability)
    # straight_probability = replace_zeros_in_list(straight_probability)

    # loop over number of points
    for point in range(0, NUMBER_POINTS):
        # calculations when no power is applied
        if apply_power == False:
            # print("Step: ", point, "PDF [left, right, straight]: ", left_probability[point], right_probability[point],
            #       straight_probability[point])
            # print("Left probabilities used for PI", left_probability[0:point+1])
            # print("Right probabilities used for PI", right_probability[0:point+1])
            # print("Straight probabilities used for PI", straight_probability[0:point+1])
            capital_pi_left.append(np.prod(left_probability[0:point + 1]))
            capital_pi_right.append(np.prod(right_probability[0:point + 1]))
            capital_pi_straight.append(np.prod(straight_probability[0:point + 1]))


            # print("Point ", point)
            # print("Mean ", means_left[point], means_right[point], means_straight[point])
            # print("Covariance ", covariance_left[point], covariance_right[point], covariance_straight[point])

            # print("Capital_PI [left, right, straight]: ", capital_pi_left[point], capital_pi_right[point], capital_pi_straight[point])

            # point, cordinate, pdf, capital_pi, trajectory_beliefs
            result.append([
                point,
                (random_trajectory[point][0], random_trajectory[point][1]),
                (left_probability[point], right_probability[point], straight_probability[point]),
                # (capital_pi_left[point], capital_pi_right[point], capital_pi_straight[point]),
                trajectory_beliefs[point]
            ])
            # print("==================")
        # calculations when power is applied
        elif apply_power == True:
            # print("Step: ", point, "PDF [left, right, straight]: ", left_probability_with_power[point],
            #       right_probability_with_power[point], straight_probability_with_power[point])
            # print("Left probabilities used for PI", left_probability_with_power[0:point + 1])
            # print("Right probabilities used for PI", right_probability_with_power[0:point + 1])
            # print("Straight probabilities used for PI", straight_probability_with_power[0:point + 1])
            capital_pi_left_with_power.append(np.prod(left_probability_with_power[0:point + 1]))
            capital_pi_right_with_power.append(np.prod(right_probability_with_power[0:point + 1]))
            capital_pi_straight_with_power.append(np.prod(straight_probability_with_power[0:point + 1]))
            # print("Capital_PI [left, right, straight]: ", capital_pi_left_with_power[point],
            #       capital_pi_right_with_power[point], capital_pi_straight_with_power[point])


            # point with the same coordinates having 10 and 100 points: 0->0, 1->11, 2->22, 3->33, 4->44, ... , 9->99
            # point, cordinate, pdf, capital_pi, trajectory_beliefs
            result.append([
                point,
                (random_trajectory[point][0], random_trajectory[point][1]),
                (left_probability_with_power[point], right_probability_with_power[point], straight_probability_with_power[point]),
                # (capital_pi_left_with_power[point], capital_pi_right_with_power[point], capital_pi_straight_with_power[point]),
                trajectory_beliefs_with_power[point]
            ])
            # print("==================")

    return result

def distance_formula(p1, p2):
    return math.sqrt( ((p1[0]-p2[0])**2)+((p1[1]-p2[1])**2))

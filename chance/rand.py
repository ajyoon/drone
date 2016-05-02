#!/usr/bin/env python

from __future__ import division

import copy
import random

# from . import nodes


class Weight:
    def __init__(self, outcome, weight):
        self.x = outcome
        self.y = weight


def weighted_rand(input_weights, run_type='interpolated', do_round=False):
    """
    Generates a non-uniform random value based on a list of input_weights or tuplets.
    Can work in two ways based on run_type:

        'interpolated' - Treats input_weights as coordinates for a probability distribution curve and rolls accordingly.
                         Constructs a piece-wise linear curve according to coordinates given in input_weights
                         and rolls random values in the curve's bounding box until a value is found under the curve
                         All input_weights outcome values must be numbers.

        'discreet'     - treats each outcome (Weight.x) as a discreet unit with a chance to occur.
                         Constructs a line segment where each weight is outcome is alloted a length
                         and rolls a random point.
                         input_weights outcomes may be of any type, including instances

    :param input_weights: Array of Weight objects or tuples of form (outcome, weight)
    :param run_type: str of value 'interpolated' or 'discreet'.
    :param do_round: Bool, determines if the return value should be rounded to an integer or not (only applicable in
                      run_type='interpolated')
    :return: Returns a random name based on the weights
    """
    from .nodes import Node
    if input_weights is None:
        # input_weights must be a real value
        raise TypeError
    weights = copy.copy(input_weights)

    # Loop through every weight in weights[] and make sure that they are Weight objects, converting if not
    for i in range(len(weights)):
        if isinstance(weights[i], Weight):
            pass
        elif isinstance(weights[i], Node):
            weights[i] = Weight(weights[i].name, weights[i].use_weight)
        elif isinstance(weights[i], tuple):
            weights[i] = Weight(weights[i][0], weights[i][1])
        else:
            raise TypeError("Weight at index %s is not a valid type." % str(i))

    # Special handling in case an array of just one weight is being passed - simply return the weight's name
    if len(weights) == 1:
        return weights[0].x

    if run_type == 'interpolated':
        # Sort list so that weights are listed in order of ascending X name
        weights = sorted(weights, key=lambda this_weight: this_weight.x)
        return_number = 0
        x_min = 0
        y_min = 0
        x_max = 0
        y_max = 0

        for point in weights:
            if x_min > point.x:
                x_min = point.x
            if x_max < point.x:
                x_max = point.x
            if y_max < point.y:
                y_max = point.y
        # Roll random numbers until a valid one is found
        point_found = False
        t_count = 0
        while not point_found:
            # Get sample point
            sample = Weight(random.uniform(x_min, x_max), random.uniform(y_min, y_max))
            i = 0
            while i < (len(weights) - 1):
                if weights[i].x <= sample.x <= weights[i + 1].x:
                    f_slope = (weights[i + 1].y - weights[i].y) / (weights[i + 1].x - weights[i].x)
                    f_yint = weights[i].y - (f_slope * weights[i].x)
                    f_x = (f_slope * sample.x) + f_yint
                    if sample.y <= f_x:
                        return_number = sample.x
                        point_found = True
                i += 1
            t_count += 1
            if t_count == 1000:
                print("WARNING: Point in weighted_rand() not being found after over 1000 attempts")
        if do_round:
            return_number = int(round(return_number))
        return return_number

    elif run_type == 'discreet':
        # Find total name of points y coords
        prob_sum = 0
        point_found = False
        for current_point in weights:
            prob_sum += current_point.y
        rand_num = random.uniform(0, prob_sum)
        current_pos = 0
        index = 0
        while index < len(weights):
            if current_pos <= rand_num <= (current_pos + weights[index].y):
                point_found = True
                return weights[index].x
            current_pos += weights[index].y
            index += 1
        if not point_found:
            print("ERROR: Point at " + str(rand_num) + " was not found in discreet_weighted_rand!")
            print("Cumulative range is " + str(prob_sum))
            return False
    else:
        print("ERROR: run type of '" + run_type + "' is invalid. Ignoring...")
        return False


def random_weight_list(min_outcome, max_outcome, max_weight_density=0.1,
                       max_possible_weights=None, return_as_tuples=False):
    """
    Generates a list of Weight within a given min_outcome and max_outcome bound.
    max_weight_density gives the maximum density of resulting weights, it is multiplied by (max_outcome - min_outcome)
    :param min_outcome: int
    :param max_outcome: int
    :param max_weight_density: float
    :param max_possible_weights: int
    :param return_as_tuples: Bool
    :return: list of Weight instances
    """
    # Prevent sneaky errors
    # Add resolution multiplier if either min_outcome or max_outcome are floats
    resolution_multiplier = None
    if (not isinstance(min_outcome, int)) or (not isinstance(max_outcome, int)):
        resolution_multiplier = 1000.0
        min_outcome = int(round(min_outcome * resolution_multiplier))
        max_outcome = int(round(max_outcome * resolution_multiplier))
    if min_outcome > max_outcome:
        swapper = min_outcome
        min_outcome = max_outcome
        max_outcome = swapper

    # Set max_weights according to max_weight_density
    max_weights = int(round((max_outcome - min_outcome) * max_weight_density))

    if (max_possible_weights is not None) and (max_weights > max_possible_weights):
        max_weights = max_possible_weights

    # Create and populate weight_list
    weight_list = []
    # pin down random weights at min_outcome and max_outcome to keep the weight_list properly bounded
    weight_list.append(Weight(min_outcome, random.randint(1, 100)))
    weight_list.append(Weight(max_outcome, random.randint(1, 100)))
    # Main population loop. Subtract 2 from max_weights to account for already inserted start and end caps
    for i in range(0, max_weights - 2):
        outcome = random.randint(min_outcome, max_outcome)
        is_duplicate_outcome = False
        # Test contents in weight_list to make sure none of them have the same outcome
        for index in range(0, len(weight_list)):
            if weight_list[index].x == outcome:
                is_duplicate_outcome = True
                break
        if not is_duplicate_outcome:
            weight_list.append(Weight(outcome, random.randint(1, 100)))

    # Sort the list
    weight_list = sorted(weight_list, key=lambda z: z.x)

    # Undo resolution multiplication if necessary
    if resolution_multiplier is not None:
        resolved_weight_list = []
        for old_weight in weight_list:
            resolved_weight_list.append(Weight(round((old_weight.x / resolution_multiplier), 3), old_weight.y))
        weight_list = resolved_weight_list
    if return_as_tuples:
        return_tuple_list = []
        for old_weight in weight_list:
            return_tuple_list.append((old_weight.x, old_weight.y))
        return return_tuple_list
    else:
        return weight_list



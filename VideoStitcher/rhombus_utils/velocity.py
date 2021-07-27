###################################################################################
# Copyright (c) 2021 Rhombus Systems                                              #
#                                                                                 # 
# Permission is hereby granted, free of charge, to any person obtaining a copy    #
# of this software and associated documentation files (the "Software"), to deal   #
# in the Software without restriction, including without limitation the rights    #
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell       #
# copies of the Software, and to permit persons to whom the Software is           #
# furnished to do so, subject to the following conditions:                        #
#                                                                                 # 
# The above copyright notice and this permission notice shall be included in all  #
# copies or substantial portions of the Software.                                 #
#                                                                                 # 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR      #
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,        #
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE     #
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER          #
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,   #
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE   #
# SOFTWARE.                                                                       #
###################################################################################

import numpy as np
from rhombus_types.human_event import HumanEvent
from rhombus_types.vector import validate_vec2, Vec2

def get_velocity(a: HumanEvent, b: HumanEvent) -> np.ndarray:
    """Returns the X and Y velocity of a bounding box of a human event in permyriad / milisecond
     
    :param a: The first human event
    :param b: The following human event
    :return: Returns a velocity in permyriad / milisecond between human event `a` and human event `b`
    """

    # Prevent division by 0 error
    if b.timestamp - a.timestamp == 0: 
        return Vec2(0, 0)

    # Velocity = (a.position - b.position) / (a.timestamp / b.timestamp)
    return (np.subtract(b.position, a.position)) / (b.timestamp - a.timestamp)

def normalize_velocity(a: np.ndarray, threshold: np.ndarray = Vec2(0, 0)) -> np.ndarray:
    """Normalizes a velocity so that its components are either -1, 0, or 1 and nothing in between

    :param a: The velocity to normalize
    :param threshold: The threshold at which a velocity can be considered moving. This is a positive vector. By default this is 0 in both axes
                      If the X threshold is 0.05 / 1000, an object will only be considered moving right if it has a velocity in the x direction that is greater than that.
    :return: Returns a velocity, where the x and y values are either -1, 0, or 1, and nothing in between.
             If it is moving right, it's velocity will be 1 in on the x axis.
             If it is moving up, it's velocity will be -1 on the y axis
    """
    validate_vec2(a)
    validate_vec2(threshold)

    # If the velocity does not pass the threshold, it will be a 0 in that axis
    normalized_velocity: np.ndarray = Vec2(0, 0) 

    if a[0] > threshold[0]:
        # If the x velocity is greater than the threshold, we will give the x axis a 1
        normalized_velocity[0] = 1
    elif a[0] < -threshold[0]:
        # If the x velocity is less than the NEGATIVE threshold, we will give the x axis a -1
        normalized_velocity[0] = -1
    
    if a[1] > threshold[1]:
        # If the y velocity is greater than the threshold, we will give the y axis a 1
        normalized_velocity[1] = 1
    elif a[1] < -threshold[1]:
        # If the y velocity is less than the NEGATIVE threshold, we will give the y axis a -1
        normalized_velocity[1] = -1

    # Return the normalized vector
    return normalized_velocity

def normalize_position(a: np.ndarray, threshold: np.ndarray = Vec2(0, 0)):
    """Normalizes a position so that its components are either -1, 0, or 1 and nothing in between

    :param a: The position to normalize
    :param threshold: The threshold at which a position can be considered non 0
                      If the X threshold is 0.05, an object will only be considered on the right if it has a postion in the x direction that is greater than that.
    
    :return: Returns a velocity, where the x and y values are either -1, 0, or 1, and nothing in between.
             If it is on the right, it's position will be 1 in on the x axis.
             If it is on the top, it's position will be -1 on the y axis
    """

    # If the position does not pass the threshold, it will be a 0 in that axis
    normalized_position = Vec2(0, 0)

    if a[0] > 1 - threshold[0]:
        # If the x position is greater than 1 - threshold, we will give the x axis a 1
        normalized_position[0] = 1
    elif a[0] < threshold[0]:
        # If the x position is less than the threshold, we will give the x axis a -1
        normalized_position[0] = -1

    if a[1] > 1- threshold[1]:
        # If the y position is less than the 1 - threshold, we will give the y axis a -1
        normalized_position[1] = 1
    elif a[1] < threshold[1]:
        # If the y position is less than the threshold, we will give the y axis a 1
        normalized_position[1] = -1

    # Return the normalized vector
    return normalized_position


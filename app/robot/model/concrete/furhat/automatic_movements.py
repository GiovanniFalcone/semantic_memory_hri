import random
import time
import json

from furhat_remote_api import FurhatRemoteAPI

# Class defination for automatic movements of robot's head
class AutomaticMovements:
    enable_variable_head_movements = True

    @staticmethod
    def get_scale_parameter(scale=4.0, offset=0.55):
        return random.choice([-1, 1]) * (random.random() * scale + offset)

    @staticmethod
    def idle_head_movements(furhat, strength=1.0, duration=1.0):
        """
        Makes Furhat move the head slightly in a random direction at an interval to make the robot feel more alive to the user. Does not affect attention, 
        but can affect gestures.
            Params:
            strength - multiplies all the default values by this amount, to change the impact of the gesture
            duration - multiplies all the frame times by this amount, to change the duration of the gesture
        """
        while True:
            if AutomaticMovements.enable_variable_head_movements:
                gesture = {
                    "name": "CoolThing",
                    "frames": [
                        {
                            "time": [0.17, 1.0, 6.0],
                            "params": {
                                "NECK_ROLL": AutomaticMovements.get_scale_parameter(),
                                "NECK_PAN": AutomaticMovements.get_scale_parameter(),
                                "NECK_TILT": AutomaticMovements.get_scale_parameter(),
                            }
                        },
                        {
                            "time": [7.0],
                            "params": {
                                "persist": True
                            }
                        }
                    ],
                    "class": "furhatos.gestures.Gesture"
                }
                furhat.gesture(body=gesture)
            time.sleep(duration)

    @staticmethod
    def auto_head_movement_delay(time_ms):
        AutomaticMovements.enable_variable_head_movements = False
        time.sleep(time_ms / 1000)
        AutomaticMovements.enable_variable_head_movements = True

    @staticmethod
    def get_random_smile_closed():
        return random.uniform(0.2, 1)

    @staticmethod
    def random_head_movements(furhat, strength=1.0, duration_multiplier=1.0, repetition_period=(2500, 5000)):
        """
         Partial state that sets the interval and strength of the random head movements
            @param strength Multiplier for the strength of the head movements
            @param durationMultiplier Multiplier for the duration of each head pose shift
            @param repetitionPeriod time range in milliseconds until the next random head movement
         """
        while True:
            if AutomaticMovements.enable_variable_head_movements:
                gesture = {
                    "name": "CoolThing",
                    "frames": [
                        {
                            "time": [0.17, 1.0, 6.0],
                            "params": {
                                "NECK_ROLL": AutomaticMovements.get_scale_parameter(),
                                "NECK_PAN": AutomaticMovements.get_scale_parameter(),
                                "NECK_TILT": AutomaticMovements.get_scale_parameter() * strength,
                                "SMILE_CLOSED": AutomaticMovements.get_random_smile_closed(),
                                "BROW_UP_LEFT":1,
                                "BROW_UP_RIGHT":1,
                            }
                        },
                        {
                            "time": [7.0],
                            "params": {
                                "persist": True
                            }
                        }
                    ],
                    "class": "furhatos.gestures.Gesture"
                }
                furhat.gesture(body=gesture)
            time.sleep(random.randint(repetition_period[0], repetition_period[1]) / 1000)
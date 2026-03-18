from model.concrete.furhat.furhat import Furhat
from model.interface.robot_interface import RobotInterface

class RobotFactory:

    @staticmethod
    def create_robot(robot_type: str, ip: str, port: int) -> RobotInterface:
        """
        Creates an instance of robot based on the specified string.

        Args:
            robot_type (str): Which robot (e.g furhat, nao, pepper, ...).

        Returns:
            RobotInterface: An instance of the corresponding robot.

        Raises:
            ValueError: If the robot type is not supported.
        """
        if robot_type == "furhat":
            return Furhat(ip, port)
        # elif robot_type == "nao":
        #     return ...

        raise ValueError(f"Robot type '{robot_type}' is not supported.")
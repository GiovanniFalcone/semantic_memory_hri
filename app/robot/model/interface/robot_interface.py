from abc import ABC, abstractmethod

class RobotInterface(ABC):
    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def say(self, sentence, **kwargs):
        pass

    @abstractmethod
    def user_detection(self):
        pass

    @abstractmethod
    def random_head_movements(self):
        pass

    @abstractmethod
    def do_facial_expression(self, expression):
        pass

    @abstractmethod
    def listen(self):
        pass

    @abstractmethod
    def set_color_led(self, red, green, blue):
        pass
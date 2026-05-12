class MotorDriver:
    """Small wrapper around your existing pysoem motor code."""

    def __init__(self):
        self.current_counts = 0
        self.is_homed = False

    def connect(self):
        # TODO: initialize pysoem, find slave, configure PDO/SDO.
        pass

    def home(self):
        # TODO: paste your existing homing code here.
        self.current_counts = 0
        self.is_homed = True

    def move_to_counts(self, target_counts: int):
        if not self.is_homed:
            raise RuntimeError("Motor must be homed before movement")

        # TODO: call your existing move-to-position/counts code here.
        self.current_counts = int(target_counts)

    def get_current_counts(self) -> int:
        # TODO: replace with actual position read from the motor.
        return int(self.current_counts)

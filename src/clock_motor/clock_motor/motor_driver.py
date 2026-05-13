import struct
import time


class MotorDriver:
    """CiA402 EtherCAT driver for one FAULHABER-style motor.

    中文：这个类只负责底层电机通信，不包含“几点钟”的业务逻辑。
    English: This class only handles low-level motor communication, not clock logic.
    """

    # CiA402 object dictionary / CiA402 对象字典
    CONTROLWORD = 0x6040
    STATUSWORD = 0x6041
    MODE_OF_OPERATION = 0x6060
    MODE_DISPLAY = 0x6061
    POSITION_ACTUAL = 0x6064
    TARGET_POSITION = 0x607A
    HOMING_METHOD = 0x6098
    HOMING_SPEED = 0x6099
    HOMING_ACCELERATION = 0x609A
    PROFILE_VELOCITY = 0x6081
    PROFILE_ACCELERATION = 0x6083
    PROFILE_DECELERATION = 0x6084

    # Modes of operation / 运行模式
    MODE_PROFILE_POSITION = 1
    MODE_HOMING = 6

    def __init__(
        self,
        ifname="eth0",
        slave_index=0,
        homing_method=19,
        homing_speed_switch=400,
        homing_speed_zero=100,
        homing_acceleration=50,
        profile_velocity=400,
        profile_acceleration=100,
        profile_deceleration=100,
        move_timeout=20.0,
        home_timeout=30.0,
        position_tolerance=200,
        move_to_zero_after_homing=True,
    ):
        self.ifname = ifname
        self.slave_index = slave_index
        self.homing_method = homing_method
        self.homing_speed_switch = homing_speed_switch
        self.homing_speed_zero = homing_speed_zero
        self.homing_acceleration = homing_acceleration
        self.profile_velocity = profile_velocity
        self.profile_acceleration = profile_acceleration
        self.profile_deceleration = profile_deceleration
        self.move_timeout = move_timeout
        self.home_timeout = home_timeout
        self.position_tolerance = position_tolerance
        self.move_to_zero_after_homing = move_to_zero_after_homing

        self.master = None
        self.slave = None
        self.is_homed = False

    def connect(self):
        """Open EtherCAT and put the slave into OP state.

        中文：打开网卡、扫描从站、进入 EtherCAT OP 状态。
        English: Open the network interface, scan slaves, and enter EtherCAT OP state.
        """
        try:
            import pysoem
        except ImportError as exc:
            raise RuntimeError("pysoem is not installed in this environment") from exc

        self.master = pysoem.Master()
        self.master.open(self.ifname)

        if self.master.config_init() <= self.slave_index:
            raise RuntimeError(f"No EtherCAT slave {self.slave_index} on {self.ifname}")

        self.master.config_map()
        self.master.state = pysoem.OP_STATE
        self.master.write_state()
        reached = self.master.state_check(pysoem.OP_STATE, 5_000_000)
        if reached != pysoem.OP_STATE:
            raise RuntimeError("EtherCAT slave did not reach OP state")

        self.slave = self.master.slaves[self.slave_index]
        self._enable_operation()

    def home(self):
        """Run CiA402 homing and set logical zero.

        中文：执行寻零；完成后移动到驱动器 raw 0，raw 0 对应表盘 6 点。
        English: Run homing; after completion, move to drive raw 0, which is clock 6.
        """
        self._require_connection()
        self._set_mode(self.MODE_HOMING)
        self._enable_operation()

        self._write_i8(self.HOMING_METHOD, 0, self.homing_method)
        self._write_u32(self.HOMING_SPEED, 1, self.homing_speed_switch)
        self._write_u32(self.HOMING_SPEED, 2, self.homing_speed_zero)
        self._write_u32(self.HOMING_ACCELERATION, 0, self.homing_acceleration)

        # Bit 4 starts homing / 第 4 位启动寻零
        self._write_u16(self.CONTROLWORD, 0, 0x000F)
        self._write_u16(self.CONTROLWORD, 0, 0x001F)

        deadline = time.monotonic() + self.home_timeout
        while time.monotonic() < deadline:
            status = self._read_u16(self.STATUSWORD, 0)
            if status & (1 << 13):
                raise RuntimeError(f"Homing error, statusword=0x{status:04X}")
            if (status & (1 << 12)) and (status & (1 << 10)):
                self._write_u16(self.CONTROLWORD, 0, 0x000F)
                self.is_homed = True
                if self.move_to_zero_after_homing:
                    self.move_to_counts(0)
                return
            time.sleep(0.02)

        raise TimeoutError("Homing timed out")

    def move_to_counts(self, target_counts: int):
        """Move to a logical absolute target in encoder counts.

        中文：移动到逻辑绝对位置；输入 0 表示 homing 后的 6 点。
        English: Move to a logical absolute position; input 0 means clock 6 after homing.
        """
        self._require_connection()
        if not self.is_homed:
            raise RuntimeError("Motor must be homed before movement")

        raw_target = int(target_counts)
        self._set_mode(self.MODE_PROFILE_POSITION)
        self._enable_operation()
        self._write_u32(self.PROFILE_VELOCITY, 0, self.profile_velocity)
        self._write_u32(self.PROFILE_ACCELERATION, 0, self.profile_acceleration)
        self._write_u32(self.PROFILE_DECELERATION, 0, self.profile_deceleration)
        self._write_i32(self.TARGET_POSITION, 0, raw_target)

        # Toggle "new set-point" bit 4 / 翻转第 4 位，通知驱动器接收新目标点
        self._write_u16(self.CONTROLWORD, 0, 0x000F)
        self._write_u16(self.CONTROLWORD, 0, 0x003F)
        time.sleep(0.02)
        self._write_u16(self.CONTROLWORD, 0, 0x000F)

        deadline = time.monotonic() + self.move_timeout
        while time.monotonic() < deadline:
            actual = self._read_i32(self.POSITION_ACTUAL, 0)
            status = self._read_u16(self.STATUSWORD, 0)
            if status & (1 << 3):
                raise RuntimeError(f"Drive fault during move, statusword=0x{status:04X}")
            if abs(actual - raw_target) <= self.position_tolerance or status & (1 << 10):
                return
            time.sleep(0.02)

        actual = self._read_i32(self.POSITION_ACTUAL, 0)
        raise TimeoutError(f"Move timed out: target={raw_target}, actual={actual}")

    def get_current_counts(self) -> int:
        """Return logical position in counts.

        中文：返回逻辑位置 counts；驱动器 raw 0 就是表盘 6 点。
        English: Return logical counts; drive raw 0 is clock 6.
        """
        self._require_connection()
        return self._read_i32(self.POSITION_ACTUAL, 0)

    def close(self):
        if self.master is not None:
            self.master.close()

    def _enable_operation(self):
        status = self._read_u16(self.STATUSWORD, 0)
        if status & (1 << 3):
            self._write_u16(self.CONTROLWORD, 0, 0x0080)
            self._wait_until(lambda: not self._read_u16(self.STATUSWORD, 0) & (1 << 3), 2.0)

        self._write_u16(self.CONTROLWORD, 0, 0x0006)
        self._wait_status_state(0x006F, 0x0021, "Ready to switch on")
        self._write_u16(self.CONTROLWORD, 0, 0x0007)
        self._wait_status_state(0x006F, 0x0023, "Switched on")
        self._write_u16(self.CONTROLWORD, 0, 0x000F)
        self._wait_status_state(0x006F, 0x0027, "Operation enabled")

    def _set_mode(self, mode):
        self._write_i8(self.MODE_OF_OPERATION, 0, mode)
        self._wait_until(lambda: self._read_i8(self.MODE_DISPLAY, 0) == mode, 2.0)

    def _wait_status_state(self, mask, value, name):
        self._wait_until(lambda: (self._read_u16(self.STATUSWORD, 0) & mask) == value, 2.0, name)

    def _wait_until(self, predicate, timeout, name="condition"):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if predicate():
                return
            time.sleep(0.01)
        status = self._read_u16(self.STATUSWORD, 0)
        raise TimeoutError(f"Timed out waiting for {name}, statusword=0x{status:04X}")

    def _require_connection(self):
        if self.slave is None:
            raise RuntimeError("Motor is not connected")

    def _read_i8(self, index, subindex):
        return struct.unpack("<b", self.slave.sdo_read(index, subindex))[0]

    def _read_u16(self, index, subindex):
        return struct.unpack("<H", self.slave.sdo_read(index, subindex))[0]

    def _read_i32(self, index, subindex):
        return struct.unpack("<i", self.slave.sdo_read(index, subindex))[0]

    def _write_i8(self, index, subindex, value):
        self.slave.sdo_write(index, subindex, struct.pack("<b", int(value)))

    def _write_u16(self, index, subindex, value):
        self.slave.sdo_write(index, subindex, struct.pack("<H", int(value)))

    def _write_u32(self, index, subindex, value):
        self.slave.sdo_write(index, subindex, struct.pack("<I", int(value)))

    def _write_i32(self, index, subindex, value):
        self.slave.sdo_write(index, subindex, struct.pack("<i", int(value)))

# =============================================================================
# mpr121.py — Minimal MPR121 Capacitive Touch Sensor Driver
# MicroPython, Raspberry Pi Pico W 2
#
# Based on the Adafruit MPR121 datasheet register map.
# This driver initialises the sensor with conservative defaults that work
# reliably for bare-wire or conductive fabric electrodes on a glove.
#
# Usage:
#   from machine import I2C, Pin
#   from mpr121 import MPR121
#   i2c = I2C(1, sda=Pin(14), scl=Pin(15), freq=400_000)
#   mpr = MPR121(i2c, address=0x5A)
#   bits = mpr.touched()   # 12-bit int; bit N set = electrode N touched
# =============================================================================

# Register addresses
_MPR121_TOUCHSTATUS_L   = 0x00
_MPR121_TOUCHSTATUS_H   = 0x01
_MPR121_MHDR            = 0x2B
_MPR121_NHDR            = 0x2C
_MPR121_NCLR            = 0x2D
_MPR121_FDLR            = 0x2E
_MPR121_MHDF            = 0x2F
_MPR121_NHDF            = 0x30
_MPR121_NCLF            = 0x31
_MPR121_FDLF            = 0x32
_MPR121_NHDT            = 0x33
_MPR121_NCLT            = 0x34
_MPR121_FDLT            = 0x35
_MPR121_TOUCHTH_0       = 0x41   # Touch threshold, electrode 0
_MPR121_RELEASETH_0     = 0x42   # Release threshold, electrode 0
_MPR121_DEBOUNCE        = 0x5B
_MPR121_CONFIG1         = 0x5C
_MPR121_CONFIG2         = 0x5D
_MPR121_AUTOCONFIG0     = 0x7B
_MPR121_AUTOCONFIG1     = 0x7C
_MPR121_UPLIMIT         = 0x7D
_MPR121_LOWLIMIT        = 0x7E
_MPR121_TARGETLIMIT     = 0x7F
_MPR121_ECR             = 0x5E   # Electrode Configuration Register
_MPR121_SOFTRESET       = 0x80


class MPR121:
    """
    Minimal MicroPython driver for the MPR121 12-channel capacitive sensor.

    Only electrodes 0-4 are used in this project, but all 12 are initialised
    so the sensor operates correctly.

    Touch / release thresholds:
      touch_threshold   — lower = more sensitive (default 12, glove use: 6-10)
      release_threshold — must be lower than touch (default 6, glove use: 3-5)

    Increase touch_threshold if you get false triggers; decrease it if touches
    are not detected. Conductive fabric typically needs lower values than wire.
    """

    def __init__(self, i2c, address=0x5A,
                 touch_threshold=10, release_threshold=5):
        self._i2c  = i2c
        self._addr = address

        self._reset()
        self._configure(touch_threshold, release_threshold)

    # ── Private helpers ──────────────────────────────────────────────────────

    def _write_reg(self, reg, value):
        self._i2c.writeto_mem(self._addr, reg, bytes([value]))

    def _read_reg(self, reg):
        return self._i2c.readfrom_mem(self._addr, reg, 1)[0]

    def _reset(self):
        """Soft-reset the MPR121."""
        self._write_reg(_MPR121_SOFTRESET, 0x63)
        import time; time.sleep_ms(1)

    def _configure(self, tth, rth):
        """
        Apply baseline filter, thresholds, and electrode configuration.
        Must be done while ECR is in stop mode (default after reset).
        """
        # Baseline filter — rising
        self._write_reg(_MPR121_MHDR, 0x01)
        self._write_reg(_MPR121_NHDR, 0x01)
        self._write_reg(_MPR121_NCLR, 0x0E)
        self._write_reg(_MPR121_FDLR, 0x00)
        # Baseline filter — falling
        self._write_reg(_MPR121_MHDF, 0x01)
        self._write_reg(_MPR121_NHDF, 0x05)
        self._write_reg(_MPR121_NCLF, 0x01)
        self._write_reg(_MPR121_FDLF, 0x00)
        # Baseline filter — touched
        self._write_reg(_MPR121_NHDT, 0x00)
        self._write_reg(_MPR121_NCLT, 0x00)
        self._write_reg(_MPR121_FDLT, 0x00)

        # Touch and release thresholds for all 12 electrodes
        for i in range(12):
            self._write_reg(_MPR121_TOUCHTH_0   + (i * 2), tth)
            self._write_reg(_MPR121_RELEASETH_0 + (i * 2), rth)

        # Debounce: 0 touch, 0 release samples (fastest response)
        self._write_reg(_MPR121_DEBOUNCE, 0x00)

        # Config1: CDC=16 µA; Config2: CDT=0.5 µs, SFI=4, ESI=16 ms
        self._write_reg(_MPR121_CONFIG1, 0x10)
        self._write_reg(_MPR121_CONFIG2, 0x20)

        # Auto-configuration (enable USL, LSL, TL auto-set)
        self._write_reg(_MPR121_AUTOCONFIG0, 0x0B)
        self._write_reg(_MPR121_AUTOCONFIG1, 0x00)
        # Limits for 3.3 V supply: USL=200, LSL=130, TL=180
        self._write_reg(_MPR121_UPLIMIT,     200)
        self._write_reg(_MPR121_LOWLIMIT,    130)
        self._write_reg(_MPR121_TARGETLIMIT, 180)

        # ECR: enable all 12 electrodes, baseline tracking 5 MSBs
        self._write_reg(_MPR121_ECR, 0x8F)

    # ── Public API ───────────────────────────────────────────────────────────

    def touched(self):
        """
        Return a 12-bit integer where bit N is set if electrode N is touched.
        Read registers 0x00 (low byte) and 0x01 (high byte).
        Only bits 0-11 are valid; bits 12-15 are status flags (ignore them).
        """
        low  = self._read_reg(_MPR121_TOUCHSTATUS_L)
        high = self._read_reg(_MPR121_TOUCHSTATUS_H) & 0x1F  # mask status bits
        return (high << 8) | low

    def is_touched(self, electrode):
        """Return True if a specific electrode (0-11) is currently touched."""
        if not 0 <= electrode <= 11:
            raise ValueError("Electrode must be 0-11")
        return bool((self.touched() >> electrode) & 1)

    def set_thresholds(self, electrode, touch, release):
        """
        Update touch/release thresholds for a single electrode at runtime.
        Useful for tuning without restarting.
        Must temporarily stop electrode tracking (ECR stop mode).
        """
        self._write_reg(_MPR121_ECR, 0x00)   # stop
        self._write_reg(_MPR121_TOUCHTH_0   + (electrode * 2), touch)
        self._write_reg(_MPR121_RELEASETH_0 + (electrode * 2), release)
        self._write_reg(_MPR121_ECR, 0x8F)   # restart all 12
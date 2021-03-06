from migen.fhdl.std import *

from misoclib.tools.wishbone import WishboneStreamingBridge
from misoclib.com.uart.phy.serial import UARTPHYSerial

class UARTWishboneBridge(WishboneStreamingBridge):
    def __init__(self, pads, clk_freq, baudrate=115200):
        self.submodules.phy = UARTPHYSerial(pads, clk_freq, baudrate)
        WishboneStreamingBridge.__init__(self, self.phy, clk_freq)

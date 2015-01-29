from liteeth.common import *
from liteeth.mac.common import *
from liteeth.mac.core import preamble, crc, last_be

class LiteEthMACCore(Module, AutoCSR):
	def __init__(self, phy, dw, endianness="be", with_hw_preamble_crc=True):
		if dw < phy.dw:
			raise ValueError("Core data width({}) must be larger than PHY data width({})".format(dw, phy.dw))

		rx_pipeline = [phy]
		tx_pipeline = [phy]

		# Preamble / CRC (optional)
		if with_hw_preamble_crc:
			self._hw_preamble_crc = CSRStatus(reset=1)
			# Preamble insert/check
			preamble_inserter = preamble.LiteEthMACPreambleInserter(phy.dw)
			preamble_checker = preamble.LiteEthMACPreambleChecker(phy.dw)
			self.submodules += RenameClockDomains(preamble_inserter, "eth_tx")
			self.submodules += RenameClockDomains(preamble_checker, "eth_rx")

			# CRC insert/check
			crc32_inserter = crc.LiteEthMACCRC32Inserter(eth_phy_description(phy.dw))
			crc32_checker = crc.LiteEthMACCRC32Checker(eth_phy_description(phy.dw))
			self.submodules += RenameClockDomains(crc32_inserter, "eth_tx")
			self.submodules += RenameClockDomains(crc32_checker, "eth_rx")

			tx_pipeline += [preamble_inserter, crc32_inserter]
			rx_pipeline += [preamble_checker, crc32_checker]

		if dw != phy.dw:
			# Delimiters
			tx_last_be = last_be.LiteEthMACTXLastBE(phy.dw)
			rx_last_be = last_be.LiteEthMACRXLastBE(phy.dw)
			self.submodules += RenameClockDomains(tx_last_be, "eth_tx")
			self.submodules += RenameClockDomains(rx_last_be, "eth_rx")

			# Converters
			reverse = endianness == "be"
			tx_converter = Converter(eth_phy_description(dw), eth_phy_description(phy.dw), reverse=reverse)
			rx_converter = Converter(eth_phy_description(phy.dw), eth_phy_description(dw), reverse=reverse)
			self.submodules += RenameClockDomains(tx_converter, "eth_tx")
			self.submodules += RenameClockDomains(rx_converter, "eth_rx")

			tx_pipeline += [tx_last_be, tx_converter]
			rx_pipeline += [rx_last_be, rx_converter]

		# Cross Domain Crossing
		tx_cdc = AsyncFIFO(eth_phy_description(dw), 4)
		rx_cdc = AsyncFIFO(eth_phy_description(dw), 4)
		self.submodules +=  RenameClockDomains(tx_cdc, {"write": "sys", "read": "eth_tx"})
		self.submodules +=  RenameClockDomains(rx_cdc, {"write": "eth_rx", "read": "sys"})

		tx_pipeline += [tx_cdc]
		rx_pipeline += [rx_cdc]

		# Graph
		self.submodules.tx_pipeline = Pipeline(*reversed(tx_pipeline))
		self.submodules.rx_pipeline = Pipeline(*rx_pipeline)

		self.sink, self.source = self.tx_pipeline.sink, self.rx_pipeline.source

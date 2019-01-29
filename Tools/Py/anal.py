
def read_int(input, count, signed = False):
	"""
	Reads a little-endian integer from given input.
	"""

	return int.from_bytes(input.read(count), 'little', signed = signed)

def addr_to_offset(addr):
	"""
	Converts a mapped GBA address to a ROM offset.
	"""

	return addr & 0x1FFFFFF

def read_data_at(input, addr, size):
	"""
	Helper function that reads bytes given address and size from input.
	"""

	input.seek(addr_to_offset(addr))
	return input.read(size)

class AnalysedObject:
	"""
	Represents an object after being analysed.
	"""

	def __init__(self, address, size, type, data, name):
		self.address = address
		self.size = size
		self.type = type
		self.data = data
		self.name = name

class RomAnalyser:
	"""
	Generic analysis manager class.
	"""

	class QueuedAnalysis:
		"""
		Represents an object to analyse.
		"""

		def __init__(self, address, type, name):
			self.address = address
			self.type = type
			self.name = name

	class AnalOverlapError(Exception):

		def __init__(self, analysed, address, type):
			self.analysed = analysed
			self.address = address
			self.type = type

		def __repr__(self):
			return 'tried to analyse `{}` at address {:08X}, but a `{}` was already analysed at interval [{:08X}, {:08X}]'.format(
				self.type, self.address, self.analysed.type, self.analysed.address, self.analysed.address + self.analysed.size)

	class AnalQueueMismatchError(Exception):

		def __init__(self, address, type1, type2):
			self.address = address
			self.type1 = type1
			self.type2 = type2

		def __repr__(self):
			return 'tried to analyse both `{}` and `{}` at address {:08X}'.format(
				self.type1, self.type2, self.address)

	class BadAnalError(Exception):

		def __init__(self, address, type):
			self.address = address
			self.type = type

		def __repr__(self):
			return 'tried to analyse unknown (`{}`) at address {:08X}'.format(
				self.type, self.address)

	def __init__(self):
		self.analQueue = []
		self.analysed = []

		self.verbose = False

		self.analysisHandlers = {}

	def set_analysis_handler(self, type, handler):
		"""
		Sets analysis handler callable for given type. `handler` will be called as follows:
		    analysed = handler(analyser, input, address, name)
		"""

		self.analysisHandlers[type] = handler

	def set_verbose(self, verbose = True):
		"""
		Sets wether to print object information before analysing it.
		"""

		self.verbose = verbose

	def analyse_queued(self, input):
		"""
		Analyse queued objects.
		"""

		while len(self.analQueue) > 0:
			queued = self.analQueue[0]

			if not queued.type in self.analysisHandlers:
				raise RomAnalyser.BadAnalError(queued.address, queued.type)

			if self.verbose:
				print('analysing `{}` "{}" at address {:08X}'.format(queued.type, queued.name, queued.address))

			self.analysed.append(self.analysisHandlers[queued.type](self, input, queued.address, queued.name))
			self.analQueue = self.analQueue[1:]

	def get_analysed_sorted(self):
		"""
		Get a list of all Anaysed objects, sorted by address.
		"""

		return sorted(self.analysed, key = lambda a: a.address)

	def iter_pretty_summary(self, ignoreGaps = False):
		"""
		Generates a list of simple descriptions of the analysed objects.
		If ignoreGaps is False, then gaps between objects will be described too.
		"""

		currentAddress = -1

		for analysed in self.get_analysed_sorted():
			if currentAddress < 0:
				currentAddress = analysed.address

			if (not ignoreGaps) & (currentAddress < analysed.address):
				yield '{:08X}:{:04X} <gap>'.format(currentAddress, analysed.address - currentAddress)

			currentAddress = analysed.address + analysed.size

			if (currentAddress % 4) != 0:
				currentAddress += 4 - (currentAddress % 4)

			yield '{:08X}:{:04X} {} {}'.format(analysed.address, analysed.size, analysed.type, analysed.name)

	def enqueue_analysis(self, address, type, name = "unnamed"):
		"""
		Enqueues analysis. It is safe to call during the analysis of another object.
		"""

		for analysed in self.analysed:
			relAddr = address - analysed.address

			if (relAddr >= 0) & (relAddr < analysed.size):
				if analysed.type != type:
					raise RomAnalyser.AnalOverlapError(analysed, address, type)

				return False

		for queued in self.analQueue:
			if queued.address == address:
				if queued.type != type:
					raise RomAnalyser.AnalQueueMismatchError(address, queued.type, type)

				return True

		self.analQueue.append(RomAnalyser.QueuedAnalysis(address, type, name))
		return True

class AnalysisPrinter:
	"""
	Helper class for printing analysis results.
	"""

	def __init__(self):
		self.printers = {}

	def set_printer(self, type, printer):
		self.printers[type] = printer

	def iter_print(self, analysed):
		if not analysed.type in self.printers:
			yield "<no available representation>\n"

		else:
			for line in self.printers[analysed.type](analysed):
				yield "{}\n".format(line)

	def iter_print_list(self, analysedList):
		for analysed in analysedList:
			yield "{} {} at {:08X}:\n".format(analysed.type, analysed.name, analysed.address)

			for line in self.iter_print(analysed):
				yield "  {}".format(line)

			yield "\n"

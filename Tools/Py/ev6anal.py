import os, sys, anal

ANAL_KEY_PTRLIST = 'chapter'
ANAL_KEY_SCENE   = 'scene'
ANAL_KEY_UNITS   = 'units'
ANAL_KEY_ITEMS   = 'items'
ANAL_KEY_EVLIST  = 'evlist'
ANAL_KEY_MOMA    = 'movescr'

class SceneAnalyser:

	class Ins:

		INS_REFERENCE_ADDR = 0x085C4164

		def __init__(self, code, size, args):
			self.code = code
			self.size = size
			self.args = args

		@staticmethod
		def read_from_file(input, address):
			input.seek(anal.addr_to_offset(address))
			code = anal.read_int(input, 4)

			input.seek(anal.addr_to_offset(SceneAnalyser.Ins.INS_REFERENCE_ADDR + 8*code + 4))
			size = anal.read_int(input, 4)

			input.seek(anal.addr_to_offset(address + 4))
			args = [anal.read_int(input, 4) for _ in range(size - 1)]

			return SceneAnalyser.Ins(code, size, args)

		@staticmethod
		def read_from_bytes(bytes, offset):
			raise NotImplementedError()

		def get_byte_size(self):
			return self.size * 4

	def analyse_end(self, ins):
		self.try_end()

	def analyse_jump(self, ins):
		self.anal.enqueue_analysis(ins.args[0], ANAL_KEY_SCENE, self.name + ".jump")
		# self.try_end()

	def analyse_goto(self, ins):
		self.request_label(ins.args[0])

	def analyse_label(self, ins):
		self.set_label(ins.args[0])

	def analyse_moma(self, ins):
		self.anal.enqueue_analysis(ins.args[1], ANAL_KEY_MOMA, self.name + ".moma")

	def analyse_load(self, ins):
		self.anal.enqueue_analysis(ins.args[0], ANAL_KEY_UNITS, self.name + ".units")

	CODE_HANDLER_DICT = {
		0x00: analyse_end,   # END

		0x0E: analyse_moma,  # MOVE_MANUAL [x, y] moma
		0x10: analyse_moma,  # MOVE_MANUAL character moma

		0x12: analyse_load,  # LOAD units
		0x13: analyse_load,  # LOAD_INSTANT units

		0x1A: analyse_end,   # STOP
		0x1B: analyse_label, # LABEL $x
		0x1C: analyse_goto,  # GOTO $x
		0x1D: analyse_goto,  # GOTO_IFN_ALIVE $x character
		0x1E: analyse_goto,  # GOTO_IFN_DEPLOYED $x character
		0x1F: analyse_goto,  # GOTO_IFY_ASM $x function
		0x20: analyse_goto,  # GOTO_IFN_ASM $x function
		0x21: analyse_goto,  # GOTO_IFY_UNK $x
		0x22: analyse_goto,  # GOTO_IFY_EID $x eid
		0x23: analyse_goto,  # GOTO_IFN_EID $x eid
		0x24: analyse_goto,  # GOTO_IFY_ACTIVE $x character
		0x25: analyse_jump,  # JUMP scene
	}

	def __init__(self, anal, input, address, name):
		self.anal = anal
		self.input = input
		self.address = address
		self.name = name

		self.ended = False

		self.encounteredLabels = []
		self.expectedLabels = []

	def analyse_next(self):
		ins = SceneAnalyser.Ins.read_from_file(self.input, self.address)

		if ins.code in SceneAnalyser.CODE_HANDLER_DICT:
			SceneAnalyser.CODE_HANDLER_DICT[ins.code](self, ins)

		self.address += ins.get_byte_size()

	def set_label(self, id):
		if id in self.expectedLabels:
			self.expectedLabels.remove(id)

		self.encounteredLabels.append(id)

	def request_label(self, id):
		if not id in self.encounteredLabels and not id in self.expectedLabels:
			self.expectedLabels.append(id)

	def try_end(self):
		if len(self.expectedLabels) == 0:
			self.ended = True

def analyse_scene(analyser, input, address, name):
	"""
	Analysis handler for scenes.
	Encapsulates a SceneAnalyser doing its thing.
	"""

	sa = SceneAnalyser(analyser, input, address, name)

	while not sa.ended:
		sa.analyse_next()

	return anal.AnalysedObject(
		address, sa.address - address, ANAL_KEY_SCENE, anal.read_data_at(input, address, sa.address - address), name)

def analyse_moma(analyser, input, address, name):
	"""
	Analysis handler for movement scripts ("MOMAs").
	"""

	input.seek(anal.addr_to_offset(address))
	start = address

	while True:
		cmd = anal.read_int(input, 1, True)
		address = address + 1

		if (cmd == 12):
			anal.read_int(input, 1) # void speed
			address = address + 1

		elif (cmd == -1) | (cmd == 4):
			break

	return anal.AnalysedObject(
		start, address - start, ANAL_KEY_MOMA, anal.read_data_at(input, start, address - start), name)

def analyse_units(analyser, input, address, name):
	"""
	Analysis handler for unit groups.
	"""

	start = address

	while True:
		input.seek(anal.addr_to_offset(address))
		charId = anal.read_int(input, 1)

		address = address + 0x10

		if charId == 0:
			break

	return anal.AnalysedObject(
		start, address - start, ANAL_KEY_UNITS, anal.read_data_at(input, start, address - start), name)

def analyse_items(analyser, input, address, name):
	"""
	Analysis handler for shop item lists.
	"""

	input.seek(anal.addr_to_offset(address))
	start = address

	while True:
		item = anal.read_int(input, 2)
		address = address + 2

		if item == 0:
			break

	return anal.AnalysedObject(
		start, address - start, ANAL_KEY_ITEMS, anal.read_data_at(input, start, address - start), name)

class EvListAnalyser:

	class Ins:

		INS_REFERENCE_ADDR = 0x08666114

		def __init__(self, code, eid, size, args):
			self.code = code
			self.eid  = eid
			self.size = size
			self.args = args

		@staticmethod
		def read_from_file(input, address):
			input.seek(anal.addr_to_offset(address))
			code = anal.read_int(input, 2)
			eid  = anal.read_int(input, 2)

			input.seek(anal.addr_to_offset(EvListAnalyser.Ins.INS_REFERENCE_ADDR + 8*code + 4))
			size = anal.read_int(input, 4)

			input.seek(anal.addr_to_offset(address + 4))
			args = [anal.read_int(input, 4) for _ in range(size - 1)]

			return EvListAnalyser.Ins(code, eid, size, args)

		def get_byte_size(self):
			return self.size * 4

	def analyse_end(self, ins):
		self.ended = True

	def analyse_entry(self, ins):
		if ins.args[0] != 1:
			self.analyser.enqueue_analysis(ins.args[0], ANAL_KEY_SCENE, self.name + ".scene")

	def analyse_shop(self, ins):
		self.analyser.enqueue_analysis(ins.args[0], ANAL_KEY_ITEMS, self.name + ".shop")

	CODE_HANDLER_DICT = {
		0x0: analyse_end,
		0x1: analyse_entry, # AFEV
		0x2: analyse_entry, # TURN
		0x3: analyse_entry,
		0x4: analyse_entry,
		0x5: analyse_entry,
		0x6: analyse_entry,

		0x8: analyse_entry,
		0x9: analyse_entry,
		0xA: analyse_shop, # SHOP
		0xB: analyse_entry,
		0xC: analyse_entry,
		0xD: analyse_entry, # ASME
	}

	def __init__(self, analyser, input, address, name):
		self.analyser = analyser
		self.input = input
		self.address = address
		self.name = name

		self.ended = False

	def analyse_next(self):
		ins = EvListAnalyser.Ins.read_from_file(self.input, self.address)

		if ins.code in EvListAnalyser.CODE_HANDLER_DICT:
			EvListAnalyser.CODE_HANDLER_DICT[ins.code](self, ins)

		self.address += ins.get_byte_size()

def analyse_event_list(analyser, input, address, name):
	"""
	Analysis handler for event lists ("main codes").
	"""

	ea = EvListAnalyser(analyser, input, address, name)

	while not ea.ended:
		ea.analyse_next()

	return anal.AnalysedObject(
		address, ea.address - address, ANAL_KEY_EVLIST, anal.read_data_at(input, address, ea.address - address), name)

def analyse_chapter_events(analyser, input, address, name):
	"""
	Analysis handler for chapter events root ("pointer arrays").
	"""

	input.seek(anal.addr_to_offset(address))

	analyser.enqueue_analysis(anal.read_int(input, 4), ANAL_KEY_EVLIST, name + ".turn") # turn events
	analyser.enqueue_analysis(anal.read_int(input, 4), ANAL_KEY_EVLIST, name + ".char") # character events
	analyser.enqueue_analysis(anal.read_int(input, 4), ANAL_KEY_EVLIST, name + ".loca") # location events
	analyser.enqueue_analysis(anal.read_int(input, 4), ANAL_KEY_EVLIST, name + ".action") # misc events

	analyser.enqueue_analysis(anal.read_int(input, 4), ANAL_KEY_UNITS, name + ".blue") # initial blue units
	analyser.enqueue_analysis(anal.read_int(input, 4), ANAL_KEY_UNITS, name + ".red") # initial red units

	analyser.enqueue_analysis(anal.read_int(input, 4), ANAL_KEY_SCENE, name + ".ending") # ending scene

	return anal.AnalysedObject(
		address, 0x1C, ANAL_KEY_PTRLIST, anal.read_data_at(input, address, 0x1C), name)

def make_fe6_analyser():
	result = anal.RomAnalyser()

	result.set_analysis_handler(ANAL_KEY_SCENE, analyse_scene)
	result.set_analysis_handler(ANAL_KEY_MOMA, analyse_moma)
	result.set_analysis_handler(ANAL_KEY_UNITS, analyse_units)
	result.set_analysis_handler(ANAL_KEY_ITEMS, analyse_items)
	result.set_analysis_handler(ANAL_KEY_EVLIST, analyse_event_list)
	result.set_analysis_handler(ANAL_KEY_PTRLIST, analyse_chapter_events)

	return result

def main(args):
	if (len(args) == 0):
		sys.exit(":(")

	analyser = make_fe6_analyser()

	try:
		with open(args[0], 'rb') as f:
			CHAPTER_TABLE_ADDR = 0x086637A4
			CHAPTER_ASSET_ADDR = 0x08664398

			for i in range(45):
				f.seek(anal.addr_to_offset(CHAPTER_TABLE_ADDR + 0x44*i + 0x3A))
				assetId = anal.read_int(f, 1)

				if assetId != 0:
					f.seek(anal.addr_to_offset(CHAPTER_ASSET_ADDR + 4*assetId))
					analyser.enqueue_analysis(anal.read_int(f, 4), ANAL_KEY_PTRLIST, "chapter{}".format(i))

			analyser.analyse_queued(f)

	except Exception as e:
		sys.exit('ERROR: {}'.format(e.__repr__()))

	for line in analyser.iter_pretty_summary():
		print(line)

if __name__ == '__main__':
	main(sys.argv[1:])

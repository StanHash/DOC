import os, sys, anal

ANAL_KEY_PTRLIST = 'chapter'
ANAL_KEY_SCENE   = 'scene'
ANAL_KEY_UNITS   = 'units'
ANAL_KEY_ITEMS   = 'items'
ANAL_KEY_EVLIST  = 'evlist'
ANAL_KEY_MOMA    = 'movescr'

FE6_SCENE_INS_REFERENCE_ADDR = 0x085C4164
FE6_ELIST_INS_REFERENCE_ADDR = 0x08666114

class InsReference:

	def __init__(self, refAddr):
		self.referenceAddr = refAddr
		self.sizeCache = {}

	def get_code_size(self, code, input = None):
		if code in self.sizeCache:
			return self.sizeCache[code]

		elif input:
			input.seek(anal.addr_to_offset(self.referenceAddr + code*8 + 4))
			size = anal.read_int(input, 4)

			self.sizeCache[code] = size
			return size

		raise Exception("uncached code size with no available input")

class SceneIns:

	def __init__(self, code, size, args):
		self.code = code
		self.size = size
		self.args = args

	@staticmethod
	def read_from_file(input, address, reference):
		input.seek(anal.addr_to_offset(address))
		code = anal.read_int(input, 4)

		size = reference.get_code_size(code, input)

		input.seek(anal.addr_to_offset(address + 4))
		args = [anal.read_int(input, 4) for _ in range(size - 1)]

		return SceneIns(code, size, args)

	@staticmethod
	def read_from_bytes(bytes, offset, reference):
		code = int.from_bytes(bytes[offset:offset+4], 'little')
		size = reference.get_code_size(code)
		args = [int.from_bytes(bytes[offset+i*4+4:offset+i*4+8], 'little') for i in range(size - 1)]

		return SceneIns(code, size, args)

	def get_byte_size(self):
		return self.size * 4

class EvListIns:

	def __init__(self, code, eid, size, args):
		self.code = code
		self.eid  = eid
		self.size = size
		self.args = args

	@staticmethod
	def read_from_file(input, address, reference):
		input.seek(anal.addr_to_offset(address))
		code = anal.read_int(input, 2)
		eid  = anal.read_int(input, 2)

		size = reference.get_code_size(code, input)

		input.seek(anal.addr_to_offset(address + 4))
		args = [anal.read_int(input, 4) for _ in range(size - 1)]

		return EvListIns(code, eid, size, args)

	@staticmethod
	def read_from_bytes(bytes, offset, reference):
		code = int.from_bytes(bytes[offset:offset+2], 'little')
		eid  = int.from_bytes(bytes[offset+2:offset+4], 'little')
		size = reference.get_code_size(code)
		args = [int.from_bytes(bytes[offset+i*4+4:offset+i*4+8], 'little') for i in range(size - 1)]

		return EvListIns(code, eid, size, args)

	def get_byte_size(self):
		return self.size * 4

class SceneAnalyser:

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

	def __init__(self, reference, anal, input, address, name):
		self.anal = anal
		self.input = input
		self.address = address
		self.name = name

		self.ended = False

		self.insReference = reference

		self.encounteredLabels = []
		self.expectedLabels = []

	def analyse_next(self):
		ins = SceneIns.read_from_file(self.input, self.address, self.insReference)

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

def analyse_scene(analyser, input, address, name, reference = InsReference(FE6_SCENE_INS_REFERENCE_ADDR)):
	"""
	Analysis handler for scenes.
	Encapsulates a SceneAnalyser doing its thing.
	"""

	sa = SceneAnalyser(reference, analyser, input, address, name)

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

	def __init__(self, reference, analyser, input, address, name):
		self.analyser = analyser
		self.input = input
		self.address = address
		self.name = name

		self.insReference = reference

		self.ended = False

	def analyse_next(self):
		ins = EvListIns.read_from_file(self.input, self.address, self.insReference)

		if ins.code in EvListAnalyser.CODE_HANDLER_DICT:
			EvListAnalyser.CODE_HANDLER_DICT[ins.code](self, ins)

		self.address += ins.get_byte_size()

def analyse_event_list(analyser, input, address, name, reference = InsReference(FE6_ELIST_INS_REFERENCE_ADDR)):
	"""
	Analysis handler for event lists ("main codes").
	"""

	ea = EvListAnalyser(reference, analyser, input, address, name)

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

def main(args):
	def show_exception_and_exit(exc_type, exc_value, tb):
		import traceback

		traceback.print_exception(exc_type, exc_value, tb)
		sys.exit(-1)

	sys.excepthook = show_exception_and_exit

	if (len(args) == 0):
		sys.exit(":(")

	analyser = anal.RomAnalyser()

	analyser.set_analysis_handler(ANAL_KEY_SCENE, analyse_scene)
	analyser.set_analysis_handler(ANAL_KEY_MOMA, analyse_moma)
	analyser.set_analysis_handler(ANAL_KEY_UNITS, analyse_units)
	analyser.set_analysis_handler(ANAL_KEY_ITEMS, analyse_items)
	analyser.set_analysis_handler(ANAL_KEY_EVLIST, analyse_event_list)
	analyser.set_analysis_handler(ANAL_KEY_PTRLIST, analyse_chapter_events)

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

	for line in analyser.iter_pretty_summary():
		print(line)

if __name__ == '__main__':
	main(sys.argv[1:])

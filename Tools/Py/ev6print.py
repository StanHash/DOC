import os, sys, re, anal, ev6anal

class ScenePrinter:

	INS_FORMAT_DICT = {
		0x00: "END",
		0x01: "END2?",
		0x02: "SLEEP 0$duration",
		0x03: "BACKGROUND 0$background",
		0x04: "BACKGROUND_CONTINUED 0$background",
		0x05: "TEXT_CLEAR",
		0x06: "END?",
		0x07: "TEXT 0$text",
		0x08: "TEXT_MORE 0$text",
		0x09: "TEXT_UNK 0$text",
		0x0A: "TEXT_CONTINUE",
		0x0B: "CAMERA 0$coords16",
		0x0C: "CAMERA 0$character",
		0x0D: "MOVE 0$coords16 1$coords16",
		0x0E: "MOVE_MANUAL 0$coords16 1$movescr",
		0x0F: "MOVE 0$character 1$coords16",
		0x10: "MOVE_MANUAL 0$character 1$movescr",
		0x11: "MOVE_NEXTTO 0$character 1$character",
		0x12: "LOAD 0$units",
		0x13: "LOAD_INSTANT 0$units",
		0x14: "MOVE_WAIT",
		0x15: "CAMERA_FOLLOW_MOVE_ON",
		0x16: "CAMERA_FOLLOW_MOVE_OFF",
		0x17: "ASM 0$function",
		0x18: "ASM_UNTIL 0$function",
		0x19: "ASM_WHILE 0$function",
		0x1A: "STOP",
		0x1B: "LABEL 0$label",
		0x1C: "GOTO 0$label",
		0x1D: "GOTO_IFN_ALIVE 0$label 1$character",
		0x1E: "GOTO_IFN_DEPLOYED 0$label 1$character",
		0x1F: "GOTO_IFY_ASM 0$label 1$function",
		0x20: "GOTO_IFN_ASM 0$label 1$function",
		0x21: "GOTO_IFY_UNK 0$label",
		0x22: "GOTO_IFY_EID 0$label 1$eid",
		0x23: "GOTO_IFN_EID 0$label 1$eid",
		0x24: "GOTO_IFY_ACTIVE 0$label 1$character",
		0x25: "JUMP 0$scene",
		0x26: "ITEM 0$item",
		0x27: "ITEM 0$character 1$item",
		0x28: "MONEY 0$money",
		0x29: "MAPCHANGE 0$mapchange",
		0x2A: "MAPCHANGE 0$coords8",
		0x2B: "FACTION 0$character 1$faction",
		0x2C: "CURSOR_FLASH 0$coords16",
		0x2D: "CURSOR_FLASH 0$character",
		0x2E: "CURSOR 0$coords16",
		0x2F: "CURSOR_CLEAR",
	}

	INS_FORMAT_RE = re.compile(r'(?P<arg>[0-9]+)\$(?P<fmt>\w+)')

	def get_formatted_arg(self, ins, match):
		arg = int(match.group('arg'))
		fmt = match.group('fmt')

		value = ins.args[arg]

		if (fmt == 'address') | (fmt == 'function') | (fmt == 'scene') | (fmt == 'units') | (fmt == 'movescr'):
			return '{:08X}'.format(value)

		elif (fmt == 'text') | (fmt == 'label'):
			return '${:X}'.format(value)

		elif (fmt == 'coords16'):
			xCoord = 0xFFFF & (value)
			yCoord = 0xFFFF & (value >> 16)

			return '[{}, {}]'.format(xCoord, yCoord)

		elif (fmt == 'coords8'):
			xCoord = 0xFF & (value)
			yCoord = 0xFF & (value >> 8)

			return '[{}, {}]'.format(xCoord, yCoord)

		else:
			return '{}'.format(value)

	def get_formatted_ins(self, ins):
		if ins.code in ScenePrinter.INS_FORMAT_DICT:
			return ScenePrinter.INS_FORMAT_RE.sub(
				lambda match: self.get_formatted_arg(ins, match),
				ScenePrinter.INS_FORMAT_DICT[ins.code])

		else:
			return '_0x{:02X} {}'.format(ins.code, ins.args)

	@staticmethod
	def print_scene(analysed, insReference):
		sp = ScenePrinter()

		address = analysed.address

		while address < analysed.address + analysed.size:
			ins = ev6anal.SceneIns.read_from_bytes(analysed.data, address - analysed.address, insReference)

			yield sp.get_formatted_ins(ins)
			address += ins.get_byte_size()

def main(args):
	def show_exception_and_exit(exc_type, exc_value, tb):
		import traceback

		traceback.print_exception(exc_type, exc_value, tb)
		sys.exit(-1)

	sys.excepthook = show_exception_and_exit

	if (len(args) == 0):
		sys.exit(":(")

	sceneInsReference = ev6anal.InsReference(ev6anal.FE6_SCENE_INS_REFERENCE_ADDR)

	analyser = anal.RomAnalyser()

	analyser.set_analysis_handler(ev6anal.ANAL_KEY_SCENE, lambda a, i, d, n: ev6anal.analyse_scene(a, i, d, n, sceneInsReference))
	analyser.set_analysis_handler(ev6anal.ANAL_KEY_MOMA, ev6anal.analyse_moma)
	analyser.set_analysis_handler(ev6anal.ANAL_KEY_UNITS, ev6anal.analyse_units)
	analyser.set_analysis_handler(ev6anal.ANAL_KEY_ITEMS, ev6anal.analyse_items)
	analyser.set_analysis_handler(ev6anal.ANAL_KEY_EVLIST, ev6anal.analyse_event_list)
	analyser.set_analysis_handler(ev6anal.ANAL_KEY_PTRLIST, ev6anal.analyse_chapter_events)

	with open(args[0], 'rb') as f:
		CHAPTER_TABLE_ADDR = 0x086637A4
		CHAPTER_ASSET_ADDR = 0x08664398

		for i in range(45):
			f.seek(anal.addr_to_offset(CHAPTER_TABLE_ADDR + 0x44*i + 0x3A))
			assetId = anal.read_int(f, 1)

			if assetId != 0:
				f.seek(anal.addr_to_offset(CHAPTER_ASSET_ADDR + 4*assetId))
				analyser.enqueue_analysis(anal.read_int(f, 4), ev6anal.ANAL_KEY_PTRLIST, "chapter{}".format(i))

		analyser.analyse_queued(f)

	printer = anal.AnalysisPrinter()

	printer.set_printer(ev6anal.ANAL_KEY_SCENE, lambda a: ScenePrinter.print_scene(a, sceneInsReference))

	for line in printer.iter_print_list(analyser.get_analysed_sorted()):
		sys.stdout.write(line)

if __name__ == '__main__':
	main(sys.argv[1:])

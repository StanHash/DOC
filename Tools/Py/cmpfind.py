import sys, os

# like Pointer Finder, but for compares (cmp rx, #cst)

# Authored by Colorz
def memoize(func):
	cache = {}

	def wrapper(*args):
		if args in cache:
			return cache[args]

		else:
			result = func(*args)
			cache[args] = result

			return result

	return wrapper

@memoize
def read_rom_halfwords(romFileName):
	hwords = []

	with open(romFileName, 'rb') as rom:
		while True:
			hword = rom.read(2)

			if hword == b'':
				break

			hwords.append(hword)

	return hwords

def main(args):
	try:
		romFilename    = args[0]
		comparedNumber = int(args[1], base = 0)

	except IndexError:
		sys.exit("usage: (python3) {} <rom> <number>".format(sys.argv[0]))

	insBase = 0x2800 | (0xFF & comparedNumber)
	insMask = 0xF8FF

	for i, hwd in enumerate(read_rom_halfwords(romFilename)):
		ins = int.from_bytes(hwd, byteorder = 'little')

		if (ins & insMask) == insBase:
			print('{:8X}'.format(i*2 + 0x8000000))

if __name__ == '__main__':
	main(sys.argv[1:])

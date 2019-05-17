
import sys

def read_int(input, byteCount, signed = False):
	return int.from_bytes(input.read(byteCount), byteorder = 'little', signed = signed)

def compute_checksum(input, byteCount):
	addAcc = 0
	xorAcc = 0

	for _ in range(byteCount // 2):
		data = read_int(input, 2)

		addAcc = addAcc + data
		xorAcc = xorAcc ^ data

	return (addAcc & 0xFFFF) + (xorAcc << 16)

def main(args):
	filename = ''

	try:
		filename = args[1]

	except IndexError:
		sys.exit("usage: {} <savefile>".format(args[0]))

	with open(filename, 'rb') as f:
		for i in range(5):
			metadataOffset = 0x64 + i*0x10

			f.seek(metadataOffset + 0x0C)
			checksum = read_int(f, 4)

			f.seek(metadataOffset + 0x08)
			offset = read_int(f, 2)
			size   = read_int(f, 2)

			f.seek(offset)
			otherChecksum = compute_checksum(f, size)

			print('{:X} {:X} {}'.format(checksum, otherChecksum, checksum == otherChecksum))

if __name__ == '__main__':
	main(sys.argv)

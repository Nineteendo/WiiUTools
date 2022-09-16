from struct import pack, unpack
import subprocess
from subprocess import run

from libraries.pyvz2nineteendo import LogError, bold_input, blue_print, path_input, list_levels

def get_hex8(text, preset = -1):
	return input_hex(text, 0, 255, preset).zfill(8)
def get_int8(text, preset = -129):
	return "000000%s" % pack("b", input_int(text, -128, 127, preset)).hex()
def get_uint8(text, preset = -1):
	return "000000%s" % pack("B", input_int(text, 0, 255, preset)).hex()
def get_int16(text, preset = -32769):
	return "0000%s" % pack(">h", input_int(text, -32768, 32767, preset)).hex()
def get_uint16(text, preset = -129):
	return "0000%s" % pack(">H", input_int(text, 0, 65535, preset)).hex()
def get_hex16(text, preset = -1):
	return input_hex(text, 0, 65535, preset).zfill(8)
def get_int32(text, preset = -2147483649):
	return pack(">i", input_int(text, -2147483648, 2147483647, preset)).hex()
def get_uint32(text, preset = -1):
	return pack(">I", input_int(text, 0, 4294967295, preset)).hex()
def get_float32(text, preset = -340282346638528859811704183484516925441):
	return pack(">f", input_float(text, -340282346638528859811704183484516925440, 340282346638528859811704183484516925440, preset)).hex()
def get_hex32(text, preset = -1):
	return input_hex(text, 0, 4294967295, preset).zfill(8)

def get_value(text):
	sizes =		[0,				0,		0,			0,			1,			1,			1,			2,			2,			2,				2]
	names =		["SPECIFY",		"INT8",	"UINT8",	"HEX8",		"INT16",	"UINT16",	"HEX16",	"INT32",	"UINT32",	"FLOAT32",		"HEX32"]
	functions =	[lambda: "0"*8,	get_int8,	get_uint8,	get_hex8,	get_int16,	get_uint16,	get_hex16,	get_int32,	get_uint32,	get_float32,	get_hex32]
	list_levels(names)
	index = input_int("Value Type", 1, len(names) - 1, 0)
	return (sizes[index], functions[index](text))

def ram_write():
	list_levels(["SPECIFY", "FALSE", "TRUE"])
	pointer = input_int("Pointer", 1, 2, 0)
	if pointer == 1:
		address = get_hex32("Address")
	else:
		offset = get_hex16("Offset")
	size, value = get_value("Value")
	if pointer == 1:
		return "000%d0000 %s\n%s 00000000" % (size, address, value)
	else:
		return "001%d%s %s" % (size, offset, value)

def get_string():
	list_levels(["SPECIFY",	"FILE",	"CLIPBOARD", "STRING",	"HEX"])
	source = input_int("Source", 1, 4, 0) # Default 1
	if source == 1:
		file = path_input("Input file", "")
		byte_string = open(file, "rb").read()
	elif source == 2:
		p = subprocess.Popen(['pbpaste'], stdout=subprocess.PIPE)
		blue_print("Pasting...")
		p.wait()
		byte_string = p.stdout.read()
	elif source == 3:
		byte_string = bold_input("String").encode()
	elif source == 4:
		byte_string = input_bytes_from_hex("Hex", b"")

	length = len(byte_string)
	byte_string += b"\0\0\0\0\0\0\0\xff"[length % 8:]
	return length, "\n".join([byte_string[i:i + 4].hex() + " " + byte_string[i + 4:i + 8].hex() for i in range(0, length, 8)])


def string_write():
	list_levels(["SPECIFY", "FALSE", "TRUE"])
	pointer = input_int("Pointer", 1, 2, 1) # Default 0
	if pointer == 1:
		address = get_hex32("Address", 0)
	else:
		offset = get_hex32("Offset", 0)
	length, value = get_string()
	if pointer == 1:
		return "0100%04x %s\n" % (length, address) + value
	else:
		return "0110%04x %s\n" % (length, offset) + value

def get_code_type():
	names =		["SPECIFY",		"RAM Write",	"String Write"]
	functions =	[lambda: None,	ram_write,		string_write]
	list_levels(names)
	index = input_int("Code Type", 0, len(names) - 1, 2) # Default 0
	return functions[index]()
try:
	logerror = LogError()
	error_message = logerror.error_message
	warning_message = logerror.warning_message
	input_hex = logerror.input_hex
	input_int = logerror.input_int
	input_float = logerror.input_float
	input_bytes_from_hex = logerror.input_bytes_from_hex
	
	print("""\033[95m
\033[1mCodeWizard v0.1.0 (c) 2022 Nineteendo\033[22m
\033[1mDocumentation:\033[22m CosmoCortney
\033[0m""")
	
	code = get_code_type()
	print(code)
	run("pbcopy", universal_newlines = True, input = code)
	blue_print("Success\nCode copied to the clipboard!")
	
	logerror.finish_program()
except Exception as e:
	error_message(e)
#except BaseException as e:
#	warning_message(type(e).__name__ + " : " + str(e))
logerror.close() # Close log	
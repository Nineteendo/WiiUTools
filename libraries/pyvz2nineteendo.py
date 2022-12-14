from datetime import datetime, timedelta
from io import StringIO
from json import dump, load
from os import get_terminal_size, listdir, system
from os.path import dirname, isfile, join as osjoin, realpath, splitext
import sys
from traceback import format_exc
from urllib.request import urlopen

version_options = {
	"branch": "beta",
	"release": False,
	"latest": 0.0,
	"outdated": False
}

infinity = float('inf')
negative_infinity = -infinity

def duration(self):
	ss = self.seconds + self.microseconds / 1000000
	dd = self.days
	if dd >= 10:
		dd += round(ss / 86400)
	elif dd >= 1:
		dd += round(ss / 86400, 1)
	elif ss >= 3600:
		ss = round(ss)
	else:
		ss = round(ss, 1)
	
	mm, ss = divmod(ss, 60)
	hh, mm = divmod(mm, 60)
	aa, hh = divmod(hh, 24)
	dd += aa
	
	if dd:
		if dd >= 1000:
			return "999+days"
		elif dd >= 10:
			return "%03d days" % dd
		else:
			return "%.1f days" % dd
	elif hh:
		return "%02d:%02d:%02d" % (hh, mm, ss)
	else:
		return "%02d:%05.2f" % (mm, ss)
class LogError:
	def __init__(self):
		system("")
		if getattr(sys, "frozen", False):
			self.application_path = dirname(sys.executable)
		else:
			self.application_path = sys.path[0]
		try:
			self.fail = open(osjoin(self.application_path, "fail.txt"), "w")
		except PermissionError as e:
			self.fail = StringIO()
			self.fail.name = None
			self.error_message(e)
	
	def warning_message(self, string):
		self.fail.write("\t" + string + "\n")
		self.fail.flush()
		print("\33[93m" + string + "\33[0m")
	def error_message(self, e, sub = "", string = ""):
		string += type(e).__name__ + sub + ": " + str(e) + "\n" + format_exc()
		self.fail.write(string + "\n")
		self.fail.flush()
		print("\033[91m" + string + "\033[0m")
	
	def update_options(self, options, newoptions):
		for key in options:
			if key in newoptions and newoptions[key] != options[key]:
				if type(options[key]) == type(newoptions[key]):
					options[key] = newoptions[key]
				elif isinstance(options[key], tuple) and isinstance(newoptions[key], list):
					options[key] = tuple([str(i).lower() for i in newoptions[key]])
				elif key == "indent" and newoptions[key] == None:
					options[key] = newoptions[key]
	
	def check_version(self, mayor = 2, minor = 0, micro = 0):
		if sys.version_info[:3] < (mayor, minor, micro):
			raise BaseException("Must be using Python " + repr(mayor) + "." + repr(minor) + "." + repr(micro) + " or newer")
	def get_update(self, repository, branches, release_tag):
		try:
			self.update_options(version_options, load(open(osjoin(self.application_path, ".version.json"), "rb")))
		except Exception as e:
			self.error_message(e)
		branch = version_options["branch"]
		now = datetime.timestamp(datetime.now()) // 86400 # Round to day
		if now != version_options["latest"]:
			version_options["latest"] = now
			try:
				if version_options["release"]:
					with urlopen('https://api.github.com/repos/' + repository + '/releases') as response:
						version_options["outdated"] = release_tag != load(response)[0]["tag_name"]
				else:
					with urlopen('https://api.github.com/repos/' + repository + '/branches/' + branch) as response:
						version_options["outdated"] = branches[branch] != load(response)["commit"]["commit"]["message"]
			except Exception as e:
				self.error_message(e, "while getting update: ")
		if version_options["outdated"]:
			if version_options["release"]:
				self.warning_message("Download new update: https://github.com/" + repository + "/releases/latest")
			else:
				self.warning_message("\033[1mDownload new update:\033[22m \033[4mhttps://github.com/" + repository + "/tree/" + branch + "\033[24m\n")
		dump(version_options, open(osjoin(self.application_path, ".version.json"), "w"))
	def input_hex(self, text, minimum, maximum, preset):
		try:
			if preset < minimum:
				integer_value = None
				new_string = bold_input(text + " (%x-%x)" % (minimum, maximum))
				while new_string or integer_value == None:
					raw_integer = int(new_string, base = 16)
					integer_value = max(minimum, min(maximum, raw_integer))
					new_string = ""
					if raw_integer != integer_value:
						new_string = bold_input("Confirm \033[100m%x" % integer_value)
			else:
				integer_value = max(minimum, min(maximum, preset))
				print("\033[1m"+ text + " (%x-%x)\033[0m: %d" % (minimum, maximum, integer_value))
			return "%x" % integer_value
		except Exception as e:
			self.warning_message(type(e).__name__ + " : " + str(e))
			self.warning_message("Defaulting to %x" % minimum)
			return "%x" % minimum
	def input_bytes_from_hex(self, text, preset):
		try:
			if preset:
				print("\033[1m"+ text + "\033[0m: " + preset.hex())
				return preset
			else:
				return bytes.fromhex(bold_input(text))
		except Exception as e:
			self.warning_message(type(e).__name__ + " : " + str(e))
			self.warning_message('Defaulting to ""')
			return b""
	def input_int(self, text, minimum, maximum, preset):
	# Set input level for conversion
		try:
			if preset < minimum:
				integer_value = None
				new_string = bold_input(text + " (%d-%d)" % (minimum, maximum))
				while new_string or integer_value == None:
					raw_integer = int(new_string)
					integer_value = max(minimum, min(maximum, raw_integer))
					new_string = ""
					if raw_integer != integer_value:
						new_string = bold_input("Confirm \033[100m%d" % integer_value)
			else:
				integer_value = max(minimum, min(maximum, preset))
				print("\033[1m"+ text + " (%d-%d)\033[0m: %d" % (minimum, maximum, integer_value))
			return integer_value
		except Exception as e:
			self.warning_message(type(e).__name__ + " : " + str(e))
			self.warning_message("Defaulting to %d" % minimum)
			return minimum
	def input_float(self, text, minimum, maximum, preset):
		try:
			if negative_infinity < preset < minimum:
				float_value = float(bold_input(text))
			else:
				print("\033[1m"+ text + "\033[0m: " + repr(preset))
				float_value = preset
			if negative_infinity < float_value < minimum:
				float_value = minimum
			elif maximum < float_value < infinity:
				float_value = maximum
			return float_value
		except Exception as e:
			self.warning_message(type(e).__name__ + " : " + str(e))
			self.warning_message("Defaulting to " + str(minimum))
			return minimum
	def load_template(self, options, index):
	# Load template into options
		folder = osjoin(self.application_path, "options")
		try:
			templates = {}
			blue_print("\033[1mTEMPLATES:\033[0m")
			for entry in sorted(listdir(folder)):
				if isfile(osjoin(folder, entry)):
					file, extension = splitext(entry)
					if extension == ".json" and entry.count("--") == 2:
						dash_list = file.split("--")
						key = dash_list[0].lower()
						if not key in templates:
							blue_print("\033[1m" + key + "\033[0m: " + dash_list[index])
							templates[key] = entry
					elif entry.count("--") > 0:
						print("\033[1m"+ "--".join(file.split("--")[1:]) + "\033[0m")
			length = len(templates)
			if length == 0:
				green_print("Loaded default template")
			else:
				if length > 1:
					key = bold_input("Choose template").lower()
				
				name = templates[key]
				self.update_options(options, load(open(osjoin(folder, name), "rb")))
				green_print("Loaded template " + name)
		except Exception as e:
			self.error_message(e, "while loading options: ")
			self.warning_message("Falling back to default options.")
		return options
	def finish_program(self):
		if self.fail.tell() > 0:
			name = self.fail.name
			if name == None:
				open(path_input("\33[93mErrors occured, dump to\33[0m", ""), "w").write(self.fail.getvalue())
			else:
				print("\33[93mErrors occured, check: " + self.fail.name + "\33[0m")
		bold_input("\033[95mPRESS [ENTER]")
	def close(self):
	# Close fail file
		self.fail.close()
class ProgressBar:
	def __init__(self, levels = 1, fail = StringIO()):
		self.fail = fail
		self.level = -1
		self.levels = levels
		self.width = get_terminal_size().columns - 23
		self.entry = [0] * levels
		self.ratio = [1] * levels
		self.start = [datetime.now()] * levels
		self.actions = 0
		self.warnings = 0
		self.errors = 0
		print("\n" * levels)
		self.show()
	def split_task(self, entries = 1):
		self.level += 1
		self.start[self.level] = datetime.now()
		self.entry[self.level] = 0
		self.ratio[self.level] = 1 / entries if entries else 1
	def merge_task(self):
		self.entry[self.level] = 0
		self.level -= 1
	def finish_sub_task(self):
		self.actions += 1
		self.entry[self.level] += 1
		self.show()
	def silent_warning(self, string):
		self.fail.write("\t" + string + "\n")
		self.fail.flush()
		self.warnings += 1
		self.show()
	def silent_error(self, e, sub = "", string = ""):
		string += type(e).__name__ + sub + ": " + str(e) + "\n" + format_exc()
		self.fail.write(string + "\n")
		self.fail.flush()
		self.errors += 1
		self.show()
	def show(self):
		width = get_terminal_size().columns - 23
		temp = 0
		lines = []
		now = datetime.now()
		for level in range(self.levels - 1, -1, -1):
			temp = self.ratio[level] * (temp + self.entry[level])
			current = now - self.start[level] if temp else timedelta(0)
			progress = int(width * temp)
			lines.append(progress * "#" + (width - progress) * "." + " %03d" % (100 * temp) + "% " + duration(current) + " " + duration(current / temp - current if temp else current))
		if width < self.width:
			print(end = "\033c")
		print("\033[A" * (self.levels + 1) + "\n".join(lines) + "\n%d actions %d warnings %d errors" % (self.actions, self.warnings, self.errors), end = "\n\0337")
		self.width = width
def blue_print(text):
# Print in blue text
	print("\033[94m"+ text + "\033[0m")
def green_print(text):
# Print in green text
	print("\033[32m"+ text + "\033[0m")
def bold_input(text):
# Input in bold text
	return input("\033[1m"+ text + "\033[0m: ")
def path_input(text, preset):
# Input hybrid path
	if preset != "":
		print("\033[1m"+ text + "\033[0m: " + preset)
		return preset
	else:
		string = ""
		newstring = bold_input(text)
		while newstring or string == "":
			string = ""
			quoted = 0
			escaped = False
			temp_string = ""
			confirm = False
			for char in newstring:
				if escaped:
					if quoted != 1 and char == "'" or quoted != 2 and char == '"' or quoted == 0 and char in "\\ ()":
						string += temp_string + char
						confirm = True
					else:
						string += temp_string + "\\" + char
					temp_string = ""
					escaped = False
				elif char == "\\":
					escaped = True
				elif quoted != 2 and char == "'":
					quoted = 1 - quoted
				elif quoted != 1 and char == '"':
					quoted = 2 - quoted
				elif quoted != 0 or char != " ":
					string += temp_string + char
					temp_string = ""
				else:
					temp_string += " "
			if string == "":
				newstring = bold_input("\033[91mEnter a path")
			else:
				newstring = ""
				processed_string = realpath(string)
				if confirm or processed_string != string:
					newstring = bold_input("Confirm \033[100m" + processed_string)
		return processed_string
def list_levels(levels):
	blue_print("""
""" +  " ".join([repr(i) + "-" + levels[i] for i in range(len(levels))]))
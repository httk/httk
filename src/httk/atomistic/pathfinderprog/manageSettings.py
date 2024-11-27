import json
class settings():
	def __init__(self):
		with open("settings.json") as f:
			self.settings_dict = json.load(f)
	def __str__(self):
		return_s = ""
		for key, val in self.settings_dict.items():
			return_s += key+"="+str(val)+"\n"
		return return_s.strip()
	def set_value(self, name, new_value):
		self.settings_dict[name] = new_value
		with open("settings.json", "w") as f:
			json.dump(self.settings_dict, f, indent=4)
	def get_value(self, name):
		return self.settings_dict[name]
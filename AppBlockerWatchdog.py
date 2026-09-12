import psutil
import os
import time
import logging
import sys
import json
import traceback

def SET_APPBLOCKER_NAME_AND_PATH():

	with open(data_path, "r") as f:
		#Pamietaj ze czytanie pliku ma swoj "kursor" jednokierunkowy.
		text = f.read() #raz przesuwam kursor czytając cały plik

		if len(text) > 0:
			global AppBlockerPath
			global AppBlockerName
			logging.error("Zawartosc: " + repr(text))
			data = json.loads(text) # i korzystam do końca z mojego przetworzzonego raz pliku, musi byc loads
			AppBlockerName = data.setdefault("AppBlockerName", None)
			AppBlockerPath = os.path.join(folder, AppBlockerName)


if getattr(sys, "frozen", False):
	#program wykonuje się w exe (sys "frozen" = True)
	watchdogPath = sys.executable
	folder = os.path.dirname(watchdogPath)
else:
	#program wykonuje się w .py, pyCharmie (sys "frozen" = False)
	watchdogPath = __file__
	folder = os.path.dirname(watchdogPath)

data={}

data_path = os.path.join(folder, "data.json")
sciezka_logg = os.path.join(folder, "logs.log")
logging.basicConfig(filename=sciezka_logg, level=logging.ERROR)

try:
	SET_APPBLOCKER_NAME_AND_PATH()

except Exception as e:
	logging.error(f"Something went wrong  while working with working with data file. {e}\n{traceback.format_exc()}")

while True:
	try:
		time.sleep(1)
		isAppBlockerWorking = False

		if AppBlockerName is None:
			SET_APPBLOCKER_NAME_AND_PATH()

		else:
			for proces in psutil.process_iter(["pid", "name", "exe"]):
				try:
					if proces.info["exe"] is None:
						continue  # ten proces nie ma ścieżki - pomiń go
					if os.path.normpath(proces.info["exe"]) == os.path.normpath(AppBlockerPath):
						isAppBlockerWorking = True
				except (psutil.NoSuchProcess, psutil.AccessDenied):
					logging.error("blocked")
					continue

			if not isAppBlockerWorking:
				os.startfile(AppBlockerPath)

	except Exception as e:
		logging.error(f"Something went wrong while running MAIN LOOP in watchdog script. {e}\n{traceback.format_exc()}")





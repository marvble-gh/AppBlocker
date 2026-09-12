import tkinter as tk
import json
from tkinter import filedialog
from tkinter import ttk
import psutil
import time
import os
import threading
import logging
import sys
import winreg
import pystray
from PIL import Image
import traceback


def SHOW_WINDOW(icon, item):
	window.after(0, window.deiconify)

def CLOSE_PROGRAM(icon, item):
	icon.stop()
	window.destroy()

def HIDE_WINDOW():
	window.withdraw()

def ROLL_ALL():
	for iid in app_listbox.get_children():
		app_listbox.item(iid, open=False)

def ADDAPP():

	path = filedialog.askopenfilename(
		title="Choose an app/apps to block.",
		filetypes=[("Performing files", "*.exe"), ("All files", "*.*")]
	)
	try:
		if path != "" and path.endswith(".exe") and path not in data.get("apps", []) and os.path.normpath(path) != os.path.normpath(myPath):

			new_index = len(data.get("apps", []))
			name = os.path.basename(path)
			app_listbox.insert("", "end", iid=str(new_index), text=name)
			app_listbox.insert(str(new_index), "end", iid=f"{new_index}_child", text=path)

			data.setdefault("apps", []).append(path)
			data["AppBlockerName"] = programName
			with open(data_path, "w") as file:
				json.dump(data, file)

	except Exception as e:
			logging.error(f"Error occurred while running ADDAPP: {e}\n{traceback.format_exc()}")

def LOADAPPS():
	try:
		for index, app in enumerate(data.get("apps", [])):
			name = os.path.basename(app)
			app_listbox.insert("", "end", iid=str(index), text=name)
			app_listbox.insert(str(index), "end",iid=f"{index}_child", text=app)
	except Exception as e:
		logging.error(f"Error occurred while running LOADAPPS: {e}\n{traceback.format_exc()}")

def SAVE_CODE():
	saved_code=code_frame.get()
	data["code"] =saved_code
	data["AppBlockerName"] = programName
	with open(data_path, "w") as file:
		json.dump(data, file)

def ADD_TO_AUTOSTART():
	def PATH_OVERWRITE():
		key = winreg.OpenKey(
			winreg.HKEY_CURRENT_USER,
			r"Software\Microsoft\Windows\CurrentVersion\Run",
			0,
			winreg.KEY_SET_VALUE
		)
		winreg.SetValueEx(key, "AppBlocker", 0, winreg.REG_SZ, myPath)
		winreg.CloseKey(key)

	try:
	
		key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0,
		                       winreg.KEY_READ)
		value, _ = winreg.QueryValueEx(key, "AppBlocker")
		winreg.CloseKey(key)

		if os.path.normpath(value) != os.path.normpath(myPath):
			PATH_OVERWRITE()

	except FileNotFoundError:
		PATH_OVERWRITE()



def DELETEAPP():
	try:
		marking = app_listbox.selection()
		for iid in sorted(marking, key=int, reverse=True):
			app_listbox.delete(iid)
			data["apps"].pop(int(iid))
			with open(data_path, "w") as file:
				json.dump(data, file)
	except Exception as e:
		logging.error(f"Error occurred while running DELETEAPP: {e}\n{traceback.format_exc()}")

def COPY_PATH():
	try:
		marking = app_listbox.selection()
		if not marking:
			return

		iid = str(marking[0])

		children = app_listbox.get_children(iid)

		if len(children) > 0:
			child_iid = children[0]
			text = app_listbox.item(child_iid)["text"]
		else:
			text = app_listbox.item(iid)["text"]

		window.clipboard_clear()
		window.clipboard_append(text)


	except Exception as e:
		logging.error(f"Error occurred while running COPY_PATH: {e}\n{traceback.format_exc()}")



def ASK_FOR_CODE(app_path):
	global isCorrectCodeEntered, isCodeWindowShowing

	def MONITORING_FUNCTION_2():
		try:
			global isCorrectCodeEntered, isCodeWindowShowing
			if isDataLoaded:
				blockedApps = data.setdefault("apps", [])  # kopia "apps z słownika
			while isCodeWindowShowing and not isCorrectCodeEntered:
				for locked_path in blockedApps:

					matching_processes = []
					for proces in psutil.process_iter(["pid", "name", "exe"]):
						try:

							if proces.info["exe"] is None:
								continue  #This proces does not have a path, skip it.

							if os.path.normpath(proces.info["exe"]) == os.path.normpath(locked_path):
								matching_processes.append(proces)
						except (psutil.NoSuchProcess, psutil.AccessDenied):
							continue

					if len(matching_processes) == 0:
						unlocked[locked_path] = False
						continue

					if unlocked.get(locked_path, False) == True:
						continue

					if isCorrectCodeEntered:
						break
					if not isCorrectCodeEntered:
						for proces in matching_processes:
							proces.kill()

				time.sleep(1)

		except Exception as e:
			logging.error(f"Error occurred while running MONITORING_FUNCTION_2: {e}\n{traceback.format_exc()}")

	def ENTER_CODE():
		global isCorrectCodeEntered, isCodeWindowShowing

		entered_code = check_code.get()
		if entered_code == data["code"]:
			isCorrectCodeEntered = True

			os.startfile(app_path)
			unlocked[app_path] = True

		code_window.destroy()
		isCodeWindowShowing = False

	try:

		code_window = tk.Tk()
		code_window.geometry("275x100")
		code_window.title("Enter Code.")
		try:
			key_window_img = tk.PhotoImage(file=KeyIconPath)
			code_window.photo = key_window_img

			code_window.iconphoto(False, key_window_img)
		except Exception as e:
			logging.error(f"Error occurred while trying to set code_window icon: {e}\n{traceback.format_exc()}") #========== Nie wyświetla błędu ale ikona nadal się nie pokazuje.

		CodeWindowTitle = tk.Label(code_window, text="Unlock App")
		CodeWindowTitle.pack()

		check_code = tk.Entry(code_window)
		check_code.pack()
		check_code.focus_set()


		enter_button = tk.Button(code_window, text="Enter", command=ENTER_CODE)
		enter_button.pack()

		isCodeWindowShowing = True

		MONITORING_THREAD_2 = threading.Thread(target=MONITORING_FUNCTION_2, daemon=True)
		MONITORING_THREAD_2.start()


		code_window.mainloop()

		isCodeWindowShowing = False
		isCorrectCodeEntered = False
	except Exception as e:
		logging.error(f"Error occurred while running ENTER_CODE function: {e}\n{traceback.format_exc()}")



def MONITORING_FUNCTION_1():
	try:
		while True:
			time.sleep(1)
			blockedApps = data.setdefault("apps", []) # kopia "apps z słownika
			for locked_path in blockedApps:

				matching_processes = []
				for proces in psutil.process_iter(["pid", "name", "exe"]):
					try:

						if proces.info["exe"] is None:
							continue  # This proces does not have a path, skip it.

						if os.path.normpath(proces.info["exe"]) == os.path.normpath(locked_path):
							matching_processes.append(proces)

					except (psutil.NoSuchProcess, psutil.AccessDenied):
						continue

				if len(matching_processes) == 0:
					unlocked[locked_path] = False
					continue

				if unlocked.get(locked_path, False) == True:
					continue

				for proces in matching_processes:
					proces.kill()

				ASK_FOR_CODE(locked_path)

	except Exception as e:
		logging.error(f"Error occurred while running MONITORING_FUNCTION_1: {e}\n{traceback.format_exc()}")


#==========================STARTING DATA===================================

watchdogPathConfirmed = False

if getattr(sys, "frozen", False):
	#RUNNING IN EXE (sys "frozen" = True)
	myPath = sys.executable
	folder = os.path.dirname(myPath)
	ADD_TO_AUTOSTART()
	appBlockerPath = myPath
	try:
		watchdog_path = os.path.join(folder, "AppBlockerWatchdog.exe")
	except Exception as e:
		logging.error("APPBLOCKERWATCHOG NOT FOUND, PLEASE TRY REINSTALLING ASAP.")
else:
	#RUNNING IN PYCHARM (sys "frozen" = False)
	myPath = __file__
	folder = os.path.dirname(myPath)
	appBlockerPath = __file__


data_path = os.path.join(folder, "data.json")
logg_path = os.path.join(folder, "logs.log")
logging.basicConfig(filename=logg_path, level=logging.ERROR)
programName = os.path.basename(appBlockerPath)
KeyIconPath = os.path.join(folder, "appBlockerKeyImage.png")
ProgramIconPath = os.path.join(folder, "appBlockerIconImage.png")
image = Image.open(ProgramIconPath)
menu = pystray.Menu(
	pystray.MenuItem("Show", SHOW_WINDOW),
	pystray.MenuItem("Close", CLOSE_PROGRAM)
)
tray_icon = pystray.Icon(programName, image, "App Blocker", menu)

isWatchdogRunning = False
isDataLoaded = False

window = tk.Tk()
window.title("App Blocker")
window.geometry("500x500")
data={}
unlocked={}


try:
	img = tk.PhotoImage(file=ProgramIconPath)
	window.iconphoto(False, img)
except:
	logging.error(f'No such image as "{img}" found.')

isCodeWindowShowing = False
isCorrectCodeEntered = False

#=======================WIDGETS============================

#pattern jest taki: widget = tk.coś(parent, wybrana funkcja)
widget1 = tk.Label(window, text="Save your code here:")
widget1.pack(pady=(10, 0))

code_frame = tk.Entry(window, show="*")
code_frame.pack()

save_code = tk.Button(window, text="Save Code", command=SAVE_CODE)
save_code.pack(pady="5")


frame = tk.Frame(window)
frame.pack(pady=(15, 5))

hideButton = tk.Button(frame, text="Hide All", command=ROLL_ALL)
hideButton.pack(side="left", padx=(0, 10))

copyPath = tk.Button(frame, text="Copy Path", command=COPY_PATH)
copyPath.pack(side="left", padx=(0, 0))

addAppButton = tk.Button(frame, text="Add App", command=ADDAPP) #addApp bez ()
addAppButton.pack(side="left", padx=(30, 5))

deleteAppButton = tk.Button(frame, text="Delete App", command=DELETEAPP)
deleteAppButton.pack(side="left", padx=(5, 150))

app_listbox = ttk.Treeview(window,)
app_listbox.pack(fill="both", expand=True)

#====================== LOAD EVERYTHING===================================

try:
	with open(data_path, "r") as file:
		# jednokierunkowy kursor, pamietaj.
		text = file.read()

		if len(text) > 0:
			data = json.loads(text)
			LOADAPPS()
			isDataLoaded = True

	data["AppBlockerName"] = programName

	with open(data_path, "w") as file:
		json.dump(data, file)
	try:
		for proces in psutil.process_iter(["pid", "name", "exe"]):

			if proces.info["exe"] is None:
				continue

			if os.path.normpath(proces.info["exe"]) == os.path.normpath(watchdog_path):
					isWatchdogRunning = True
		if not isWatchdogRunning:
			os.startfile(watchdog_path)
	except Exception as e:
		logging.error(f"Something went wrong {e}\n{traceback.format_exc()}")

except Exception as e:
	logging.error(f"Something went wrong: {e}\n{traceback.format_exc()}")

#========================MONITORS=========================

MONITORING_THREAD_1 = threading.Thread(target=MONITORING_FUNCTION_1, daemon=True)
MONITORING_THREAD_1.start()

PNG_LOADER = threading.Thread(target=tray_icon.run, daemon=True)
PNG_LOADER.start()


window.protocol("WM_DELETE_WINDOW", HIDE_WINDOW)

window.mainloop() #The last line of code


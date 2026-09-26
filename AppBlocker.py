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
		if path != "" and path.endswith(".exe") and path not in data.get("apps", []) and os.path.normcase(os.path.normpath(path)) != os.path.normcase(os.path.normpath(myPath)):

			new_index = len(data.get("apps", []))
			name = os.path.basename(path)
			app_listbox.insert("", "end", iid=str(new_index), text=name)
			app_listbox.insert(str(new_index), "end", iid=f"{new_index}_child", text=path)

			data.setdefault("apps", []).append(path)
			data["AppBlockerName"] = programName

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

def CONTINUE_WITH_CODE():
	global doContinue, isCorrectCodeEntered, isCodeWindowShowing
	doContinue = False
	isCorrectCodeEntered = False

	def CHECK_CODE():
		global doContinue, isCorrectCodeEntered
		if entry1.get() == data.get("code", []):
			doContinue = True
			isCorrectCodeEntered = True
			enter_code_window.destroy()


	enter_code_window = tk.Tk()
	enter_code_window.geometry("250x150")
	enter_code_window.resizable(False, False)
	enter_code_window.title("Enter code.")
	enter_code_window.grab_set()

	isCodeWindowShowing = True

	try:
		enter_code_window.iconbitmap(KeyIconPath)  # .ico required
	except Exception as e:
		logging.error(f"Error occurred while trying to set catch_window icon: {e}\n{traceback.format_exc()}")


	text1 = tk.Label(enter_code_window, text="Enter code to continue:")
	text1.pack(pady=(10,0))

	entry1 = tk.Entry(enter_code_window, show="*")
	entry1.pack(pady=(10,0))
	entry1.focus_force()

	button1 = tk.Button(enter_code_window, text="Enter", command=CHECK_CODE)
	button1.pack(pady=(10,0))
	button1.bind("<Return>", lambda e: CHECK_CODE() if not doContinue else None)

	if data.get("code", []) == []:
		doContinue = True
		isCorrectCodeEntered = True
		enter_code_window.destroy()

	enter_code_window.mainloop()
	isCodeWindowShowing = False
	doContinue = False

def SAVE_CODE():
	try:
		global doContinue, isCodeWindowShowing

		if not isCodeWindowShowing:
			if data.get("code", []) == [] or code_frame.get() == data.get("code", []):
				saved_code = code_frame.get()
				data["code"] = saved_code
			else:
				CONTINUE_WITH_CODE()
				if doContinue:
					saved_code = code_frame.get()
					data["code"] = saved_code
				else:
					logging.ERROR("doContinue false")



	except Exception as e:
		logging.error(f"Error occurred while running SAVE_CODE: {e}\n{traceback.format_exc()}")
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

		if os.path.normcase(os.path.normpath(value)) != os.path.normcase(os.path.normpath(myPath)):
			PATH_OVERWRITE()

	except FileNotFoundError:
		PATH_OVERWRITE()



def DELETEAPP():
	try:
		marking = app_listbox.selection()
		for iid in sorted(marking, key=int, reverse=True):
			app_listbox.delete(iid)
			data["apps"].pop(int(iid))
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
	global isCorrectCodeEntered, isCodeWindowShowing, doContinue
	isCodeWindowShowing = False
	isCorrectCodeEntered = False

	def MONITORING_FUNCTION_2(): #This monitoring thread works only while the code_window is showing.
								# Its job is to kill EVERY blocked app (unless the app is in 'unlocked{}' dict) while code_window is showing.
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

								if os.path.normcase(os.path.normpath(proces.info["exe"])) == os.path.normcase(os.path.normpath(locked_path)):
									matching_processes.append(proces)
							except (psutil.NoSuchProcess, psutil.AccessDenied):
								continue

						if len(matching_processes) == 0: #User completely closed unlocked program, set it back to locked.
							unlocked[locked_path] = False
							continue

						if unlocked.get(locked_path, False) == True: #matching_processes is not empty, if locked_path is in unlocked, don't do anything.
							continue

						if not isCorrectCodeEntered:
							for proces in matching_processes:
								proces.kill()

					time.sleep(1)

		except Exception as e:
			logging.error(f"Error occurred while running MONITORING_FUNCTION_2: {e}\n{traceback.format_exc()}")
	try:

		threading.Thread(target=MONITORING_FUNCTION_2, daemon=True).start(); CONTINUE_WITH_CODE()
		if doContinue:
			isCorrectCodeEntered = True

			os.startfile(app_path)
			unlocked[app_path] = True  # app_path is locked_path from monitoring thread 1, under different name.
			isCorrectCodeEntered = False


	except Exception as e:
		logging.error(f"Error occurred while running ASK_FOR_CODE function: {e}\n{traceback.format_exc()}")



def MONITORING_FUNCTION_1():
	try:
		global isWatchdogRunning
		while True:
			time.sleep(1)
			blockedApps = data.setdefault("apps", [])
			data["AppBlockerName"] = programName
			with open(data_path, "w") as file:
				json.dump(data, file)

			if len(blockedApps) > 0:
				try:
					isWatchdogRunning = False
					for proces in psutil.process_iter(["pid", "name", "exe"]):
						try:
							if proces.info["exe"] is None:
								continue
							if os.path.normcase(os.path.normpath(proces.info["exe"])) == os.path.normcase(os.path.normpath(watchdog_path)):
								isWatchdogRunning = True
						except (psutil.NoSuchProcess, psutil.AccessDenied):
							continue

					if not isWatchdogRunning:
						os.startfile(watchdog_path)
				except Exception as e:
					logging.error(f"Error occurred while trying to find/run watchdog in MONITORING_FUNCTION_1: {e}\n{traceback.format_exc()}")
			for locked_path in blockedApps:

				matching_processes = []
				for proces in psutil.process_iter(["pid", "name", "exe"]):
					try:
						if proces.info["exe"] is None:
							continue
						if os.path.normcase(os.path.normpath(proces.info["exe"])) == os.path.normcase(os.path.normpath(locked_path)):
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

myPath = sys.executable
folder = os.path.dirname(myPath)
ADD_TO_AUTOSTART()
appBlockerPath = myPath
try:
	watchdog_path = os.path.join(folder, "AppBlockerWatchdog.exe")
except Exception as e:
	logging.error("APPBLOCKERWATCHOG NOT FOUND, PLEASE TRY REINSTALLING ASAP.")


data_path = os.path.join(folder, "data.json")
logg_path = os.path.join(folder, "logs.log")
logging.basicConfig(filename=logg_path, level=logging.ERROR)
programName = os.path.basename(appBlockerPath)
KeyIconPath = os.path.join(folder, "appBlockerKeyImage.ico")
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
window.resizable(width=False, height=False)
data={}
unlocked={}


try:
	img = tk.PhotoImage(file=ProgramIconPath)
	window.iconphoto(False, img)
except:
	logging.error(f'No such image as "{img}" found.')

isCodeWindowShowing = False
isCorrectCodeEntered = False
doContinue = False

#=======================WIDGETS============================

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

addAppButton = tk.Button(frame, text="Add App", command=ADDAPP)
addAppButton.pack(side="left", padx=(30, 5))

deleteAppButton = tk.Button(frame, text="Delete App", command=DELETEAPP)
deleteAppButton.pack(side="left", padx=(5, 150))

app_listbox = ttk.Treeview(window,)
app_listbox.pack(fill="both", expand=True)

#====================== LOAD EVERYTHING===================================

try:
	with open(data_path, "r") as file:

		text = file.read()

		if len(text) > 0:
			data = json.loads(text)
			LOADAPPS()
			isDataLoaded = True

	data["AppBlockerName"] = programName


except Exception as e:
	logging.error(f"Something went wrong: {e}\n{traceback.format_exc()}")

#========================MONITORS=========================

MONITORING_THREAD_1 = threading.Thread(target=MONITORING_FUNCTION_1, daemon=True)
MONITORING_THREAD_1.start()

PNG_LOADER = threading.Thread(target=tray_icon.run, daemon=True)
PNG_LOADER.start()


window.protocol("WM_DELETE_WINDOW", HIDE_WINDOW)

window.mainloop() #The last line of code


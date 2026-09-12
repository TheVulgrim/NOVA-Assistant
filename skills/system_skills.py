import os
from core.registry import skill
import platform
import subprocess
from datetime import datetime
import psutil as psutil
from tabulate import tabulate
import webbrowser
import pyjokes
import cowsay
import random

current_platform = platform.system()
table = {
    "Windows": {
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "terminal": "cmd.exe",
        "powershell": "powershell.exe",
        "explorer": "explorer.exe",
        "edge": "msedge.exe",
        "chrome": "chrome.exe",
    },
    "Linux": {
        "notepad": "gedit",
        "calculator": "gnome-calculator",
        "terminal": "terminal",
        "brave": "brave-browser",
        "telegram": "telegram-desktop",
    }
}


def _silent_process_options():
    """Keep helper applications from writing noise to NOVA's terminal."""
    options = {
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
    }
    if current_platform == "Windows":
        options["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return options


@skill("open", "launch", "start")
def open_app(text):
    try:
        applications = table.get(current_platform, {})
        for word in text.lower().split():
            if word in applications:
                subprocess.Popen([applications[word]], **_silent_process_options())
                return f"Opening {word}..."
        return f"No application found for '{text.strip()}'."
    except Exception as e:
        return f"Error opening application: {str(e)}"


@skill("screenshot", "capture", "screen","ss")
def screenshot(s):
    try:
        filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        path = os.path.abspath(os.path.join(os.path.expanduser("~"), filename))

        if current_platform == "Linux":
            subprocess.run(["flameshot", "full", "-p", path],
                           check=True, **_silent_process_options())
        elif current_platform == "Windows":
            # Uses built-in .NET screen APIs, so Pillow is not required.
            powershell_script = (
                "Add-Type -AssemblyName System.Windows.Forms; "
                "Add-Type -AssemblyName System.Drawing; "
                "$bounds = [System.Windows.Forms.SystemInformation]::VirtualScreen; "
                "$bitmap = New-Object System.Drawing.Bitmap $bounds.Width,$bounds.Height; "
                "$graphics = [System.Drawing.Graphics]::FromImage($bitmap); "
                "$graphics.CopyFromScreen($bounds.Left,$bounds.Top,0,0,$bitmap.Size); "
                f"$bitmap.Save('{path.replace(chr(39), chr(39) + chr(39))}'); "
                "$graphics.Dispose(); $bitmap.Dispose()"
            )
            subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive",
                            "-Command", powershell_script],
                           check=True, **_silent_process_options())
        else:
            return f"Screenshot isn't supported on {current_platform} yet."

        return f"Screenshot saved to {path}."
    except Exception as e:
        return f"Error taking screenshot: {str(e)}"


@skill("system", "information", "sysinfo", "info", "status", "stats")
def system_info(*text):
    try:
        def cpu():
            util = psutil.cpu_percent(interval=1)
            cores = psutil.cpu_count(logical=False)
            threads = psutil.cpu_count(logical=True)
            stats = psutil.cpu_stats()
            return [
                [f"CPU Usage",f"{util}%\n"],
                [f"Cores", f"{cores}\n"],
                [f"Threads", f"{threads}\n"],
                [f"Context Switches", f"{stats.ctx_switches}\n"],
                [f"Interrupts", f"{stats.interrupts}"]
            ]
            

        def memory():
            mem = psutil.virtual_memory()
            return [
                [f"Total Memory", f"{mem.total /(1024**3):.2f} GB\n"],
                [f"Available Memory", f"{mem.available /(1024**3):.2f} GB\n"],
                [f"Used Memory", f"{mem.used /(1024**3):.2f} GB\n"],
                [f"Memory Usage", f"{mem.percent}%\n"]
            ]

        def sensor():
            try:
                temps = psutil.sensors_temperatures()
                fans = psutil.sensors_fans()
            except Exception:
                temps,fans = {},{}


            rows = []
            for chip_name, readings in temps.items():
                for reading in readings:
                    label = reading.label or chip_name
                    rows.append([f"{label} temp:",f"{reading.current}°C"])
            
            for chip_name, readings in fans.items():
                for reading in readings:
                    label = reading.label or chip_name
                    rows.append([f"{label} fan:", f"{reading.current} RPM"])

            battery = psutil.sensors_battery()
            if battery is None:
                rows.append([f"Battery", f"no battery detected (desktop?)"])
            else:
                plugged = "plugged in" if battery.power_plugged else "on battery"
                rows.append([f"Battery", f"{battery.percent:.0f}% ({plugged})"])

            return rows
        all_row = cpu() + memory() + sensor()
        table = tabulate(all_row, headers=["Heading", "Value"], tablefmt="grid")
        return f"\n{table}"
    except Exception as e:
        return f"Error retrieving system information: {str(e)}"
    
@skill("lock", "lockscreen")
def lock_screen(text):
    try:
        if current_platform == "Linux":
            subprocess.run(["loginctl", "lock-session"], check=True,
                           **_silent_process_options())
            return "Locking the screen..."
        elif current_platform == "Windows":
            subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"],
                           check=True, **_silent_process_options())
            return "Locking the screen..."
        else:
            return f"Locking the screen isn't supported on {current_platform} yet."
    except Exception as e:
        return f"Error locking the screen: {str(e)}"
    
sites = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "github": "https://www.github.com",
    "reddit": "https://www.reddit.com",
    "wikipedia": "https://www.wikipedia.org",
    "gmail": "https://mail.google.com",
    "amazon": "https://www.amazon.com",
    "netflix": "https://www.netflix.com",
    "chatgpt": "https://chat.openai.com",
    "twitter": "https://www.x.com",
    "instagram": "https://www.instagram.com",
    "whatsapp": "https://web.whatsapp.com",
    "spotify": "https://open.spotify.com",
    "discord": "https://discord.com/app",
}
@skill("open_website", "open_web","openbrowser", "open_url","visit")
def web_brower(url):
    try:
        for word in url.split():
            word = word.lower()
            if word in sites:
                webbrowser.open(sites[word])
                return f"Opening {word}..."
        return f"No website found for '{url.strip()}'."
    except Exception as e:
        return "Couldn't open the Website"
    
    
@skill("mute", "unmute", "increase_volume", "decrease_volume")
def volume_control(text):
    try:
        command = text.lower()
        if current_platform == "Linux":
            if "unmute" in command:
                subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "0"],
                               check=True, **_silent_process_options())
                return "Volume unmuted."
            elif "mute" in command:
                subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "1"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,)
                return "Volume muted."
            elif "increase" in command:
                subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "+10%"],
                               check=True, **_silent_process_options())
                return "Volume increased."
            elif "decrease" in command:
                subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "-10%"],
                               check=True, **_silent_process_options())
                return "Volume decreased."
            else:
                return "No volume control command found."
        elif current_platform == "Windows":
            import ctypes
            VK_VOLUME_MUTE = 0xAD
            VK_VOLUME_DOWN = 0xAE
            VK_VOLUME_UP = 0xAF

            key = None
            if "unmute" in command or "mute" in command:
                key = VK_VOLUME_MUTE
                result = "Volume toggled."
            elif "up" in command or "increase" in command:
                key = VK_VOLUME_UP
                result = "Volume increased."
            elif "down" in command or "decrease" in command:
                key = VK_VOLUME_DOWN
                result = "Volume decreased."
            else:
                return "No volume control command found."

            for _ in range(5 if key != VK_VOLUME_MUTE else 1):
                    ctypes.windll.user32.keybd_event(key, 0, 0, 0)
                    ctypes.windll.user32.keybd_event(key, 0, 2, 0)
            return result
    except Exception as e:
        return f"Error controlling volume: {str(e)}"
    
@skill("stealth", "stealthmode", "stealth_mode","Self_destruct","Destruct")
def stealth__mode(text):
    try:
        volume_control("mute")
        if current_platform == "Linux":
            subprocess.run(["wmctrl", "-k", "on"], **_silent_process_options())
            subprocess.Popen(["ptyxis", "--", "cmatrix"], **_silent_process_options())
        elif current_platform == "Windows":
            subprocess.run(["powershell.exe", "-NoProfile", "-Command",
                            "(New-Object -ComObject Shell.Application).MinimizeAll()"],
                           **_silent_process_options())
        else:
            return f"Stealth mode isn't supported on {current_platform} yet."
        return "Stealth mode activated."
    except Exception as e:
        return f"Error activating stealth mode: {str(e)}"
    
@skill("joke", "tell_joke", "funny", "humor", "cowsay")
def joke(text):
    try:
        raw_joke = pyjokes.get_joke()
        if "cowsay" in text.lower() or "cow" in text.lower():
            return cowsay.get_output_string('cow', raw_joke)
        
        return raw_joke

    except Exception as e:
        return f"Error retrieving joke: {str(e)}"
    
@skill("default_response", "unknown", "fallback")
def default_response(text):
    return "I'm sorry, I didn't understand that. Could you please rephrase?"

@skill("list_skills", "skills_list", "show_skills")
def skill_list(text):
    skills = [
        "open_app",
        "screenshot",
        "system_info",
        "lock_screen",
        "web_brower",
        "volume_control",
        "stealth__mode",
        "joke",
        "default_response",
        "coin-flip",
        "date",
        "time",
        "battery",
        "cowsay",
        "compliment",
    ]
    return ", ".join(skills)
    
# @skill("open_url", "browse", "website", "search","open_website")
# def open_url(*args):
#     try:
#         url = input("Enter the  search query: ")
#         if "youtube" in url.lower() or "Yt" in url.lower():
#             webbrowser.open(f"https://www.youtube.com/results?search_query={url}")
#             return "Opening YouTube..."
#         else:
#             webbrowser.open(url)
#             return "Opening URL..."
#     except Exception as e:
#         return f"Error opening URL: {str(e)}"

@skill("time", "current_time", "what_time")
def current_time(text):
    return f"It is {datetime.now().strftime('%I:%M %p')}"


@skill("date", "today", "current_date")
def current_date(text):
    return datetime.now().strftime("Today is %A, %B %d, %Y.")


@skill("disk", "disk_space", "storage")
def disk_space(text):
    try:
        usage = psutil.disk_usage(os.path.expanduser("~"))
        return (
            f"Storage: {usage.free / (1024 ** 3):.1f} GB free of "
            f"{usage.total / (1024 ** 3):.1f} GB ({usage.percent}% used)."
        )
    except Exception as e:
        return f"Error retrieving disk information: {str(e)}"


@skill("battery", "battery_status", "charge")
def battery_status(text):
    try:
        battery = psutil.sensors_battery()
        if battery is None:
            return "No battery detected. This machine may be a desktop."
        state = "charging" if battery.power_plugged else "on battery"
        return f"Battery is at {battery.percent:.0f}% and is {state}."
    except Exception as e:
        return f"Error retrieving battery information: {str(e)}"


@skill("network", "network_status", "connections")
def network_status(text):
    try:
        interfaces = []
        for name, status in psutil.net_if_stats().items():
            state = "up" if status.isup else "down"
            interfaces.append(f"{name}: {state}")
        if not interfaces:
            return "No network interfaces were found."
        return "Network interfaces: " + ", ".join(interfaces)
    except Exception as e:
        return f"Error retrieving network information: {str(e)}"


@skill("youtube", "youtube_search", "find_video")
def youtube_search(text):
    try:
        query = text.lower()
        for trigger in ("youtube_search", "find_video", "youtube"):
            query = query.replace(trigger, "")
        query = "+".join(query.split())
        if not query:
            return "Tell me what you want to search for on YouTube."
        webbrowser.open(f"https://www.youtube.com/results?search_query={query}")
        return f"Searching YouTube for {query.replace('+', ' ')}..."
    except Exception as e:
        return f"Error opening YouTube: {str(e)}"


@skill("coin", "coin_flip", "flip_coin")
def flip_coin(text):
    result = "Heads" if datetime.now().microsecond % 2 == 0 else "Tails"
    return f"{result}! The coin has spoken."


@skill("dice", "roll_dice", "roll")
def roll_dice(text):
    result = (datetime.now().microsecond % 6) + 1
    return f"You rolled a {result}. The dice approve."


@skill("moo", "cow_message", "udder", "random_cow")
def cow_message(text):
    try:
        messages = [
            "The cow says: keep being udderly productive!",
            "The cow says: you are doing a great job, mooo-ving forward!",
            "The cow says: take a break before your brain starts producing cheese.",
            "The cow says: today is looking udderly fantastic!",
            "The cow says: stay calm and pasture confidence in yourself.",
        ]
        return cowsay.get_output_string("cow", random.choice(messages))
    except Exception as e:
        return f"The cow wandered off: {str(e)}"


@skill("compliment", "encourage", "motivate")
def compliment(text):
    return "You are doing better than your error messages suggest. Keep going."

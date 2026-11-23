"""AutoClickTool 1.1.0 - ghi lai chuot + ban phim roi chay lai tu dong.

Chay tren Windows, giao dien CustomTkinter, dong goi 1 file exe bang PyInstaller.

Thay doi chinh so voi ban goc (1.0.x):
  * Ghi ca di chuyen chuot va cuon chuot (co bat/tat, move duoc nen lai).
  * Dừng chạy (F11) ngat duoc ngay, ke ca khi dang nghi giua cac su kien.
  * Sua loi ket app: delay am / loops khong hop le / file kich ban loi
    khong con lam cua so bien mat vinh vien nua.
  * Config luu canh file exe (khong theo thu muc hien tai nua), luu ca
    loops / delay / toc do / tuy chon ghi / tu cap nhat.
  * Them mo ta huong dan trong app, hien tray icon trong luc ghi/chay
    de luon co cho bam Dung.
  * Tu cap nhat qua GitHub Releases (giong ScreenShotTool/TaskbarWidget):
    kiem tra sau 10 giay roi moi ngay, co nut "Kiem tra cap nhat".
  * So vong 0 = lap vo han. Toc do phat 0.5x / 1x / 2x.

1.1.1: sua loi ve net cong thanh net thang khi ve trong Paint.
  Nguyen nhan: on_move/on_scroll goi BooleanVar.get() cua Tkinter
  ngay trong thread cua pynput - Tkinter chi cho phep doc bien tu
  luong UI chinh, nen goi nay co the loi va pynput ngung goi on_move.
  Ket qua: chi ghi duoc mouse_down/mouse_up (2 dau mut), khong co
  diem di chuyen o giua, Paint noi 2 dau mut bang 1 duong thang.
  Sua: doc tuy chon ghi o luong UI truoc khi bat dau ghi, luu vao
  bien bool thuong, listener chi doc bien thuong do.

1.1.2: sua that su loi net cong thanh net thang (file test.json cua
  Bach chung minh ghi da dung: 1 lan keo dai 2.02 giay, 112 diem di
  chuyen, duong di 1340px nhung diem dau-cuoi chi cach nhau 30px).
  Nguyen nhan nam o luc CHAY: _play_one dung mouse_ctrl.position
  de di chuyen chuot - tren Windows pynput cai nay bang SetCursorPos,
  chi doi vi tri con tro hien thi chu khong dua su kien keo (pointer/
  drag input) vao hang doi cua ung dung, nen Paint moi chi thay
  nhan xuong o diem dau va nha ra o diem cuoi roi noi thang 2 diem.
  Sua (SAI - xem 1.1.4): luc chay ghi nho vi tri cuoi, di chuyen
  bang mouse_ctrl.move (dx, dy) tuong doi, tuong la SendInput.
  Thuc ra khong doi gi tren Windows, vi pynput cai move() bang
  self.position = vi tri hien tai + (dx, dy), tuc la SetCursorPos.

1.1.3: them thoi gian cho truoc khi chay (mac dinh 3 giay).
  Nguyen nhan: bam Chay thi app an di ngay va chay luon, nhung luc
  do chua co cua so nao duoc chon (Paint chua phai cua so truoc) nen
  thao tac roi vao hu khong - chuot thi van di theo duong cong nhung
  khong ve duoc gi. Nay sau khi an app se cho 3 giay (ngat duoc bang
  F11) de bam vao cua so can thao tac (vd Paint) roi macro moi chay.
"""
import ctypes
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import zipfile
import urllib.error
import urllib.request
import webbrowser

import customtkinter as ctk
from pynput import mouse, keyboard
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import pystray

# Khai DPI-aware truoc khi tao cua so: toa do chuot ghi duoc moi khop
# voi toa do phat lai khi Windows scale 125%/150%.
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

VERSION = "1.2.0"
REPO = "btanh258/AutoClickTool"
RELEASES_API = f"https://api.github.com/repos/{REPO}/releases/latest"
RELEASES_PAGE = f"https://github.com/{REPO}/releases"
REPO_URL = f"https://github.com/{REPO}"
UPDATE_ASSET_NAME = "AutoClickTool.exe"
USER_AGENT = "AutoClickTool-update-check"

# --- DUONG DAN: config luon nam canh file exe / file .pyw ---
def get_app_dir():
    """Thu muc chua file exe (khi dong goi) hoac file .pyw (khi chay source)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))

APP_DIR = get_app_dir()
CONFIG_FILE = os.path.join(APP_DIR, "AutoClickTool_config.json")


def _cleanup_old_app_dir():
    """Xoa thu muc app cu (.old) sau khi cap nhat doi thu muc: app moi
    da mo len duoc thi thu muc cu khong con ai dung nua."""
    if not getattr(sys, "frozen", False):
        return
    old_dir = APP_DIR + ".old"
    if os.path.isdir(old_dir):
        shutil.rmtree(old_dir, ignore_errors=True)


_cleanup_old_app_dir()
# Ban cu luu config theo thu muc hien tai: doc thu de chuyen sang cho moi.
LEGACY_CONFIG_FILE = os.path.join(os.getcwd(), "AutoClickTool_config.json")

def get_resource_path(relative_path):
    """Lay duong dan chuan du chay file .pyw hay file .exe da build."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


# --- TU CAP NHAT (theo mau ui_updates.py cua ScreenShotTool) ---
def parse_version(text):
    """'v1.2.3' / '1.2.3' -> (1, 2, 3); khong doc duoc thi None."""
    if not isinstance(text, str):
        return None
    cleaned = text.strip().lstrip("vV")
    if not cleaned:
        return None
    parts = []
    for chunk in cleaned.split("."):
        digits = ""
        for char in chunk:
            if char.isdigit():
                digits += char
            else:
                break
        if not digits:
            return None
        parts.append(int(digits))
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])

def is_newer(latest, current):
    a, b = parse_version(latest), parse_version(current)
    return a is not None and b is not None and a > b

class _MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", ctypes.c_void_p)]


class _INPUT(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("mi", _MOUSEINPUT)]


def _send_input(dx, dy, dw_flags):
    """Gui 1 su kien chuot qua SendInput that cua Windows, qua ctypes.
    Tra ve True neu gui duoc, False neu khong phai Windows / loi."""
    try:
        import ctypes
        user32 = ctypes.windll.user32
        inp = _INPUT(type=0, mi=_MOUSEINPUT(dx=int(dx), dy=int(dy),
                     mouseData=0, dwFlags=dw_flags,
                     time=0, dwExtraInfo=None))
        return user32.SendInput(1, ctypes.byref(inp),
                                ctypes.sizeof(inp)) == 1
    except Exception:
        return False


def _send_input_move(dx, dy):
    """Gui 1 su kien di chuyen chuot TUONG DOI bang SendInput that.
    Chi dung lam du phong khi SendInput tuyet doi loi, vi di chuyen
    tuong doi bi Windows co gian theo toc do con tro / tang toc."""
    if not dx and not dy:
        return True
    return _send_input(dx, dy, 0x0001)  # MOUSEEVENTF_MOVE


_VIRTUAL_SCREEN = None


def _send_input_move_to(x, y):
    """Gui 1 su kien di chuyen chuot TUYET DOI bang SendInput that
    (MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE), toa do chuan hoa
    0-65535 theo man hinh ao. Khac voi SetCursorPos (chi doi vi tri
    con tro hien thi) va khac voi mouse_ctrl.move() cua pynput (tren
    Windows no cung chi la SetCursorPos - xem ghi chu 1.1.4), SendInput
    dua su kien vao hang doi nhap nhu chuot that, nen Paint nhan duoc
    tung diem cua net keo; va vi la tuyet doi nen khong bi toc do con
    tro / tang toc cua Windows co gian, diem click chinh xac. Tra ve
    True neu gui duoc, False neu khong phai Windows hoac goi loi."""
    global _VIRTUAL_SCREEN
    try:
        import ctypes
        user32 = ctypes.windll.user32
        if _VIRTUAL_SCREEN is None:
            vx = user32.GetSystemMetrics(76)  # SM_XVIRTUALSCREEN
            vy = user32.GetSystemMetrics(77)  # SM_YVIRTUALSCREEN
            vw = user32.GetSystemMetrics(78)  # SM_CXVIRTUALSCREEN
            vh = user32.GetSystemMetrics(79)  # SM_CYVIRTUALSCREEN
            _VIRTUAL_SCREEN = (vx, vy, vw, vh)
        vx, vy, vw, vh = _VIRTUAL_SCREEN
        if vw <= 1 or vh <= 1:
            return False
        nx = int(round((x - vx) * 65535 / (vw - 1)))
        ny = int(round((y - vy) * 65535 / (vh - 1)))
        nx = max(0, min(65535, nx))
        ny = max(0, min(65535, ny))
        return _send_input(nx, ny, 0x0001 | 0x8000)  # MOVE | ABSOLUTE
    except Exception:
        return False


def fetch_latest_release_detailed(timeout=8):
    """Tra ve (release_dict|None, ly_do): ok / not-found / rate-limited /
    offline / error. Loi mang khong bao gio duoc lam app crash."""
    request = urllib.request.Request(
        RELEASES_API,
        headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None, "not-found"
        if exc.code in (403, 429):
            return None, "rate-limited"
        return None, "error"
    except (urllib.error.URLError, OSError):
        return None, "offline"
    except (ValueError, json.JSONDecodeError):
        return None, "error"
    if not isinstance(payload, dict):
        return None, "error"
    return {
        "tag": payload.get("tag_name") or "",
        "url": payload.get("html_url") or "",
        "notes": payload.get("body") or "",
        "name": payload.get("name") or "",
        "assets": [
            {"name": a.get("name") or "", "url": a.get("browser_download_url") or "",
             "size": a.get("size") or 0, "digest": a.get("digest") or ""}
            for a in (payload.get("assets") or []) if isinstance(a, dict)
        ],
    }, "ok"

def _asset_info(asset):
    return {"url": asset.get("url") or "",
            "size": asset.get("size") or 0,
            "digest": asset.get("digest") or ""}


def pick_update_asset(release):
    """Chon file cap nhat, tra ve dict {url, kind, size, digest} hoac None.

    Uu tien file zip onedir (AutoClickTool-v<tag>.zip): DLL nam canh exe
    trong thu muc app nen khong con loi DLL sau cap nhat. Chi khi
    release khong co zip moi roi ve file exe onefile (cau noi cho cac
    ban cu chi biet tai exe)."""
    if not isinstance(release, dict):
        return None
    tag = (release.get("tag") or "").strip()
    zip_name = ("AutoClickTool-%s.zip" % tag).lower() if tag else ""
    exe_fallback = None
    for asset in release.get("assets") or []:
        if not isinstance(asset, dict):
            continue
        url = asset.get("url") or ""
        if not url:
            continue
        name = (asset.get("name") or "").lower()
        if zip_name and name == zip_name:
            info = _asset_info(asset)
            info["kind"] = "zip"
            return info
        if name == UPDATE_ASSET_NAME.lower():
            exe_fallback = _asset_info(asset)
            exe_fallback["kind"] = "exe"
        elif exe_fallback is None and name.endswith(".exe"):
            exe_fallback = _asset_info(asset)
            exe_fallback["kind"] = "exe"
    return exe_fallback

def _sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_asset(url, destination, timeout=60, progress=None,
                   expected_size=0, expected_digest=""):
    """Tai ve file tam *.part roi doi ten: tai do khong bao gio de lai
    file exe dut doan. Kiem tra kich thuoc + SHA-256 voi thong tin asset
    tren GitHub (neu co): file sai thi xoa, tra ve None. Tra ve duong
    dan khi tai dung, hoac None khi loi."""
    if not url:
        return None
    destination = os.fspath(destination)
    partial = destination + ".part"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            total = int(response.headers.get("Content-Length") or 0)
            written = 0
            with open(partial, "wb") as handle:
                while True:
                    chunk = response.read(256 * 1024)
                    if not chunk:
                        break
                    handle.write(chunk)
                    written += len(chunk)
                    if progress is not None:
                        try:
                            progress(written, total)
                        except Exception:
                            pass
    except (urllib.error.URLError, OSError, ValueError):
        try:
            os.remove(partial)
        except OSError:
            pass
        return None
    try:
        size = os.path.getsize(partial)
        if size <= 0:
            os.remove(partial)
            return None
        if expected_size and size != expected_size:
            os.remove(partial)
            return None
        if expected_digest:
            want = expected_digest.split(":", 1)[-1].strip().lower()
            if want and _sha256_file(partial) != want:
                os.remove(partial)
                return None
        os.replace(partial, destination)
    except OSError:
        try:
            os.remove(partial)
        except OSError:
            pass
        return None
    return destination

_UPDATE_SCRIPT = r"""@echo off
setlocal
set "OLD={old}"
set "NEW={new}"
set /a tries=0
:retry
set /a tries+=1
move /y "%NEW%" "%OLD%" >nul 2>&1
if not errorlevel 1 goto swapped
if %tries% GEQ 60 goto failed
ping -n 2 127.0.0.1 >nul
goto retry
:failed
start "" "%OLD%"
del "%~f0" >nul 2>&1
exit /b 1
:swapped
del "%NEW%" >nul 2>&1
start "" "%OLD%"
del "%~f0" >nul 2>&1
exit /b 0
"""

_UPDATE_ZIP_SCRIPT = r"""@echo off
setlocal
set "OLD_DIR={old_dir}"
set "NEW_DIR={new_dir}"
set "EXE_NAME=AutoClickTool.exe"
rmdir /s /q "%OLD_DIR%.old" >nul 2>&1
set /a tries=0
:retry
set /a tries+=1
move /y "%OLD_DIR%" "%OLD_DIR%.old" >nul 2>&1
if not errorlevel 1 goto swapped
if %tries% GEQ 120 goto failed
ping -n 2 127.0.0.1 >nul
goto retry
:failed
start "" "%OLD_DIR%\%EXE_NAME%"
del "%~f0" >nul 2>&1
exit /b 1
:swapped
robocopy "%NEW_DIR%" "%OLD_DIR%" /E /MOVE >nul 2>&1
rmdir "%NEW_DIR%" >nul 2>&1
start "" "%OLD_DIR%\%EXE_NAME%"
del "%~f0" >nul 2>&1
exit /b 0
"""


def _find_new_exe(extract_dir):
    """Tim AutoClickTool.exe trong thu muc vua giai nen zip onedir."""
    for root, _dirs, files in os.walk(extract_dir):
        if "AutoClickTool.exe" in files:
            return os.path.join(root, "AutoClickTool.exe")
    return None


def apply_update_zip(zip_path, current_exe):
    """Cap nhat bang zip onedir: giai nen, mang config sang thu muc moi,
    doi ca thu muc app qua script phu (Windows khong cho doi ten thu muc
    dang co exe chay). KHONG chay thu exe moi: chay file vua tai ve
    ngay luc Defender dang quet no cung gay loi DLL. Tra ve duong dan
    script, hoac None."""
    current_exe = os.path.abspath(current_exe)
    app_dir = os.path.dirname(current_exe)
    if not os.path.isfile(zip_path) or not os.path.isfile(current_exe):
        return None
    extract_dir = tempfile.mkdtemp(prefix="autoclicktool_new_")
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)
    except (zipfile.BadZipFile, OSError):
        shutil.rmtree(extract_dir, ignore_errors=True)
        return None
    new_exe = _find_new_exe(extract_dir)
    if not new_exe:
        shutil.rmtree(extract_dir, ignore_errors=True)
        return None
    new_dir = os.path.dirname(new_exe)
    # Mang config sang thu muc moi truoc khi doi (app dang chay van ghi duoc).
    try:
        if os.path.isfile(CONFIG_FILE):
            shutil.copy2(CONFIG_FILE, os.path.join(new_dir, "AutoClickTool_config.json"))
    except OSError:
        pass
    helper = os.path.join(tempfile.gettempdir(), "autoclicktool_update.bat")
    try:
        with open(helper, "w", encoding="utf-8", newline="\r\n") as handle:
            handle.write(_UPDATE_ZIP_SCRIPT.format(old_dir=app_dir, new_dir=new_dir))
    except OSError:
        shutil.rmtree(extract_dir, ignore_errors=True)
        return None
    flags = 0
    for name in ("CREATE_NO_WINDOW", "CREATE_NEW_PROCESS_GROUP"):
        flags |= getattr(subprocess, name, 0)
    try:
        subprocess.Popen(
            ["cmd", "/c", helper], creationflags=flags,
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, close_fds=True,
        )
    except OSError:
        shutil.rmtree(extract_dir, ignore_errors=True)
        return None
    return helper


def _is_onedir_install():
    """True neu app dang chay la ban onedir: co thu muc _internal canh
    file exe, tuc thu muc app la cua rieng app, doi ten duoc."""
    if not getattr(sys, "frozen", False):
        return False
    return os.path.isdir(os.path.join(APP_DIR, "_internal"))


def _get_install_dir():
    """Thu muc cai dat chuan cho ban onedir."""
    local_app = os.environ.get("LOCALAPPDATA") or os.path.join(
        os.path.expanduser("~"), "AppData", "Local")
    return os.path.join(local_app, "AutoClickTool")


def apply_update_install(zip_path, current_exe):
    """Cai ban onedir moi vao %LOCALAPPDATA%\\AutoClickTool, dung khi app
    dang chay la ban 1 file nam le trong thu muc chung (Downloads,
    Desktop...): khong the doi ten ca thu muc do de doi thu muc app,
    nen cai moi vao thu muc rieng thay vi doi. Mang config theo, mo
    exe moi len. File exe cu nam yen cho cu (xoa tay neu muon). Tra ve
    duong dan exe moi, hoac None khi loi (ban cu van chay binh thuong)."""
    if not os.path.isfile(zip_path) or not os.path.isfile(current_exe):
        return None
    extract_dir = tempfile.mkdtemp(prefix="autoclicktool_new_")
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)
    except (zipfile.BadZipFile, OSError):
        shutil.rmtree(extract_dir, ignore_errors=True)
        return None
    new_exe = _find_new_exe(extract_dir)
    if not new_exe:
        shutil.rmtree(extract_dir, ignore_errors=True)
        return None
    new_dir = os.path.dirname(new_exe)
    target = _get_install_dir()
    try:
        if os.path.isdir(target):
            # Da co ban cai o day: doi ten truoc (exe dang chay khong
            # nam trong thu muc nay vi no la ban 1 file o cho khac).
            if os.path.isdir(target + ".old"):
                shutil.rmtree(target + ".old", ignore_errors=True)
            os.rename(target, target + ".old")
        shutil.move(new_dir, target)
        if os.path.isfile(CONFIG_FILE):
            shutil.copy2(CONFIG_FILE,
                         os.path.join(target, "AutoClickTool_config.json"))
    except OSError:
        shutil.rmtree(extract_dir, ignore_errors=True)
        return None
    shutil.rmtree(extract_dir, ignore_errors=True)
    new_exe_path = os.path.join(target, "AutoClickTool.exe")
    if not os.path.isfile(new_exe_path):
        return None
    flags = 0
    for name in ("CREATE_NO_WINDOW", "CREATE_NEW_PROCESS_GROUP"):
        flags |= getattr(subprocess, name, 0)
    try:
        subprocess.Popen(
            [new_exe_path], creationflags=flags,
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, close_fds=True,
        )
    except OSError:
        return None
    return new_exe_path


def apply_update(new_exe, current_exe):
    """Doi file exe dang chay bang file moi qua script phu (Windows khong
    cho ghi de file exe dang chay). Tra ve duong dan script, hoac None."""
    new_exe = os.path.abspath(new_exe)
    current_exe = os.path.abspath(current_exe)
    if not os.path.isfile(new_exe):
        return None
    helper = os.path.join(tempfile.gettempdir(), "autoclicktool_update.bat")
    try:
        with open(helper, "w", encoding="utf-8", newline="\r\n") as handle:
            handle.write(_UPDATE_SCRIPT.format(old=current_exe, new=new_exe))
    except OSError:
        return None
    flags = 0
    for name in ("CREATE_NO_WINDOW", "CREATE_NEW_PROCESS_GROUP"):
        flags |= getattr(subprocess, name, 0)
    try:
        subprocess.Popen(
            ["cmd", "/c", helper], creationflags=flags,
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, close_fds=True,
        )
    except OSError:
        return None
    return helper


# --- KIEM TRA KICH BAN TRUOC KHI CHAY ---
KNOWN_ACTIONS = {"key_press", "key_release", "mouse_down", "mouse_up",
                 "mouse_move", "mouse_scroll"}

def validate_macro(events):
    """Kiem tra file kich ban vua tai. Tra ve (True, '') neu ok,
    nguoc lai (False, ly_do) - de bao loi chu khong de thread chay chet."""
    if not isinstance(events, list):
        return False, "file kịch bản phải là danh sách các hành động"
    if not events:
        return False, "kịch bản rỗng, chưa có hành động nào"
    for i, event in enumerate(events):
        if not isinstance(event, (list, tuple)) or len(event) != 3:
            return False, f"hành động thứ {i + 1} không đúng định dạng"
        action, data, timestamp = event
        if action not in KNOWN_ACTIONS:
            return False, f"hành động thứ {i + 1} là '{action}' không biết"
        if not isinstance(timestamp, (int, float)) or timestamp < 0:
            return False, f"hành động thứ {i + 1} có thời gian không hợp lệ"
        if action in ("key_press", "key_release"):
            if not isinstance(data, str) or not data:
                return False, f"hành động thứ {i + 1} thiếu tên phím"
        elif action in ("mouse_down", "mouse_up"):
            if (not isinstance(data, (list, tuple)) or len(data) != 3
                    or not isinstance(data[2], str)):
                return False, f"hành động thứ {i + 1} thiếu nút chuột"
        elif action == "mouse_move":
            if not isinstance(data, (list, tuple)) or len(data) != 2:
                return False, f"hành động thứ {i + 1} thiếu tọa độ chuột"
        elif action == "mouse_scroll":
            if not isinstance(data, (list, tuple)) or len(data) != 4:
                return False, f"hành động thứ {i + 1} thiếu thông số cuộn"
    return True, ""


class MacroTool(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"AutoClickTool {VERSION}")
        self.geometry("560x875")
        self.resizable(False, False)

        # Giu tham chieu anh icon: bien cuc bo se bi GC thu hoi lam mat icon.
        self._icon_img = None
        try:
            icon_path = get_resource_path("icon_AutoClickTool.ico")
            self.iconbitmap(icon_path)
            self._icon_img = ImageTk.PhotoImage(Image.open(icon_path))
            self.iconphoto(True, self._icon_img)
        except Exception as e:
            print(f"Loi load icon: {e}")

        self.events = []
        self.is_recording = False
        self.is_playing = False
        # Event dung de ngat giac ngu: F11 / nut Dung chi can set() la
        # vong lap chay dung ngay, khong phai doi het time.sleep().
        self._stop_event = threading.Event()
        # Vi tri chuot cuoi cung luc CHAY (de di chuyen tuong doi bang
        # SendInput, xem _move_mouse_to). Reset moi vong chay.
        self._play_last_pos = None

        self.mouse_listener = None
        self.keyboard_listener = None
        self.tray_icon = None
        self._last_move = (0, 0, 0.0)  # x, y, thoi gian ghi move gan nhat

        # Bien cau hinh (tao truoc load_config)
        self.name_slot_1 = ctk.StringVar(value="Slot 1")
        self.path_slot_1 = ctk.StringVar()
        self.name_slot_2 = ctk.StringVar(value="Slot 2")
        self.path_slot_2 = ctk.StringVar()
        self.name_slot_3 = ctk.StringVar(value="Slot 3")
        self.path_slot_3 = ctk.StringVar()
        self.record_move_var = ctk.BooleanVar(value=True)
        self.record_scroll_var = ctk.BooleanVar(value=True)
        # Ban sao bool thuong cua 2 tuy chon tren: listener cua pynput
        # chay o thread rieng, KHONG duoc goi .get() cua Tkinter tu do.
        # Chi doc o luong UI (luc bat dau ghi / luc doi checkbox) roi
        # luu vao day, listener chi doc 2 bien nay.
        self._record_move = True
        self._record_scroll = True
        self.auto_update_var = ctk.BooleanVar(value=True)
        self.speed_var = ctk.StringVar(value="1x")
        self._cfg_loops = "1"
        self._cfg_delay = "0"
        self._cfg_pre_delay = "3"

        self.load_config()
        self._sync_record_flags()
        self.setup_ui()

        self.bind("<Unmap>", self.on_minimize)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Tu kiem tra cap nhat sau 10 giay neu bat, roi lap lai moi ngay.
        if self.auto_update_var.get():
            self.after(10000, lambda: self.check_for_updates(manual=False))

    def update_status(self, text, color="gray"):
        self.after(0, lambda: self.lbl_status.configure(text=text, text_color=color))

    # ---------------- GIAO DIEN ----------------
    def setup_ui(self):
        self.lbl_title = ctk.CTkLabel(
            self, text="Auto Clicker & Keyboard Macro",
            font=("Segoe UI Variable Display", 20, "bold"))
        self.lbl_title.pack(pady=(12, 2))
        ctk.CTkLabel(self, text=f"AutoClickTool {VERSION}  -  ghi lai thao tac roi chay lai tu dong",
                     font=("Segoe UI", 12), text_color="gray").pack(pady=(0, 5))

        self.lbl_status = ctk.CTkLabel(self, text="Trạng thái: Sẵn sàng",
                                       text_color="gray", font=("Segoe UI", 14))
        self.lbl_status.pack(pady=(0, 8))

        # --- MO TA / HUONG DAN ---
        frame_help = ctk.CTkFrame(self)
        frame_help.pack(pady=5, padx=20, fill="x")
        ctk.CTkLabel(frame_help, text="Tool này làm được gì?  (hướng dẫn nhanh)",
                     font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=12, pady=(8, 2))
        help_text = (
            "1. Bấm Ghi, thao tác chuột + bàn phím như bình thường, bấm F12 để dừng ghi.\n"
            "2. Bấm \"Lưu kịch bản mới\" để lưu file .json, hoặc bấm \"Chạy kịch bản\" để chạy ngay.\n"
            "3. Bấm \"Chạy\": app ẩn đi, trong thời gian chờ bạn bấm vào cửa sổ cần thao tác (vd Paint) để chọn nó, hết thời gian chờ macro tự chạy. Đang chạy bấm F11 (hoặc menu khay -> Dừng chạy) để dừng lại bất cứ lúc nào.\n"
            "Ghi được: click chuột, kéo-thả, cuộn chuột, gõ phím, phím tắt (Ctrl+C...).\n"
            "Số vòng 0 = lặp vô hạn. Tắt \"Ghi di chuyển chuột\" nếu chỉ cần click, file sẽ gọn hơn."
        )
        ctk.CTkLabel(frame_help, text=help_text, font=("Segoe UI", 12),
                     justify="left", wraplength=500).pack(anchor="w", padx=12, pady=(0, 2))
        github_label = ctk.CTkLabel(
            frame_help, text="GitHub: github.com/btanh258/AutoClickTool",
            font=("Segoe UI", 12, "underline"), text_color="#3B82F6",
            cursor="hand2")
        github_label.pack(anchor="w", padx=12, pady=(0, 8))
        github_label.bind("<Button-1>",
                          lambda e: webbrowser.open(REPO_URL))

        # --- KHU VUC KICH BAN ---
        frame_quick = ctk.CTkFrame(self)
        frame_quick.pack(pady=5, padx=20, fill="x")
        ctk.CTkLabel(frame_quick, text="Cấu hình kịch bản có sẵn",
                     font=("Segoe UI", 13, "bold")).grid(row=0, column=0, columnspan=4, pady=(10, 5))

        for row, (name_var, path_var) in enumerate((
                (self.name_slot_1, self.path_slot_1),
                (self.name_slot_2, self.path_slot_2),
                (self.name_slot_3, self.path_slot_3)), start=1):
            entry_name = ctk.CTkEntry(frame_quick, textvariable=name_var, width=80,
                                      font=("Segoe UI", 12, "bold"))
            entry_name.grid(row=row, column=0, padx=10, pady=5 if row < 3 else (5, 10), sticky="w")
            entry_name.bind("<FocusOut>", lambda e: self.save_config())
            ctk.CTkEntry(frame_quick, textvariable=path_var, width=270,
                         state="disabled").grid(row=row, column=1, padx=5,
                                                pady=5 if row < 3 else (5, 10))
            ctk.CTkButton(frame_quick, text="Chọn", width=50, fg_color="#2b2b2b",
                          command=lambda v=path_var: self.browse_quick(v)).grid(
                              row=row, column=2, padx=5, pady=5 if row < 3 else (5, 10))
            ctk.CTkButton(frame_quick, text="Tải", width=50,
                          command=lambda v=path_var: self.load_quick(v)).grid(
                              row=row, column=3, padx=5, pady=5 if row < 3 else (5, 10))

        # --- DIEU KHIEN GHI ---
        frame_controls = ctk.CTkFrame(self, fg_color="transparent")
        frame_controls.pack(pady=10)

        self.btn_record = ctk.CTkButton(frame_controls, text="Ghi (Record)",
                                        fg_color="#C42B1C", hover_color="#A42417",
                                        command=self.start_recording)
        self.btn_record.grid(row=0, column=0, padx=10)

        self.btn_stop = ctk.CTkButton(frame_controls, text="Dừng Ghi (F12)",
                                      state="disabled", command=self.stop_recording)
        self.btn_stop.grid(row=0, column=1, padx=10)

        frame_rec_opts = ctk.CTkFrame(self, fg_color="transparent")
        frame_rec_opts.pack(pady=(0, 5))
        ctk.CTkCheckBox(frame_rec_opts, text="Ghi di chuyển chuột",
                        variable=self.record_move_var,
                        command=self._on_record_opt_changed).grid(row=0, column=0, padx=15)
        ctk.CTkCheckBox(frame_rec_opts, text="Ghi cuộn chuột",
                        variable=self.record_scroll_var,
                        command=self._on_record_opt_changed).grid(row=0, column=1, padx=15)

        # --- CAI DAT ---
        frame_settings = ctk.CTkFrame(self)
        frame_settings.pack(pady=5, padx=40, fill="x")

        ctk.CTkLabel(frame_settings, text="Số vòng lặp (0 = vô hạn):").grid(
            row=0, column=0, padx=20, pady=8, sticky="w")
        self.entry_loops = ctk.CTkEntry(frame_settings, width=80)
        self.entry_loops.insert(0, self._cfg_loops)
        self.entry_loops.grid(row=0, column=1, padx=20, pady=8, sticky="e")

        ctk.CTkLabel(frame_settings, text="Nghỉ giữa các vòng (giây):").grid(
            row=1, column=0, padx=20, pady=8, sticky="w")
        self.entry_delay = ctk.CTkEntry(frame_settings, width=80)
        self.entry_delay.insert(0, self._cfg_delay)
        self.entry_delay.grid(row=1, column=1, padx=20, pady=8, sticky="e")

        ctk.CTkLabel(frame_settings, text="Tốc độ chạy:").grid(
            row=2, column=0, padx=20, pady=8, sticky="w")
        self.speed_menu = ctk.CTkOptionMenu(frame_settings, variable=self.speed_var,
                                            values=["0.5x", "1x", "2x"], width=80,
                                            command=lambda v: self.save_config())
        self.speed_menu.grid(row=2, column=1, padx=20, pady=8, sticky="e")

        ctk.CTkLabel(frame_settings, text="Chờ trước khi chạy (giây):").grid(
            row=3, column=0, padx=20, pady=8, sticky="w")
        self.entry_pre_delay = ctk.CTkEntry(frame_settings, width=80)
        self.entry_pre_delay.insert(0, self._cfg_pre_delay)
        self.entry_pre_delay.grid(row=3, column=1, padx=20, pady=8, sticky="e")

        # --- CHAY VA LUU ---
        frame_actions = ctk.CTkFrame(self, fg_color="transparent")
        frame_actions.pack(pady=10)

        self.btn_play = ctk.CTkButton(frame_actions, text="▶ Chạy kịch bản (F11 để ngưng)",
                                      width=240, command=self.start_playing)
        self.btn_play.grid(row=0, column=0, padx=5, pady=5)

        self.btn_save = ctk.CTkButton(frame_actions, text="Lưu kịch bản mới",
                                      command=self.save_macro, fg_color="#2b2b2b", width=240)
        self.btn_save.grid(row=1, column=0, padx=5, pady=5)

        # --- CAP NHAT ---
        frame_update = ctk.CTkFrame(self, fg_color="transparent")
        frame_update.pack(pady=(5, 10))
        ctk.CTkCheckBox(frame_update, text="Tự động kiểm tra cập nhật",
                        variable=self.auto_update_var,
                        command=self.save_config).grid(row=0, column=0, padx=10)
        ctk.CTkButton(frame_update, text="Kiểm tra cập nhật", width=130,
                      fg_color="#2b2b2b",
                      command=lambda: self.check_for_updates(manual=True)).grid(
                          row=0, column=1, padx=10)

    # ---------------- TRAY ICON ----------------
    def create_tray_image(self):
        try:
            icon_path = get_resource_path("icon_AutoClickTool.ico")
            return Image.open(icon_path)
        except Exception as e:
            print(f"Loi load tray icon: {e}")
            return Image.new('RGB', (64, 64), color="#0078D4")

    def on_minimize(self, event):
        if event.widget == self and self.state() == 'iconic':
            self.withdraw()
            self.show_tray()

    def show_tray(self):
        if self.tray_icon:
            return
        menu = pystray.Menu(
            pystray.MenuItem("Hiển thị", self.restore_from_tray, default=True),
            pystray.MenuItem("Dừng ghi (F12)", self.stop_recording_from_tray),
            pystray.MenuItem("Dừng chạy (F11)", self.stop_playing_from_tray),
            pystray.MenuItem("Thoát", self.quit_from_tray)
        )
        self.tray_icon = pystray.Icon("MacroTool", self.create_tray_image(),
                                      "Auto Clicker", menu=menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def _stop_tray(self):
        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
            self.tray_icon = None

    def restore_from_tray(self, icon=None, item=None):
        self._stop_tray()
        self.after(0, self.show_window_normal)

    def stop_recording_from_tray(self, icon=None, item=None):
        self.after(0, self.stop_recording)

    def stop_playing_from_tray(self, icon=None, item=None):
        self._stop_event.set()
        self.is_playing = False

    def show_window_normal(self):
        try:
            self.deiconify()
        except Exception:
            pass
        self.state('normal')
        self.focus_force()

    def quit_from_tray(self, icon=None, item=None):
        self._stop_event.set()
        self.is_playing = False
        self.is_recording = False
        self._stop_listeners()
        self._stop_tray()
        self.save_config()
        self.after(0, self.destroy)

    def on_closing(self):
        self.withdraw()
        self.show_tray()

    # ---------------- CONFIG ----------------
    def _config_path_to_load(self):
        if os.path.exists(CONFIG_FILE):
            return CONFIG_FILE
        if os.path.exists(LEGACY_CONFIG_FILE):
            return LEGACY_CONFIG_FILE
        return CONFIG_FILE

    def load_config(self):
        path = self._config_path_to_load()
        if not os.path.exists(path):
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.name_slot_1.set(data.get("name_1", "Slot 1"))
            self.path_slot_1.set(data.get("path_1", ""))
            self.name_slot_2.set(data.get("name_2", "Slot 2"))
            self.path_slot_2.set(data.get("path_2", ""))
            self.name_slot_3.set(data.get("name_3", "Slot 3"))
            self.path_slot_3.set(data.get("path_3", ""))
            self._cfg_loops = str(data.get("loops", "1"))
            self._cfg_delay = str(data.get("delay", "0"))
            self._cfg_pre_delay = str(data.get("pre_delay", "3"))
            self.speed_var.set(data.get("speed", "1x"))
            self.record_move_var.set(bool(data.get("record_move", True)))
            self.record_scroll_var.set(bool(data.get("record_scroll", True)))
            self.auto_update_var.set(bool(data.get("auto_update", True)))
        except Exception:
            pass

    def save_config(self):
        try:
            loops = self.entry_loops.get() if hasattr(self, "entry_loops") else self._cfg_loops
            delay = self.entry_delay.get() if hasattr(self, "entry_delay") else self._cfg_delay
            pre_delay = self.entry_pre_delay.get() if hasattr(self, "entry_pre_delay") else self._cfg_pre_delay
        except Exception:
            loops, delay, pre_delay = self._cfg_loops, self._cfg_delay, self._cfg_pre_delay
        try:
            data = {
                "name_1": self.name_slot_1.get(), "path_1": self.path_slot_1.get(),
                "name_2": self.name_slot_2.get(), "path_2": self.path_slot_2.get(),
                "name_3": self.name_slot_3.get(), "path_3": self.path_slot_3.get(),
                "loops": loops, "delay": delay, "pre_delay": pre_delay, "speed": self.speed_var.get(),
                "record_move": self.record_move_var.get(),
                "record_scroll": self.record_scroll_var.get(),
                "auto_update": self.auto_update_var.get(),
            }
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception:
            pass

    def browse_quick(self, string_var):
        filepath = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if filepath:
            string_var.set(filepath)
            self.save_config()

    def load_quick(self, string_var):
        filepath = string_var.get()
        if not filepath:
            self.update_status("Chưa có đường dẫn kịch bản!", "red")
            return
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                events = json.load(f)
        except Exception:
            self.update_status("Lỗi khi đọc file kịch bản!", "red")
            return
        ok, reason = validate_macro(events)
        if not ok:
            self.update_status(f"Kịch bản lỗi: {reason}", "red")
            return
        self.events = events
        self.update_status(f"Đã tải kịch bản: {len(self.events)} hành động", "green")

    def _sync_record_flags(self):
        """Doc 2 tuy chon ghi tu bien Tkinter - CHI goi o luong UI."""
        try:
            self._record_move = bool(self.record_move_var.get())
            self._record_scroll = bool(self.record_scroll_var.get())
        except Exception:
            pass

    def _on_record_opt_changed(self):
        self._sync_record_flags()
        self.save_config()

    # ---------------- GHI ----------------
    def get_key_str(self, key):
        if hasattr(key, 'char') and key.char is not None:
            code = ord(key.char)
            if 1 <= code <= 26:
                # Ctrl+chu: lay chu cai tu phim vat ly (vk) thay vi cong
                # 96 kieu cu - vd Ctrl+M truoc day co the thanh phim khac.
                vk = getattr(key, 'vk', None)
                if isinstance(vk, int) and 65 <= vk <= 90:
                    return chr(vk).lower()
                if isinstance(vk, int) and 48 <= vk <= 57:
                    return chr(vk)
                return chr(code + 96)
            return key.char
        return str(key)

    def on_press(self, key):
        try:
            if key == keyboard.Key.f12:
                self.after(0, self.stop_recording)
                return False
            if self.is_recording:
                self.events.append(('key_press', self.get_key_str(key),
                                    time.time() - self.start_time))
        except Exception:
            pass

    def on_release(self, key):
        try:
            if self.is_recording:
                self.events.append(('key_release', self.get_key_str(key),
                                    time.time() - self.start_time))
        except Exception:
            pass

    def on_click(self, x, y, button, pressed):
        try:
            if self.is_recording:
                action = 'mouse_down' if pressed else 'mouse_up'
                self.events.append((action, (x, y, str(button)),
                                    time.time() - self.start_time))
        except Exception:
            pass

    def on_move(self, x, y):
        # CHI doc bien bool thuong o day: goi bien Tkinter tu thread
        # cua pynput la nguyen nhan 1.1.0 mat het diem di chuyen.
        try:
            if not self.is_recording or not self._record_move:
                return
            now = time.time() - self.start_time
            lx, ly, lt = self._last_move
            # Nen move: chi ghi khi di chuyen >= 8px hoac da hon 50ms ke tu
            # diem ghi gan nhat - neu khong file kich ban phinh len hang
            # nghin dong chi vi re chuot.
            if abs(x - lx) < 8 and abs(y - ly) < 8 and now - lt < 0.05:
                return
            self._last_move = (x, y, now)
            self.events.append(('mouse_move', (x, y), now))
        except Exception:
            pass

    def on_scroll(self, x, y, dx, dy):
        try:
            if self.is_recording and self._record_scroll:
                self.events.append(('mouse_scroll', (x, y, dx, dy),
                                    time.time() - self.start_time))
        except Exception:
            pass

    def _stop_listeners(self):
        for listener in (self.keyboard_listener, self.mouse_listener):
            if listener:
                try:
                    listener.stop()
                except Exception:
                    pass
        self.keyboard_listener = None
        self.mouse_listener = None

    def start_recording(self):
        if self.is_recording:
            return
        self.events = []
        self._last_move = (0, 0, 0.0)
        # Doc tuy chon ghi o luong UI, truoc khi listener bat dau chay.
        self._sync_record_flags()
        self.is_recording = True
        self._stop_event.clear()
        self.update_status("Đang ghi... Nhấn F12 để dừng (hoặc menu khay -> Dừng ghi)",
                           "#C42B1C")
        self.btn_record.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.start_time = time.time()

        self.withdraw()
        # Hien tray ngay trong luc ghi: neu F12 bi app khac chiem thi
        # nguoi dung van con cho de dung ghi / hien lai cua so.
        self.show_tray()

        self.keyboard_listener = keyboard.Listener(on_press=self.on_press,
                                                   on_release=self.on_release)
        self.mouse_listener = mouse.Listener(on_click=self.on_click,
                                             on_move=self.on_move,
                                             on_scroll=self.on_scroll)
        self.keyboard_listener.start()
        self.mouse_listener.start()

    def stop_recording(self):
        if not self.is_recording:
            return
        self.is_recording = False
        self._stop_listeners()
        n_move = sum(1 for e in self.events if e[0] == 'mouse_move')
        n_click = sum(1 for e in self.events if e[0] in ('mouse_down', 'mouse_up'))
        n_scroll = sum(1 for e in self.events if e[0] == 'mouse_scroll')
        n_key = sum(1 for e in self.events if e[0] in ('key_press', 'key_release'))
        self.update_status(
            f"Đã ghi: {len(self.events)} hành động "
            f"({n_move} di chuyển, {n_click} click, {n_scroll} cuộn, {n_key} phím)",
            "green")
        self.btn_record.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self._stop_tray()
        self.show_window_normal()

    # ---------------- CHAY ----------------
    def _parse_play_settings(self):
        """Doc loops/delay/speed/pre_delay TREN LUONG UI, tra ve
        (loops, delay, speed, pre_delay) hoac (None, loi). loops=0
        nghia la vo han; delay am la loi; pre_delay la thoi gian cho
        sau khi an app de bam vao cua so dich truoc khi chay."""
        try:
            loops = int(self.entry_loops.get())
        except (ValueError, TypeError):
            return None, "số vòng lặp phải là số nguyên"
        try:
            delay_loops = float(self.entry_delay.get())
        except (ValueError, TypeError):
            return None, "thời gian nghỉ phải là số"
        if loops < 0:
            return None, "số vòng lặp không được âm (0 = vô hạn)"
        if delay_loops < 0:
            return None, "thời gian nghỉ không được âm"
        try:
            speed = float(self.speed_var.get().replace("x", ""))
            if speed <= 0:
                raise ValueError
        except (ValueError, AttributeError):
            speed = 1.0
        try:
            pre_delay = float(self.entry_pre_delay.get())
            if pre_delay < 0:
                raise ValueError
        except (ValueError, AttributeError):
            pre_delay = 3.0
        return (loops, delay_loops, speed, pre_delay), ""

    def start_playing(self):
        if not self.events:
            self.update_status("Không có kịch bản để chạy!", "red")
            return
        if self.is_playing:
            return
        settings, error = self._parse_play_settings()
        if settings is None:
            self.update_status(error, "red")
            return
        loops, delay_loops, speed, pre_delay = settings
        self.save_config()
        self._stop_event.clear()
        self.is_playing = True
        self.withdraw()
        self.show_tray()
        threading.Thread(target=self.play_macro,
                         args=(loops, delay_loops, speed, pre_delay),
                         daemon=True).start()

    def _sleep_interruptible(self, seconds):
        """Ngu nhung dung ngay khi _stop_event duoc set (F11 / nut Dung).
        Tra ve False neu bi ngat, True neu ngu het."""
        if seconds <= 0:
            return not self._stop_event.is_set()
        return not self._stop_event.wait(timeout=seconds)

    def play_macro(self, loops, delay_loops, speed, pre_delay=3.0):
        def on_press_play(key):
            if key == keyboard.Key.f11:
                self._stop_event.set()
                self.is_playing = False
                return False

        play_listener = keyboard.Listener(on_press=on_press_play)
        play_listener.start()
        try:
            mouse_ctrl = mouse.Controller()
            keyboard_ctrl = keyboard.Controller()
            if pre_delay and pre_delay > 0:
                # App vua an: cho nguoi dung bam vao cua so can thao
                # tac (vd Paint) de chon no, roi macro moi chay.
                # Ngat duoc ngay bang F11.
                self.update_status(
                    f"Sẽ chạy sau {pre_delay:g} giây - bấm vào cửa sổ cần thao tác (vd Paint)...",
                    "green")
                if not self._sleep_interruptible(pre_delay):
                    return
            loop_no = 0
            while not self._stop_event.is_set():
                if loops != 0 and loop_no >= loops:
                    break
                loop_no += 1
                total = "vo han" if loops == 0 else str(loops)
                self.update_status(f"Đang chạy vòng {loop_no}/{total}... (F11 để dừng)",
                                   "green")
                prev_timestamp = 0
                self._play_last_pos = None
                stopped = False
                for event in self.events:
                    if self._stop_event.is_set():
                        stopped = True
                        break
                    try:
                        action, data, timestamp = event
                    except (ValueError, TypeError):
                        continue
                    time_to_wait = (timestamp - prev_timestamp) / speed
                    if time_to_wait > 0:
                        if not self._sleep_interruptible(time_to_wait):
                            stopped = True
                            break
                    prev_timestamp = timestamp
                    try:
                        self._play_one(mouse_ctrl, keyboard_ctrl, action, data)
                    except Exception:
                        # 1 hanh dong loi khong duoc giet ca vong chay.
                        continue
                if stopped or self._stop_event.is_set():
                    break
                if loops != 0 and loop_no >= loops:
                    break
                if delay_loops > 0:
                    if not self._sleep_interruptible(delay_loops):
                        break
        finally:
            self.is_playing = False
            try:
                play_listener.stop()
            except Exception:
                pass
            self.update_status("Đã dừng/hoàn thành chạy kịch bản", "green")
            self.after(0, self._finish_playing)

    def _finish_playing(self):
        self._stop_tray()
        self.show_window_normal()

    def _move_mouse_to(self, mouse_ctrl, x, y):
        """Di chuyen chuot toi (x, y) luc CHAY, bang su kien nhap that.

        Thu SendInput TUYET DOI truoc (xem _send_input_move_to): moi
        buoc di chuyen deu la su kien nhap that nhu chuot that - Paint
        can tung diem giua de ve net - va toa do tuyet doi khong bi
        toc do con tro / tang toc cua Windows co gian nen diem click
        chinh xac. Dung SetCursorPos (mouse_ctrl.position / .move()
        cua pynput, vi tren Windows move() cung chi la SetCursorPos)
        thi con tro van chay theo duong cong tren man hinh nhung Paint
        chi thay nhan/nha chuot o 2 dau mut va noi thang chung lai.
        Chi khi SendInput tuyet doi loi moi roi ve SendInput tuong
        doi, roi ve .position.
        """
        if _send_input_move_to(x, y):
            self._play_last_pos = (x, y)
            return
        last = getattr(self, '_play_last_pos', None)
        if last is None:
            try:
                cur = mouse_ctrl.position
                dx, dy = x - cur[0], y - cur[1]
            except Exception:
                mouse_ctrl.position = (x, y)
                self._play_last_pos = (x, y)
                return
        else:
            dx, dy = x - last[0], y - last[1]
        if (dx or dy) and not _send_input_move(dx, dy):
            mouse_ctrl.position = (x, y)
        self._play_last_pos = (x, y)

    def _play_one(self, mouse_ctrl, keyboard_ctrl, action, data):
        if action in ('key_press', 'key_release'):
            key_obj = self._parse_key(data)
            if key_obj is None:
                return
            if action == 'key_press':
                keyboard_ctrl.press(key_obj)
            else:
                keyboard_ctrl.release(key_obj)
        elif action in ('mouse_down', 'mouse_up'):
            x, y, btn_str = data
            self._move_mouse_to(mouse_ctrl, x, y)
            btn_obj = mouse.Button.left
            try:
                btn_obj = getattr(mouse.Button, btn_str.split('.')[1],
                                  mouse.Button.left)
            except Exception:
                pass
            if action == 'mouse_down':
                mouse_ctrl.press(btn_obj)
            else:
                mouse_ctrl.release(btn_obj)
        elif action == 'mouse_move':
            x, y = data
            self._move_mouse_to(mouse_ctrl, x, y)
        elif action == 'mouse_scroll':
            x, y, dx, dy = data
            self._move_mouse_to(mouse_ctrl, x, y)
            mouse_ctrl.scroll(dx, dy)

    def _parse_key(self, data):
        """Chuoi phim ghi duoc -> doi tuong pynput. Ho tro 'Key.xxx',
        phim don 'a', va dang ket hop 'ctrl+c' / 'alt+x'."""
        if not isinstance(data, str) or not data:
            return None
        if data.startswith('Key.'):
            return getattr(keyboard.Key, data.split('.')[1], None)
        if '+' in data:
            parts = data.lower().split('+')
            main = parts[-1]
            # Cac phim bo tro duoc giu boi su kien ghi rieng, nen o day
            # chi can tra ve phim chinh.
            return main
        return data

    # ---------------- LUU ----------------
    def save_macro(self):
        if not self.events:
            self.update_status("Chưa có kịch bản để lưu - bấm Ghi trước đã!", "red")
            return
        filepath = filedialog.asksaveasfilename(defaultextension=".json",
                                                filetypes=[("JSON files", "*.json")])
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(self.events, f, ensure_ascii=False, indent=2)
                self.update_status("Đã lưu kịch bản thành công", "green")
            except Exception:
                self.update_status("Lỗi khi lưu kịch bản!", "red")

    # ---------------- CAP NHAT ----------------
    def check_for_updates(self, manual=False):
        if manual:
            self.update_status("Đang kiểm tra cập nhật...", "gray")
        def run():
            release, reason = fetch_latest_release_detailed()
            self.after(0, lambda: self._on_update_checked(release, reason, manual))
        threading.Thread(target=run, daemon=True).start()
        # Lap lai moi ngay neu bat tu cap nhat.
        if not manual and self.auto_update_var.get():
            self.after(24 * 60 * 60 * 1000,
                       lambda: self.check_for_updates(manual=False))

    def _on_update_checked(self, release, reason, manual):
        if release is None:
            if manual:
                msg = {"not-found": "Chưa có bản phát hành trên GitHub.",
                       "rate-limited": "GitHub giới hạn lượt gọi, thử lại sau.",
                       "offline": "Không có mạng, không kiểm tra được cập nhật."}.get(
                           reason, "Không kiểm tra được cập nhật.")
                self.update_status(msg, "red")
            return
        tag = release.get("tag") or ""
        if not is_newer(tag, VERSION):
            if manual:
                self.update_status(f"Đã là bản mới nhất ({VERSION})", "green")
            return
        # Co ban moi: hoi truoc khi tai, khong tu tai lang.
        if not messagebox.askyesno(
                "Có cập nhật mới",
                f"AutoClickTool {tag} đã có (bạn đang dùng {VERSION}).\n"
                "Tải và cài đặt ngay bây giờ?"):
            self.update_status(f"Có bản mới {tag} (bạn đã bỏ qua)", "gray")
            return
        if not getattr(sys, "frozen", False):
            # Chay tu source thi khong co exe de thay: mo trang release.
            self.update_status(f"Bản mới {tag} - mở trang tải về...", "green")
            webbrowser.open(release.get("url") or RELEASES_PAGE)
            return
        asset = pick_update_asset(release)
        if not asset:
            self.update_status(f"Bản {tag} chưa có file cập nhật, mở trang tải về...",
                               "red")
            webbrowser.open(release.get("url") or RELEASES_PAGE)
            return
        self.update_status(f"Đang tải bản {tag}...", "green")
        kind = asset.get("kind") or "exe"
        filename = ("AutoClickTool_new.zip" if kind == "zip"
                    else "AutoClickTool_new.exe")
        def run_download():
            dest = os.path.join(tempfile.gettempdir(), filename)
            path = download_asset(asset.get("url") or "", dest,
                                  expected_size=asset.get("size") or 0,
                                  expected_digest=asset.get("digest") or "")
            self.after(0, lambda: self._on_download_done(path, tag, kind))
        threading.Thread(target=run_download, daemon=True).start()

    def _on_download_done(self, path, tag, kind="exe"):
        if not path:
            self.update_status("Tải bản mới thất bại, thử lại sau.", "red")
            return
        if kind == "zip":
            # Ban onedir thi doi thu muc app; ban 1 file thi cai moi vao
            # thu muc rieng (xem apply_update_install).
            if _is_onedir_install():
                ok = apply_update_zip(path, sys.executable) is not None
            else:
                ok = apply_update_install(path, sys.executable) is not None
        else:
            ok = apply_update(path, sys.executable) is not None
        if not ok:
            self.update_status("Không cài đặt được bản mới.", "red")
            return
        # Dung tray icon + listener truoc khi thoat de tien trinh tat han,
        # script doi thu muc moi doi ten duoc ngay.
        self._stop_tray()
        self._stop_listeners()
        self.update_status(f"Đã tải {tag}, đang khởi động lại...", "green")
        self.after(500, self.destroy)


if __name__ == "__main__":
    app = MacroTool()
    app.mainloop()

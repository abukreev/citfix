#!/usr/bin/env python

from Xlib import X, XK, error, ext
from Xlib.display import Display
import Xlib
import signal,sys
import psutil
import time

SUBSTRING = "desktop (SSL/TLS Secured, 256 bit)"
KEYS = [
    64, # ALT_L_KEY
    23, # TAB_KEY
    133 # WIN_L_KEY
]

display = None
root = None

def childrenOfWindow(window):
    for child in window.query_tree().children:
        yield child
        for child2 in childrenOfWindow(child):
            yield child2

def getWindowTitle(window):
    return window.get_wm_name()

def windowIsOurs(window):
    try:
        return SUBSTRING in str(window.get_wm_name())
    except UnicodeDecodeError:
        return False

def findWindowByName():
    for window in childrenOfWindow(root):
        try:
            if windowIsOurs(window):
                return window
        except error.BadWindow:
            continue
    return None

def getPidByWindow(window):
    type_atom = display.intern_atom('_NET_WM_PID')
    try:
        type = window.get_full_property(type_atom, X.AnyPropertyType)
        try:
            pid = type.value[0]
            return pid
        except AttributeError:
            pass
    except error.BadWindow:
        pass
    return None

def waitForWindow():
    pass

def grabKey(window, key):
    window.grab_key(
        key,
        X.AnyModifier,
        1,
        X.GrabModeAsync,
        X.GrabModeAsync
    )

def grabKeys(window):
    for key in KEYS:
        grabKey(window, key)

def pressKey(window, keycode):
    sendKey(window, keycode, Xlib.protocol.event.KeyPress)

def releaseKey(window, keycode):
    sendKey(window, keycode, Xlib.protocol.event.KeyRelease)

def sendKey(window, keycode, fun):
    event = fun(
        time = int(time.time()),
        root = root,
        window = window,
        same_screen = 0, child = Xlib.X.NONE,
        root_x = 0, root_y = 0, event_x = 0, event_y = 0,
        state = 0,
        detail = keycode
    )
    window.send_event(event, propagate = True)
    display.flush()
    display.sync()

def initXStuff():
    global display
    display = Display()
    global root
    root = display.screen().root
    root.change_attributes(event_mask = X.KeyPressMask)
    root.change_attributes(event_mask = X.KeyReleaseMask)

def main():
    initXStuff()

    while True:
        try:
            window = findWindowByName()
            if not window:
                print 'Window is None'
                window = waitForWindow()
            title = getWindowTitle(window)
            pid = getPidByWindow(window)
            print 'pid = {}; window id = {}; title = {}'.format(hex(window.id), pid, title)

            altPressed = False
            tabCounter = 0
            while True:
                grabKeys(window)
                while True:
                    event = root.display.next_event()
                    if event.type == X.KeyPress:
                        keycode = event.detail
                        if keycode in KEYS:
                            pressKey(window, keycode)
                    elif event.type == X.KeyRelease:
                        keycode = event.detail
                        if keycode in KEYS:
                            releaseKey(window, keycode)
        except KeyboardInterrupt:
            print 'Exiting...'
            break
if __name__ == '__main__':
    main()


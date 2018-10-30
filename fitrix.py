#!/usr/bin/env python

from Xlib import X, XK, error, ext
from Xlib.display import Display
import Xlib
import signal,sys
import psutil
import time

SUBSTRING = "desktop (SSL/TLS Secured, 256 bit)"
ALT_TAB = 64

def childrenOfWindows(window):
    for child in window.query_tree().children:
        yield child
        for child2 in childrenOfWindows(child):
            yield child2

def getWindowTitle(display, window):
    return window.get_wm_name()

def windowIsOurs(window):
    try:
        return SUBSTRING in str(window.get_wm_name())
    except UnicodeDecodeError:
        return False

def findWindowByName(root):
    for window in childrenOfWindows(root):
        try:
            if windowIsOurs(window):
                return window
        except error.BadWindow:
            continue
    return None

def getPidByWindow(display, window):
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

def grabKey(root, window, key):
    window.grab_key(
        key,
        X.AnyModifier,
        1,
        X.GrabModeAsync,
        X.GrabModeAsync
    )

def ungrabKey(window, key):
    window.ungrab_key(key, X.AnyModifier)

def sendKeystroke(root, display, window, keycode):
    event = Xlib.protocol.event.KeyPress(
        time = int(time.time()),
        root = root,
        window = window,
        same_screen = 0, child = Xlib.X.NONE,
        root_x = 0, root_y = 0, event_x = 0, event_y = 0,
        state = Xlib.X.ShiftMask,
        detail = keycode
        )
    window.send_event(event, propagate = True)
    display.flush()
    display.sync()
    time.sleep(0.1) # magic
    event = Xlib.protocol.event.KeyRelease(
        time = int(time.time()),
        root = display.screen().root,
        window = window,
        same_screen = 0, child = Xlib.X.NONE,
        root_x = 0, root_y = 0, event_x = 0, event_y = 0,
        state = Xlib.X.ShiftMask,
        detail = keycode
        )
    window.send_event(event, propagate = True)
    window.send_event(event, propagate = True)
    display.flush()
    display.sync()

def main():
    display = Display()
    root = display.screen().root
    
    window = findWindowByName(root)
    if not window:
        print 'Window is None'
        window = waitForWindow()
    title = getWindowTitle(display, window)
    pid = getPidByWindow(display, window)
    print 'pid = {}; window id = {}; title = {}'.format(hex(window.id), pid, title)
#    while True:
    sendKeystroke(root, display, window, 0x10)

#        root.change_attributes(event_mask = X.KeyReleaseMask)
#        grabKey(root, window, ALT_TAB)
#        while True:
#            event = root.display.next_event()
#            if event.type == X.KeyRelease:
#                keycode = event.detail
#                if keycode == ALT_TAB:
#                    print '!!!'
#                    ungrabKey(window, ALT_TAB)
#                    sendKeystroke(display, window, 10)
#                    grabKey(root, window, ALT_TAB)

if __name__ == '__main__':
    main()


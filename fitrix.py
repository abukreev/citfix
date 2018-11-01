#!/usr/bin/env python

from Xlib import X, XK, error, ext
from Xlib.display import Display
import Xlib
import signal,sys
import psutil
import time

SUBSTRING = "desktop (SSL/TLS Secured, 256 bit)"
KEYS = [
    23, # TAB_KEY
    37, # CTRL_L_KEY
    64, # ALT_L_KEY
    112, # PGUP_KEY
    11, # PGDOWN_KEY
    133 # WIN_L_KEY
]

display = None
root = None
citrixWindow = None
NET_WM_NAME = None
WM_NAME = None

def childrenOfWindow(window):
    try:
        for child in window.query_tree().children:
            yield child
            for child2 in childrenOfWindow(child):
                yield child2
    except Xlib.error.BadWindow:
        raise StopIteration

def windowIsOurs(window):
    try:
        return SUBSTRING in getWindowTitle(window)
    except UnicodeDecodeError:
        return False

def findOurWindowUnderThis(parent):
    if windowIsOurs(parent):
        return parent
    for window in childrenOfWindow(parent):
        try:
            if windowIsOurs(window):
                return window
        except error.BadWindow:
            continue
    return None

def initWindow(window):
    window.change_attributes(event_mask = Xlib.X.KeyPressMask)
    window.change_attributes(event_mask = Xlib.X.KeyReleaseMask)
    window.change_attributes(event_mask = Xlib.X.StructureNotifyMask)
    window.change_attributes(event_mask = Xlib.X.SubstructureNotifyMask)

def printWinInfo(window):
    title = getWindowTitle(window)
    pid = getPidByWindow(window)
    print 'pid = {}; window id = {}; title = {}'.format(hex(window.id), pid, title)

def getWindowTitle(window):
    return str(window.get_wm_name())

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

def checkWindow(window):
    if windowIsOurs(window):
        ourWindow = window
    else: 
        ourWindow = findOurWindowUnderThis(window)
    printWinInfo(ourWindow)
    global citrixWindow
    citrixWindow = ourWindow
    initWindow(ourWindow)
    #grabKeys(ourWindow)

def grabKey(window, key):
    window.grab_key(
        key,
        X.AnyModifier,
        1,
        X.GrabModeAsync,
        X.GrabModeAsync
    )

def grabKeys(window):
#    for key in KEYS:
#        grabKey(window, key)
    window.grab_keyboard(True, X.GrabModeAsync, X.GrabModeAsync, X.CurrentTime)

def ungrabKeys():
    display.ungrab_keyboard(1, X.CurrentTime)

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

def init():
    global display
    display = Display()
    global root
    root = display.screen().root
    global NET_WM_NAME
    NET_WM_NAME = display.intern_atom('_NET_WM_NAME')  # UTF-8
    global WM_NAME
    WM_NAME = display.intern_atom('WM_NAME')         
    root.change_attributes(event_mask = Xlib.X.FocusChangeMask)

def processEvents():
    while True:
        event = root.display.next_event()
        print event
        processKeyEvent(event)
        processCreateEvent(event)
        processFocusEvent(event)

def processKeyEvent(event):
    if event.type == X.KeyPress:
        keycode = event.detail
        if keycode in KEYS:
            pressKey(citrixWindow, keycode)
    elif event.type == X.KeyRelease:
        keycode = event.detail
        if keycode in KEYS:
            releaseKey(citrixWindow, keycode)

def processCreateEvent(event):
    if event.type == X.PropertyNotify:
        if event.atom == 421:
            checkWindow(event.window)

def processFocusEvent(event):
    print 'processFocusEvent'
    if event.type == X.FocusIn:
        print 'Focus In'
        if event.window == citrixWindow:
            grabKeys(citrixWindow)
    elif event.type == X.FocusOut:
        print 'Focus Out'
        if event.window == citrixWindow:
            ungrabKeys()

def main():
    init()
    checkWindow(root)
    try:
        processEvents()
    except KeyboardInterrupt:
        print 'Exiting...'

if __name__ == '__main__':
    main()


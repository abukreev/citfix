#!/usr/bin/env python

from Xlib import X, XK, error, ext
from Xlib.display import Display
import Xlib
import signal,sys
import psutil
import time

SUBSTRING = "desktop (SSL/TLS Secured, 256 bit)"
MAGIC_KEY = 105

display = None
root = None
citrixWindow = None
NET_WM_NAME = None
WM_NAME = None
NET_ACTIVE_WINDOW = None
forward_keys = False


def childrenOfWindow(window):
    try:
        for child in window.query_tree().children:
            yield child
            for child2 in childrenOfWindow(child):
                yield child2
    except Xlib.error.BadWindow:
        raise StopIteration

def parentsOfWindiow(window):
    try:
        yield window.query_tree().parent
    except Xlib.error.BadWindow:
        raise StopIteration

def isOurWindow(window):
    try:
        return SUBSTRING in getWindowTitle(window)
    except UnicodeDecodeError:
        return False

def findOurWindowUnderThis(parent):
    if isOurWindow(parent):
        return parent
    for window in childrenOfWindow(parent):
        if isOurWindow(window):
            return window
    for window in parentsOfWindiow(parent):
        if isOurWindow(window):
            return window
    return None

def initWindow(window):
    window.change_attributes(event_mask = Xlib.X.KeyPressMask)
    window.change_attributes(event_mask = Xlib.X.KeyReleaseMask)
    window.change_attributes(event_mask = Xlib.X.StructureNotifyMask)
    window.change_attributes(event_mask = Xlib.X.SubstructureNotifyMask)

def printWinInfo(window):
    title = getWindowTitle(window)
    pid = getPidByWindow(window)
    winid = hex(window.id) if window else None
    print 'pid = {}; window id = {}; title = {}'.format(winid, pid, title)

def getWindowTitle(window):
    try:
        return str(window.get_wm_name())
    except AttributeError:
        return None

def getPidByWindow(window):
    if window:
      type_atom = display.intern_atom('_NET_WM_PID')
      try:
          type = window.get_full_property(type_atom, X.AnyPropertyType)
          if type:
            pid = type.value[0]
            return pid
      except error.BadWindow:
          pass
    return None

def grabKey(window, key):
    window.grab_key(
        key,
        X.AnyModifier,
        1,
        X.GrabModeAsync,
        X.GrabModeAsync
    )

def grabKeys(window):
    window.grab_keyboard(True, X.GrabModeAsync, X.GrabModeAsync, X.CurrentTime)

def ungrabKeys():
    global display
    display.ungrab_keyboard(0, X.CurrentTime)

def checkWindow(window):
    global citrixWindow
    ourWindow = None
    if isOurWindow(window):
        ourWindow = window
    else: 
        ourWindow = findOurWindowUnderThis(window)

    if ourWindow:
        citrixWindow = ourWindow
        initWindow(citrixWindow)
        print ('Found our window')
        printWinInfo(citrixWindow)
        grabKeys(citrixWindow)
    elif citrixWindow:
        citrixWindow = None
        print ('Lost our window')
        ungrabKeys()

def pressKey(window, event):
    sendKey(window, event, Xlib.protocol.event.KeyPress, 0)

def releaseKey(window, event):
    sendKey(window, event, Xlib.protocol.event.KeyRelease, 0)

def sendKey(window, old_event, fun, state):
    new_event = fun(
        time = int(time.time()),
        root = root,
        window = window,
        same_screen = old_event.same_screen,
        child = Xlib.X.NONE,
        root_x = 0,
        root_y = 0,
        event_x = 0,
        event_y = 0,
        state = old_event.state,
        detail = old_event.detail
    )
    window.send_event(new_event, propagate = True)
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
    global NET_ACTIVE_WINDOW
    NET_ACTIVE_WINDOW = display.intern_atom('_NET_ACTIVE_WINDOW')
    root.change_attributes(event_mask = Xlib.X.PropertyChangeMask)

def processEvents():
    while True:
        event = root.display.next_event()
        processKeyEvent(event)
        processPropertyEvent(event)

def processKeyEvent(event):
    global citrixWindow
    print ("processKeyEvent: citrixWindow = {}".format(citrixWindow))
    if citrixWindow:
        if event.type == X.KeyPress:
            keycode = event.detail
            print("keycode = {}".format(keycode))
            if keycode == MAGIC_KEY:
                print("Magic key has been pressed")
                citrixWindow = None
                ungrabKeys()
            else:
                pressKey(citrixWindow, event)
        elif event.type == X.KeyRelease:
            keycode = event.detail
            releaseKey(citrixWindow, event)

#def processCreateEvent(event):
#    if event.type == X.PropertyNotify:
#        if event.atom == 421:
#            checkWindow(event.window)

def processPropertyEvent(event):
    print ("processPropertyEvent")
    if event.type == X.PropertyNotify:
        if event.atom == NET_ACTIVE_WINDOW:
          focusedWindow = display.get_input_focus().focus
          printWinInfo(focusedWindow)
          checkWindow(focusedWindow)

def main():
    init()
#    checkWindow(root)
    try:
        processEvents()
    except KeyboardInterrupt:
        print 'Exiting...'

if __name__ == '__main__':
    main()


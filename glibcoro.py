#+
# glibcoro -- An interface between asyncio and the GLib event loop.
#
# The goal of this project is to implement an interface to the GLib/GTK+
# event loop as a subclass of asyncio.AbstractEventLoop, taking full
# advantage of the coroutine feature available in Python 3.5 and later.
#-

import sys
import time
import types
import asyncio
import gi
from gi.repository import \
    GLib

# TODO: handle threading?

class GLibEventLoop(asyncio.AbstractEventLoop) :

    # <https://developer.gnome.org/glib/stable/glib-The-Main-Event-Loop.html>

    def __init__(self) :
        self._gloop = GLib.MainLoop()
    #end __init__

    def run_forever(self) :
        self._gloop.run()
    #end run_forever

    def run_until_complete(self, future) :

        async def awaitit() :
            await future
            self.stop()
        #end awaitit

    #begin run_until_complete
        self.create_task(awaitit())
        self.run_forever()
    #end run_until_complete

    def stop(self) :
        self._gloop.quit()
    #end stop

    def is_running(self) :
        return \
            self._gloop.is_running()
    #end is_running

    def is_closed(self) :
        TBD
    #end is_closed

    def close(self) :
        TBD
    #end close

    def _timer_handle_cancelled(self, handle) :
        sys.stderr.write("cancelling timer %s\n" % (repr(handle,))) # debug
    #end _timer_handle_cancelled

    def call_exception_handler(self, context) :
        # TBD
        sys.stderr.write("call_exception_handler: %s\n " % repr(context))
    #end call_exception_handler

    # TODO: shutdown_asyncgens?

    def call_soon(self, callback, *args) :

        def doit(hdl) :
            sys.stderr.write("call_soon_doing, hdl = %s\n" % (hdl,)) # debug
            if not hdl._cancelled :
                hdl._run()
            #end if
            sys.stderr.write("call_soon hdl %s done\n" % (hdl,)) # debug
            return \
                False # always one-shot
        #end doit

    #begin call_soon
        sys.stderr.write("call_soon %s(%s)\n" % (repr(callback), repr(args))) # debug
        hdl = asyncio.Handle(callback, args, self)
        GLib.idle_add(doit, hdl)
        return \
            hdl
    #end call_soon

    def _call_timed_common(self, when, callback, args) :

        def doit(hdl) :
            sys.stderr.write("call_doing, hdl = %s\n" % (repr(hdl),),) # debug
            exc = None
            result = None
            if False :
                try :
                    result = callback(*args)
                except Exception as excp :
                    exc = excp
                #end try
            else :
                if not hdl._cancelled :
                    hdl._run()
                #end if
            #end if
            if False : # debug -- future is set done by asyncio?
                if exc != None :
                    call_done.set_exception(excp)
                else :
                    call_done.set_result(result)
                #end if
            #end if
            sys.stderr.write("call_done, result = %s, exc = %s\n" % (repr(result), repr(exc))) # debug
            return \
                False # always one-shot
        #end doit

    #begin _call_timed_common
        hdl = asyncio.TimerHandle(when, callback, args, self) # TBD should be TimerHandle
        GLib.timeout_add(max(round((when - self.time()) * 1000), 0), doit, hdl)
        return \
            hdl
    #end _call_timed_common

    def call_later(self, delay, callback, *args) :
        sys.stderr.write("call_later %s(%s) after %.3fs\n" % (repr(callback), repr(args), delay)) # debug
        return \
            self._call_timed_common(delay + self.time(), callback, args)
    #end call_later

    def call_at(self, when, callback, *args) :
        sys.stderr.write("call_at %s(%s) after %.3fs\n" % (repr(callback), repr(args), when - self.time())) # debug
        return \
            self._call_timed_common(when, callback, args)
    #end call_at

    def time(self) :
        # might as well do same thing as asyncio.BaseEventLoop
        return \
            time.monotonic()
    #end time

    def create_future(self) :
        sys.stderr.write("create_future\n") # debug
        return \
            asyncio.Future(loop = self)
    #end create_future

    def create_task(self, coro) :
        return \
            asyncio.Task(coro)
              # will call my call_soon routine to schedule itself
    #end create_task

    # TODO: threads, executor, network, pipes and subprocesses
    # TODO: readers, writers, sockets, signals
    # TODO: task factory, exception handlers, debug flag

    def get_debug(self) :
        return \
            False
    #end get_debug

#end GLibEventLoop

_running_loop = None

class GLibEventLoopPolicy(asyncio.AbstractEventLoopPolicy) :

    def get_event_loop(self) :
        global _running_loop
        if _running_loop == None :
            _running_loop = self.new_event_loop()
        #end if
        return \
            _running_loop
    #end get_event_loop

    def set_event_loop(self, loop) :
        if not isinstance(loop, GLibEventLoop) :
            raise TypeError("loop must be a GLibEventLoop")
        #end if
        _running_loop = loop
    #end set_event_loop

    def new_event_loop(self) :
        return \
            GLibEventLoop()
    #end new_event_loop

    # TODO: get/set_child_watcher

#end GLibEventLoopPolicy

def install() :
    "installs this module as the default purveyor of asyncio event loops."
    asyncio.set_event_loop_policy(GLibEventLoopPolicy())
#end install

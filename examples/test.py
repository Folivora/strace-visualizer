#!/usr/bin/env python3

from threading import Thread
from time import sleep

def threaded_function():
    #sleep(500)
    print("hello world")


if __name__ == "__main__":
    thread = Thread(target = threaded_function)
    thread.start()
    thread.join()
    print("thread finished...exiting")

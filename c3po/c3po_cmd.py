#!/usr/bin/env python
# -*- coding: utf-8 -*-

from mod import initializer
from mod import communicator
from mod.communicator import git_push, git_checkout


def main():

    initializer.initialize()

    # command = initializer.initialize()
    #
    # if command[0] == 'push':
    #     git_push(command[1])
    # elif command[0] == 'checkout':
    #     git_checkout()
    # elif command[0] in ALLOWED_COMMANDS:
    #     com = communicator.Communicator()
    #     getattr(com, command[0])()


if __name__ == '__main__':
    main()

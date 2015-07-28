#!/usr/bin/env python
# -*- coding: utf-8 -*-

from mod import initializer
from mod import communicator
from mod.communicator import git_push, git_checkout


def main():

    initializer.initialize()

if __name__ == '__main__':
    main()

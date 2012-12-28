#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
The gitbot executable
"""
from gitbot.engine import Engine


def main():
    """Main"""
    Engine(raise_exceptions=True).run()

if __name__ == "__main__":
    main()

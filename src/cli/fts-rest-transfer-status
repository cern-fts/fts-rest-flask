#!/usr/bin/env python3
import logging
import sys
import traceback

from fts3.cli import JobShower


def main():
    try:
        shower = JobShower()
        shower(sys.argv[1:])
    except Exception as e:
        logging.critical(str(e))
        if logging.getLogger().getEffectiveLevel() == logging.DEBUG:
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

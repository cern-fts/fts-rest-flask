#!/usr/bin/env python3
import logging
import sys
import traceback

from fts3.cli import ServerStatus


def main():
    try:
        banning = ServerStatus()
        sys.exit(banning(sys.argv[1:]))
    except Exception as e:
        logging.critical(str(e))
        if logging.getLogger().getEffectiveLevel() == logging.DEBUG:
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import logging
import sys
from classes.bot import Bot

def main():
    try:        
        logging.basicConfig(format='[%(asctime)s] [%(levelname)s] %(message)s', level=logging.DEBUG)
        bot = Bot()
        bot.communicate()
        
    except KeyboardInterrupt:
        logging.info("exiting")
        sys.exit(0)
        
    except Exception as e:
        logging.error(f"{e=}")
        sys.exit(1)

if __name__ == "__main__":
    main()
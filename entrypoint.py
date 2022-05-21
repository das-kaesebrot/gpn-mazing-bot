#!/usr/bin/env python3
import logging
import sys
from classes.bot import Bot

def main():
    try:        
        logging.basicConfig(format='[%(asctime)s] [%(levelname)s] %(message)s', level=logging.INFO)
        bot = Bot()
        bot.communicate()
        
    except KeyboardInterrupt:
        logging.info("exiting")
        sys.exit(0)
        
    except Exception as e:
        if not "wall" in str(e):
            logging.error(f"{e=}")
            sys.exit(1)
    
    finally:
        logging.info(f"Stats: {bot.wins=} {bot.losses=}")

if __name__ == "__main__":
    main()
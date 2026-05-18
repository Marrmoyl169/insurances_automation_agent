import schedule
import time
import subprocess
import logging
from datetime import datetime
import pytz

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

PRAGUE_TZ = pytz.timezone("Europe/Prague")
RUN_TIME = "13:00"  # Prague time


def run_main():
    now = datetime.now(PRAGUE_TZ).strftime("%Y-%m-%d %H:%M")
    logger.info(f"Starting main.py at {now} Prague time...")
    subprocess.run(["python3", "main.py"])
    logger.info("main.py finished.")


schedule.every().monday.at(RUN_TIME).do(run_main)
schedule.every().tuesday.at(RUN_TIME).do(run_main)
schedule.every().wednesday.at(RUN_TIME).do(run_main)
schedule.every().thursday.at(RUN_TIME).do(run_main)
schedule.every().friday.at(RUN_TIME).do(run_main)

logger.info(f"Scheduler started. Will run main.py every weekday at {RUN_TIME} Prague time.")

while True:
    schedule.run_pending()
    time.sleep(60)
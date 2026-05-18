from sheets import get_all_rows
from logic import check_cancellation, check_renewal
from bot import notify_with_button
from memory import save_pending
from messages import build_cancel_message, build_renewal_message
import logging
from dotenv import load_dotenv
import os

load_dotenv()
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)



def find_cases(data: dict) -> tuple:
    """Iterates over all rows and finds cancellations and renewals."""
    cancellations = []
    renewals = []
    total_rows = 0

    for tab_name, rows in data.items():
        logger.info(f"Processing tab: {tab_name} (rows: {len(rows)})")
        for i, row in enumerate(rows):
            total_rows += 1
            try:
                if row.get("Status") != "Active":
                    continue

                entry = {
                    "name": row.get("Name ", "").strip(),
                    "agreement": row.get("Insurance Agreement Number ", ""),
                    "lease_period": row.get("Lease period", "").strip(),
                    "insurance_period": row.get("Insurance period", "").strip(),
                    "crm_link": row.get("crm_link", "no link"),
                    "tab_name": tab_name,
                    "row_index": i
                }

                should_cancel, _ = check_cancellation(row)
                if should_cancel:
                    cancellations.append(entry)
                    logger.info(f"Cancellation found: row {i+2}, guest {entry['name']}")

                should_renew, _ = check_renewal(row)
                if should_renew:
                    renewals.append(entry)
                    logger.info(f"Renewal found: row {i+2}, guest {entry['name']}")

            except Exception as e:
                logger.warning(f"Error in row {i+2} (tab {tab_name}): {e}")

    logger.info(f"Successfully read {total_rows} rows. Cancellations: {len(cancellations)}, Renewals: {len(renewals)}.")
    return cancellations, renewals


def main():
    logger.info("Starting insurance check...")

    data = get_all_rows(SPREADSHEET_ID)
    cancellations, renewals = find_cases(data)

    if cancellations:
        message = build_cancel_message(cancellations)
        save_pending(cancellations)
        notify_with_button(message, "confirm_cancel")
    else:
        logger.info("No policies to cancel.")

    if renewals:
        message = build_renewal_message(renewals)
        save_pending(renewals, pending_type="renewal")
        notify_with_button(message, "confirm_renewal")
    else:
        logger.info("No policies to renew.")

    logger.info("Check completed.\n" + "-" * 40)


main()
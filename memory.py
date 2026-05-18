import json
import os
import logging
from datetime import date, timedelta

logger = logging.getLogger(__name__)

PENDING_CANCEL_FILE = "pending_cancellations.json"
PENDING_RENEWAL_FILE = "pending_renewals.json"
AWAITING_FILE = "awaiting_confirmation.json"


# ─── PENDING ────────────────────────────────────────────────────────────────

def save_pending(items, pending_type="cancel"):
    file = PENDING_CANCEL_FILE if pending_type == "cancel" else PENDING_RENEWAL_FILE
    with open(file, "w") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved {len(items)} pending {pending_type} items to {file}.")

def load_pending(pending_type="cancel"):
    file = PENDING_CANCEL_FILE if pending_type == "cancel" else PENDING_RENEWAL_FILE
    if not os.path.exists(file):
        logger.warning(f"Pending file not found: {file}")
        return []
    with open(file, "r") as f:
        items = json.load(f)
    logger.info(f"Loaded {len(items)} pending {pending_type} items from {file}.")
    return items

def clear_pending(pending_type="cancel"):
    file = PENDING_CANCEL_FILE if pending_type == "cancel" else PENDING_RENEWAL_FILE
    if os.path.exists(file):
        os.remove(file)
        logger.info(f"Cleared pending file: {file}.")
    else:
        logger.warning(f"Tried to clear {file}, but file not found.")


# ─── AWAITING ────────────────────────────────────────────────────────────────

def add_awaiting_group(cancellations):
    today = date.today()
    next_ask = today + timedelta(days=2)
    while next_ask.weekday() >= 5:
        next_ask += timedelta(days=1)

    group = {
        "id": f"cancel_{today.strftime('%Y%m%d')}",
        "sent_date": today.strftime("%Y-%m-%d"),
        "next_ask_date": next_ask.strftime("%Y-%m-%d"),
        "cancellations": cancellations
    }

    groups = load_awaiting()
    groups.append(group)

    with open(AWAITING_FILE, "w") as f:
        json.dump(groups, f, ensure_ascii=False, indent=2)

    logger.info(f"Added awaiting group '{group['id']}', next ask: {group['next_ask_date']}.")
    return group["id"]

def load_awaiting():
    if not os.path.exists(AWAITING_FILE):
        logger.warning(f"Awaiting file not found: {AWAITING_FILE}")
        return []
    with open(AWAITING_FILE, "r") as f:
        groups = json.load(f)
    logger.info(f"Loaded {len(groups)} awaiting groups.")
    return groups

def get_groups_to_ask():
    today = date.today().strftime("%Y-%m-%d")
    groups = load_awaiting()
    due = [g for g in groups if g["next_ask_date"] <= today]
    logger.info(f"Groups due today: {len(due)}.")
    return due

def confirm_group(group_id):
    groups = load_awaiting()
    groups = [g for g in groups if g["id"] != group_id]
    with open(AWAITING_FILE, "w") as f:
        json.dump(groups, f, ensure_ascii=False, indent=2)
    logger.info(f"Group '{group_id}' confirmed and removed.")

def postpone_group(group_id):
    groups = load_awaiting()
    for g in groups:
        if g["id"] == group_id:
            next_ask = date.today() + timedelta(days=1)
            while next_ask.weekday() >= 5:
                next_ask += timedelta(days=1)
            g["next_ask_date"] = next_ask.strftime("%Y-%m-%d")
            logger.info(f"Group '{group_id}' postponed to {g['next_ask_date']}.")
            break
    with open(AWAITING_FILE, "w") as f:
        json.dump(groups, f, ensure_ascii=False, indent=2)
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def parse_date_range(date_str):
    try:
        date_str = date_str.strip()
        parts = date_str.split("-")
        start_str = parts[0].strip()
        end_str = parts[1].strip()
        start = datetime.strptime(start_str, "%d.%m.%Y")
        end = datetime.strptime(end_str, "%d.%m.%Y")
        return start, end
    except Exception as e:
        logger.warning(f"Failed to parse date range '{date_str}': {e}")
        raise


def check_cancellation(row):
    """Lease end < Insurance end AND Lease end < today"""
    today = datetime.today()
    insurance_str = row.get("Insurance period", "")
    lease_str = row.get("Lease period", "")

    if not insurance_str or not lease_str:
        logger.warning(f"Missing date for guest '{row.get('Name', '').strip()}': insurance='{insurance_str}', lease='{lease_str}'")
        return False, None

    _, insurance_end = parse_date_range(insurance_str)
    _, lease_end = parse_date_range(lease_str)

    if lease_end < insurance_end and lease_end < today:
        logger.debug(f"Cancellation condition met: lease_end={lease_end.date()}, insurance_end={insurance_end.date()}")
        return True, lease_end

    return False, None


def check_renewal(row):
    """Insurance end < today AND Lease end > today"""
    today = datetime.today()
    insurance_str = row.get("Insurance period", "")
    lease_str = row.get("Lease period", "")

    if not insurance_str or not lease_str:
        logger.warning(f"Missing date for guest '{row.get('Name', '').strip()}': insurance='{insurance_str}', lease='{lease_str}'")
        return False, None

    _, insurance_end = parse_date_range(insurance_str)
    _, lease_end = parse_date_range(lease_str)

    if insurance_end < today and lease_end > today:
        logger.debug(f"Renewal condition met: insurance_end={insurance_end.date()}, lease_end={lease_end.date()}")
        return True, insurance_end

    return False, None
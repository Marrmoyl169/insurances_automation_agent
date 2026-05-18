import logging

logger = logging.getLogger(__name__)


def build_cancel_message(cancellations: list) -> str:
    """Generates a cancellation letter for the insurer."""
    logger.info(f"Building cancellation message for {len(cancellations)} policies...")

    count = len(cancellations)
    intro = f"Hi! I found {'1 insurance policy' if count == 1 else f'{count} insurance policies'} to cancel."
    request_line = "Ráda bych Vás požádala o zrušení " + (
        "následující pojistky:" if count == 1 else "následujících pojistek:"
    )

    lines = "\n".join([f"{c['agreement']} – {c['name']}" for c in cancellations])
    details = "\n\n".join([
        f"Name: {c['name']}\nLease period: {c['lease_period']}\nLink: {c['crm_link']}"
        for c in cancellations
    ])

    message = (
        f"{intro}\n\n"
        f"Here is the letter for your insurer:\n\n"
        f"Dobrý den, Michale,\n"
        f"doufám, že se máte dobře!\n\n"
        f"{request_line}\n\n"
        f"{lines}\n\n"
        f"Předem děkuji za vyřízení.\n\n"
        f"S pozdravem,\n"
        f"Mariya\n\n"
        f"---\n"
        f"{details}"
    )

    logger.info("Cancellation message built successfully.")
    return message


def build_renewal_message(renewals: list) -> str:
    """Generates a renewal notification message."""
    logger.info(f"Building renewal message for {len(renewals)} policies...")

    count = len(renewals)
    intro = (
        f"Hi! I found {'1 insurance policy' if count == 1 else f'{count} insurance policies'} to renew!\n"
        f"The guest{'s are' if count > 1 else ' is'} still living there, but the insurance has already expired ☹️"
    )

    details = "\n\n".join([
        f"*Guest name:* {r['name']}\n"
        f"*Lease period:* {r['lease_period']}\n"
        f"*Insurance period:* {r['insurance_period']}\n"
        f"*Reservation link:* {r['crm_link']}"
        for r in renewals
    ])

    message = f"{intro}\n\n{details}"

    logger.info("Renewal message built successfully.")
    return message
from django.core.management.base import BaseCommand
from django.utils import timezone

from forex.models import IdentityVerification


def auto_check_document(verification):
    """Automated document validation heuristic. Return ('approved'|'rejected', note).

    In production, replace with a real identity-verification lookup (e.g. Nigeria
    NIN / National ID / Voter's Card API). Kept isolated so swapping is one change.
    """
    doc_type = (verification.doc_type or '').lower()
    doc_number = ''.join(verification.doc_number.split())

    # Minimal sanity checks: 18+ characters for NIN, plausible lengths otherwise.
    if doc_type == 'nin' and len(doc_number) != 11:
        return 'rejected', 'NIN must be exactly 11 digits.'
    if doc_type == 'national_id' and len(doc_number) < 10:
        return 'rejected', 'National ID looks too short.'
    if doc_type == 'voters_card' and len(doc_number) < 8:
        return 'rejected', "Voter's card number looks invalid."

    return 'approved', 'Automatically verified.'


class Command(BaseCommand):
    help = 'Auto-check pending KYC documents (run via cron).'

    def handle(self, *args, **options):
        pending = IdentityVerification.objects.filter(status='pending').select_related('user')
        approved = 0
        rejected = 0
        for verification in pending:
            decision, note = auto_check_document(verification)
            verification.status = decision
            verification.review_note = note
            verification.reviewed_at = timezone.now()
            verification.save(update_fields=['status', 'review_note', 'reviewed_at'])
            self.stdout.write(
                f"{verification.user.email}: {verification.get_doc_type_display()} -> {decision}"
            )
            approved += decision == 'approved'
            rejected += decision == 'rejected'

        self.stdout.write(self.style.SUCCESS(
            f"Done. {approved} approved, {rejected} rejected."
        ))

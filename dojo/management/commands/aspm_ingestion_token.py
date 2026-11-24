from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from dojo.aspm_ingestion.models import IngestionToken
from dojo.aspm_ingestion.services import SCOPES, issue_token
from dojo.models import Product
from dojo.scm.models import Repository


class Command(BaseCommand):
    help = "Issue a product-scoped machine token (shown once), or revoke an existing token by id."

    def add_arguments(self, parser):
        parser.add_argument("--product", type=int)
        parser.add_argument("--repository", type=int)
        parser.add_argument("--user", help="Existing dedicated service user with unusable password, or a new username")
        parser.add_argument("--days", type=int, default=30)
        parser.add_argument("--scopes", default="submit,status,read,finalize,reports")
        parser.add_argument("--label", default="CI/CD")
        parser.add_argument("--revoke", type=int)

    def handle(self, *args, **options):
        if options["revoke"]:
            if not IngestionToken.objects.filter(pk=options["revoke"]).update(revoked_at=timezone.now()):
                msg = "Unknown token id."
                raise CommandError(msg)
            self.stdout.write("Token revoked.")
            return
        if not options["product"] or not options["user"] or not 1 <= options["days"] <= 365:
            msg = "Supply --product, --user and --days between 1 and 365."
            raise CommandError(msg)
        scopes = options["scopes"].split(",")
        if not set(scopes) <= SCOPES:
            msg = "Unknown scope."
            raise CommandError(msg)
        product = Product.objects.get(pk=options["product"])
        repository = Repository.objects.get(pk=options["repository"], product=product) if options["repository"] else None
        user, created = get_user_model().objects.get_or_create(username=options["user"])
        if created:
            user.set_unusable_password()
            user.save()
        token, raw = issue_token(user=user, product=product, repository=repository, scopes=scopes,
                                 expires_at=timezone.now() + timedelta(days=options["days"]), label=options["label"])
        self.stderr.write(f"Token id: {token.pk}; expires {token.expires_at.isoformat()}. Store the following secret in the CI secret store.")
        self.stdout.write(raw)

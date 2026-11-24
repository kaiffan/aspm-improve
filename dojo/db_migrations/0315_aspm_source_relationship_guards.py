from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("dojo", "0314_aspm_terminal_evidence_guards")]
    operations = [migrations.RunSQL(r"""
        CREATE FUNCTION aspm_guard_test_engagement() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            IF EXISTS (SELECT 1 FROM dojo_scanrun WHERE test_id=OLD.id) THEN
                RAISE EXCEPTION 'ASPM source test cannot move to another engagement' USING ERRCODE='23514';
            END IF;
            RETURN NEW;
        END $$;
        CREATE TRIGGER aspm_test_engagement_guard BEFORE UPDATE ON dojo_test FOR EACH ROW
            WHEN (OLD.engagement_id IS DISTINCT FROM NEW.engagement_id) EXECUTE FUNCTION aspm_guard_test_engagement();
        CREATE FUNCTION aspm_guard_engagement_identity() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            IF EXISTS (SELECT 1 FROM dojo_scanrun s JOIN dojo_test t ON t.id=s.test_id WHERE t.engagement_id=OLD.id) THEN
                RAISE EXCEPTION 'ASPM source engagement identity is immutable' USING ERRCODE='23514';
            END IF;
            RETURN NEW;
        END $$;
        CREATE TRIGGER aspm_engagement_identity_guard BEFORE UPDATE ON dojo_engagement FOR EACH ROW
            WHEN (ROW(OLD.product_id,OLD.commit_id) IS DISTINCT FROM ROW(NEW.product_id,NEW.commit_id))
            EXECUTE FUNCTION aspm_guard_engagement_identity();
    """, r"""
        DROP TRIGGER aspm_engagement_identity_guard ON dojo_engagement;
        DROP FUNCTION aspm_guard_engagement_identity();
        DROP TRIGGER aspm_test_engagement_guard ON dojo_test;
        DROP FUNCTION aspm_guard_test_engagement();
    """)]

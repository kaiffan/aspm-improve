from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("dojo", "0313_aspm_rate_model_state")]
    operations = [migrations.RunSQL(r"""
        CREATE FUNCTION aspm_guard_terminal_delete() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            IF OLD.status='COMPLETED' THEN
                RAISE EXCEPTION 'Completed ASPM evidence cannot be deleted' USING ERRCODE='23514';
            END IF;
            RETURN OLD;
        END $$;
        CREATE TRIGGER aspm_scan_delete_guard BEFORE DELETE ON dojo_scanrun FOR EACH ROW EXECUTE FUNCTION aspm_guard_terminal_delete();
        CREATE TRIGGER aspm_report_delete_guard BEFORE DELETE ON dojo_generatedreport FOR EACH ROW EXECUTE FUNCTION aspm_guard_terminal_delete();
        CREATE FUNCTION aspm_guard_observation_source() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            IF EXISTS (SELECT 1 FROM dojo_scanrun WHERE id=OLD.scan_id AND status='COMPLETED') THEN
                RAISE EXCEPTION 'Completed ASPM observation source is immutable' USING ERRCODE='23514';
            END IF;
            RETURN NEW;
        END $$;
        CREATE TRIGGER aspm_observation_source_guard BEFORE UPDATE ON dojo_findingobservation FOR EACH ROW EXECUTE FUNCTION aspm_guard_observation_source();
    """, r"""
        DROP TRIGGER aspm_observation_source_guard ON dojo_findingobservation;
        DROP FUNCTION aspm_guard_observation_source();
        DROP TRIGGER aspm_report_delete_guard ON dojo_generatedreport;
        DROP TRIGGER aspm_scan_delete_guard ON dojo_scanrun;
        DROP FUNCTION aspm_guard_terminal_delete();
    """)]

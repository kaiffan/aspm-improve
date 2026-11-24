from django.db import migrations

SQL = r"""
CREATE TABLE aspm_ingestion_rate (
    token_id bigint PRIMARY KEY REFERENCES dojo_ingestiontoken(id) ON DELETE CASCADE,
    bucket_minute bigint NOT NULL,
    requests integer NOT NULL CHECK (requests > 0)
);

CREATE FUNCTION aspm_guard_scan() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM dojo_commit c JOIN dojo_repository r ON r.id=c.repository_id
                   WHERE c.id=NEW.commit_id AND r.product_id=NEW.product_id) THEN
        RAISE EXCEPTION 'ASPM scan product/commit mismatch' USING ERRCODE='23514';
    END IF;
    IF NEW.test_id IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM dojo_test t JOIN dojo_engagement e ON e.id=t.engagement_id
        WHERE t.id=NEW.test_id AND e.product_id=NEW.product_id AND e.commit_id=NEW.commit_id
    ) THEN
        RAISE EXCEPTION 'ASPM scan test mismatch' USING ERRCODE='23514';
    END IF;
    IF TG_OP='UPDATE' THEN
        IF OLD.status='COMPLETED' OR
           ROW(NEW.product_id,NEW.commit_id,NEW.submitted_by_id,NEW.delivery_key,NEW.fingerprint,
               NEW.scanner,NEW.metadata,NEW.artifact_path,NEW.artifact_sha256,NEW.artifact_size,NEW.original_name)
           IS DISTINCT FROM
           ROW(OLD.product_id,OLD.commit_id,OLD.submitted_by_id,OLD.delivery_key,OLD.fingerprint,
               OLD.scanner,OLD.metadata,OLD.artifact_path,OLD.artifact_sha256,OLD.artifact_size,OLD.original_name)
           OR (OLD.test_id IS NOT NULL AND NEW.test_id IS DISTINCT FROM OLD.test_id) THEN
            RAISE EXCEPTION 'ASPM evidence identity is immutable' USING ERRCODE='23514';
        END IF;
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER aspm_scan_guard BEFORE INSERT OR UPDATE ON dojo_scanrun FOR EACH ROW EXECUTE FUNCTION aspm_guard_scan();

CREATE FUNCTION aspm_guard_observation() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE target uuid;
BEGIN
    IF TG_OP='DELETE' THEN target:=OLD.scan_id; ELSE target:=NEW.scan_id; END IF;
    IF EXISTS (SELECT 1 FROM dojo_scanrun WHERE id=target AND status='COMPLETED') THEN
        RAISE EXCEPTION 'Completed ASPM observations are immutable' USING ERRCODE='23514';
    END IF;
    IF TG_OP='DELETE' THEN RETURN OLD; END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER aspm_observation_guard BEFORE INSERT OR UPDATE OR DELETE ON dojo_findingobservation FOR EACH ROW EXECUTE FUNCTION aspm_guard_observation();

CREATE FUNCTION aspm_guard_report() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM dojo_commitscanset s WHERE s.id=NEW.scan_set_id AND s.commit_id=NEW.commit_id) THEN
        RAISE EXCEPTION 'ASPM report scan set mismatch' USING ERRCODE='23514';
    END IF;
    IF TG_OP='UPDATE' AND (OLD.status='COMPLETED' OR
        ROW(NEW.commit_id,NEW.version,NEW.scan_set_id,NEW.manifest) IS DISTINCT FROM ROW(OLD.commit_id,OLD.version,OLD.scan_set_id,OLD.manifest)) THEN
        RAISE EXCEPTION 'ASPM report is immutable' USING ERRCODE='23514';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER aspm_report_guard BEFORE INSERT OR UPDATE ON dojo_generatedreport FOR EACH ROW EXECUTE FUNCTION aspm_guard_report();

CREATE FUNCTION aspm_guard_set() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP IN ('UPDATE','DELETE') THEN
        RAISE EXCEPTION 'ASPM finalized set is immutable' USING ERRCODE='23514';
    END IF;
    IF EXISTS (SELECT 1 FROM jsonb_array_elements_text(NEW.scan_ids) AS ids(id)
               WHERE NOT EXISTS (SELECT 1 FROM dojo_scanrun s WHERE s.id=ids.id::uuid AND s.commit_id=NEW.commit_id)) THEN
        RAISE EXCEPTION 'ASPM finalized set contains another commit' USING ERRCODE='23514';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER aspm_set_guard BEFORE INSERT OR UPDATE OR DELETE ON dojo_commitscanset FOR EACH ROW EXECUTE FUNCTION aspm_guard_set();

CREATE FUNCTION aspm_guard_token() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.repository_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM dojo_repository WHERE id=NEW.repository_id AND product_id=NEW.product_id) THEN
        RAISE EXCEPTION 'ASPM token repository mismatch' USING ERRCODE='23514';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER aspm_token_guard BEFORE INSERT OR UPDATE ON dojo_ingestiontoken FOR EACH ROW EXECUTE FUNCTION aspm_guard_token();

CREATE FUNCTION aspm_guard_repository_identity() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF ROW(NEW.product_id, NEW.url) IS DISTINCT FROM ROW(OLD.product_id, OLD.url) AND
        (EXISTS (SELECT 1 FROM dojo_commit c JOIN dojo_scanrun s ON s.commit_id=c.id WHERE c.repository_id=OLD.id)
         OR EXISTS (SELECT 1 FROM dojo_ingestiontoken WHERE repository_id=OLD.id)) THEN
        RAISE EXCEPTION 'ASPM repository evidence identity is immutable' USING ERRCODE='23514';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER aspm_repository_guard BEFORE UPDATE ON dojo_repository FOR EACH ROW EXECUTE FUNCTION aspm_guard_repository_identity();

CREATE FUNCTION aspm_guard_commit_identity() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF ROW(NEW.repository_id,NEW.sha) IS DISTINCT FROM ROW(OLD.repository_id,OLD.sha) AND
       (EXISTS (SELECT 1 FROM dojo_scanrun WHERE commit_id=OLD.id) OR EXISTS (SELECT 1 FROM dojo_commitscanset WHERE commit_id=OLD.id)) THEN
        RAISE EXCEPTION 'ASPM commit evidence identity is immutable' USING ERRCODE='23514';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER aspm_commit_guard BEFORE UPDATE ON dojo_commit FOR EACH ROW EXECUTE FUNCTION aspm_guard_commit_identity();
"""

REVERSE = """
DROP TRIGGER aspm_commit_guard ON dojo_commit;
DROP FUNCTION aspm_guard_commit_identity();
DROP TRIGGER aspm_repository_guard ON dojo_repository;
DROP FUNCTION aspm_guard_repository_identity();
DROP TRIGGER aspm_token_guard ON dojo_ingestiontoken;
DROP FUNCTION aspm_guard_token();
DROP TRIGGER aspm_set_guard ON dojo_commitscanset;
DROP FUNCTION aspm_guard_set();
DROP TRIGGER aspm_report_guard ON dojo_generatedreport;
DROP FUNCTION aspm_guard_report();
DROP TRIGGER aspm_observation_guard ON dojo_findingobservation;
DROP FUNCTION aspm_guard_observation();
DROP TRIGGER aspm_scan_guard ON dojo_scanrun;
DROP FUNCTION aspm_guard_scan();
DROP TABLE aspm_ingestion_rate;
"""


class Migration(migrations.Migration):
    dependencies = [("dojo", "0311_aspm_api_ingestion")]
    operations = [migrations.RunSQL(SQL, REVERSE)]

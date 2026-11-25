from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("dojo", "0317_aspm_outbound_webhooks")]
    operations = [migrations.RunSQL(r'''

CREATE FUNCTION aspm_emit_webhook(p_product bigint, p_type text, p_payload jsonb) RETURNS void LANGUAGE plpgsql AS $$
DECLARE targets jsonb;
BEGIN
    SELECT jsonb_object_agg(id::text, revision) INTO targets FROM dojo_webhooksubscription
      WHERE product_id=p_product AND enabled AND NOT archived AND events @> jsonb_build_array(p_type);
    IF targets IS NOT NULL THEN
        INSERT INTO dojo_webhookevent(id, product_id, event_type, occurred_at, payload, subscribers, expanded)
          VALUES(gen_random_uuid(), p_product, p_type, clock_timestamp(),
            p_payload || jsonb_build_object('project', jsonb_build_object('id', p_product)), targets, false);
    END IF;
END $$;

CREATE FUNCTION aspm_capture_webhook() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE pid bigint; rid bigint; sha text; context jsonb; attrs jsonb; payload jsonb; event text; old_data jsonb; new_data jsonb;
BEGIN
    IF NOT EXISTS(SELECT 1 FROM dojo_webhooksubscription WHERE enabled AND NOT archived) THEN RETURN NEW; END IF;
    IF TG_TABLE_NAME='dojo_repository' THEN
        PERFORM aspm_emit_webhook(NEW.product_id, 'repository.created', jsonb_build_object(
          'repository', jsonb_build_object('id', NEW.id), 'attributes', jsonb_build_object('repository_id', NEW.id)));
        RETURN NEW;
    ELSIF TG_TABLE_NAME='dojo_commit' THEN
        SELECT product_id INTO pid FROM dojo_repository WHERE id=NEW.repository_id;
        PERFORM aspm_emit_webhook(pid, 'commit.first_seen', jsonb_build_object('repository',jsonb_build_object('id',NEW.repository_id),
          'commit',jsonb_build_object('sha',NEW.sha),'attributes',jsonb_build_object('repository_id',NEW.repository_id)));
        RETURN NEW;
    ELSIF TG_TABLE_NAME='dojo_scanrun' THEN
        IF TG_OP='UPDATE' AND NEW.status=OLD.status THEN RETURN NEW; END IF;
        SELECT repository_id, c.sha INTO rid, sha FROM dojo_commit c WHERE id=NEW.commit_id;
        attrs=jsonb_build_object('repository_id',rid,'scanner',NEW.scanner,'severity',COALESCE((SELECT jsonb_agg(key) FROM jsonb_each(NEW.severity_summary) WHERE value::text::bigint>0),'[]'::jsonb),
          'pipeline_id',NEW.metadata->>'pipeline_id','source','api');
        payload=jsonb_build_object('repository',jsonb_build_object('id',rid),'commit',jsonb_build_object('sha',sha),
          'scan',jsonb_build_object('id',NEW.id,'status',NEW.status),'correlation_id',NEW.metadata->>'correlation_id','attributes',attrs);
        PERFORM aspm_emit_webhook(NEW.product_id,'scan.' || lower(NEW.status),payload);
        IF NEW.status='COMPLETED' THEN PERFORM aspm_emit_webhook(NEW.product_id,'commit.scan_completed',payload); END IF;
        RETURN NEW;
    ELSIF TG_TABLE_NAME='dojo_generatedreport' THEN
        IF TG_OP='UPDATE' AND NEW.status=OLD.status THEN RETURN NEW; END IF;
        IF NEW.status NOT IN ('COMPLETED','FAILED') THEN RETURN NEW; END IF;
        SELECT r.product_id,c.repository_id,c.sha INTO pid,rid,sha FROM dojo_commit c JOIN dojo_repository r ON r.id=c.repository_id WHERE c.id=NEW.commit_id;
        event=CASE WHEN NEW.status='COMPLETED' THEN 'report.generated' ELSE 'report.failed' END;
        PERFORM aspm_emit_webhook(pid,event,jsonb_build_object('repository',jsonb_build_object('id',rid),'commit',jsonb_build_object('sha',sha),
          'report',jsonb_build_object('id',NEW.id,'status',NEW.status,'version',NEW.version),
          'attributes',jsonb_build_object('repository_id',rid,'source','api')));
        RETURN NEW;
    END IF;
    -- Finding changes: compare the database's actual OLD/NEW values, including bulk/PATCH writes.
    SELECT e.product_id INTO pid FROM dojo_test t JOIN dojo_engagement e ON e.id=t.engagement_id WHERE t.id=NEW.test_id;
    attrs=jsonb_build_object('severity',NEW.severity,'finding_status', CASE
      WHEN NEW.false_p THEN 'false_positive' WHEN NEW.duplicate THEN 'duplicate'
      WHEN NEW.out_of_scope THEN 'out_of_scope' WHEN NEW.is_mitigated THEN 'mitigated'
      WHEN NEW.active THEN 'active' ELSE 'inactive' END,'source','live');
    SELECT jsonb_build_object('repository_id',c.repository_id,'scanner',s.scanner,'pipeline_id',s.metadata->>'pipeline_id')
      INTO context FROM dojo_scanrun s JOIN dojo_commit c ON c.id=s.commit_id WHERE s.test_id=NEW.test_id;
    payload=jsonb_build_object('finding',jsonb_build_object('id',NEW.id,'severity',NEW.severity), 'attributes',attrs || COALESCE(context,'{}'::jsonb));
    IF TG_OP='INSERT' THEN
        PERFORM aspm_emit_webhook(pid,'finding.created',payload);
    ELSE
        old_data=jsonb_build_array(OLD.title,OLD.description,OLD.mitigation,OLD.severity,OLD.active,OLD.verified,OLD.false_p,OLD.duplicate,OLD.out_of_scope,OLD.is_mitigated,OLD.risk_accepted);
        new_data=jsonb_build_array(NEW.title,NEW.description,NEW.mitigation,NEW.severity,NEW.active,NEW.verified,NEW.false_p,NEW.duplicate,NEW.out_of_scope,NEW.is_mitigated,NEW.risk_accepted);
        IF old_data IS DISTINCT FROM new_data THEN PERFORM aspm_emit_webhook(pid,'finding.updated',payload); END IF;
        IF NEW.severity IS DISTINCT FROM OLD.severity THEN PERFORM aspm_emit_webhook(pid,'finding.severity_changed',payload); END IF;
        IF jsonb_build_array(NEW.active,NEW.verified,NEW.duplicate,NEW.out_of_scope,NEW.is_mitigated,NEW.risk_accepted) IS DISTINCT FROM
           jsonb_build_array(OLD.active,OLD.verified,OLD.duplicate,OLD.out_of_scope,OLD.is_mitigated,OLD.risk_accepted) THEN
            PERFORM aspm_emit_webhook(pid,'finding.status_changed',payload);
        END IF;
        IF NEW.false_p IS DISTINCT FROM OLD.false_p THEN PERFORM aspm_emit_webhook(pid,'finding.false_positive_changed',payload); END IF;
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER aspm_webhook_repository AFTER INSERT ON dojo_repository FOR EACH ROW EXECUTE FUNCTION aspm_capture_webhook();
CREATE TRIGGER aspm_webhook_commit AFTER INSERT ON dojo_commit FOR EACH ROW EXECUTE FUNCTION aspm_capture_webhook();
CREATE TRIGGER aspm_webhook_scan AFTER INSERT OR UPDATE ON dojo_scanrun FOR EACH ROW EXECUTE FUNCTION aspm_capture_webhook();
CREATE TRIGGER aspm_webhook_report AFTER INSERT OR UPDATE ON dojo_generatedreport FOR EACH ROW EXECUTE FUNCTION aspm_capture_webhook();
CREATE TRIGGER aspm_webhook_finding AFTER INSERT OR UPDATE ON dojo_finding FOR EACH ROW EXECUTE FUNCTION aspm_capture_webhook();

CREATE FUNCTION aspm_guard_webhook_event() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF (to_jsonb(NEW)-'expanded') IS DISTINCT FROM (to_jsonb(OLD)-'expanded') THEN
        RAISE EXCEPTION 'ASPM webhook event content is immutable' USING ERRCODE='23514';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER aspm_webhook_immutable BEFORE UPDATE ON dojo_webhookevent FOR EACH ROW EXECUTE FUNCTION aspm_guard_webhook_event();
''', r'''
DROP TRIGGER aspm_webhook_repository ON dojo_repository;
DROP TRIGGER aspm_webhook_commit ON dojo_commit;
DROP TRIGGER aspm_webhook_scan ON dojo_scanrun;
DROP TRIGGER aspm_webhook_report ON dojo_generatedreport;
DROP TRIGGER aspm_webhook_finding ON dojo_finding;
DROP TRIGGER aspm_webhook_immutable ON dojo_webhookevent;
DROP FUNCTION aspm_guard_webhook_event();
DROP FUNCTION aspm_capture_webhook();
DROP FUNCTION aspm_emit_webhook(bigint,text,jsonb);''')]

"""Small real ZAP import/reimport on the dedicated RC copy; no bulk_create."""
import argparse
import http.client
import json
import time
from pathlib import Path
from uuid import uuid4
from xml.etree.ElementTree import Element, SubElement, tostring

def report(indices, namespace):
    root = Element("OWASPZAPReport", {"version": "2.16.1"})
    site = SubElement(root, "site", {"name": "https://aspm-rc1.invalid", "host": "aspm-rc1.invalid", "port": "443", "ssl": "true"})
    alerts = SubElement(site, "alerts")
    for index in indices:
        alert = SubElement(alerts, "alertitem")
        for name, value in {
            "alert": f"ASPM RC1 {namespace} rule {index:02}", "pluginid": str(90000+index),
            "riskcode": str(1+index%3), "confidence": "2", "cweid": str([79,89,22,200][index%4]),
            "desc": "Synthetic scanner evidence for performance isolation",
            "solution": "Fixture mitigation", "reference": "https://aspm-rc1.invalid/rule",
        }.items():
            SubElement(alert, name).text = value
        instances = SubElement(alert, "instances")
        for endpoint in range(3):
            instance = SubElement(instances, "instance")
            for name, value in {"uri": f"https://aspm-rc1.invalid/{namespace}/service/{index}/{endpoint}?q=sample",
                                "method": "GET", "param": "q", "evidence": "synthetic", "attack": "", "requestheader": "GET /sample HTTP/1.1\r\nHost: aspm-rc1.invalid\r\n", "requestbody": "", "responseheader": "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n", "responsebody": "Sanitized fixture evidence"}.items():
                SubElement(instance, name).text = value
    return tostring(root, encoding="utf-8", xml_declaration=True)

def submit(operation, token, fields, payload):
    boundary = "round3-" + uuid4().hex
    body = bytearray()
    for key, value in fields.items():
        body.extend(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{key}\"\r\n\r\n{value}\r\n".encode())
    body.extend(f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"round3.xml\"\r\nContent-Type: application/xml\r\n\r\n".encode())
    body.extend(payload)
    body.extend(f"\r\n--{boundary}--\r\n".encode())
    conn = http.client.HTTPConnection("127.0.0.1", 48086, timeout=75)
    start = time.time()
    try:
        conn.request("POST", f"/api/v2/{operation}/", body=body, headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Authorization": "Token " + token, "Accept": "application/json",
        })
        response = conn.getresponse()
        data = json.loads(response.read())
        result = {"status":response.status, "start":start, "end":time.time(),
                  "test":data.get("test"), "deduplication_complete":data.get("deduplication_complete"),
                  "statistics":data.get("statistics"), "sql_count":response.getheader("X-Perf-SQL-Count"), "sql_ms":response.getheader("X-Perf-SQL-Ms"), "payload_bytes":len(payload)}
        if response.status >= 400:
            result["error_fields"] = sorted(data) if isinstance(data, dict) else []
        return result
    finally:
        conn.close()

parser = argparse.ArgumentParser()
parser.add_argument("label")
parser.add_argument("output", type=Path)
parser.add_argument("--rounds", type=int, default=3)
args = parser.parse_args()
import sys
account=json.load(sys.stdin)[0]
account['product_type_name']='ASPM RC1 isolated '+args.label
account['product_name']='ASPM RC1 isolated '+args.label
common={"scan_type":"ZAP Scan", "active":"true", "verified":"true", "minimum_severity":"Info", "push_to_jira":"false", "deduplication_execution_mode":"async_wait"}
all_steps=[]
for rep in range(1,args.rounds+1):
    namespace=f"{args.label}-{rep}"
    context={**common,"auto_create_context":"true","product_type_name":account["product_type_name"],"product_name":account["product_name"],"engagement_name":"RC1 "+namespace,"deduplication_on_engagement":"false"}
    steps=[]
    for operation,endpoint,fields,indices in (
        ("import","import-scan",{**context,"test_title":"Primary"},range(40)),
        ("reimport","reimport-scan",None,range(4,44)),
        ("duplicates","import-scan",{**context,"test_title":"Duplicate peer"},range(4,44)),
    ):
        if fields is None: fields={**common,"test":steps[0]["test"],"close_old_findings":"true"}
        row=submit(endpoint,account["token"],fields,report(indices,namespace))
        row.update(operation=operation,rep=rep,alerts=len(indices),phase=args.label)
        steps.append(row);all_steps.append(row)
        args.output.write_text(json.dumps(all_steps,indent=2)+"\n")
        print(operation,rep,row["status"],round((row["end"]-row["start"])*1000,1),row["deduplication_complete"],flush=True)
        if row["status"]!=201 or not row["deduplication_complete"]:raise SystemExit(1)

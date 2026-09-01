from datetime import datetime, timezone
from app.models import Icd11Term, NamasteTerm

NAMASTE_SYSTEM = "https://namaste.gov.in/sat-e"
ICD11_SYSTEM = "http://id.who.int/icd/release/11/mms"


def codesystem_resource(terms: list[NamasteTerm]) -> dict:
    return {"resourceType": "CodeSystem", "id": "namaste", "url": NAMASTE_SYSTEM,
            "version": "mock-2026.1", "name": "NAMASTESATE", "title": "Mock NAMASTE SAT-E terminology",
            "status": "active", "content": "complete", "caseSensitive": True,
            "concept": [{"code": term.code, "display": term.title_en, "definition": term.definition,
                         "designation": [{"language": "sa", "value": term.title_sanskrit},
                                         {"language": "ta", "value": term.title_tamil}]} for term in terms]}


def conceptmap_resource(rows, source_code: str | None = None) -> dict:
    grouped: dict[str, list] = {}
    for link, target in rows:
        grouped.setdefault(link.namaste_code, []).append((link, target))
    groups = []
    for code, links in grouped.items():
        groups.append({"source": NAMASTE_SYSTEM, "target": ICD11_SYSTEM,
                       "element": [{"code": code, "target": [
                           {"code": target.code, "display": target.title, "equivalence": link.equivalence,
                            "comment": f"{link.mapping_method}; similarity={link.similarity:.2f}"}
                           for link, target in links]}]})
    return {"resourceType": "ConceptMap", "id": f"namaste-icd11{('-' + source_code) if source_code else ''}",
            "url": "https://demo.namaste.local/fhir/ConceptMap/namaste-icd11", "status": "active",
            "name": "NAMASTEToICD11TM2", "title": "Mock NAMASTE to ICD-11 TM2 map", "sourceUri": NAMASTE_SYSTEM,
            "targetUri": ICD11_SYSTEM, "group": groups}


def condition_resource(condition_id: int, patient_id: str, encounter_id: str | None,
                       source: NamasteTerm, mappings, clinical_status: str, note: str | None) -> dict:
    coding = [{"system": NAMASTE_SYSTEM, "code": source.code, "display": source.title_en,
               "userSelected": True}]
    for link, target in mappings:
        coding.append({"system": ICD11_SYSTEM, "code": target.code, "display": target.title,
                       "extension": [{"url": "https://demo.namaste.local/fhir/StructureDefinition/mapping-equivalence",
                                      "valueCode": link.equivalence}]})
        if target.biomedical_code:
            coding.append({"system": "http://id.who.int/icd/release/11/mms", "code": target.biomedical_code,
                           "display": target.biomedical_title})
    resource = {"resourceType": "Condition", "id": str(condition_id), "clinicalStatus": {
        "coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": clinical_status}]},
        "code": {"coding": coding, "text": source.title_en}, "subject": {"reference": patient_id},
        "recordedDate": datetime.now(timezone.utc).isoformat()}
    if encounter_id:
        resource["encounter"] = {"reference": encounter_id}
    if note:
        resource["note"] = [{"text": note}]
    return resource

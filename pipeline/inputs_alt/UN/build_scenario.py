#!/usr/bin/env python3
"""Create the scenario card and both fixed chain configs from list IDs."""
import yaml
from pathlib import Path
ROOT=Path(__file__).resolve().parent
specs=[
 ("applications.university","university","self_describing","university association or historical set", "Review excludes applications when the applicant's university is listed by a named university association or historical set.", "Exclude an application if the applicant's university is listed by a named university association or historical set."),
 ("applicants.nationality","country","code","international body or programme", "Review excludes applications whose applicant nationality appears on a named international body or programme roster.", "Exclude an application if its applicant's nationality appears on a named international body or programme roster."),
 ("applications.sponsor_company","sponsor_company","self_describing","equity index, company ranking or financial-stability roster", "Review excludes applications sponsored by a company appearing in a named equity index, company ranking or financial-stability roster.", "Exclude an application if its sponsoring company appears in a named equity index, company ranking or financial-stability roster."),
]
templates=[]; fields={}
for field,universe,value_form,noun,source,rule in specs:
    ids=[x["id"] for x in yaml.safe_load((ROOT/"lists"/f"{universe}.yaml").read_text()) or []]
    fields[field]={"universe":universe,"value_form":value_form}
    for i in range(1,4):
        templates.append({"id":f"{universe}_rule_{i}","field":field,"effect":"exclude_record",
            "source":"Supplement: "+source,"rule":rule,
            "plausible":ids})
scenario={"business_process":"An international education foundation reviews scholarship applications and totals cases for follow-up by funding programme.",
 "fields":fields,"rule_templates":templates,
 "label_nouns":["award record","review docket","settlement note","audit pass"]}
(ROOT/"scenario.yaml").write_text(yaml.safe_dump(scenario,allow_unicode=True,sort_keys=False),encoding="utf-8")
(ROOT/"chains").mkdir(exist_ok=True)
for i,seed in [(1,20266101),(2,20266102)]:
 cfg={"id":f"UN{i}","dataset":"UN","seed":seed,"period":{"start":"2026-10-16"},"snapshot":"2026-10-16",
      "fields":[{"field":f,"universe":u,"templates":[f"{u}_rule_{n}" for n in range(1,4)]} for f,u,_,_,_,_ in specs],
      "slots":5,"probe":{"criterion":"soft"}}
 (ROOT/"chains"/f"UN{i}.yaml").write_text(yaml.safe_dump(cfg,allow_unicode=True,sort_keys=False),encoding="utf-8")
print(f"scenario templates={len(templates)} chains=2 fields={len(fields)}")

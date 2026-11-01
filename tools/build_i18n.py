"""Build redesign/shared/i18n.js from i18n/i18n.template.js + i18n/es.json (Spanish UI strings)."""
import json, os
os.chdir(os.path.join(os.path.dirname(__file__), ".."))
d = json.load(open("i18n/es.json"))
open("redesign/shared/i18n.js", "w").write(open("i18n/i18n.template.js").read().replace("__DICT__", json.dumps(d, ensure_ascii=False)))
print(f"i18n.js: {len(d)} Spanish strings")

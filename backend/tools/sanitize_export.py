"""Make a test fixture from a real export by replacing the FUT.GG userId.

The userId also prefixes card instance ids ("<userId>-<n>") and playedAt keys,
so it is replaced everywhere in the text, keeping ids consistent.

    python tools/sanitize_export.py records/FC27_x.json ../fixtures/sanitized_exports/FC27_x.json
"""
import json
import sys

FAKE_USER_ID = "1000000"


def main(src, dst):
    text = open(src, encoding="utf-8").read()
    user_ids = {str(p["userId"]) for p in json.loads(text)["players"] if p.get("userId")}
    for uid in user_ids:
        text = text.replace(uid, FAKE_USER_ID)
    json.loads(text)  # still valid
    open(dst, "w", encoding="utf-8", newline="\n").write(text)
    print(f"replaced userIds {sorted(user_ids)} -> {FAKE_USER_ID}")


if __name__ == "__main__":
    main(*sys.argv[1:3])

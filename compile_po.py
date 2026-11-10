"""
Genera archivos .mo conformes con GNU gettext y especificación de charset UTF-8.
"""
import struct
import array
from pathlib import Path


def generate_mo(po_path: Path, mo_path: Path):
    ID = 1
    STR = 2
    section = None
    subforum = False

    lines = po_path.read_text(encoding="utf-8").splitlines()
    msgid = msgstr = ""
    messages = {}

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("msgid "):
            if section == STR:
                messages[msgid] = msgstr
            msgid = line[6:].strip('"')
            msgstr = ""
            section = ID
        elif line.startswith("msgstr "):
            msgstr = line[7:].strip('"')
            section = STR
        elif line.startswith('"') and line.endswith('"'):
            val = line[1:-1].encode("utf-8").decode("unicode_escape")
            if section == ID:
                msgid += val
            elif section == STR:
                msgstr += val

    if section == STR:
        messages[msgid] = msgstr

    # Create the keys array
    keys = list(messages.keys())
    # The header metadata key is "" and must be first
    if "" in keys:
        keys.remove("")
        keys.insert(0, "")

    offsets = []
    ids = b""
    strs = b""

    for key in keys:
        val = messages[key]
        key_bytes = key.encode("utf-8")
        val_bytes = val.encode("utf-8")

        offsets.append((len(ids), len(key_bytes), len(strs), len(val_bytes)))
        ids += key_bytes + b"\0"
        strs += val_bytes + b"\0"

    keystart = 7 * 4 + len(keys) * 4 * 4
    valuestart = keystart + len(ids)

    klist = []
    vlist = []
    for o1, l1, o2, l2 in offsets:
        klist.extend([l1, keystart + o1])
        vlist.extend([l2, valuestart + o2])

    output = struct.pack(
        "Iiiiiii",
        0x950412DE,  # Magic
        0,           # Version
        len(keys),   # Number of strings
        7 * 4,       # Offset of table with start of original strings
        7 * 4 + len(keys) * 8,  # Offset of table with start of translation strings
        0,           # Size of hashing table
        0            # Offset of hashing table
    )
    output += struct.pack(f"{len(klist)}i", *klist)
    output += struct.pack(f"{len(vlist)}i", *vlist)
    output += ids
    output += strs

    mo_path.write_bytes(output)
    print(f"Compilado: {po_path.name} -> {mo_path}")


if __name__ == "__main__":
    base = Path(__file__).resolve().parent / "locale"
    for lang in ["es", "en"]:
        po = base / lang / "LC_MESSAGES" / "django.po"
        mo = base / lang / "LC_MESSAGES" / "django.mo"
        if po.exists():
            generate_mo(po, mo)

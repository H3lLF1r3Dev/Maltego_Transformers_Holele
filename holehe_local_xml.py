#!/usr/bin/env python3
import sys
import re
import subprocess
from pathlib import Path
import xml.etree.ElementTree as ET


STATUS_EXISTS = "exists"
STATUS_NOT_USED = "not_used"
STATUS_RATE_LIMITED = "rate_limited"


def add_entity(entities_node, etype: str, value: str, fields: dict | None = None):
    ent = ET.SubElement(entities_node, "Entity", {"Type": etype})
    val = ET.SubElement(ent, "Value")
    val.text = value

    if fields:
        af = ET.SubElement(ent, "AdditionalFields")
        for k, v in fields.items():
            f = ET.SubElement(
                af,
                "Field",
                {
                    "Name": k,
                    "DisplayName": k,
                    "MatchingRule": "strict",
                },
            )
            f.text = str(v)
    return ent


def build_xml_skeleton():
    msg = ET.Element("MaltegoMessage")
    resp = ET.SubElement(msg, "MaltegoTransformResponseMessage")
    entities = ET.SubElement(resp, "Entities")
    return msg, entities


def main():
    # Maltego passa o valor da entidade como 1º argumento em Local Transform
    email = sys.argv[1].strip() if len(sys.argv) > 1 else ""

    msg, entities = build_xml_skeleton()

    # Nunca permitir resposta vazia
    if not email:
        add_entity(entities, "maltego.Phrase", "HOLEHE: No email provided")
        sys.stdout.write(ET.tostring(msg, encoding="unicode"))
        return

    root = Path(__file__).resolve().parents[1]  # .../holehe-maltego
    holehe_bin = root / "venv" / "bin" / "holehe"

    if not holehe_bin.exists():
        add_entity(entities, "maltego.Phrase", f"HOLEHE: binary not found: {holehe_bin}")
        sys.stdout.write(ET.tostring(msg, encoding="unicode"))
        return

    # Executa holehe (captura stdout; nada fora de XML deve sair)
    try:
        proc = subprocess.run(
            [str(holehe_bin), email],
            capture_output=True,
            text=True,
            timeout=180
        )
        out = proc.stdout or ""
    except Exception as e:
        add_entity(entities, "maltego.Phrase", f"HOLEHE: execution error: {e}")
        sys.stdout.write(ET.tostring(msg, encoding="unicode"))
        return

    # Parse do output
    # Linhas típicas:
    # [x] instagram.com
    # [+] amazon.com
    # [-] docker.com
    # 121 websites checked in 10.11 seconds
    # Twitter : @palenath
    # Github : https://github.com/megadose/holehe
    re_checked = re.compile(r"(\d+)\s+websites\s+checked\s+in\s+([\d.]+)\s+seconds", re.I)
    re_kv = re.compile(r"^([A-Za-z0-9 _-]+)\s*:\s*(.+)$")

    # Contadores e dedupe
    seen = set()
    counts = {STATUS_EXISTS: 0, STATUS_NOT_USED: 0, STATUS_RATE_LIMITED: 0}
    checked_total = None
    seconds_total = None

    # Achados “high value”
    twitter_handle = None
    urls_found = set()

    lines = [ln.strip() for ln in out.splitlines() if ln.strip()]

    for line in lines:
        # Ignorar barras/progress do tqdm e ruído
        if "████" in line or line.endswith("it/s]") or line.startswith("100%|"):
            continue

        m = re_checked.search(line)
        if m:
            checked_total = int(m.group(1))
            seconds_total = float(m.group(2))
            continue

        # Captura "Twitter : @handle", "Github : https://..."
        mkv = re_kv.match(line)
        if mkv:
            k = mkv.group(1).strip().lower()
            v = mkv.group(2).strip()

            if k == "twitter":
                twitter_handle = v
            # guardar URLs em geral
            if v.startswith("http://") or v.startswith("https://"):
                urls_found.add(v)
            continue

        # Status lines
        status = None
        domain = None

        if line.startswith("[+]"):
            status = STATUS_EXISTS
            domain = line.replace("[+]", "").strip()
        elif line.startswith("[-]"):
            status = STATUS_NOT_USED
            domain = line.replace("[-]", "").strip()
        elif line.startswith("[x]"):
            status = STATUS_RATE_LIMITED
            domain = line.replace("[x]", "").strip()

        if not domain or not status:
            continue

        # Deduplicação
        key = (domain.lower(), status)
        if key in seen:
            continue
        seen.add(key)

        # Criar entidade consistente
        # Para manter o grafo limpo: tudo vira Website (mesmo not_used/rate_limited)
        add_entity(
            entities,
            "maltego.Website",
            domain,
            {
                "status": status,
                "source": "holehe",
                "input_email": email,
            },
        )
        counts[status] += 1

    # Summary node (sempre)
    summary_parts = [
        f"HOLEHE Summary for {email}",
        f"exists={counts[STATUS_EXISTS]}",
        f"not_used={counts[STATUS_NOT_USED]}",
        f"rate_limited={counts[STATUS_RATE_LIMITED]}",
    ]
    if checked_total is not None and seconds_total is not None:
        summary_parts.append(f"checked={checked_total}")
        summary_parts.append(f"seconds={seconds_total:.2f}")

    add_entity(
        entities,
        "maltego.Phrase",
        " | ".join(summary_parts),
        {
            "exists": counts[STATUS_EXISTS],
            "not_used": counts[STATUS_NOT_USED],
            "rate_limited": counts[STATUS_RATE_LIMITED],
            "checked": checked_total if checked_total is not None else "",
            "seconds": f"{seconds_total:.2f}" if seconds_total is not None else "",
            "source": "holehe",
        },
    )

    # High value findings: Twitter + URLs
    if twitter_handle:
        add_entity(
            entities,
            "maltego.Phrase",
            f"Twitter handle: {twitter_handle}",
            {"source": "holehe", "platform": "twitter", "input_email": email},
        )

    for u in sorted(urls_found):
        add_entity(
            entities,
            "maltego.URL",
            u,
            {"source": "holehe", "input_email": email},
        )

    # Se por alguma razão não parseou nenhum domínio, ainda assim não fica vazio
    if sum(counts.values()) == 0:
        add_entity(
            entities,
            "maltego.Phrase",
            f"HOLEHE executed but no domains were parsed for {email}",
            {"source": "holehe"}
        )

    sys.stdout.write(ET.tostring(msg, encoding="unicode"))


if __name__ == "__main__":
    main()


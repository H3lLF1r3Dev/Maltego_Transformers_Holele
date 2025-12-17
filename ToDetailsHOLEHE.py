import sys
import subprocess
from pathlib import Path
from maltego_trx.maltego import MaltegoTransform

def main():
    mt = MaltegoTransform()

    # 1) Input correto no Maltego TRX: vem do STDIN (XML)
    email = ""
    try:
        email = (mt.getValue() or "").strip()
    except Exception:
        email = ""

    # Fallback para testes via terminal
    if not email and len(sys.argv) > 1:
        email = sys.argv[1].strip()

    # 2) Sempre retornar pelo menos 1 entidade
    if not email:
        mt.addEntity("maltego.Phrase", "No email provided (input was empty)")
        mt.returnOutput()
        return

    # 3) Descobrir o binário holehe dentro do venv (portável)
    root = Path(__file__).resolve().parents[1]  # .../holehe-maltego
    holehe_bin = root / "venv" / "bin" / "holehe"

    if not holehe_bin.exists():
        mt.addEntity("maltego.Phrase", f"holehe binary not found: {holehe_bin}")
        mt.returnOutput()
        return

    # 4) Executar holehe e capturar output (não poluir stdout do TRX)
    try:
        proc = subprocess.run(
            [str(holehe_bin), email],
            capture_output=True,
            text=True,
            timeout=120
        )
    except Exception as e:
        mt.addEntity("maltego.Phrase", f"holehe execution error: {e}")
        mt.returnOutput()
        return

    stdout = proc.stdout or ""
    lines = [ln.strip() for ln in stdout.splitlines() if ln.strip()]

    created = 0

    for line in lines:
        if line.startswith("[+]"):
            service = line.replace("[+]", "").strip()
            ent = mt.addEntity("maltego.Website", service)
            ent.addProperty("status", "status", "strict", "exists")
            created += 1

        elif line.startswith("[-]"):
            service = line.replace("[-]", "").strip()
            ent = mt.addEntity("maltego.Phrase", service)
            ent.addProperty("status", "status", "strict", "not_used")
            created += 1

        elif line.startswith("[x]"):
            service = line.replace("[x]", "").strip()
            ent = mt.addEntity("maltego.Phrase", service)
            ent.addProperty("status", "status", "strict", "rate_limited")
            created += 1

    # Se nada foi parseado, ainda assim devolve algo
    if created == 0:
        mt.addEntity("maltego.Phrase", f"holehe ran OK but no parsable lines for {email}")

    mt.returnOutput()

if __name__ == "__main__":
    main()


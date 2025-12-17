# HOLEHE Local Transform para Maltego — Guia de Instalação e Uso

Este repositório fornece um **Local Transform do Maltego** que executa o **holehe** em um **ambiente virtual Python (venv)** e retorna os resultados para o Maltego como **XML válido do Maltego** (não requer Transform Server).

Compatível com **macOS** (Intel/Apple Silicon), e tende a funcionar em outras plataformas com pequenas adaptações de caminho.

---

## O que este Transform faz

Dada uma entidade **Email Address** no Maltego, o transform:

* Executa o `holehe` localmente (dentro de um `venv`)
* Faz o parse do output e retorna entidades no Maltego:

  * `maltego.Website` para cada domínio encontrado
  * `maltego.Phrase` com **resumo** (contagens e tempo)
  * Opcional: `maltego.URL` (quando o holehe imprimir URLs)
  * Opcional: `maltego.Phrase` com handle do Twitter (quando aparecer)

Inclui também:

* **Deduplicação** de domínios (evita repetição no grafo)
* **Saída estável** (não retorna “Empty Response”)

---

## Requisitos

* Maltego Graph (Desktop)
* Python 3.10+ (3.11 testado)
* Homebrew (recomendado no macOS)

---

## Estrutura esperada do repositório

```
holehe-maltego/
├─ transforms/
│  └─ holehe_local_xml.py
├─ venv/
├─ requirements.txt
└─ README.md
```

---

## 1) Instalar Python (recomendado via Homebrew)

Caso ainda não tenha Python 3:

```bash
brew install python@3.11
```

Verifique:

```bash
python3 --version
```

---

## 2) Clonar o repositório

```bash
git clone https://github.com/<SEU_USUARIO>/<SEU_REPO>.git
cd <SEU_REPO>
```

A partir daqui, `<PROJECT_ROOT>` significa a pasta onde o repositório foi clonado.

Exemplo:

* `<PROJECT_ROOT> = /caminho/para/holehe-maltego`

---

## 3) Criar e preparar o ambiente virtual (venv)

A partir do `<PROJECT_ROOT>`:

```bash
python3 -m venv venv
```

Instale as dependências usando o Python do venv (recomendado):

```bash
./venv/bin/python -m pip install --upgrade pip
./venv/bin/python -m pip install holehe
```

Verifique se o `holehe` está disponível no venv:

```bash
./venv/bin/holehe --help
```

---

## 4) Validar o script do transform (teste via terminal)

Execute o transform local (XML) diretamente:

```bash
./venv/bin/python -u transforms/holehe_local_xml.py test@gmail.com | head -n 2
```

A saída esperada começa com:

```xml
<MaltegoMessage><MaltegoTransformResponseMessage>...
```

Se você enxergar esse cabeçalho XML, está pronto para configurar no Maltego.

## 5) Configurar o Local Transform no Maltego (passo a passo)

### 5.1 Abrir o gerenciador de Local Transforms

No Maltego:

* **Transforms → Manage Local Transforms**
* Clique em **New Local Transform**

### 5.2 Preencher os campos básicos

Sugestão de valores:

* **Display name:**
  `HOLEHE – Email Enumeration`

* **Description:**
  `Enumera serviços online associados a um endereço de e-mail usando holehe (local).`

* **Transform ID:**
  `local.holehe.email.details`

* **Author:**
  Seu nome/handle

* **Input entity type:**
  `Email Address [maltego.EmailAddress]`

* **Transform set:**
  `(none)` (opcional)

Clique em **Next**.

### 5.3 Configurar execução (crítico)

Preencha exatamente:

#### Command line

Use o Python do venv (caminho completo):

```
<PROJECT_ROOT>/venv/bin/python
```

#### Command parameters

Use modo unbuffered + caminho do script:

```
-u <PROJECT_ROOT>/transforms/holehe_local_xml.py
```

#### Working directory

```
<PROJECT_ROOT>
```

(Opcional) Debug:

* Marque **Show debug info**

Salve/Finalize.

---

## 6) Executar o transform no Maltego

1. Crie um grafo novo
2. Arraste uma entidade **Email Address** para o canvas
3. Defina o valor do e-mail (ex.: `test@gmail.com`)
4. Clique com o botão direito na entidade:

   * **Local Transforms → HOLEHE – Email Enumeration**
5. Execute

Você deverá ver:

* Vários nós `Website`
* Um nó `Phrase` com **resumo**
* Opcionalmente nós `URL` / indicações de handle

---

## Legenda de saída (holehe)

O holehe usa o padrão:

* `[+]` Email usado
* `[-]` Email não usado
* `[x]` Rate limit (bloqueio/limite do serviço)

No Maltego isso é mapeado para a propriedade `status`:

* `exists`
* `not_used`
* `rate_limited`

---

## Troubleshooting

### “Empty Response” ao executar

Geralmente significa que o Maltego **não recebeu XML válido**.

Confirme sua configuração:

* Command line aponta para `<PROJECT_ROOT>/venv/bin/python`
* Command parameters contém `-u <PROJECT_ROOT>/transforms/holehe_local_xml.py`
* Working directory é `<PROJECT_ROOT>`

Confirme pelo terminal que o output começa com XML:

```bash
./venv/bin/python -u transforms/holehe_local_xml.py test@gmail.com | head -n 1
```

---

### “ModuleNotFoundError: holehe”

Você instalou o holehe em outro Python. Reinstale usando o Python do venv:

```bash
./venv/bin/python -m pip install holehe
```

---

### Muitos resultados “rate_limited” ou incompletos

Isso é esperado em alguns serviços por causa de:

* rate limiting
* mecanismos anti-bot
* CAPTCHA
* bloqueio por IP

Sugestões:

* executar novamente em outro momento
* testar com provedores diferentes (gmail/outlook/etc.)
* validar com e-mails “conhecidos” para checagem

---

## Observações de segurança e conformidade

* Este transform realiza enumeração OSINT de presença de e-mail em serviços.
* Utilize apenas com autorização e em conformidade com leis/políticas aplicáveis.
* Pode haver falso positivo/negativo devido a limitações e mudanças nos serviços.

---

## Créditos

* **holehe** por @megadose
* by H3lLF1r3Dev
* Integração para Maltego (Local Transform) adaptada para execução local e saída XML estável.

<img width="1294" height="1086" alt="image" src="https://github.com/user-attachments/assets/ebbec580-a166-46f6-809a-bfb6b22d93fa" />


# CLAUDE.md — Enterprises Go Digital (EGD) Chatbot Wiki

This is an LLM Wiki (Karpathy's pattern). You are a disciplined wiki
maintainer, not a general chatbot: you answer from the wiki, the wiki
answers from `raw/`, and every claim traces back to a source.

The schema is adapted from the sibling MSME wiki
(`~/Desktop/KB/MSME Bots/CLAUDE.md`). Set up on **2026-10-28**. The wiki
is empty and is built from `raw/` in the batches below.

## Objective

Give the **EGD Chatbot** (the "EGD Assistant") accurate, consistent and
approved answers about the Enterprises Go Digital Program and its platform,
`enterprisedigital.gov.kh`: what the programme offers, who qualifies, how to
register or apply, exact amounts and times, and who to contact.

The chatbot has one backend, one knowledge base and two channels: a
Telegram bot and a widget on the website. It serves two audiences:

- **Public:** MSMEs (formal and informal), Digital Solution Providers
  (DSPs), development partners, and trainers or digital experts. They get
  public content only.
- **Internal:** authorised EGD staff. They also get content marked
  `[INTERNAL]`: implementation progress, the platform approval workflow,
  and Policy Research Office information (scope pending a management
  decision).

The chatbot's response rules shape the wiki:

- It answers only from the knowledge base. Outside it, it says it doesn't
  have the information and gives the hotlines and the Telegram support
  link.
- It replies in the user's language (Khmer or English), never mixed, and
  uses only the **official Glossary terms** for Khmer.
- It quotes figures exactly. Never round, estimate or restate them in
  other units.

So **accuracy, exact figures, official Khmer terms and the public/internal
split come before coverage.**

**Out of scope:** other TSC programmes not part of EGD; general digital or
technology advice; vendor-specific product advice beyond the DSP listing;
MSME registration and licensing (that's the MSME wiki).

## Domain anchors

These framing facts have to be right from the first page. Confirm each one
against `raw/` as you ingest, and record it with a citation.

- **Who runs it:** the EGD Program is implemented by the **Enterprises Go
  Digital Department** of **Techo Startup Center (TSC)**, a public
  administrative institution under the **Ministry of Economy and Finance
  (MEF)**. It is fully funded by the **Skills Development Fund (SDF)** and
  charges no enrolment fees or commissions. It also runs the ADB-funded
  project "Supporting the Adoption of Digital Technologies and Fostering
  Innovation in MSMEs" (2024–2028).
- **The offer:** DAA (free, about 5 minutes) → DA Training (DA1–DA6, with
  a TSC certificate) → DA Grant voucher → certified DSP solution. E-Learning
  is self-paced. Login is by **CamDigiKey**.
- **Figures to quote exactly** (Project Brief and KB, 2026-09-11):
  - DA Grant maximum: **$400 (or 1,600,000 Riels)** formal and **$250 (or
    1,000,000 Riels)** informal.
  - Grant processing time: a maximum of **2 working days**.
  - Voucher validity: up to **12 months**.
  - Training approval: usually **1–2 working days**.

  Keep every official figure on `wiki/reference/official-figures.md`, with
  its exact wording and source.
- **Grant mechanics:** the enterprise pays the DSP first. TSC reimburses it
  after implementation and a progress report. Hardware, equipment, network
  infrastructure and human resources are not eligible.
- **The official docs disagree in places.** Record each disagreement on
  the pages concerned; don't pick a side silently.
  - The KB says "five priority activities" and defers to the Program Book,
    which is not in `raw/`. The Public FAQ says "three core activities".
  - The live site (2026-10-28) shows the DAA as "coming soon". The KB
    and Brief cover only DA1–DA6, but the Glossary (4.9, 4.10) and the site
    add the Digital Technology Capacity Training and the Tourism Digital
    Adoption Initiative.
  - The Brief lists three hotlines; the KB and the site list one.
  - Every disagreement goes on `wiki/reference/source-conflicts.md`, with
    the interim answer.
- **Pending management decisions** (Project Brief Part 4): Policy Research
  Office scope, chatbot tone, the website widget, and KB approval. Pages
  resting on unapproved content carry `status: draft`. Track decisions on
  `wiki/internal/pending-decisions.md`.

## Layers

- **`raw/`**: immutable sources. Never edit a file's contents. You may move
  and rename files only to file them (see Inbox).
  - Layout: `raw/<Entity>/<Year|undated>/<name>`. Entities so far: `EGD`
    (EGD Department / TSC). Add `TSC`, `MEF`, `ADB`, `RGC` and so on as
    sources arrive.
  - Name: `<YYYY[-MM[-DD]]|undated>_<Type>[-<No>]_<English-Title>[_variant].<ext>`.
  - `<Type>` values:
    - Programme: `ProgramBook`, `SOP`, `Guidebook`, `Guide`, `Form`,
      `Checklist`.
    - Chatbot material: `KnowledgeBase`, `FAQ`, `Glossary`, `Briefing`.
    - Policy and legal: `Strategy`, `Policy`, `Law`, `SubDecree`,
      `Prakas`, `Decision`, `Notice`, `Letter`.
    - Data and secondary: `Report`, `Dataset`, `Slides`, `Notes`,
      `Screenshot`.
  - Variants: `_alt-OCR`, `_scan`, `_KH`, `_EN`, `_Annex-1`.
  - Companion files (`.docx`, `.pdf`, `.md`, `.txt`, `.json`, `.xlsx`)
    share one stem and one folder. A `.md` beside a `.docx` is its
    transcription (`scripts/docx_to_md.py`).
  - **Temporary sources** (internal drafts the user wants used but not
    published) go in `raw/_temporary/<Entity>/<Year>/`, which is
    gitignored. Register them on `wiki/reference/temporary-sources.md` and
    label every claim from them "**Temporary (internal working paper)**".
  - Exact or text-identical copies go to `raw/_duplicates/<Entity>/<Year>/`.
    Non-sources go to `raw/_unrelated/`.
  - Record every move in `raw/_MOVED_FILES.tsv`.
- **Inbox**: new files arrive in a `raw/[TO INGEST]_*` folder or loose at
  the `raw/` root. File them first (see Inbox → raw).
- **`wiki/`**: the layer you own and write.
- **`app-integration/`**: hand-written instructions (`egd-chatbot-instruction.md`, written 2026-10-28)
  for the chatbot's generation layer. These cover the response rules,
  out-of-scope fallback text (hotlines plus `t.me/EGD_support`), the
  access-control rule and the language rule. Derive them from the wiki and
  update them when it changes. Not part of the wiki and not synced to
  Neo4j.
- **`scripts/`**: run with `python3 scripts/<name>.py`.
  - `docx_to_md.py <in.docx> <out.md> [--note]` transcribes Word files,
    keeping tables in body order.
  - `ocr_pdf.py` OCRs scans page by page through the local Khmer Document
    Parser API (see lessons).
  - `sync_neo4j.py` with `wikigraph/` mirrors the wiki into Neo4j (see
    Neo4j).
  - `lint_wiki.py` runs the mechanical lint: frontmatter, `audience`,
    sources that exist, unique slugs, public→internal links and missing
    link targets. Run it after every batch.
  - Planned: `build_source_catalogue.py` (every `raw/` source and the pages
    citing it) and a chatbot export to `data/`.
- **`data/`**: generated exports only. Regenerate them; never hand-edit.
- **Git:** initialised 2026-10-28 on `main` (first commit `03cc676`). PDFs
  go through Git LFS (`.gitattributes`); run `git lfs install` on any new
  clone. Never commit `.env`. Commit after each batch, filing and lint
  pass. **No remote yet**: push only once the user names a repo.
- **This file**: the schema. Update it as conventions settle. Call out
  each schema change to the user, and keep it lean. History goes in
  `wiki/log.md`, not here.

## Wiki structure

```
wiki/
  index.md        # catalogue of every page, one line each, grouped by folder
  log.md          # append-only activity log
  overview.md     # big-picture synthesis, once there's enough material
  glossary.md     # official English ↔ Khmer terms, from the Glossary source
  organisation/   # EGD Program, EGD Department, TSC, MEF, SDF, ADB project, offices
  platform/       # EGD Platform, its sections, CamDigiKey login
  programs/       # DAA, DA Training, DA Grant, DSP programme, E-Learning
  courses/        # one page per training course (DA1–DA6 and any others)
  processes/      # step-by-step: register, apply, get reimbursed, become a DSP
  policies/       # policy frameworks EGD aligns with (DESPF 2021–2035, Pentagonal Strategy)
  internal/       # [INTERNAL] staff-only content (audience: internal)
  reference/      # official figures, contacts, FAQ map, pending decisions, source gaps
  queries/        # syntheses worth keeping
  lint-reports/   # one file per lint pass
```

### Page rules

- **Filenames:** lowercase kebab-case slugs, e.g. `da-grant.md` or
  `dsp-registration.md`. Each slug must be **unique across all folders**:
  wikilinks and the Neo4j sync resolve on the slug alone.
- **Language:** write in English. On first use of a programme term, give
  the **official Glossary Khmer term**: "DA Grant (ជំនួយថវិកា…)".
  - Copy the Khmer exactly from the Glossary; never coin or translate a
    Khmer term yourself.
  - If a term has no Glossary entry, mark it "(no official Khmer term)"
    and list it on `glossary.md` as a gap.
  - Where the FAQ's Khmer and English answers differ in substance, record
    both and flag it.
- **Frontmatter on every page:**
  - `title`
  - `type`: organisation, program, course, process, platform, policy,
    reference, query or lint-report
  - `audience`: **public** or **internal**. Every page under `internal/`
    is `internal`. A public page must contain no internal content. The
    chatbot filters on this field, so when in doubt use `internal`.
  - `status`: draft, current, superseded or pending-decision
  - `date`: the date of the underlying source, or of the pass for a lint
    report. Omit it if there is neither.
  - `sources`: a list of `raw/` paths. Lint reports omit `sources`.
- **One-line summary** at the top. `index.md` uses it.
- **Citations:** every figure, eligibility rule, step or contact cites a
  `raw/` path and section ("Project Brief §2.5, 2026-09-11").
- **Exact figures:** copy amounts, times and validity periods **verbatim**,
  currency and units included ("$400 (or 1,600,000 Riels)"). Never round
  or convert.
- **Links:** use `[[wikilinks]]` freely. A programme page links to its
  courses, processes and the platform; a process page links to its
  programme and any forms.
- **Supersession:** never silently overwrite. Mark the old fact
  superseded, say what replaced it and when, and keep it on the page.
- **Confidence:** web-sourced or secondary facts (website snapshots, notes,
  screenshots) carry a visible lower-confidence caveat. The four chatbot
  documents are the user's working set, but they are **not yet
  management-approved** (Project Brief §4.4). Treat them as authoritative
  for now and flag their internal conflicts.
- **Diagrams:** mermaid or ASCII code blocks, with short English labels.

## Source-handling lessons

- **Filename dates can be YYYYDDMM.** The first four sources were named
  `20261109_…`, but the PDFs were created on 2026-09-11. They were filed as
  `2026-09-11`. Check a date against the document or file metadata before
  trusting a filename.
- **The chatbot documents overlap heavily.** The Project Brief restates the
  KB, and the FAQ restates both in Q&A form. Ingest the KB as the base
  text. Then use the Brief for scope, rules and internal content, and the
  FAQ for answer wording and edge cases. Note each disagreement.
- **The FAQ is bilingual Q&A.** Compare the Khmer and English answers
  before citing either. Some questions are unnumbered (the first and third
  in §1); cite them by position, e.g. "FAQ 1.1".
- **Never stitch excerpts.** At setup, joining `head` and `tail` output made
  FAQ Q1.4 look mismatched; it wasn't. Read contiguous ranges before
  claiming a source defect.
- **The FAQ doesn't use Glossary Khmer.** For DA Training, the DA Grant and
  E-Learning it uses its own wording, and it writes ្ដ where the Glossary
  writes ្ត. Pages and answers use the Glossary form. Variants are listed
  on `glossary.md`, and any search code must normalise ្ត/្ដ and «»/“”.
- **Website Khmer titles aren't Glossary terms.** The live site titles DA2
  and both non-DA programmes differently. Use the Glossary form in answers,
  and record site variants on `glossary.md`.
- **Website statuses are snapshots.** Course "accepting applications" and
  "coming soon" labels change. Pages record the date seen and send users to
  the link; never state a status as a standing fact.
- **Official PDFs linked from the EGD site may be filed** when `raw/` lacks
  a document the chatbot sources cite. Download each into its own empty
  scratch folder, check it, and file it under its document date. Record the
  URL and MD5 in `_MOVED_FILES.tsv`. Example: the Grant Guidebook,
  2026-10-28.
- **Grant Guidebook citations:** "GB ¶n", by the Guidebook's own paragraph
  numbers, not PDF pages. Printed page numbers are 2 behind PDF pages
  (printed 08 = PDF page 10). The Guidebook numbers ¶12 twice; cite the
  second as ¶12b. Its text layer is garbled (legacy font); use the `.md`
  OCR and check bare figures against the page image.
- **Newer chatbot docs vs the older Guidebook:** where the 2026 KB and the
  2024 Guidebook differ on a figure, the KB wins and the difference goes
  on `source-conflicts`. The Guidebook fills rules the KB leaves out;
  label them as Guidebook conditions.
- **Generate verbatim tables by script.** `wiki/glossary.md` was built from
  the source table, not retyped, so the Khmer can't drift. Rebuild it the
  same way if the Glossary changes.
- **Missing core documents.** The KB and Brief cite the **EGD Program Book**,
  the **EGD Platform SOP 2026** and the **EGD Progress Report 2025**. None is
  in `raw/`. Record what depends on them as a source gap on
  `wiki/reference/source-gaps.md`.
- **Use only documents in `raw/`.** If `raw/` can't settle a point, record
  a source gap. The chatbot must then answer "I don't have that
  information" and give the contacts, never a guess. Web findings go in
  `raw/<Entity>/<Year>/<date>_Notes_<Subject>-Web-Compiled.md`, with a
  source URL and a confidence level per claim. The site's
  `/archive/laws-and-regulations` page is a lead for policy sources.
- **OCR tools** (for scans; the current sources are Word files with clean
  text):
  - `scripts/ocr_pdf.py <pdf> <out.md> [--pages 1-5] [--note "..."]` uses
    only the user's local Khmer Document Parser API at
    `http://localhost:8000`. Check `GET /health` first. If it's down, ask
    the user to start it. Don't install tesseract or other engines.
  - Send one page at a time. Render pages larger than about 1 MB or 1200 pt
    to PNG first (`pdftoppm -scale-to 2000`). `/ocr-image` reads a single
    line only.
  - Check a PDF's text layer first; legacy Khmer fonts often extract as
    nonsense.
  - Khmer **១ often OCRs as "9"**. Check figures against the page image.
- **Quote YAML source items that contain ": "**, or they parse as maps.
- **Duplicates:** before filing, compare a new file against `raw/` by MD5,
  then by title, date and text. A `.pdf` that is a Word export of a
  `.docx` is a companion, not a duplicate.
- **Enumerate sources with `find`**, not from memory, and check coverage by
  script: every `raw/` stem should be cited by some page.

## Operations

### Inbox → raw (before ingesting)

For each file in an inbox folder or loose at the `raw/` root:

1. Identify its entity, type, number, date and language.
2. Check it against `raw/` for duplicates.
3. Move it to `raw/<Entity>/<Year>/` under the naming scheme, or to
   `_duplicates/`.
4. Transcribe it: `docx_to_md.py` for Word files, the OCR API for scans.
5. Append a row to `_MOVED_FILES.tsv`.

Log it as `## [YYYY-MM-DD] file | <inbox name>`, listing each file as new or
duplicate with its new path. Filing only moves and transcribes files; the
content is ingested in the matching batch.

### Ingest (batch mode, low supervision; the default)

1. **Plan:** list the batch: sources, order and the pages you expect.
   Show the plan in one short message, then proceed unless it raises a
   real question.
2. **Ingest each source:** read it, create or update the pages it touches,
   update `glossary.md` and `reference/official-figures.md`, and set
   `audience` on every page.
3. **After each batch:** update `index.md`; append
   `## [YYYY-MM-DD] ingest | <batch name>` to `log.md` with the sources and
   pages touched; run a quick lint of the new pages; **review this file**
   (fold in lessons, update "Current state", keep it lean).
4. **Stop and ask only** when sources conflict on a figure or rule the
   chatbot will quote, or when audience (public vs internal) is unclear.
   Record other judgement calls in the log.
5. **End of batch:** give a short summary of pages made, open questions
   and flags. Then re-sync Neo4j (`python3 scripts/sync_neo4j.py`) once
   credentials are in `.env`.

**Build order:**

1. Glossary and organisation: the full `glossary.md` from the Glossary
   source; EGD Program, EGD Department, TSC, MEF, SDF, ADB project; the
   policy-alignment pages; contacts and hours.
2. EGD Platform and CamDigiKey; the DAA.
3. DA Training: the programme page, DA1–DA6, E-Learning, and the
   registration process.
4. DA Grant: amounts, eligibility, eligible solutions, application, voucher
   and reimbursement.
5. DSPs: eligibility, benefits, documents, registration.
6. Public FAQ cross-check: map every FAQ question to its wiki page on
   `reference/faq-map.md`, and add any facts found only in the FAQ.
7. Internal content (`internal/`): implementation progress structure,
   approval workflow and authority levels, the Policy Research Office
   (pending-decision). Then write `app-integration/`.
8. Website and archive: the web-compiled notes, plus any policy documents
   the user adds.

### Query

Read `index.md`, drill into the relevant pages, and answer with citations
to wiki pages and their `raw/` sources. Respect `audience`: say when an
answer draws on internal pages. If the wiki is thin, read `raw/` and flag
the gap. After a real synthesis, ask whether to file it in `wiki/queries/`;
if yes, log `## [YYYY-MM-DD] query | <topic>`.

### Lint

Check for contradictions, stale claims, orphan pages (except `queries/` and
`lint-reports/`), broken links, and missing frontmatter or citations. Also
check that:

- every page has an `audience` value;
- no public page links to or quotes an internal page;
- every figure on a page matches `official-figures.md` exactly;
- every Khmer term on a page matches the Glossary.

Write findings to `wiki/lint-reports/YYYY-MM-DD-<slug>.md`, fix the
unambiguous ones, mark each fixed or open, and log
`## [YYYY-MM-DD] lint | <summary>`.

## Neo4j / MCP

`scripts/sync_neo4j.py` and `scripts/wikigraph/` were copied from the MSME
wiki on 2026-10-28 and re-namespaced:

- **The database may be shared** with the MSME wiki (`:MSMEPage`) and biz
  gov (`:Page`). Every node, index and constraint here uses the label
  **`:EGDPage`**, with the indexes `egd_page_slug`, `egdPageFulltext` and
  `egdPageEmbedding`. **Never query or delete on `:Page` or `:MSMEPage`.**
  Sync deletes `:EGDPage` nodes whose page is gone, so the namespace is
  what protects the other wikis.
- Type labels: Organisation, Program, Course, Process, Platform, Policy,
  Reference, Query. The `audience` frontmatter is stored as a node
  property so the chatbot can filter internal pages.
- `wiki/lint-reports/`, `index.md` and `log.md` are excluded. Sync is
  derived from the markdown; never hand-edit the graph.
- It needs `neo4j`, `pyyaml`, `python-dotenv` and `fastembed`.
- **Secrets:** `.env` (from `.env.example`) holds `NEO4J_URI`,
  `NEO4J_USERNAME`, `NEO4J_PASSWORD` and optionally `NEO4J_DATABASE`.
  Never print or commit `.env`.
- No MCP server yet. If one is added, copy the MSME `mcp_server/`,
  re-namespace it, enforce `audience` filtering server-side, and keep tool
  schemas Gemini-safe (plain string and integer arguments, no `anyOf`,
  `null` or `additionalProperties`).

## Current state

- **2026-10-28:** schema set up. Four chatbot documents filed to
  `raw/EGD/2026/` (`.docx`, a `.pdf` export and a `.md` transcription
  each): Project Brief, Knowledge Base, Public FAQ, Glossary. A website
  snapshot was saved as web-compiled notes.
- **Done:**
  - Batch 1 (2026-10-28): glossary and organisation, 14 pages.
    - `glossary` (51 entries).
    - The six organisation pages and the two policy pages.
    - Reference: `contacts`, `official-figures` (already lists the grant,
      DAA, training and DSP figures), `source-gaps`, `source-conflicts`
      (5 open, 1 resolved).
    - Internal: `pending-decisions`.
    - Lint: 0 errors; 8 forward links to batch 2–5 pages.
  - Batch 2 (2026-10-28): EGD Platform, CamDigiKey, DAA, 6 pages.
    - `egd-platform`, `camdigikey`, `platform-data-privacy`,
      `digital-adoption-assessment`, `getting-started-with-egd`,
      `request-expert-consultation`.
    - The DAA was confirmed live from a fresh site check (new web notes),
      so `source-conflicts` #3 is resolved.
  - Batch 3 (2026-10-28): DA Training, 12 pages.
    - `da-training`, `da-training-registration`, `e-learning`,
      `trainers-and-digital-experts`.
    - Eight course pages: DA1–DA6, generated from a template, and the two
      non-DA programmes.
    - `source-conflicts` #5 has an interim answer: DA Training is six
      activities; the other two are "other programmes", without DA facts.
  - Batch 4 (2026-10-28): DA Grant, 3 pages.
    - `da-grant`, `da-grant-application`, `da-grant-general-conditions`.
    - The **Grant Guidebook** (Nov 2024, v6, Khmer) was downloaded from the
      grant page, filed under `raw/EGD/2024/` and OCR'd.
    - Conflicts #4, #8 and #9 resolved; #7 is open: the Guidebook has a
      single 400-dollar cap vs the 2026 tiers of $400 and $250.
  - Batch 5 (2026-10-28): DSPs, 2 pages (`digital-solution-providers`,
    `dsp-registration`), plus `overview`.
    **Public content (build order 1–5) is complete:** 38 pages, 0 lint
    errors, 0 missing links.
  - Batch 6 (2026-10-28): `faq-map`. All 22 FAQ questions map to pages.
    The FAQ has no figures, URLs or phone numbers.
  - Batch 7 (2026-10-28): internal pages `platform-approval-workflow`,
    `egd-implementation-progress` (structure only, no figures) and
    `policy-research-office` (pending-decision), plus
    `app-integration/egd-chatbot-instruction.md`.
  - **The build order is complete through batch 7:** 42 pages (38 public,
    4 internal), 0 lint errors.
- **Neo4j:** credentials are in `.env` (a new Aura instance; the file was
  created 2026-10-28). **Last synced 2026-10-28:** 42 pages, all with
  embeddings, 316 `LINKS_TO`, 0 unresolved links. `audience` was verified
  in the graph: 38 public, 4 internal.
- **Open for the EGD team** (`source-conflicts`):
  - #1: five vs three activities;
  - #2: the hotlines;
  - #5: the non-DA programmes;
  - #7: the Guidebook's single cap vs the $250 informal tier.

  Also: the registered-micro inference; the Khmer fallback text; the four
  Part 4 decisions.
- **Next:**
  - Batch 8, when sources arrive: the Program Book, Platform SOP 2026,
    Progress Report 2025, Internal FAQ, and the policy PDFs from the
    website archive.
  - Re-check the live site's course statuses periodically.
  - A first full lint pass to `wiki/lint-reports/`.
- **Source gaps:** EGD Program Book, Platform SOP 2026, Progress Report
  2025, an Internal FAQ (Brief Appendix A.2), and any 2026 edition of the
  Grant Guidebook. The Nov 2024 edition was filed on 2026-10-28.

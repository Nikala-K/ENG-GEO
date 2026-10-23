# English → Georgian dictionary: options research

Goal: type one English word, get its Georgian meaning(s).

> Note: the research sandbox could not open the sites directly (network policy), so the
> facts below come from web search results. Entry counts and access terms should be
> checked before relying on them.

## 1. Existing tools you can use today

| Tool | What it is | Size | Cost / access | Notes |
|---|---|---|---|---|
| [dictionary.ge](https://dictionary.ge/en/guide) (Margaliti, TSU Lexicographic Centre) | Online version of the 14-volume *Comprehensive English-Georgian Dictionary* | ~110,000 entries | Historically registration + fee; free at the National Library of Georgia | Best academic quality: multiple senses, collocations, examples. No public API found. |
| [Glosbe en→ka](https://glosbe.com/en/ka) | Crowd-sourced + corpus-based dictionary | unknown | Free | Lists several translations ranked by frequency, with example sentences. Quality varies. |
| Targmne.com, Translate.ge | Georgian online dictionaries | ~62,000 / ~26,000 entries ([lexicool listing](https://www.lexicool.com/online-dictionary.asp?FSP=A66)) | Free | Current status not verified. |
| Google Translate / Microsoft Translator | Machine translation | — | Free web / paid API | Usually gives one translation; not a real dictionary. Azure has a dictionary-lookup endpoint, but Georgian support there is unverified (check `GET /languages?scope=dictionary` for `ka`). |
| Apps: [LinGEO](https://apps.apple.com/app/id919796414), [English to Georgian Dictionary](https://apps.apple.com/us/app/id1496508558), [Freelang](https://www.freelang.net/dictionary/georgian.php), PeaceBridge Chrome extension | Offline/mobile dictionaries | 50k–60k words | Free / freemium | Fine for personal use; data is not reusable. |

**If you only need a tool for yourself:** use dictionary.ge for quality and Glosbe as a free fallback.

## 2. Data you could build on

| Source | License | Usefulness |
|---|---|---|
| **Wiktionary via [wiktextract / kaikki.org](https://github.com/tatuylonen/wiktextract)** | CC BY-SA (attribution) | **Best open source.** English entries carry a `translations` list with `"code": "ka"` items, tied to a specific sense (e.g. *Georgianize* → აქართულებს, sense "to make Georgian"). Gives you "meanings grouped by sense" out of the box. Coverage is partial: common words are covered well, rare ones often aren't. |
| Georgian Wiktionary (ka.wiktionary.org) | CC BY-SA | Georgian headwords with English glosses; can be inverted to add more pairs. |
| [MUSE bilingual dictionaries](https://github.com/facebookresearch/MUSE) (Meta) | CC BY-NC | ~5k word pairs per pair if en-ka exists (not confirmed); one translation per word; non-commercial only. |
| [English–Georgian parallel corpus](https://lexikos.journals.ac.za/pub/article/view/1701) (corp.dict.ge) | unclear | Good for example sentences; access terms unknown. |
| Margaliti / TSU data | Copyrighted | Highest quality; would need a licensing deal with TSU Lexicographic Centre. |
| LLM (e.g. Claude API) | Generated output | Can list multiple meanings by part of speech for almost any word. Risk: occasionally invents or misspells Georgian words, so results must be labelled and ideally checked against a real dictionary. |

No open, free English→Georgian dictionary **API** was found.

## 3. What we could build

### Option A — Static Wiktionary dictionary (recommended MVP)
1. Download the English wiktextract JSONL from kaikki.org.
2. Script (Python): keep entries that have `translations` with `code == "ka"`; output
   `{ word, pos, senses: [{ gloss, georgian: [...] }] }`.
3. Ship as a compressed JSON or SQLite file plus a small web page (search box, autocomplete,
   results grouped by part of speech and sense).
4. Host free on GitHub Pages. No backend, no running costs, works offline as a PWA.

Pros: free, open license, real dictionary data. Cons: gaps for less common words.

### Option B — LLM-powered lookup
Small backend (serverless function) that sends the word to an LLM with a strict JSON schema
(`pos`, `meaning in English`, `georgian[]`, example). Cache every answer.
Pros: covers everything, handles phrases and inflected forms. Cons: per-lookup cost (small),
needs an API key and server, can be wrong.

### Option C — Hybrid (recommended end state)
Look up Wiktionary data first; if missing or thin, fall back to the LLM and mark the result as
"AI-generated". Add a "report / suggest a fix" button so corrections accumulate into our own data.
Later additions: lemmatization (*ran* → *run*), Georgian→English reverse lookup, audio,
example sentences from the parallel corpus.

### Option D — License professional data
Contact TSU Lexicographic Centre about using the Margaliti data. Best quality, but slow and
probably not free.

## Suggested next step
Build Option A: a data-extraction script plus a one-page search UI, then add the LLM fallback.

# AllHail rebuild plan

AllHail turns photos, documents and typed text into speech. It replaces the Streamlit app in this repo and joins OverBoard, AllAboard and OverHeard. It is an installable web app (PWA) for Android phones, iPhones and laptops. Everything runs on the device except two things that need the cloud: describing a photo, and the premium cloud voices.

## Who it is for

1. **A student with a vision impairment.** Open the app, point the camera and tap one huge button. The app speaks a description of what's in front of them. It has to work fully with VoiceOver (iPhone) and TalkBack (Android), with no small targets and no reading required.
2. **A sighted teacher preparing materials ahead of time.** The teacher uploads a painting, worksheet or document, reads and edits the description, previews it, and downloads an MP3 to post on Google Classroom. The old `app.py` had this as "Process image into text first" plus Download MP3, and it stays.

## How speech works

Speech uses an ordered fallback list, like OverHeard's translators. If one voice fails, is unavailable or is still downloading, the next one is used. Settings can change the order.

| | 1st | 2nd | 3rd | 4th |
|---|---|---|---|---|
| **Phone** | Device voice (`speechSynthesis`) | Kokoro (runs in the browser) | Google Cloud free allowances | Lemonfox |
| **Laptop** | Kokoro | Device voice | Google Cloud free allowances | Lemonfox |
| **MP3 download** | Kokoro | Google Cloud free allowances | Lemonfox | — |

- **Phone or laptop** is decided by what the device can do (touch screen, memory, WebGPU), not by its name. Settings can override it.
- **Kokoro** is a one-time download of about 90 MB, stored by the browser. While it downloads, the next voice in the list speaks, so nobody waits.
- **Device voices can't be saved as a file**, so MP3 downloads skip them.
- **Google Cloud free allowances** are used best first. Each one stops at 90% of its monthly limit:
  1. Chirp 3 HD (1M characters)
  2. Neural2 (1M, shared with Polyglot)
  3. WaveNet (4M, shared with Standard)
  4. Studio (1M)

  The server keeps its own count of characters for each allowance, saved in Cloud Storage because Cloud Run's disk is wiped. If the count can't be read, Google is skipped. If Google returns a quota or billing error, that allowance is set aside for the rest of the month. Gemini voices have no free allowance and aren't used.
- **One voice per job.** A long document or MP3 never changes voice halfway through. A different voice is chosen only when the next job starts.
- **Lemonfox** is the last resort, if its account is renewed.

## How photo descriptions work

- Before upload, every image is prepared on the device:
  - It's turned upright using the camera's rotation tag.
  - It's shrunk (longest side about 1,568 px, JPEG).
  - It's redrawn so only the pixels are sent: no GPS location, no camera details. If that step fails, the image is not sent.
- Teachers often have crooked or sideways scans with no rotation tag, so teacher mode has a rotate button and the preview shows exactly what will be sent. The prompts also tell the model that text may be sideways or upside down.
- `POST /api/describe` sends it to OpenRouter, using the fallback chains below (chosen by the bake-off in `tools/vision-bakeoff/`). Every request sets `provider.data_collection: "deny"`, so only providers that don't keep or train on the data are used.

| Button | 1st | If blank, cut off or refused | Then | Then |
|---|---|---|---|---|
| **Quick look** (mostly students, speed matters) | Claude Haiku 5.5, thinking off (~0.5 s) | Gemini 3.5 Flash-Lite | GLM 5.3 Flash | — |
| **Full detail** (students and teachers) | GLM 5.3 Flash | Claude Haiku 5.5, thinking on | Haiku again, thinking off | Gemini 3.5 Flash-Lite |

  - A blank answer, an answer cut off at the length limit, a provider error, or a refusal ("I can't help with that") all count as failures, and the next model is tried at once.
  - GLM 5.3 leads Full detail (owner's decision, 2026-11-15). It scored best on Full detail in the final judged run. With v5 it named all three test paintings and called Cole's statue headless. Haiku's Full detail answers kept making factual slips: the seated de Hooch man "stands", "The Consummation of Empire, the third panel", the wrong signature spot.
  - Haiku with thinking on sometimes thinks until it runs out of room (a 250-bubble answer sheet), and capping its thinking budget doesn't work through OpenRouter. So when Haiku is reached, it's retried with thinking off.
  - The chains live in server config, so they can be changed without a code change. Qwen 3.7 Flash is a supported option (cheapest, and the owner likes its feel) but isn't in a default chain: it takes about 3 s, and its provider rejects nudity outright.
  - All prompts use version **v5** in `tools/vision-bakeoff/variants.ts`.
- There are two buttons, each with its own prompt:
  - **Quick look:** a short description (60–150 words) to get your bearings.
  - **Full detail:** everything a sighted classmate could study. It reads all the text exactly, including handwriting, circled answers and grades. It also describes the whole image area by area: figures, setting, colors, light, style and mood for artwork, and axes, values and trends for charts. A painting with no text gets this too, so a student can analyse it in class.
- Scanned PDFs with no text layer go through Full detail one page at a time.
- Before speaking, text is tidied up for the voice. Fractions like "3/4" become "3 quarters", because some voices read them as dates or say "slash". Leftover markdown symbols are removed. The text shown on screen stays as the model wrote it.
- With no internet, the app says plainly that photos can't be described right now. Typed text and documents still work with on-device voices.

## Building it, in order

### 1. Choose the vision models
- First run (2026-11-14), 10 models on 3 clean computer-made images (a worksheet, a sign, a bar chart):
  - Every model got every fact right, so these images are too easy to separate the models.
  - Cost per photo ranged from about $0.0001 to $0.0008. The exception was `gpt-4o-mini`, which the old app used: about $0.004–0.006, 10–20 times the others, because OpenAI charges a lot for images on that model.
  - Speed: Qwen3-VL was about 0.2 s, Claude Haiku 5.5 about 0.4 s, and most others under 2 s.
  - Qwen 3.7 Flash and Gemma 4 return nothing unless thinking is turned off. `models.txt` marks them `no-thinking`.
  - Claude Haiku 5.5's read-aloud answers were the most natural to listen to.
- Second run (2026-11-14): 23 real photos from the owner, both prompts, 460 calls, $0.40 in total. The photos covered art scans, phone photos of art, art on a TV, handwriting, marked-up quizzes, screens, a chart, an AI-generated nude and a horror image.
  - **Proposed primary: Claude Haiku 5.5.**
    - Its handwriting transcription was perfect.
    - It was the fastest of the accurate models (about 0.5 s).
    - It named famous paintings (Cole, Repin).
    - It described the nude and horror images plainly and suitably for school.
    - It cost about $0.40–0.75 per 1,000 photos.
  - **Proposed fallback: Gemini 3.5 Flash-Lite.** It's from a different company, so one outage doesn't take out both. It named both paintings and never failed, at about 1 s and $1.60 per 1,000.
  - **Close behind:** Qwen 3.7 Flash, which was very accurate and the cheapest, but about 3 s and it fails on nudity. Also GLM 5.3 Flash, which scored well on keywords but misread and dropped handwritten lines.
  - **Drop:**
    - Mistral Small: invents things, for example a "winged woman" and a "cannon" in Cole's painting.
    - gpt-4o-mini: 10 times the cost, and it refused the nude.
    - gpt-5-nano: weakest overall.
    - Gemini 2.5 Flash-Lite: blocked the nude.
  - The speech cleaner must also strip single `*asterisks*`. Haiku italicises titles that way.
  - These picks came from automatic fact checks and a read-through.
- The owner read the answers and liked how Qwen 3.7 and Gemini 3.5 Flash-Lite captured the mood. Haiku and GLM were also very good, but Haiku kept saying "the most striking…". That led to the prompt tests below.
- Third run, prompt versions (2026-11-14): 4 finalists × 4 prompt versions × 23 photos × 2 buttons = 736 answers. Three judges from different companies scored every answer blind against the image: GPT-6.1 Sol, Claude Sonnet 5.5 and Gemini 3.1 Pro (`judge.ts`).

  | Version | What changed | Judges' score | Invented expressions |
  |---|---|---|---|
  | v1 | original | 7.38 | 9 |
  | **v2** | **open with what it is and its mood, keep atmosphere throughout, ban stock phrases** | **7.48** | **11** |
  | v3 | v2 + "describe what the artist would most want you to notice first", with examples ("a sly smile") | 7.28 | 29 |
  | v4 | v3 without the examples | 7.37 | 14 |

  - **v2 won.** The "notice first" instruction was too leading. With examples, it nearly tripled invented expressions, such as a "wide grin" on a Totoro and a "knowing smile" on de Hooch's woman. v2 also halved Haiku's stock phrases (23 down to 11 in 46 answers).
  - Haiku's blank answers turned out to be thinking running away (see above), not random glitches.
- Fourth run, final check (v2, final thinking settings), judged the same way:

  | Model | Quick look | Full detail | Notes |
  |---|---|---|---|
  | Claude Haiku 5.5 | **8.12** | 7.15 thinking off; best of all with thinking on (7.71 in run 3) | fastest; perfect handwriting |
  | GLM 5.3 Flash | 7.87 | **7.39** | strong on mood; sometimes drops handwritten lines |
  | Qwen 3.7 Flash | 7.98 | 6.81 | cheapest; 3 s; rejects nudity |
  | Gemini 3.5 Flash-Lite | 7.71 | 6.56 | never failed; pleasant to listen to, but less complete |

  - Judges marked at least one small invented or overstated detail in about 80% of answers from every model, for example which way a figure faces. No model is perfect. That's one reason teacher mode lets the teacher edit the text before downloading.
- Owner's blind check of the expression flags (2026-11-15). The 46 answers the judges flagged for invented expressions or gazes were re-voted blind by the owner, with model, version and judge names hidden. Only about half the flags held up:

  | Version | Flagged | Model was right | Judge was right | Unsure |
  |---|---|---|---|---|
  | v1 | 7 | 3 | 2 | 2 |
  | **v2** | 7 | 3 | 3 | 0 (1 note only) |
  | v3 | 21 | 9 | **9** | 3 |
  | v4 | 11 | 4 | 5 | 2 |

  - **v2 stays.** v3's "notice first" examples still produced three times as many real mistakes.
  - **Emotions were mostly read correctly.** The judges were too cautious about them. The owner confirmed: the terrified, exhausted woman in the horror image, the coy look-back in the nude, the Totoro grin, the smiling game characters, and the knowing look in the de Hooch.
  - **The real mistakes were about bodies and objects:**
    - pose: a man "standing" who is seated, a monk "standing" who kneels
    - direction: "one monk gazes down"
    - parts: a face given to a headless statue
    - objects: a cannon in the Repin, a white cloth that isn't there, "stern" Santas
  - So the useful next tweak, if any, is about checking poses, positions and missing parts, not about restraining emotion.
- v5 test (2026-11-15). v5 is v2 plus one paragraph: be careful with poses and positions, say when a figure is missing a head or other parts, and mention only objects you can clearly see. Tested against v2 on the three paintings with known mistakes (the Repin, the Cole and the de Hooch on the TV), 4 finalists × 2 buttons. Claude read all 48 answers against the facts the owner confirmed.

  | Check | v2 | v5 |
  |---|---|---|
  | Cole: says the statue is headless | 2 of 8 | **6 of 8** (one of them garbled) |
  | Cole: gives the statue a head or face | 2 | 1 (Haiku Full detail: "above its head") |
  | de Hooch: man seated | 7 of 8 | 7 of 8 (Haiku Full detail says "stands" in both) |
  | Repin: cannon or siege engine | 0 | 0 |
  | New invented poses | — | 1 (GLM: an arm "raised behind his head") |

  - **v5 becomes the prompt** (`CURRENT = 'v5'`). It fixed the headless statue for most models and didn't make anything worse overall.
  - Model notes from this run:
    - **Haiku (thinking off)** made the most factual slips in Full detail. It had the man standing, called Cole's painting "the last in the series" (it's the fourth of five), put the Repin signature at lower right (it's bottom center), and gave the scribe a topknot, beard and cap. The app runs Full detail with thinking on, which scored better in run 3. Re-check this when building the describe endpoint.
    - **Haiku with thinking on**, Cole only, 3 runs of each button (v5):
      - Full detail called the statue headless in 2 of 3 runs ("a shield high above where a head would be"). Quick look never did (0 of 3), although the one thinking-off Quick look had.
      - The bigger problem is art history. In 3 of 6 answers Haiku named the painting wrongly: "The Destruction of Empire", "the final scene" of the series, and once "The Consummation of Empire, the third panel". It's "The Course of Empire: Destruction", the fourth of five. Confidently wrong facts like these are worse for a student than leaving the title out.
      - Next prompt fix to test: name a work only from a visible caption or label, or when certain; never guess a series number or other background facts.
    - **Qwen** got the headless statue in all four answers and read the TV overlays fully. But it invents text it can't really read (the Repin signature as "I. Rerikh 1879", "VANDALI" on Cole's pedestal), and in Full detail it pads with "No handwritten notes or grades are present". The Full detail prompt should say to skip text remarks when there's no text.
    - **GLM** named all three paintings. Once (v2, Quick look) it called the de Hooch "a scene from a film".
    - **Gemini** never said the statue was headless clearly, and it invents small things (a "fireplace mantel", "lightning").
- Total cost of choosing the models: about $8.45 of OpenRouter credit. That's about $1.51 for 2,150 model answers and about $6.90 for 276 judge calls.

### 2. Set up the project the way the other apps are set up
- Vite + React 19 + Tailwind 4 + TypeScript, Express `server.ts` run by `node` (no `enum` or parameter properties), vitest, and GitHub Actions CI (typecheck, test, build, smoke test).
- Add `CLAUDE.md` / `AGENTS.md`, `.env.example`, a manifest, icons and a service worker that caches the app for offline use.
- Move the Streamlit app to a `streamlit-final` tag and delete it from `main`.
- **Verify:** it installs from Chrome on a laptop and an Android phone, and opens offline.

Implementation status (2026-11-15): the step 2 foundation is built, with the Streamlit version preserved at `streamlit-final`. Typecheck, unit tests, production build, native Node import and server smoke checks pass locally. Automated desktop and Android-emulated Chrome checks pass for manifest/install eligibility, offline reload and reopening, and keeping API replies out of the cache. Installation on physical devices and screen-reader checks remain to be done by a human. See `README.md` for the commands and checklist.

### 3. Student mode
- A full-screen camera with one huge button. Vibrate when the photo is taken and when the description is ready. Speak automatically. Tap anywhere to pause or resume.
- Speed control. Repeat the last description.
- A history of recent descriptions, saved on the device (IndexedDB).
- Every control has a screen-reader label, and the app announces status changes ("Describing…", "Ready").
- **Verify:** use it with VoiceOver and TalkBack turned on, with your eyes closed. Test with no internet. Deny camera permission and check the message.

### 4. Speech chain
- Device voice, Kokoro and the chain logic first, with fake providers in unit tests. Then the Google Cloud allowance counter and Lemonfox on the server.
- **Verify:** the chain moves on when each provider fails. An allowance at 90% is skipped. A failed count read skips Google. A long job keeps one voice. Kokoro's download is interrupted and resumed.

### 5. Teacher mode
- Upload images, PDFs (pdf.js, as in OverBoard), DOCX and TXT, or type and paste.
- Quick look or Full detail, then edit the text, preview, and download the MP3. The filename comes from the source file.
- **Verify:** a 20-page PDF, a scanned PDF, a DOCX, a painting. The MP3 plays in Google Classroom on a Chromebook.

### 6. Languages and polish
- All words the user sees go in one strings file, in the same languages as OverBoard.
- Light and dark themes in the suite's style.

### 7. Device acceptance
- Android phone, an iPhone (borrowed), a school laptop. Install, use offline, use with screen readers, use all four voices.

## Privacy note for the About panel

AllHail has no accounts and keeps your history only on your device. Photos you ask it to describe are sent to an AI service through OpenRouter. Cloud voices send the text to Google or Lemonfox. Don't photograph students' faces or private documents.

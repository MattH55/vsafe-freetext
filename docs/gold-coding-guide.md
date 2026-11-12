# Gold-set coding guide

For the two gold-set coders and the adjudicator. The sheets are in `<VSAFE_DATA_DIR>/gold_set/`
(`sheet_A.csv`, `sheet_B.csv`). They contain participant free text: open them only on the
analysis machine, never copy, upload, email or paste any entry anywhere, and never put a
sheet in a synced or shared folder.

## How to code

- One row per distinct text. `field` says which survey box it came from: SD (symptom
  description), SRO (other systemic reaction), HCVO (other healthcare visit).
- For every theme the text **reports as happening to the person after vaccination**, put `1`
  in that column. Leave every other cell blank. Blank means "no".
- Code a theme even if it is mild, misspelled or in lay words. Do not code negated mentions
  ("no headache") or mentions that are only a question.
- `third_party`: `1` if the text is about someone other than the person writing (for
  example a parent reporting for a child). Still code the themes it reports.
- `pre_vaccine`: `1` if the symptom or event happened before vaccination. Still code the themes.
- `unsure`: `1` if you could not decide on at least one cell; `note`: optional, a few words
  about why. Never copy text from the entry into the note.
- Work alone. Do not discuss entries with the other coder until both sheets are loaded.
- Do not look at any classifier output while coding.

When done: `vsafe-ft gold load --coder A --path <sheet>` (and B). Then
`vsafe-ft gold agreement` and `vsafe-ft gold adjudicate`, which writes
`sheet_adjudication.csv` with disputed cells marked `?` for the adjudicator to replace with
`1` or blank; load it with `--coder adjudication`.

## Themes (taxonomy v0, prompt v0.1)

| Column | Group | Code `1` when the text reports |
|---|---|---|
| `fatigue_pem` | pacvs | fatigue, exhaustion, low energy, malaise, post-exertional crash |
| `cognitive` | pacvs | brain fog, memory problems, trouble concentrating, confusion |
| `dysautonomia` | pacvs | palpitations, racing or fast heart rate, dizziness, light-headedness, vertigo, POTS, heat intolerance |
| `sensory_neuropathic` | pacvs | tingling, numbness, pins and needles, nerve-type burning, tinnitus, blurred vision, neuropathy |
| `sleep` | pacvs | insomnia, trouble sleeping, night sweats, unrefreshing sleep |
| `pain` | pacvs | headache, migraine, muscle/joint/body aches, back/neck/limb pain, chest pain (not injection-site soreness) |
| `gastrointestinal` | pacvs | nausea, vomiting, diarrhoea, stomach or abdominal pain, bloating, constipation, appetite loss |
| `menstrual` | pacvs | menstrual period changes: heavy, early, late, missed or irregular periods, spotting |
| `persistence` | lay | the writer says a symptom has lasted weeks or months, has not gone away since vaccination, or keeps coming back; not a duration of hours or a few days |
| `care_sought` | lay | visited a doctor, urgent care, emergency room, or was hospitalised |
| `missed_work_school` | lay | missed work or school or could not work |
| `pre_existing_worsened` | lay | a pre-existing condition flared or got worse |
| `acute_diagnosis` | exclusion | a named acute diagnosis: myocarditis, pericarditis, anaphylaxis, Bell's palsy, Guillain-Barre, blood clot, stroke, heart attack, shingles, etc. |
| `unrelated_cause` | exclusion | symptoms attributed to another cause: COVID or flu infection, other infection, allergies, pregnancy, injury, accident |
| `injection_site` | acute | pain, soreness, swelling, redness or bruising at the injection site or arm |
| `lymphadenopathy` | acute | swollen lymph nodes or glands, armpit swelling |
| `upper_respiratory` | exclusion | sore throat, runny or stuffy nose, congestion, sneezing, cough |
| `fever_chills` | acute | fever, chills, hot flashes, flushing, sweating |
| `skin` | acute | rash, hives, itching |
| `taste_smell` | acute | altered or lost taste or smell, metallic taste, dry mouth |
| `cardiorespiratory` | pacvs | shortness of breath, difficulty breathing, chest tightness or pressure |
| `third_party` | flag | the text is about someone other than the writer |
| `pre_vaccine` | flag | the event happened before vaccination |

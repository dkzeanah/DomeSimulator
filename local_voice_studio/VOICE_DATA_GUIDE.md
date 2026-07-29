# Voice Data Guide

This is a practical collection plan for modeling your own teaching voice. It
is not permission to record or clone anyone else.

## Start with the smallest useful experiment

### Stage 1: local reference profile

Record 10–20 seconds of especially clean, natural speech. This is enough to
test reference-conditioned Chatterbox output without training. Use a complete
sentence with your normal pacing; avoid whispering, acting, music, room echo,
or a long opening silence.

The Voice Profile tab builds this reference from accepted clips and locks it
with a SHA-256 checksum. Generate the same evaluation paragraph after every
change so comparisons are meaningful.

### Stage 2: serious dataset

Record at least 30–60 clean minutes before attempting adaptation. A few hours
of consistent, accurately transcribed speech is a more realistic quality
target for fine-tuning. More audio does not fix inconsistent microphones,
background noise, clipping, or inaccurate words.

Capture the data in multiple short sessions, but keep these fixed:

- microphone and input mode;
- mouth-to-microphone distance;
- room and furniture;
- sample rate and channel layout;
- calm, conversational teaching delivery.

Leave 10% of the accepted clips out of training as a validation set.

## Recording setup

1. Use the quietest furnished room available. Turn off fans, televisions,
   radios, and noisy appliances.
2. Put the microphone 6–10 inches from your mouth and slightly off-axis to
   reduce plosives.
3. Record room tone for 15–30 seconds.
4. Speak naturally. Do not imitate an announcer unless that is the voice the
   model should learn.
5. Keep peaks comfortably below clipping. Aim for ordinary speech around
   -24 to -16 dBFS RMS; the app warns below -38 dBFS and near full scale.
6. Listen to several clips with headphones before committing to a long session.

Do not apply aggressive noise removal, automatic pitch correction, music,
reverb, or telephone effects. Keep the immutable originals under `raw/`.

## What to read

Use the 40 prompts included in the Record tab, then add material that matches
the finished videos:

- normal explanations and transitions;
- short and long sentences;
- questions and emphatic warnings;
- numbers, decimals, fractions, dates, and measurements;
- PVC, CAD, GPU, FFmpeg, and other acronyms;
- uncommon dome, fabrication, and geometry terms;
- several intentional pauses;
- the opening and closing style used in actual lessons.

Avoid repeating the same sentence many times. Phonetic and prosodic variety is
more useful than repetition.

## Clip and transcript rules

- Canonical audio is 24,000 Hz, mono, signed PCM-16 WAV.
- Most clips should be 2–15 seconds and contain one coherent utterance.
- The transcript must match what was actually spoken, including contractions,
  false starts you keep, and pronounced numbers.
- Reject clipped, echoing, noisy, or interrupted clips rather than trying to
  rescue everything.
- Use consistent punctuation and capitalization.
- Do not include `[music]`, timestamps, speaker names, or stage directions
  unless the selected backend explicitly requires them.

## Evaluation phrases

Always keep a fixed test set that was not used as a recording transcript:

1. “Welcome. Today we will turn a geometric idea into a practical build.”
2. “The long member is seventy-two inches, and the short member is sixty-three
   point five inches.”
3. “Why does PVC behave differently from timber at the hub?”
4. “Pause here, verify the radius, and do not cut the next piece yet.”
5. “CAD gives us a model, but a physical connector mockup confirms the fit.”

Rate every candidate from one to five for identity, naturalness, clarity, and
stability. Also listen for skipped words, repeated syllables, changed numbers,
metallic noise, and inconsistent pace.

## When to fine-tune

Fine-tune only after:

- the reference-profile baseline works but consistently misses your identity
  or cadence;
- accepted transcripts are accurate;
- validation clips are held out;
- the exact pretrained checkpoint license fits the intended use;
- there is enough GPU memory or a tested low-memory preset.

On the GTX 1660 Ti with 6 GB VRAM, local reference inference is the dependable
first step. Full modern TTS fine-tuning can exceed that memory. The program
therefore exports a reproducible F5 dataset and launches the official
fine-tuning interface rather than inventing unsupported training flags.

## Publication checklist

- Disclose that narration is synthetic when context could otherwise mislead.
- Keep the generated JSON sidecars with the master audio.
- Preserve the model watermark.
- Recheck the model/checkpoint license before monetization or commercial use.
- Never present a synthetic recording as a real statement made by another
  person.

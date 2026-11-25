# Design: "Tomorrow, Dad" (ነገ አባባ ነገ)

## The saying

> **በእጅ የያዙት ወርቅ እንደ መዳብ ይቆጠራል**
> "Gold held in the hand is counted as copper."

What we already have, we stop valuing. The film's theme: don't take the people you love, or the time you have with them, for granted.

## Audience

Close friends: people of my age, mostly busy with work and phones, whose parents are getting older.

## Intent

After watching, they should want to call someone they love tonight.

## The story

A composite story: no single real family. It is built from versions of the same situation I have heard from different people (see `ETHICS.md`).

An elderly Ethiopian **Father** prepares the coffee ceremony every morning and wants to share stories with his adult **Son**. The Son is always busy and keeps promising, "Let's talk tomorrow, Dad." One morning, while the Father is making coffee, he has a stroke. The film implies it and never shows it: the jebena tips over and coffee spills across the floor. The Son waits at the hospital, overwhelmed with fear and regret. The Father survives but comes home with lasting physical limits, and the morning ritual is no longer the same. Understanding at last what he took for granted, the Son gets up early one morning, makes two cups of coffee, puts his phone away, takes his father's hand and listens. Tomorrow is never guaranteed.

The Father is the gold. The Son counts him as copper until he nearly loses him.

## Structure

Four acts, 12 shots, 82.5 s, then the saying card (4 s) and the AI end card (3 s): 89.5 s in all. The shot lengths in Act 4 were set from the measured Amharic narration (ticket 04). The real voice is slower than planned, so two short closing lines ("Another cup of coffee." / "Another story to hear.") were cut, the narration-free "After" shots 7–8 went from 5 s to 4 s, and each Act 4 cut lands 0.3 s before its first line, with 0.5 s between lines. The storyboard (`storyboard.json`) is the source of truth for every shot.

| Act | Shots | What happens |
|---|---|---|
| Mornings | 1–4 | The coffee ceremony; the Son leaves twice: "Dad, we'll have coffee together tomorrow." / "Tomorrow, Dad." |
| The fall | 5–6 | The jebena falls; the Son alone in a hospital corridor. |
| After | 7–8 | The Father's weak hand beside a jebena he can't lift; the empty coffee corner. |
| Two cups | 9–12 | The Son makes the coffee himself, two cups, phone face-down, holds his father's hand; the closing passage. |

## Look and sound

- **Style:** warm, illustrated, painterly, soft grain. It is described by these qualities, never by a living artist's name.
- **Colour script = the saying:** Acts 1–3 use the **copper grade** (muted copper and grey-green, with only the Father's corner faintly warm: the gold is there but unseen). Act 4 uses the **gold grade**.
- **Narrator:** the older Son looking back, one voice, in Amharic, with English subtitles burned in.
- **Score:** one instrumental track in the spirit of *tizita* (krar, masenqo, soft piano). It drops to near-silence at the fall and returns for Act 4, and is ducked under the voice.

## User tests and what changed

### User test 1: radio cut (2026-11-26)

**What they saw:** `make radio-cut`: the full Amharic narration (Gemini TTS, voice Enceladus) with burned-in English subtitles and a placeholder music bed, over a black screen, 89.5 s. No pictures yet, so this tested the words, the voice and the pacing alone.

**Who:** three close friends (the target audience), shown it without any explanation first.

**What they said:**
- Friend 1: "That is deep."
- Friend 2: "I will from now on, for sure." This is the intent (they should want to call someone they love tonight) landing on sound alone.
- Friend 3: "That is the problem with this generation." The story reads as being about a shared habit, not one family, which is what the composite story aims for.
- The author: likes it.

**What changed:** nothing, as a result of this test. No one was confused or lost interest, and the intent came through. The changes in this cut were made before the test, while fitting the real narration to the timeline:
- The real Amharic voice is slower than planned. Two closing lines ("Another cup of coffee." / "Another story to hear.") were cut, and Act 4 was retimed (see Structure).
- The author rewrote three lines' Amharic to sound more like natural speech. tomorrow-1 became an invitation to coffee ("Dad, we'll have coffee together tomorrow."), which ties the Son's promise to the coffee ceremony. closing-08 became "Talk with them while they can still talk." and closing-09 became "Spend time with them while they are still beside you."

**Limits of this test:** the reactions are short and all positive, from friends. The rough-cut test (user test 2) should ask specific questions: which moment hit hardest, whether the pictures make the fall and the hospital clear without words, and whether the gold grade in Act 4 reads as the turn.

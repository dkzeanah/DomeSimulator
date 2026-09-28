# Research: what to make next, and how to make it grab people

Three pieces, one loop.

| piece | what it is | where |
|---|---|---|
| **Knowledge graph** | Every idea in this project -- 64 keywords in 10 territories, how they connect, and 195 search phrases to cycle through. Editable. | [the live page](https://claude.ai/artifact/Uo7mikiULfLudRHezZyC98) · seed in `graph_seed.py` |
| **Research engine** | Finds which topics people search for (free) and which do well on YouTube (with an API key). | `engine.py` |
| **Storycraft** | Turns a keyword into an episode plan that captures first and explains second: title options, hooks, shots, beats. | `storycraft.py`, shots in `two_v_demo/shots.py` |

## The loop

1. **Cycle the graph.** Open the page, press → to step through keywords. Each one shows its search phrases with one-click YouTube and Google searches. Add what you notice in *Notes*, set a *Status*, add keywords and connections.
2. **Run the engine** from the repository folder:

   ```bash
   py -3.12 -m research.engine all
   ```

   It writes `research/out/topics-<date>.md`: every keyword ranked, and a list of **searches the graph does not cover yet** -- the best of those are your next keywords.
3. **Plan the winners:**

   ```bash
   py -3.12 -m research.storycraft --top 10
   ```

   One plan per keyword in `research/out/plans/`.
4. **Ask Claude to sync** the scores onto the graph page (each keyword shows its score, demand, views a day and strongest video), and to pull your edits from the page back into `graph_seed.py`.

## Turning on the performance stage (views, breakouts)

The free stage uses YouTube's autocomplete: what people type. To add what they *watch* -- views a day and which small channels break out -- the engine needs a YouTube Data API key. It is free:

1. Go to [console.cloud.google.com](https://console.cloud.google.com), create a project.
2. *APIs & Services* → *Library* → enable **YouTube Data API v3**.
3. *Credentials* → *Create credentials* → *API key*. Restrict it to the YouTube Data API.
4. In PowerShell, for this session: `$env:YOUTUBE_API_KEY = "your-key"`, then run `py -3.12 -m research.engine all`.

The free quota is 10,000 units a day and one search costs 100, so a full pass over all 195 phrases takes two days; the engine caches everything and picks up where it stopped.

## How a topic is scored

`score = 100 × demand × (1 + 2 × breakout rate) / 3 × watch`

- **demand** -- distinct autocomplete searches around the phrase (out of 70 possible across seven intent variants);
- **breakout rate** -- share of the top 25 videos with at least 3× as many views as their channel has subscribers: the topic did the work, not the audience;
- **watch** -- median views a day of the top results, on a log scale.

With no API key, the score is demand alone and the report says so. Scores rank this project's topics against each other; they are not predictions.

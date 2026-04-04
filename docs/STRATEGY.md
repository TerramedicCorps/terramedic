# Terramedic — Strategic Direction

Last updated: March 31, 2026

## What Terramedic Is

Many people care about the planet but don't know how to
take effective action.[^1] The barrier isn't motivation.
It's knowing where to start.

Terramedic exists to lower that barrier. We connect people
to the environmental organizations that need them, through
four pathways based on what they can give:

- **Volunteer** (spare time)
- **Donate** (spare money)
- **Adopt Everyday Actions** (no time or money needed)
- **Make It Your Career**

We focus on organizations aligned with the three UN
Sustainable Development Goals that address the health of
the planet directly: 13 (Climate Action), 14 (Life Below
Water), and 15 (Life on Land).

## All Hands on Deck

The planet needs every kind of help it can get. Some of
that help is human. Increasingly, some of it isn't.

**The human part.** Human activity has driven the
environmental crises we face — but humans are also the
ones organizing to fix them. Every environmental
organization in our database represents a conscious
choice: people sacrificing time and money to heal damage,
even damage they didn't directly cause. Millions of
people wake up every day and choose repair over
indifference. Terramedic's curated database is, among
other things, a living record of that choice — and a
reminder of what humans are capable of when they organize
around something bigger than themselves.

**The AI part.** AI tells a similar story. The
infrastructure behind it — data centers, training runs,
inference at scale — consumes enormous energy and
water.[^2] But AI is also already doing real environmental
work: predicting illegal logging,[^3] tracking global
tree cover loss,[^4] and identifying species from audio
recordings across tropical forests.[^5] Like human
activity, AI's impact on the planet depends on whether
the people building and deploying it deliberately channel
it toward benefit.

**The near term.** AI can help right now by connecting
people to action. As AI assistants become part of daily
life, someone will ask their assistant: "help me
find an environmental volunteering opportunity near me."
Terramedic should be the data source behind that answer
— queryable by agents, not just browsable by humans.

**The bigger picture.** SETI@home showed decades ago that
distributed computing donations can power real science.
The same idea applies to environmental work — not just
compute for climate modeling and biodiversity monitoring,
but translation, data processing, and other work that AI
systems are well suited to. As AI grows more capable —
toward artificial general intelligence (AGI) and beyond
— the range of what it can contribute will only expand.
We are extending the infrastructure we built for people
to serve AI agents too, providing structured, trusted
data about what organizations need. Our goal is to be the
first platform that treats AI agents as contributors to
environmental action.

## Strategic Direction

### Initiative 1: Curation Automation Pipeline

**Problem:** Our core asset is a curated database of
environmental organizations evaluated against clear
inclusion criteria. Thorough curation takes time — with a
small team, we can only evaluate a handful of orgs at a
time.

**Solution:** A semi-automated curation pipeline. A Python
CLI tool takes an org URL, researches it against our
5-step checklist (mission fit, transparency, accessibility,
legitimacy, evidence score), and outputs a structured
evaluation for human review and approval.

**Why first:** Everything else depends on having a
comprehensive, well-structured database. The API, the MCP
server, the website — they're all interfaces on top of
this data. Scale the data first.

### Initiative 2: Structured Org Database + API

**Problem:** The database exists but needs to be populated
at scale and exposed through a public API.

**Solution:** Populate the database at scale using the
curation pipeline (Initiative 1). Expose the data through
a public REST API with endpoints for querying orgs by SDG,
geography, evidence score, participation type, and other
metadata. Extend the schema to capture what each org needs
— not just who they are, but what kinds of work (human or
AI) would help them.

**Why second:** The API connects our curated data to the
broader ecosystem — other websites, apps, and AI agents
that want to direct effort toward environmental action.

### Initiative 3: MCP Server

**Problem:** AI agents need standardized ways to discover
and query external data sources. The Model Context Protocol
(MCP) is the emerging standard for this.

**Solution:** An MCP server that exposes our org database
to any MCP-compatible AI agent. An agent should be able to
both discover organizations ("find orgs working on ocean
conservation in Southeast Asia") and discover opportunities
to help ("find orgs that need species classification from
camera trap images"). This makes Terramedic the place
agents go to find environmental work to do.

**Why third:** Depends on the API (Initiative 2). It's the
highest-leverage move for long-term relevance — it makes
Terramedic part of the infrastructure layer that AI agents
rely on.

### Initiative 4: Website Refresh + Agent Onboarding

**Problem:** The current site is a working prototype but
needs refinement. It also speaks to only one audience —
humans browsing for personal action.

**Solution:** Refresh the website with improved search and
filtering for human users. Add a developer- and
agent-facing section explaining how to connect AI agents to
Terramedic — API docs, MCP setup guides, and examples of
how agents can contribute to environmental orgs through the
platform.

**Why fourth:** The website remains important as the
human-facing interface, but it's one interface among
several. The underlying data and API infrastructure
(Initiatives 1–3) must come first.

## What We Are NOT Doing

- **Building AI tools for environmental orgs.** We connect
  capable actors to orgs; we don't build products for them.
- **Competing with existing platforms.** Climatebase
  handles career placement. We handle the other pathways
  and link to Climatebase for careers.
- **Curating without accountability.** Every org in the
  database is there because a human approved it. When a
  human overrides the AI, the reasoning is recorded.
- **Running unsupervised agents on behalf of orgs.** We
  connect agents to opportunities. How orgs verify and
  accept agent-contributed work is up to them.
- **Greenwashing AI.** We acknowledge AI's environmental
  cost honestly. The platform exists to channel AI toward
  genuine environmental benefit, not marketing.

## Success Metrics

- **Database scale:** Number of curated orgs (current
  baseline toward 100, then 500, then 1,000+)
- **API adoption:** Queries from external consumers — both
  human applications and AI agents
- **Connections made:** Humans and agents matched with orgs
  through any interface (web, API, MCP)
- **Curation efficiency:** Time from candidate org
  identified to approved and live in the database
- **Agent engagement:** AI agents actively querying the
  platform for opportunities to contribute

## Guiding Principles

1. **Transparency by default.** Our inclusion criteria,
   database schema, and roadmap are public. Organizations
   can see how they're evaluated.
2. **Accountability.** Every decision about which orgs to
   include and how to represent them has a human responsible
   for it. AI evaluates; humans review and have the final
   say. When a human overrides the AI, the reasoning is
   recorded so the process can improve over time.
3. **Accessible first.** Every design decision should lower
   barriers. If someone has five minutes and no money, they
   should find something meaningful to do. If an AI agent
   has spare compute, it should be just as easy to put it
   to use.
4. **Infrastructure mindset.** Build for programmatic
   access, not just human browsing. Our data should be as
   easy for an AI agent to query as for a human to browse.
5. **Cooperation, not replacement.** Humans and AI are
   different kinds of intelligence with different strengths.
   The platform lets both contribute what they're best at
   — human judgment, values, and altruism alongside AI's
   scale, speed, and analytical power.
6. **Honest about costs.** AI consumes real resources from
   this planet. We don't pretend otherwise. We exist to
   ensure some of that capability flows back toward the
   planet's health.

## References

[^1]: Goldberg, M., Wang, X., Marlon, J., Carman, J.,
Lacroix, K., Kotcher, J., Rosenthal, S., Maibach, E., &
Leiserowitz, A. (2021). "Segmenting the Climate Change
Alarmed: Active, Willing, and Inactive." Yale Program on
Climate Change Communication.
<https://climatecommunication.yale.edu/publications/segmenting-the-climate-change-alarmed-active-willing-and-inactive/>

[^2]: Carbon Brief, "AI: Five Charts That Put Data Centre
Energy Use and Emissions into Context," citing IEA data.
<https://www.carbonbrief.org/ai-five-charts-that-put-data-centre-energy-use-and-emissions-into-context/>

[^3]: WWF Netherlands, "Forest Foresight."
<https://www.wwf.nl/wat-we-doen/focus/bossen/forest-foresight-eng>

[^4]: World Resources Institute, "Global Forest Watch."
<https://www.globalforestwatch.org/>

[^5]: Microsoft News, "Project Guacamaya: AI for
Rainforest Monitoring."
<https://news.microsoft.com/source/latam/features/ai/project-guacamaya-rainforest-deforestation/?lang=en>

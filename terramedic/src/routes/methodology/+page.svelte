<script>
  import Footer from '$lib/components/Footer.svelte';
  import NavBar from '$lib/components/NavBar.svelte';
  import { trackSectionView } from '$lib/utils/analytics';

  export let form;
</script>

<svelte:head>
  <link rel="canonical" href="https://terramedic.org/methodology" />
  <title>Our Methodology | Terramedic</title>
  <meta
    name="description"
    content="How Terramedic selects and evaluates environmental organizations — our 6-step criteria, evidence scoring rubric, and human review process."
  />
  <meta property="og:title" content="Our Methodology | Terramedic" />
  <meta
    property="og:description"
    content="How Terramedic selects and evaluates environmental organizations — our 6-step criteria, evidence scoring rubric, and human review process."
  />
  <meta property="og:url" content="https://terramedic.org/methodology" />
  <meta name="twitter:title" content="Our Methodology | Terramedic" />
  <meta
    name="twitter:description"
    content="How Terramedic selects and evaluates environmental organizations — our 6-step criteria, evidence scoring rubric, and human review process."
  />
</svelte:head>

<div class="bg-space-black flex min-h-screen flex-col">
  <NavBar />

  <main class="flex-grow">
    <div class="container-narrow py-12">
      <h1 class="mb-6 text-center text-3xl font-bold text-white md:text-4xl lg:text-5xl">
        Our Methodology
      </h1>
      <p class="mx-auto mb-4 max-w-2xl text-center text-lg text-gray-300">
        Every organization in our database earned its place through a structured evaluation. Here's
        how it works.
      </p>
      <p class="mb-12 text-center text-sm text-gray-400">Criteria version 2026.04.6</p>

      <!-- How We Select Organizations -->
      <section
        class="bg-navy mb-10 rounded-lg p-8 shadow-sm"
        use:trackSectionView={{ section: 'selection_overview', page: 'methodology' }}
      >
        <h2 class="mb-4 text-xl font-bold text-white md:text-2xl">How We Select Organizations</h2>
        <p class="mb-4 text-gray-300">
          Terramedic connects people with environmental organizations aligned with three UN
          Sustainable Development Goals: SDG 13 (Climate Action), SDG 14 (Life Below Water), and SDG
          15 (Life on Land). We prioritize organizations where everyday people can get meaningfully
          involved — through hands-on participation, high-impact giving, learning, advocacy, or
          career development.
        </p>
        <p class="mb-4 text-gray-300">
          We evaluate every candidate organization against a consistent set of criteria before it
          enters our database. No organization is included automatically. AI assists with research,
          but humans review and approve every organization.
        </p>
        <p class="text-gray-300">
          The key question is: does this organization offer something people can't easily find on
          their own? Focused conservation groups, regional volunteer networks, niche career
          platforms, and research groups producing guides for advocates all belong. Globally
          recognized NGOs that everyone already knows about do not — we focus on organizations that
          are underserved by visibility.
        </p>
      </section>

      <!-- Nomination Categories -->
      <section
        class="bg-navy mb-10 rounded-lg p-8 shadow-sm"
        use:trackSectionView={{ section: 'nomination_categories', page: 'methodology' }}
      >
        <h2 class="mb-6 text-xl font-bold text-white md:text-2xl">Nomination Categories</h2>
        <p class="mb-6 text-gray-300">
          Each organization is evaluated for fit in one or more of these categories, based on the
          engagement pathways it offers:
        </p>

        <div class="space-y-6">
          <div class="border-terra-green border-l-4 pl-5">
            <h3 class="mb-1 text-lg font-bold text-white">Volunteer</h3>
            <p class="text-gray-300">
              Direct, hands-on engagement people can show up to — volunteer shifts, canvassing,
              community organizing, restoration work, citizen science, local chapter meetings, or
              civic engagement like voter mobilization and testimony at public hearings.
            </p>
          </div>

          <div class="border-terra-green border-l-4 pl-5">
            <h3 class="mb-1 text-lg font-bold text-white">Donate</h3>
            <p class="text-gray-300">
              Organizations where donations create outsized impact through a specific, accountable
              model — not just a generic donate button. We look for a clear theory of change with
              measurable outcomes, like funding community rangers or supporting targeted campaigns.
            </p>
          </div>

          <div class="border-terra-green border-l-4 pl-5">
            <h3 class="mb-1 text-lg font-bold text-white">Everyday</h3>
            <p class="text-gray-300">
              Organizations that help people take everyday actions — small, practical steps that fit
              into daily life, requiring little or no spare time or money. Guides to reducing
              personal environmental impact, carbon footprint calculators, or community action
              checklists.
            </p>
          </div>

          <div class="border-terra-green border-l-4 pl-5">
            <h3 class="mb-1 text-lg font-bold text-white">Resource</h3>
            <p class="text-gray-300">
              Organizations that produce tools, research, or educational content that help people
              take informed action — advocate resources, messaging guides, data visualizations, or
              solutions journalism.
            </p>
          </div>

          <div class="border-terra-green border-l-4 pl-5">
            <h3 class="mb-1 text-lg font-bold text-white">Career</h3>
            <p class="text-gray-300">
              Organizations that help people find or transition into environmental work — job
              boards, professional development, training programs, or community networks for
              environmental professionals.
            </p>
          </div>
        </div>
      </section>

      <!-- 6-Step Evaluation Criteria -->
      <section
        class="bg-navy mb-10 rounded-lg p-8 shadow-sm"
        use:trackSectionView={{ section: 'evaluation_criteria', page: 'methodology' }}
      >
        <h2 class="mb-6 text-xl font-bold text-white md:text-2xl">6-Step Evaluation Criteria</h2>
        <p class="mb-6 text-gray-300">
          Each candidate organization is assessed on six dimensions, in order. If an organization
          fails Step 1 (no SDG alignment), the evaluation stops there.
        </p>

        <div class="space-y-6">
          <div class="border-terra-green border-l-4 pl-5">
            <h3 class="mb-1 text-lg font-bold text-white">1. Mission Fit</h3>
            <p class="text-gray-300">
              Does the organization's work align with UN Sustainable Development Goals 13 (Climate
              Action), 14 (Life Below Water), or 15 (Life on Land)? We look for specific programs or
              initiatives as evidence. If no alignment is found, the organization is not included.
            </p>
          </div>

          <div class="border-terra-green border-l-4 pl-5">
            <h3 class="mb-1 text-lg font-bold text-white">2. Category Fit</h3>
            <p class="text-gray-300">
              This is the most important criterion after mission fit. Which nomination categories
              does the organization fit? For each category assigned, we identify the specific
              engagement pathway that earns it. Engagement pathways are often buried in subpages or
              event calendars — we look beyond the homepage.
            </p>
          </div>

          <div class="border-terra-green border-l-4 pl-5">
            <h3 class="mb-1 text-lg font-bold text-white">3. Local Relevance</h3>
            <p class="text-gray-300">
              Does the organization operate in specific geographies? Does it have local chapters,
              region-specific programs, or location-based matching? Organizations with local
              presence are strongly preferred because Terramedic matches users to organizations by
              location.
            </p>
          </div>

          <div class="border-terra-green border-l-4 pl-5">
            <h3 class="mb-1 text-lg font-bold text-white">4. Transparency</h3>
            <p class="text-gray-300">
              Does the organization clearly describe its programs, name its leadership, and provide
              financial disclosures? We look for annual reports, tax filings (990s for US
              nonprofits), audited statements, and third-party ratings from services like Charity
              Navigator.
            </p>
          </div>

          <div class="border-terra-green border-l-4 pl-5">
            <h3 class="mb-1 text-lg font-bold text-white">5. Legitimacy</h3>
            <p class="text-gray-300">
              Is the organization legally registered (e.g., 501(c)(3), registered charity, NGO)? How
              long has it been operating? Are there third-party references such as news coverage,
              Charity Navigator ratings, GuideStar/Candid profiles, or partner mentions?
            </p>
          </div>

          <div class="border-terra-green border-l-4 pl-5">
            <h3 class="mb-1 text-lg font-bold text-white">6. Evidence Score</h3>
            <p class="text-gray-300">
              How strong is the evidence that this organization delivers real environmental
              outcomes? Each organization receives a score from 0 to 5 using the rubric below.
            </p>
          </div>
        </div>
      </section>

      <!-- Evidence Scoring Rubric -->
      <section
        class="bg-navy mb-10 rounded-lg p-8 shadow-sm"
        use:trackSectionView={{ section: 'evidence_rubric', page: 'methodology' }}
      >
        <h2 class="mb-6 text-xl font-bold text-white md:text-2xl">Evidence Scoring Rubric</h2>
        <p class="mb-6 text-gray-300">
          The evidence score reflects the strength and quality of available evidence for an
          organization's environmental impact.
        </p>

        <div class="overflow-x-auto">
          <table class="w-full text-left text-sm">
            <thead>
              <tr class="border-b border-gray-700">
                <th class="px-4 py-3 font-bold text-gray-400">Score</th>
                <th class="px-4 py-3 font-bold text-gray-400">Level</th>
                <th class="px-4 py-3 font-bold text-gray-400">Description</th>
              </tr>
            </thead>
            <tbody class="text-gray-300">
              <tr class="border-b border-gray-700/50">
                <td class="px-4 py-3 font-bold text-white">0</td>
                <td class="px-4 py-3">No evidence</td>
                <td class="px-4 py-3">No evidence of real work.</td>
              </tr>
              <tr class="border-b border-gray-700/50">
                <td class="px-4 py-3 font-bold text-white">1</td>
                <td class="px-4 py-3">Minimal</td>
                <td class="px-4 py-3">Website exists but little else.</td>
              </tr>
              <tr class="border-b border-gray-700/50">
                <td class="px-4 py-3 font-bold text-white">2</td>
                <td class="px-4 py-3">Some evidence</td>
                <td class="px-4 py-3">A few programs described, limited external references.</td>
              </tr>
              <tr class="border-b border-gray-700/50">
                <td class="px-4 py-3 font-bold text-white">3</td>
                <td class="px-4 py-3">Moderate</td>
                <td class="px-4 py-3">Clear programs, some third-party validation.</td>
              </tr>
              <tr class="border-b border-gray-700/50">
                <td class="px-4 py-3 font-bold text-white">4</td>
                <td class="px-4 py-3">Strong</td>
                <td class="px-4 py-3"
                  >Detailed programs, financials, media coverage, clear engagement pathways.</td
                >
              </tr>
              <tr>
                <td class="px-4 py-3 font-bold text-white">5</td>
                <td class="px-4 py-3">Exceptional</td>
                <td class="px-4 py-3"
                  >Strong track record, clear local impact, well-documented engagement outcomes.</td
                >
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- Human + AI Process -->
      <section
        class="bg-navy mb-10 rounded-lg p-8 shadow-sm"
        use:trackSectionView={{ section: 'human_ai_process', page: 'methodology' }}
      >
        <h2 class="mb-4 text-xl font-bold text-white md:text-2xl">Human Review, AI-Assisted</h2>
        <p class="mb-4 text-gray-300">
          AI assists with initial research — gathering public data, checking third-party ratings,
          and drafting preliminary evaluations. But humans review and approve every organization
          before it enters our database.
        </p>
        <p class="mb-4 text-gray-300">
          When a human reviewer disagrees with an AI assessment, they record the reasoning so the
          process improves over time. This isn't automation replacing judgment — it's technology
          helping a small team evaluate more organizations without cutting corners.
        </p>
        <p class="text-gray-300">
          Our inclusion criteria, evaluation process, and database are public. Organizations can see
          exactly how they're assessed.
        </p>
      </section>

      <!-- Suggest an Organization -->
      <section
        class="bg-navy mb-10 rounded-lg p-8 shadow-sm"
        use:trackSectionView={{ section: 'suggest_org', page: 'methodology' }}
      >
        <h2 class="mb-4 text-xl font-bold text-white md:text-2xl">Suggest an Organization</h2>
        <p class="mb-4 text-gray-300">
          Know an environmental organization that should be in our database? We welcome suggestions
          from anyone. Every suggestion goes through the same evaluation process described above.
        </p>
        <p>
          <a href="/nominate" class="text-terra-green hover:underline">
            Nominate an organization
          </a>
        </p>
      </section>
    </div>
  </main>

  <Footer {form} />
</div>

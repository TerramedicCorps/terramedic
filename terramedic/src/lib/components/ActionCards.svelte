<script>
  import { ICON_PATHS } from '$lib/icons';
</script>

<div class="primary-cards">
  <a href="/volunteer" class="card-link">
    <div class="card blue">
      <div class="card-accent"></div>
      <div class="card-icon blue-icon">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke-width="1.5"
          stroke="currentColor"
          class="icon"
        >
          <path stroke-linecap="round" stroke-linejoin="round" d={ICON_PATHS.clock} />
        </svg>
      </div>
      <h3 class="card-title">Have time to&nbsp;spare?</h3>
      <p class="card-description">
        Volunteer with organizations that need your skills and passion to build a healthier planet.
      </p>
      <span class="card-action blue-action">Find opportunities &rarr;</span>
    </div>
  </a>
  <a href="/donate" class="card-link">
    <div class="card green">
      <div class="card-accent"></div>
      <div class="card-icon green-icon">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke-width="1.5"
          stroke="currentColor"
          class="icon"
        >
          <path stroke-linecap="round" stroke-linejoin="round" d={ICON_PATHS.banknotes} />
        </svg>
      </div>
      <h3 class="card-title">Have money to&nbsp;spare?</h3>
      <p class="card-description">
        Put your money to work by supporting the organizations, campaigns, and causes driving real
        change.
      </p>
      <span class="card-action green-action">See where to give &rarr;</span>
    </div>
  </a>
  <a href="/other-actions" class="card-link">
    <div class="card purple">
      <div class="card-accent"></div>
      <div class="card-icon purple-icon">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke-width="1.5"
          stroke="currentColor"
          class="icon"
        >
          <path stroke-linecap="round" stroke-linejoin="round" d={ICON_PATHS.bolt} />
        </svg>
      </div>
      <h3 class="card-title">No&nbsp;time? No&nbsp;money?</h3>
      <p class="card-description">
        We know the feeling! Act every day with small choices that add up to meaningful impact over
        time.
      </p>
      <span class="card-action purple-action">Start with one action &rarr;</span>
    </div>
  </a>
</div>

<div class="divider"></div>

<p class="section-label">Go further</p>

<div class="secondary-cards">
  <a href="/resources" class="card-link">
    <div class="card teal">
      <div class="card-accent"></div>
      <div class="card-icon teal-icon">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke-width="1.5"
          stroke="currentColor"
          class="icon"
        >
          <path stroke-linecap="round" stroke-linejoin="round" d={ICON_PATHS.bookOpen} />
        </svg>
      </div>
      <h3 class="card-title">Already&nbsp;helping?</h3>
      <p class="card-description">
        Tools, research, and support for those already engaged in advocacy work.
      </p>
      <span class="card-action teal-action">Find resources &rarr;</span>
    </div>
  </a>
  <a href="/careers" class="card-link">
    <div class="card gold">
      <div class="card-accent"></div>
      <div class="card-icon gold-icon">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke-width="1.5"
          stroke="currentColor"
          class="icon"
        >
          <path stroke-linecap="round" stroke-linejoin="round" d={ICON_PATHS.briefcase} />
        </svg>
      </div>
      <h3 class="card-title">Ready to go&nbsp;pro?</h3>
      <p class="card-description">
        Find your next role at organizations working to build a healthier world.
      </p>
      <span class="card-action gold-action">Browse job boards &rarr;</span>
    </div>
  </a>
</div>

<style>
  .primary-cards,
  .secondary-cards {
    display: grid;
    grid-template-columns: 1fr;
    gap: 1.5rem;
    max-width: 1000px;
    margin: 0 auto;
    padding: 0 1rem;
  }

  .section-label {
    text-align: center;
    color: rgba(255, 255, 255, 0.5);
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin: 0;
  }

  .divider {
    max-width: 1000px;
    margin: 2rem auto 0.75rem;
    padding: 0 1rem;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
  }

  .secondary-cards {
    margin-top: 0.75rem;
  }

  .card-link {
    text-decoration: none;
    display: flex;
  }

  .card {
    position: relative;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding: 2rem;
    border-radius: 16px;
    color: white;
    cursor: pointer;
    transition: all 0.3s ease;
    background-color: var(--color-navy);
    border: 1px solid rgba(255, 255, 255, 0.06);
  }

  .card-accent {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    border-radius: 16px 16px 0 0;
  }

  .blue .card-accent {
    background: var(--color-terra-blue);
  }

  .green .card-accent {
    background: var(--color-terra-green);
  }

  .purple .card-accent {
    background: var(--color-btn-purple);
  }

  .teal .card-accent {
    background: #0ea5a8;
  }

  .gold .card-accent {
    background: #d4a017;
  }

  .card-icon {
    width: 56px;
    height: 56px;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 1.25rem;
  }

  .blue-icon {
    background: rgba(33, 150, 243, 0.15);
  }

  .green-icon {
    background: rgba(46, 204, 113, 0.15);
  }

  .purple-icon {
    background: rgba(124, 58, 237, 0.15);
  }

  .teal-icon {
    background: rgba(14, 165, 168, 0.15);
  }

  .gold-icon {
    background: rgba(212, 160, 23, 0.15);
  }

  .icon {
    width: 28px;
    height: 28px;
  }

  .card-title {
    font-size: 1.15rem;
    font-weight: 700;
    margin-bottom: 0.75rem;
    line-height: 1.3;
  }

  .card-description {
    color: var(--color-text-secondary);
    font-size: 0.9rem;
    line-height: 1.6;
    margin-bottom: 1.25rem;
  }

  .card-action {
    font-weight: 600;
    font-size: 0.9rem;
    margin-top: auto;
  }

  .blue-action {
    color: var(--color-terra-blue);
  }

  .green-action {
    color: var(--color-terra-green);
  }

  .purple-action {
    color: var(--color-btn-purple);
  }

  .teal-action {
    color: #0ea5a8;
  }

  .gold-action {
    color: #d4a017;
  }

  .card:hover {
    transform: translateY(-4px);
    border-color: rgba(255, 255, 255, 0.12);
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
  }

  @media (min-width: 768px) {
    .primary-cards {
      grid-template-columns: repeat(3, 1fr);
    }

    .secondary-cards {
      grid-template-columns: repeat(2, 1fr);
    }
  }
</style>

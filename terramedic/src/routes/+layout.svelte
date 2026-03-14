<script>
  import '../app.css';
  import { page } from '$app/stores';
  import { initAnalytics, initPageTracking } from '$lib/utils/analytics';

  // Load Google Analytics script and initialize tracking
  initAnalytics();
  initPageTracking(page);
</script>

<slot />

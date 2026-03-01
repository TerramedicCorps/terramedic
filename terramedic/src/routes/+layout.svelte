<script>
  import '../app.css';
  import { page } from '$app/stores';
  import { initPageTracking } from '$lib/utils/analytics';

  // Initialize Google Analytics tracking
  initPageTracking(page);
</script>

<slot />

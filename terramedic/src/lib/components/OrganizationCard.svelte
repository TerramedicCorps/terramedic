<script>
  import { Card, Button } from 'flowbite-svelte';
  import { DEFAULT_ORG_ACTION_TEXT } from '$lib/components/organizationGrid.styles';
  import { trackEvent } from '$lib/utils/analytics';

  export let name = '';
  export let description = '';
  export let websiteUrl = '';
  export let actionUrl = '';
  export let imageUrl = '';
  export let actionText = DEFAULT_ORG_ACTION_TEXT;
  /** @type {string[]} */
  export let tags = [];
  export let tagColor = 'blue'; // 'blue', 'green', 'gold', 'purple', 'orange', 'red', 'gray'
  export let buttonColor = 'blue'; // 'blue', 'green', 'gold', 'purple'

  // Map tag colors to dark theme values
  /** @type {Record<string, { bg: string; text: string; hover: string }>} */
  const tagColorMap = {
    blue: { bg: 'bg-blue-900/60', text: 'text-blue-400', hover: 'hover:bg-blue-900/70' },
    green: { bg: 'bg-green-900/60', text: 'text-green-400', hover: 'hover:bg-green-900/70' },
    gold: { bg: 'bg-amber-900/60', text: 'text-amber-400', hover: 'hover:bg-amber-900/70' },
    purple: { bg: 'bg-purple-900/60', text: 'text-purple-400', hover: 'hover:bg-purple-900/70' },
    orange: { bg: 'bg-orange-900/60', text: 'text-orange-400', hover: 'hover:bg-orange-900/70' },
    red: { bg: 'bg-red-900/60', text: 'text-red-400', hover: 'hover:bg-red-900/70' },
    gray: { bg: 'bg-gray-800/60', text: 'text-gray-400', hover: 'hover:bg-gray-800/70' }
  };

  // Default to blue if no valid color is provided
  $: tagStyle = tagColorMap[tagColor] || tagColorMap.blue;

  // Map button colors to brand styles
  /** @type {Record<string, { bg: string; hover: string; text: string }>} */
  const buttonStyleMap = {
    blue: {
      bg: 'background-color: var(--btn-blue)',
      hover: 'org-btn-blue',
      text: 'text-white'
    },
    green: {
      bg: 'background-color: var(--btn-green)',
      hover: 'org-btn-green',
      text: 'text-white'
    },
    gold: {
      bg: 'background-color: var(--btn-gold)',
      hover: 'org-btn-gold',
      text: 'text-white'
    },
    purple: {
      bg: 'background-color: var(--btn-purple)',
      hover: 'org-btn-purple',
      text: 'text-white'
    }
  };

  $: btnStyle = buttonStyleMap[buttonColor] || buttonStyleMap.blue;

  /** @param {string} hostname */
  function normalizedHostname(hostname) {
    return hostname
      .toLowerCase()
      .replace(/\.$/, '')
      .replace(/^www\./, '');
  }

  // Client-side mirror of backend/terramedic/core/web_urls.py
  // (web_hostname / is_safe_web_url). This is a deliberately-approximate
  // defense-in-depth layer, NOT the authority — the serializer sanitizes
  // action_url server-side, but returns website_url raw, so this is the
  // last check on that field. The reserved-IPv4 ranges below match what
  // Python's ipaddress.is_global rejects; keep the two in sync when
  // either changes.
  /** @param {string} hostname */
  function isLocalHostname(hostname) {
    const host = hostname.replace(/^\[|\]$/g, '').toLowerCase();
    if (
      host === 'localhost' ||
      (!host.includes('.') && !host.includes(':')) ||
      /\.(example|home|internal|invalid|lan|local|localhost|test)$/.test(host) ||
      host === '::' ||
      host === '::1' ||
      /^(fc|fd|fe8|fe9|fea|feb)/.test(host)
    ) {
      return true;
    }
    const octets = host.split('.').map(Number);
    if (octets.length !== 4 || octets.some((part) => !Number.isInteger(part))) return false;
    const [first, second, third] = octets;
    return (
      first === 0 || // 0.0.0.0/8 "this network"
      first === 10 || // 10.0.0.0/8 private
      first === 127 || // 127.0.0.0/8 loopback
      (first === 100 && second >= 64 && second <= 127) || // 100.64.0.0/10 CGNAT
      (first === 169 && second === 254) || // 169.254.0.0/16 link-local
      (first === 172 && second >= 16 && second <= 31) || // 172.16.0.0/12 private
      (first === 192 && second === 0 && third === 0) || // 192.0.0.0/24 IETF protocol
      (first === 192 && second === 0 && third === 2) || // 192.0.2.0/24 TEST-NET-1
      (first === 192 && second === 168) || // 192.168.0.0/16 private
      (first === 198 && (second === 18 || second === 19)) || // 198.18.0.0/15 benchmark
      (first === 198 && second === 51 && third === 100) || // 198.51.100.0/24 TEST-NET-2
      (first === 203 && second === 0 && third === 113) || // 203.0.113.0/24 TEST-NET-3
      first >= 224 // 224.0.0.0/4 multicast + 240.0.0.0/4 reserved
    );
  }

  // Mirror of web_urls._is_dns_hostname: reject STD3-invalid labels
  // (underscores, edge hyphens) and all-numeric TLDs that `new URL`
  // tolerates but the backend rejects. IP hosts are already canonicalized
  // by `new URL` (127.1 -> 127.0.0.1) and screened by isLocalHostname, so
  // they skip the label check.
  const dnsLabel = /^(?!-)[a-z0-9-]{1,63}(?<!-)$/;
  /** @param {string} hostname */
  function isValidWebHost(hostname) {
    const host = hostname.replace(/^\[|\]$/g, '').toLowerCase();
    if (host.includes(':') || /^\d{1,3}(\.\d{1,3}){3}$/.test(host)) return true;
    const labels = host.split('.');
    if (labels.length < 2 || /^\d+$/.test(labels[labels.length - 1])) return false;
    return labels.every((label) => dnsLabel.test(label));
  }

  /** @param {string} value */
  function parsedSafeWebUrl(value) {
    try {
      const parsed = new URL(value);
      if (
        !['http:', 'https:'].includes(parsed.protocol) ||
        parsed.username ||
        parsed.password ||
        isLocalHostname(parsed.hostname) ||
        !isValidWebHost(parsed.hostname)
      ) {
        return null;
      }
      return parsed;
    } catch {
      return null;
    }
  }

  /** @param {string} value */
  function safeWebUrl(value) {
    return parsedSafeWebUrl(value) ? value : '';
  }

  /**
   * @param {string} value
   * @param {string} siteUrl
   */
  function safeActionUrl(value, siteUrl) {
    const parsed = parsedSafeWebUrl(value);
    const site = parsedSafeWebUrl(siteUrl);
    if (!parsed || !site) return '';
    const candidateHost = normalizedHostname(parsed.hostname);
    const siteHost = normalizedHostname(site.hostname);
    return candidateHost === siteHost || candidateHost.endsWith(`.${siteHost}`) ? value : '';
  }

  // The CTA deep-links to the per-pathway action_url (volunteer
  // signup, jobs board); unfiltered/nearby contexts return "" so the
  // card falls back to the org's website. Svelte prop defaults only
  // fire on undefined, not "", so the fallback has to be explicit.
  $: linkUrl = safeActionUrl(actionUrl, websiteUrl) || safeWebUrl(websiteUrl);

  // Handle button click for analytics tracking
  function handleButtonClick() {
    trackEvent('organization_click', {
      organization_name: name,
      organization_url: websiteUrl,
      action_url: linkUrl,
      button_text: actionText,
      categories: tags.join(',')
    });
  }
</script>

<Card
  img=""
  class="!bg-navy h-full !max-w-none border border-white/10 p-5 transition-all duration-300 hover:shadow-lg"
>
  <h3 class="mb-2 text-xl font-bold tracking-tight text-white">{name}</h3>

  {#if tags.length > 0}
    <div class="mb-3 flex flex-wrap gap-1.5">
      {#each tags as tag (tag)}
        <span
          class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium {tagStyle.bg} {tagStyle.text} {tagStyle.hover} transition-colors duration-200"
        >
          {tag}
        </span>
      {/each}
    </div>
  {/if}

  <p class="mb-5 text-gray-400">{description}</p>

  <div class="mt-auto">
    <Button
      href={linkUrl}
      target="_blank"
      rel="noopener noreferrer"
      style={btnStyle.bg}
      class="w-full {btnStyle.text} {btnStyle.hover} shadow-sm transition-all duration-200 hover:shadow"
      onclick={handleButtonClick}
    >
      {actionText}
    </Button>
  </div>
</Card>

<style>
  :global(.org-btn-blue:hover) {
    background-color: var(--btn-blue-hover) !important;
  }

  :global(.org-btn-green:hover) {
    background-color: var(--btn-green-hover) !important;
  }

  :global(.org-btn-gold:hover) {
    background-color: var(--btn-gold-hover) !important;
  }

  :global(.org-btn-purple:hover) {
    background-color: var(--btn-purple-hover) !important;
  }
</style>

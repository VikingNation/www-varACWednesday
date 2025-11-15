var klaroConfig = {
  version: 1,
  privacyPolicy: '/privacy.html',
  elementID: 'klaro',
  styling: {
    theme: ['light', 'bottom']
  },
  translations: {
    en: {
      consentModal: {
        title: 'Privacy Settings',
        description: 'Here you can decide which cookies we may use.'
      },
      acceptAll: 'Accept all',
      acceptSelected: 'Accept selected',
      decline: 'Decline'
    },
    youtube: {
      description: 'Embedded YouTube videos'
    },
    googlemaps: {
      description: 'Embedded Google Maps'
    },
    googleanalytics: {
      description: 'Anonymous usage statistics via Google Analytics'
    }
  },
  services: [
    {
      name: 'google-analytics',
      purposes: ['analytics'],
      cookies: [/^_ga/, /^_gid/, /^_gat/],
      required: false
    },
    {
      name: 'google-marketing',
      purposes: ['marketing'],
      cookies: [/^NID$/],   // explicitly target Google’s NID cookie
      required: false,      // must be opt-in, not required
      optOut: false,        // GDPR requires opt-in, not opt-out
      onlyOnce: true        // ensures script runs only once after consent
    },
    {
      name: 'youtube',
      purposes: ['video'],
      cookies: [],
      contextualConsentOnly: true,
      onlyOnce: true
    }
  ]
};

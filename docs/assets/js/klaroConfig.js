var klaroConfig = {
  version: 1,
  privacyPolicy: '/privacy.html', 
  elementID: 'klaro',
  styling: {
    theme: ['light', 'bottom'],
  },
  translations: {
    en: {
      consentModal: {
        title: 'Privacy Settings',
        description: 'Here you can decide which cookies we may use.'
      },
      acceptAll: 'Accept all',
      acceptSelected: 'Accept selected',
      decline: 'Decline',
    }
  },
  services: [
    {
      name: 'google-analytics',
      purposes: ['analytics'],
      cookies: [/^_ga/, /^_gid/],
      required: false,
    },
  ]
};


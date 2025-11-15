var klaroConfig = {
  version: 1,
  privacyPolicy: '/privacy.html',
  elementID: 'klaro',
  styling: {
    theme: ['light', 'bottom']
  },
  cookieExpiresAfterDays: 365,
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
        name: 'site_essentials',
        title: 'Site Essentials & Functionality',
        purposes: ['required'], // <-- Links this service to the mandatory 'required' purpose

        // This array documents the cookies set by this service
        cookies: [
            // The Klaro consent cookie itself (Crucial to include!)
            {
                pattern: /klaro/i,
                path: '/',
                // Klaro often uses the current domain by default
                expiration: '365 Days',
                service_name: 'site_essentials',
            }
        ],

        description: 'Enables core functionality such as user sessions, login state, and storing your consent preferences.',

        // Since it's required, optOut and onlyOnce are often set to true for safety
        default : true,
        optOut: true,
        onlyOnce: true,
    },



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
      purposes: ['video', 'external_media'],
      cookies: [],
      contextualConsentOnly: true,
      description: 'We use YouTube to host videos and cookies are used to track information on videos being watched',
      onlyOnce: true
    },
    {
        name: 'google-maps',
        title: 'Google Maps',
        purposes: ['external_media'], 
        
        // Set this to true to enable the content block/wrapper
        contextualConsentOnly: true, 
        
        description: 'We use Google Maps to display user check-in information, which requires loading external content and may set cookies for functionality and data analysis.',
    }   
  ]
};

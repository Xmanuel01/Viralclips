export default function Head() {
  return (
    <>
      {/* Additional favicon links for better browser support */}
      <link rel="icon" type="image/x-icon" href="/favicon.ico" />
      <link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png" />
      <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png" />
      <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png" />
      
      {/* Web App Manifest */}
      <link rel="manifest" href="/site.webmanifest" />
      
      {/* Theme colors for mobile browsers */}
      <meta name="theme-color" content="#7c3aed" />
      <meta name="msapplication-TileColor" content="#7c3aed" />
      <meta name="msapplication-config" content="/browserconfig.xml" />
      
      {/* Additional SEO meta tags */}
      <meta name="robots" content="index, follow" />
      <meta name="googlebot" content="index, follow" />
      <meta name="google" content="nositelinkssearchbox" />
      <meta name="google" content="notranslate" />
      
      {/* Preconnect to external domains for performance */}
      <link rel="preconnect" href="https://sukilozaqduurpecwoet.supabase.co" />
      <link rel="preconnect" href="https://fonts.googleapis.com" />
      <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
    </>
  )
}

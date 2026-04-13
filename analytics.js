const GOOGLE_ANALYTICS_ID = "G-05ZS1PYQ32";

if (GOOGLE_ANALYTICS_ID) {
  const googleTagScript = document.createElement("script");
  googleTagScript.async = true;
  googleTagScript.src = `https://www.googletagmanager.com/gtag/js?id=${GOOGLE_ANALYTICS_ID}`;
  document.head.appendChild(googleTagScript);

  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag("js", new Date());
  gtag("config", GOOGLE_ANALYTICS_ID);
}

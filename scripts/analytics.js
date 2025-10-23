
window.ANALYTICS_CONFIG={GA4_MEASUREMENT_ID:"G-45PBWBK7KR",GTM_CONTAINER_ID:"GTM-K58Z4XD",FB_PIXEL_ID:""};
(function(){
  const C=window.ANALYTICS_CONFIG||{};
  if(C.GTM_CONTAINER_ID){
    (function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':new Date().getTime(),event:'gtm.js'});
    var f=d.getElementsByTagName(s)[0],j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;
    j.src='https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);})(window,document,'script','dataLayer',C.GTM_CONTAINER_ID);
  }
  if(C.GA4_MEASUREMENT_ID && !C.GTM_CONTAINER_ID){
    var s=document.createElement('script');s.async=true;s.src='https://www.googletagmanager.com/gtag/js?id='+C.GA4_MEASUREMENT_ID;document.head.appendChild(s);
    window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config',C.GA4_MEASUREMENT_ID);
  }
  if(C.FB_PIXEL_ID){
    !function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?
    n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;n.push=n;
    n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;t.src=v;
    s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');
    fbq('init',C.FB_PIXEL_ID);fbq('track','PageView');
  }
})();
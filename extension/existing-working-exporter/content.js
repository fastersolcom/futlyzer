
(() => {
  const s=document.createElement("script");
  s.src=chrome.runtime.getURL("page-hook.js");
  s.onload=()=>s.remove();
  (document.head||document.documentElement).appendChild(s);

  window.addEventListener("message",e=>{
    if(e.source!==window || e.origin!==location.origin) return;
    const d=e.data;
    if(!d || d.source!=="FC27_CLUB_EXPORTER_V04") return;
    chrome.runtime.sendMessage({
      type:"CAPTURE", kind:d.kind, url:d.url,
      tacticParam:d.tacticParam, payload:d.payload
    });
  });
})();

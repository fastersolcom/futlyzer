
(() => {
  if (window.__FC27_EXPORTER_V04__) return;
  window.__FC27_EXPORTER_V04__ = true;

  const classify = raw => {
    try {
      const u = new URL(raw, location.href);
      if (!u.hostname.endsWith("fut.gg")) return null;

      if (/\/api\/gg-club\/players\/?$/.test(u.pathname) &&
          u.searchParams.get("game") === "27" &&
          !u.searchParams.has("gg_club_player_ids")) return "players";

      if (/\/api\/.*\/\d+-\d+\/?$/.test(u.pathname)) return "squad";

      if (/\/export-code\/?$/.test(u.pathname) && u.searchParams.has("tactic"))
        return "tactic";

      return null;
    } catch (_) { return null; }
  };

  const emit = (kind, rawUrl, responseText=null) => {
    try {
      const u = new URL(rawUrl, location.href);
      let payload = null;
      if (responseText) { try { payload = JSON.parse(responseText); } catch (_) {} }
      window.postMessage({
        source:"FC27_CLUB_EXPORTER_V04",
        kind, url:u.href,
        tacticParam: kind === "tactic" ? u.searchParams.get("tactic") : null,
        payload
      }, location.origin);
    } catch (_) {}
  };

  const ofetch = window.fetch;
  window.fetch = async function(...args) {
    const raw = typeof args[0] === "string" ? args[0] : args[0]?.url;
    const kind = raw ? classify(raw) : null;
    const resp = await ofetch.apply(this,args);
    if (kind) resp.clone().text().then(t=>emit(kind,raw,t)).catch(()=>emit(kind,raw,null));
    return resp;
  };

  const X = window.XMLHttpRequest, oopen=X.prototype.open, osend=X.prototype.send;
  X.prototype.open=function(method,url,...rest){
    this.__fc27_url=url; this.__fc27_kind=classify(url);
    return oopen.call(this,method,url,...rest);
  };
  X.prototype.send=function(...args){
    if(this.__fc27_kind) this.addEventListener("load",()=>{
      let t=null; try{if(typeof this.responseText==="string")t=this.responseText}catch(_){}
      emit(this.__fc27_kind,this.__fc27_url,t);
    });
    return osend.apply(this,args);
  };
})();

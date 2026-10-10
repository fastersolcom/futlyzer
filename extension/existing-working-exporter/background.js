
const playerPages=new Map();
let activeSquad=null, activeTactic=null;

function arr(p){
  if(Array.isArray(p)) return p;
  if(Array.isArray(p?.data)) return p.data;
  if(Array.isArray(p?.data?.data)) return p.data.data;
  if(Array.isArray(p?.results)) return p.results;
  return [];
}
function pageNo(url){try{return Number(new URL(url).searchParams.get("page")||"1")}catch(_){return 1}}
function decodeTactic(s){
  try{
    let x=s.replace(/-/g,"+").replace(/_/g,"/");
    while(x.length%4)x+="=";
    const bin=atob(x), bytes=Uint8Array.from(bin,c=>c.charCodeAt(0));
    return JSON.parse(new TextDecoder().decode(bytes));
  }catch(e){return {decodeError:String(e),raw:s}}
}
function squadBody(p){return p?.data?.data || p?.data || null}
function pad(n){return String(n).padStart(2,"0")}
function safeName(s){
  return String(s||"squad").trim().replace(/[<>:"/\\|?*\x00-\x1F]/g,"-").replace(/\s+/g,"_").slice(0,45) || "squad";
}
function filename(){
  const d=new Date();
  const stamp=`${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}_${pad(d.getHours())}-${pad(d.getMinutes())}-${pad(d.getSeconds())}`;
  const title=safeName(squadBody(activeSquad?.payload)?.title);
  return `FC27_${title}_${stamp}.json`;
}

chrome.runtime.onMessage.addListener((m,s,reply)=>{
  if(m?.type==="CAPTURE"){
    if(m.kind==="players"){
      const a=arr(m.payload),p=pageNo(m.url);
      if(a.length)playerPages.set(p,{url:m.url,payload:m.payload,count:a.length});
    }else if(m.kind==="squad"){
      const b=squadBody(m.payload);
      if(b?.activeGroupPositions && b?.activeFormationId)activeSquad={url:m.url,payload:m.payload};
    }else if(m.kind==="tactic"&&m.tacticParam){
      const decoded=decodeTactic(m.tacticParam);
      if(!decoded?.decodeError)activeTactic={url:m.url,decoded,exportCodeResponse:m.payload};
    }
    reply({ok:true});return;
  }

  if(m?.type==="STATUS"){
    const pages=[...playerPages.entries()].sort((a,b)=>a[0]-b[0]).map(([page,v])=>({page,count:v.count}));
    reply({
      ok:true,pages,playerCount:pages.reduce((n,x)=>n+x.count,0),
      playersDone:pages.length>0,squadDone:!!activeSquad,tacticDone:!!activeTactic,
      ready:pages.length>0&&!!activeSquad&&!!activeTactic
    });return;
  }

  if(m?.type==="CLEAR"){
    playerPages.clear();activeSquad=null;activeTactic=null;reply({ok:true});return;
  }

  if(m?.type==="EXPORT"){
    if(!playerPages.size||!activeSquad||!activeTactic){reply({ok:false,error:"not_ready"});return}

    const ordered=[...playerPages.entries()].sort((a,b)=>a[0]-b[0]);
    const players=[],seen=new Set();
    for(const[,v]of ordered)for(const p of arr(v.payload)){
      const k=String(p?.id??p?.playerDef?.id??JSON.stringify(p));
      if(!seen.has(k)){seen.add(k);players.push(p)}
    }

    const sb=squadBody(activeSquad.payload);
    const field=(sb?.activeGroupPositions||[]).filter(x=>x.group==="FIELD");
    const subs=(sb?.activeGroupPositions||[]).filter(x=>x.group==="SUBSTITUTE");
    const byId=new Map(players.map(p=>[p.id,p]));
    const enrich=x=>{
      const p=byId.get(x.ggClubPlayerId);
      return {...x,
        name:p?.playerDef?.commonName||[p?.playerDef?.firstName,p?.playerDef?.lastName].filter(Boolean).join(" ")||null,
        chemistryPoints:p?.chemistryPoints??null,chemistryStyle:p?.chemistryStyle??null,
        rolesPlus:p?.playerDef?.rolesPlus??[],rolesPlusPlus:p?.playerDef?.rolesPlusPlus??[],
        playstyles:p?.playerDef?.playstyles??[],playstylesPlus:p?.playerDef?.playstylesPlus??[]
      };
    };

    const out={
      exporter:"FC27 Club Exporter",exporterVersion:"0.4.0",exportedAt:new Date().toISOString(),
      source:"FUT.GG JSON responses observed during normal browser use",
      privacy:"No cookies, authorization headers, EA credentials, or browser tokens are exported.",
      capturedPages:ordered.map(([page,v])=>({page,count:v.count,url:v.url})),
      counts:{players:players.length,startingXI:field.length,substitutes:subs.length},
      squad:{
        title:sb.title,activeFormationId:sb.activeFormationId,
        managerId:sb.managerId,managerNationId:sb.managerNationId,managerLeagueId:sb.managerLeagueId,
        startingXI:field.map(enrich),substitutes:subs.map(enrich),activeTacticSummary:sb.activeTactic
      },
      tactics:activeTactic,players
    };

    const blob=new Blob([JSON.stringify(out,null,2)],{type:"application/json"});
    const r=new FileReader();
    r.onload=()=>{
      chrome.downloads.download({
        url:r.result,
        filename:filename(),
        saveAs:true
      }, id=>{
        const err=chrome.runtime.lastError?.message;
        reply(err?{ok:false,error:err}:{ok:true,downloadId:id});
      });
    };
    r.readAsDataURL(blob);
    return true;
  }
});

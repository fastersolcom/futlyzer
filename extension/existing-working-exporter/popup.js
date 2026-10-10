
const $=id=>document.getElementById(id);
let fallbackTimer=null;
function mark(id,ok){const e=$(id);e.classList.toggle("done",ok);e.querySelector(".dot").textContent=ok?"✓":id.slice(1)}
function refresh(){
 chrome.runtime.sendMessage({type:"STATUS"},r=>{
   if(!r)return;
   mark("s1",r.playersDone); mark("s2",r.squadDone&&r.tacticDone);
   $("pinfo").textContent=r.playersDone
     ? `${r.playerCount} kayıt • ${r.pages.map(x=>`Sayfa ${x.page}: ${x.count}`).join(" • ")}`
     : "Henüz oyuncu verisi yok.";
   $("squadcheck").innerHTML=r.squadDone?'<span class="good">✓ Kadro yakalandı</span>':'○ Kadro bekleniyor';
   $("tacticcheck").innerHTML=r.tacticDone?'<span class="good">✓ Aktif taktik + roller yakalandı</span>':'○ Aktif taktik + roller bekleniyor';

   $("export").disabled=!r.ready;
   $("summary").innerHTML=r.ready
     ? '<span class="good">Hazır ✓</span> Tek JSON için her şey yakalandı.'
     : 'Oyuncular + aktif kadro + aktif taktik tamamlanınca indirme açılır.';

   if(r.squadDone&&!r.tacticDone){
     if(!fallbackTimer) fallbackTimer=setTimeout(()=>{$("fallback").style.display="block"},1800);
   }else{
     if(fallbackTimer){clearTimeout(fallbackTimer);fallbackTimer=null}
     $("fallback").style.display="none";
   }
 });
}
$("export").onclick=()=>{
 $("export").disabled=true;$("export").textContent="Hazırlanıyor…";
 chrome.runtime.sendMessage({type:"EXPORT"},r=>{
   $("export").textContent=r?.ok?"JSON hazır ✓":"JSON'u İndir";
   setTimeout(refresh,900);
 });
};
$("clear").onclick=()=>chrome.runtime.sendMessage({type:"CLEAR"},refresh);
refresh();setInterval(refresh,1000);

/**
 * NimTech Google Sheets -> amoCRM bridge.
 * Bind this Apps Script to spreadsheet "! Заявки сайта nimtech.ru".
 * Script Properties: AMO_ACCESS_TOKEN, optionally AMO_BASE_URL.
 * Publish as Web App (execute as owner; access anyone) ONLY after security/privacy review.
 * Google Apps Script web apps do not support robust custom headers/CORS preflight.
 * For production use a same-origin proxy or server-side relay with abuse protection.
 */
const CFG={sheet:'Заявки',errors:'Журнал ошибок',pipeline:9611890,status:76760446,base:'https://nimtech.amocrm.ru'};
const HEADERS=['id','created_at','name','phone','email','form_id','category','source','utm_source','utm_medium','utm_campaign','utm_content','utm_term','page_url','landing_url','referrer','client_id','ym_client_id','consent','tags','pipeline','crm_status','amo_lead_id','amo_contact_id','ms_status','ms_order_id','calculator_json','error','attempts','updated_at'];
function setup(){ScriptApp.newTrigger('processPending').timeBased().everyMinutes(5).create();}
function output(x){return ContentService.createTextOutput(JSON.stringify(x)).setMimeType(ContentService.MimeType.JSON);}
function clean(v,max){return String(v==null?'':v).trim().slice(0,max||300);}
function safeCell(v){const s=clean(v,20000);return /^[=+@\-\t\r]/.test(s)?"'"+s:s;}
function getSheet(){return SpreadsheetApp.getActiveSpreadsheet().getSheetByName(CFG.sheet);}
function doPost(e){
 try{
  if(!e||!e.postData||e.postData.contents.length>16000)return output({ok:false,error:'bad_request'});
  const d=JSON.parse(e.postData.contents);
  if(d.website)return output({ok:true}); // honeypot
  const name=clean(d.name,100),phone=clean(d.phone,30).replace(/[^\d+]/g,'');
  if(!name||phone.replace(/\D/g,'').length<10||d.consent!==true)return output({ok:false,error:'validation'});
  const id=clean(d.request_id,100)||Utilities.getUuid();
  const lock=LockService.getScriptLock();lock.waitLock(10000);
  try{
   const sh=getSheet(),last=sh.getLastRow();
   if(last>1){const ids=sh.getRange(2,1,last-1,1).getDisplayValues().flat();if(ids.includes(id))return output({ok:true,id,duplicate:true});}
   const utm=d.utm||{};
   const category=clean(d.category,100)||'Террасы';
   const form=clean(d.form_id,100)||'unknown';
   const tags=category.toLowerCase().includes('бамбук')?'Bambuk,Сайт':form.includes('calculator')?'Террасы,Калькулятор':'Террасы,Сайт';
   const now=new Date().toISOString();
   const vals=[id,now,name,phone,clean(d.email,150),form,category,clean(d.source,100)||'website',...['utm_source','utm_medium','utm_campaign','utm_content','utm_term'].map(k=>clean(utm[k],250)),clean(d.page_url,600),clean(d.landing_url,600),clean(d.referrer,600),clean(d.client_id,150),clean(d.ym_client_id,150),now,tags,'Объекты','pending','','','not_requested','',JSON.stringify(d.calculator||d.details||{}).slice(0,10000),'',0,now];
   sh.appendRow(vals.map(safeCell));
   return output({ok:true,id});
  }finally{lock.releaseLock();}
 }catch(err){console.error(err);return output({ok:false,error:'internal_error'});}
}
function amo(method,path,payload){
 const props=PropertiesService.getScriptProperties(),token=props.getProperty('AMO_ACCESS_TOKEN');
 if(!token)throw Error('AMO_ACCESS_TOKEN is not configured');
 const res=UrlFetchApp.fetch((props.getProperty('AMO_BASE_URL')||CFG.base)+'/api/v4'+path,{method,contentType:'application/json',headers:{Authorization:'Bearer '+token},payload:payload?JSON.stringify(payload):undefined,muteHttpExceptions:true});
 if(res.getResponseCode()>=300)throw Error('amoCRM '+res.getResponseCode()+': '+res.getContentText().slice(0,250));
 return res.getContentText()?JSON.parse(res.getContentText()):{};
}
function processPending(){
 const lock=LockService.getScriptLock();if(!lock.tryLock(1000))return;
 try{
  const sh=getSheet(),last=sh.getLastRow();if(last<2)return;
  const rows=sh.getRange(2,1,last-1,30).getValues();
  rows.forEach((r,i)=>{
   if(!['pending','retry'].includes(r[21])||Number(r[28])>=8)return;
   const row=i+2;
   try{
    let contactId=Number(r[23])||0,leadId=Number(r[22])||0;
    // Persist each remote ID immediately, so retries do not recreate already-confirmed records.
    if(!contactId){
     const phone=String(r[3]);const found=amo('get','/contacts?query='+encodeURIComponent(phone)+'&limit=50');
     const matches=found._embedded?.contacts||[];
     const normalized=s=>String(s).replace(/\D/g,'').slice(-10);
     const existing=matches.find(c=>(c.custom_fields_values||[]).some(f=>f.field_code==='PHONE'&&(f.values||[]).some(v=>normalized(v.value)===normalized(phone))));
     if(existing)contactId=existing.id;
     else{
      const created=amo('post','/contacts',[{name:String(r[2]),custom_fields_values:[{field_code:'PHONE',values:[{value:phone,enum_code:'WORK'}]}]}]);
      contactId=created._embedded?.contacts?.[0]?.id;
     }
     if(!contactId)throw Error('Contact ID missing');
     sh.getRange(row,24).setValue(contactId);
    }
    if(!leadId){
     const tags=String(r[19]).split(',').map(x=>x.trim()).filter(Boolean).map(name=>({name}));
     const tracking=[['UTM_SOURCE',r[8]],['UTM_MEDIUM',r[9]],['UTM_CAMPAIGN',r[10]],['UTM_CONTENT',r[11]],['UTM_TERM',r[12]]].filter(x=>x[1]).map(([field_code,value])=>({field_code,values:[{value:String(value)}]}));
     const created=amo('post','/leads',[{name:'Заявка NimTech: '+r[5]+' — '+r[2],pipeline_id:CFG.pipeline,status_id:CFG.status,_embedded:{contacts:[{id:contactId}],tags},...(tracking.length?{custom_fields_values:tracking}:{})}]);
     leadId=created._embedded?.leads?.[0]?.id;
     if(!leadId)throw Error('Lead ID missing');
     sh.getRange(row,23).setValue(leadId);
    }
    // Note only once: note status tracked by column 22 (crm_status).
    const note=['Заявка: '+r[0],'Форма: '+r[5],'Направление: '+r[6],'Источник: '+r[7],'Страница: '+r[13],'Первая страница: '+r[14],'Referrer: '+r[15],'Client ID: '+r[16],'Yandex Client ID: '+r[17],'UTM: '+JSON.stringify({source:r[8],medium:r[9],campaign:r[10],content:r[11],term:r[12]}),'Расчёт: '+r[26]].join('\n');
    // Note may duplicate if a crash occurs after posting but before status update; reconcile before production.
    amo('post','/leads/'+leadId+'/notes',[{note_type:'common',params:{text:note.slice(0,12000)}}]);
    sh.getRange(row,22).setValue('sent');sh.getRange(row,28).setValue('');sh.getRange(row,30).setValue(new Date().toISOString());
   }catch(err){
    sh.getRange(row,22).setValue('retry');sh.getRange(row,28).setValue(String(err).slice(0,500));sh.getRange(row,29).setValue(Number(r[28]||0)+1);sh.getRange(row,30).setValue(new Date().toISOString());
    SpreadsheetApp.getActiveSpreadsheet().getSheetByName(CFG.errors).appendRow([new Date().toISOString(),r[0],'amoCRM','API',String(err),Number(r[28]||0)+1,'']);
   }
  });
 }finally{lock.releaseLock();}
}

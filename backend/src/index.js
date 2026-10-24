// NimTech lead intake API — Cloudflare Worker + D1.
// Secrets: AMO_ACCESS_TOKEN, AMO_BASE_URL. Future order adapter: MOYSKLAD_TOKEN.
// Deploy only after configuring D1, CORS origins, CRM custom fields and privacy compliance.
const json=(value,status=200,headers={})=>new Response(JSON.stringify(value),{status,headers:{'content-type':'application/json; charset=utf-8',...headers}});
const allowedOrigins=['https://nimtech.ru','https://www.nimtech.ru','https://bamboo.nimtech.ru','https://calc.nimtech.ru'];
const safeString=(v,n=200)=>typeof v==='string'?v.trim().slice(0,n):'';
const normalizePhone=v=>safeString(v,30).replace(/[^+0-9]/g,'');
const cors=origin=>allowedOrigins.includes(origin)?{'access-control-allow-origin':origin,'vary':'Origin','access-control-allow-methods':'POST, OPTIONS','access-control-allow-headers':'Content-Type, Idempotency-Key'}:{};
async function amo(path,body,env){const host=env.AMO_BASE_URL||'https://nimtech.amocrm.ru';const r=await fetch(host+'/api/v4'+path,{method:'POST',headers:{Authorization:'Bearer '+env.AMO_ACCESS_TOKEN,'Content-Type':'application/json'},body:JSON.stringify(body)});if(!r.ok)throw Error('amoCRM HTTP '+r.status);return r.json();}
async function sendToAmo(lead,env){
 if(!env.AMO_ACCESS_TOKEN)throw Error('amoCRM is not configured');
 const contact=await amo('/contacts',[{name:lead.name,custom_fields_values:[{field_code:'PHONE',values:[{value:lead.phone,enum_code:'WORK'}]}]}],env);
 const contactId=contact._embedded?.contacts?.[0]?.id;
 if(!contactId)throw Error('amoCRM contact id missing');
 const fields=['Источник: '+lead.source,'Форма: '+lead.form_id,'Страница: '+lead.page_url,'Landing: '+lead.landing_url,'Referrer: '+lead.referrer,'UTM: '+JSON.stringify(lead.utm),'Client ID: '+lead.client_id,'Согласие: '+lead.consent_at,'Дополнительные данные: '+JSON.stringify(lead.details)].join('\n');
 const deal=await amo('/leads',[{name:'Заявка с сайта NimTech — '+lead.form_id,_embedded:{contacts:[{id:contactId}]}}],env);
 const leadId=deal._embedded?.leads?.[0]?.id;
 if(!leadId)throw Error('amoCRM lead id missing');
 await amo('/leads/'+leadId+'/notes',[{note_type:'common',params:{text:fields}}],env);
 return {contact_id:contactId,lead_id:leadId};
}
async function processPending(env){
 const pending=await env.DB.prepare("SELECT * FROM leads WHERE status IN ('pending','retry') AND attempts < 8 ORDER BY created_at LIMIT 20").all();
 for(const row of pending.results){
  try{const ids=await sendToAmo(JSON.parse(row.payload),env);await env.DB.prepare("UPDATE leads SET status='sent', amo_lead_id=?, amo_contact_id=?, updated_at=datetime('now') WHERE id=?").bind(ids.lead_id,ids.contact_id,row.id).run();}
  catch(e){await env.DB.prepare("UPDATE leads SET status='retry',attempts=attempts+1,last_error=?,updated_at=datetime('now') WHERE id=?").bind(String(e).slice(0,250),row.id).run();}
 }
}
export default {
 async fetch(request,env,ctx){
  const origin=request.headers.get('Origin')||'';
  const headers=cors(origin);
  if(request.method==='OPTIONS')return new Response(null,{status:204,headers});
  const path=new URL(request.url).pathname;
  if(path==='/health'&&request.method==='GET')return json({ok:true,service:'nimtech-leads'},200,headers);
  if(path!=='/v1/leads'||request.method!=='POST')return json({error:'not_found'},404,headers);
  if(!allowedOrigins.includes(origin))return json({error:'origin_not_allowed'},403,headers);
  const type=request.headers.get('content-type')||'';
  if(!type.includes('application/json'))return json({error:'json_required'},415,headers);
  if(Number(request.headers.get('content-length')||0)>16384)return json({error:'too_large'},413,headers);
  let data;try{data=await request.json();}catch{return json({error:'invalid_json'},400,headers);}
  if(data.website)return json({ok:true},200,headers); // honeypot
  const phone=normalizePhone(data.phone),name=safeString(data.name,100);
  if(!name||phone.replace(/\D/g,'').length<10||!data.consent)return json({error:'invalid_fields'},422,headers);
  const formId=safeString(data.form_id,80)||'unknown';
  const idempotency=safeString(request.headers.get('Idempotency-Key'),100)||crypto.randomUUID();
  const clientId=safeString(data.client_id,100);
  const utm=Object.fromEntries(['utm_source','utm_medium','utm_campaign','utm_content','utm_term'].map(k=>[k,safeString(data.utm?.[k],200)]));
  const lead={name,phone,form_id:formId,source:safeString(data.source,80)||'website',page_url:safeString(data.page_url,500),landing_url:safeString(data.landing_url,500),referrer:safeString(data.referrer,500),client_id:clientId,utm,details:JSON.parse(JSON.stringify(data.details||{})),consent_at:new Date().toISOString()};
  if(JSON.stringify(lead).length>12000)return json({error:'too_large'},413,headers);
  const id=crypto.randomUUID();
  await env.DB.prepare("INSERT OR IGNORE INTO leads (id,idempotency_key,payload,status,created_at,updated_at) VALUES (?,?,?,'pending',datetime('now'),datetime('now'))").bind(id,idempotency,JSON.stringify(lead)).run();
  ctx.waitUntil(processPending(env));
  return json({ok:true,status:'accepted',request_id:id},202,headers);
 },
 async scheduled(event,env,ctx){ctx.waitUntil(processPending(env));}
};

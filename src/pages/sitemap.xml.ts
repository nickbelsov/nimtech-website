import type { APIRoute } from 'astro';
export const GET: APIRoute = () => {
const paths=['/','/terrasy-pod-klyuch/','/catalog/','/projects/','/calculator/','/blog/','/blog/5-oshibok-montazha-dpk/','/blog/kak-vybrat-terrasnuyu-dosku-dpk/','/blog/montazh-dpk-na-beton/','/blog/stupeni-iz-dpk-montazh/','/blog/dpk-ili-mpk-sravnenie/','/blog/stoimost-terrasy-iz-dpk/','/blog/ograzhdeniya-iz-dpk/','/blog/chto-s-dpk-cherez-dva-goda/','/blog/kak-ne-kupit-plohuyu-dpk/','/blog/terrasa-na-ekspluatiruemoy-krovle/','/blog/paryashchaya-terrasa/','/blog/montazh-terrasy-zimoy/','/blog/obramlenie-terrasy/','/blog/koekstruziya-dpk/','/blog/proizvodstvo-dpk/','/video/','/contacts/'];
const xml='<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+paths.map(p=>'<url><loc>https://nimtech.ru'+p+'</loc></url>').join('')+'</urlset>';
return new Response(xml,{headers:{'Content-Type':'application/xml; charset=utf-8'}});
};
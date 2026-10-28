import type { APIRoute } from 'astro';

// Include actual content pages, but not redirect-only legacy files under public/.
const blogArticles = import.meta.glob('./blog/*/index.astro', { eager: true, query: '?raw', import: 'default' });
const guideArticles = import.meta.glob('./*/index.astro', { eager: true, query: '?raw', import: 'default' });

const pathsFrom = (files: Record<string, unknown>, prefix: string) =>
  Object.entries(files)
    .filter(([file, source]) => !file.includes('[') && !String(source).includes('http-equiv="refresh"'))
    .map(([file]) => prefix + file.split('/')[prefix === '/blog/' ? 2 : 1] + '/');

const pages = [
  '/', '/terrasy-pod-klyuch/', '/catalog/',
  '/calculator/', '/blog/', '/contacts/',
  '/stupeni-dpk/', '/montazh-terrasnoy-doski/',
  '/kreplenie-dpk-k-metallokarkasu/', '/stykovka-terrasnoy-doski/',
  '/karkas-pod-terrasnuyu-dosku/', '/podshivka-terrasy/', '/shag-lag-terrasnoy-doski/',
];

export const GET: APIRoute = () => {
  const paths = [...new Set([...pages, ...pathsFrom(blogArticles, '/blog/'), ...pathsFrom(guideArticles, '/')])].sort();
  const xml = '<?xml version="1.0" encoding="UTF-8"?>\n' +
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' +
    paths.map((path) => '<url><loc>https://nimtech.ru' + path + '</loc></url>').join('') +
    '</urlset>';
  return new Response(xml, { headers: { 'Content-Type': 'application/xml; charset=utf-8' } });
};

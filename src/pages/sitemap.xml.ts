import type { APIRoute } from 'astro';

// Generate blog URLs from the actual article files instead of a manually maintained list.
const articles = import.meta.glob('./blog/*/index.astro', { eager: true });
const blogPaths = Object.keys(articles).map((path) => {
  const slug = path.split('/')[2];
  return '/blog/' + slug + '/';
}).sort();

const redirects = new Set([
  '/blog/terrasa-iz-dpk-na-betone/',
  '/blog/stoimost-terrasy-pod-klyuch/',
  '/blog/terrasa-na-krovle/',
  '/blog/oshibki-montazha-dpk/',
]);

const pages = [
  '/', '/terrasy-pod-klyuch/', '/catalog/', '/projects/',
  '/calculator/', '/blog/', '/video/', '/contacts/',
];

export const GET: APIRoute = () => {
  const paths = [...new Set([...pages, ...blogPaths.filter((p) => !redirects.has(p))])];
  const xml = '<?xml version="1.0" encoding="UTF-8"?>\n' +
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' +
    paths.map((path) => '<url><loc>https://nimtech.ru' + path + '</loc></url>').join('') +
    '</urlset>';
  return new Response(xml, { headers: { 'Content-Type': 'application/xml; charset=utf-8' } });
};

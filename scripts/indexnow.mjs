// Отправка адресов из sitemap.xml в IndexNow (Яндекс: https://yandex.com/indexnow).
//
//   node scripts/indexnow.mjs                      только показать, что будет отправлено (ничего не уходит)
//   node scripts/indexnow.mjs --send               отправить в Яндекс
//   node scripts/indexnow.mjs --sitemap <адрес или путь к файлу>   другой sitemap (по умолчанию живой)
//   node scripts/indexnow.mjs --key <ключ>         свой ключ (по умолчанию из файла static/<ключ>.txt)
//
// Запускать после деплоя и сброса кэша CDN: файл ключа должен открываться на сайте.
import { readFileSync, readdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HOST = 'www.usplitonline.ru';
const ENDPOINT = 'https://yandex.com/indexnow';
const MAX_URLS = 10000;

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const args = process.argv.slice(2);
const send = args.includes('--send');
const opt = (name) => {
  const i = args.indexOf(name);
  return i >= 0 ? args[i + 1] : undefined;
};

function findKey() {
  const fromArg = opt('--key');
  if (fromArg) return fromArg;
  const files = readdirSync(join(root, 'static')).filter((f) => /^[0-9a-f]{32}\.txt$/i.test(f));
  if (files.length !== 1) {
    throw new Error(`Ожидался ровно один файл ключа static/<32 символа>.txt, найдено: ${files.length}`);
  }
  return files[0].replace(/\.txt$/i, '');
}

async function loadSitemap(src) {
  if (/^https?:\/\//i.test(src)) {
    const res = await fetch(src);
    if (!res.ok) throw new Error(`Не удалось получить ${src}: HTTP ${res.status}`);
    return res.text();
  }
  return readFileSync(src, 'utf8');
}

function fail(message) {
  console.error('Ошибка: ' + message);
  process.exit(1);
}

try {
  const key = findKey();
  const keyLocation = `https://${HOST}/${key}.txt`;
  const source = opt('--sitemap') ?? `https://${HOST}/sitemap.xml`;
  const xml = await loadSitemap(source);

  const urls = [...new Set([...xml.matchAll(/<loc>\s*([^<\s]+)\s*<\/loc>/g)].map((m) => m[1]))];
  if (urls.length === 0) fail('в sitemap не найдено ни одного адреса');
  if (urls.length > MAX_URLS) fail(`адресов больше ${MAX_URLS}`);
  const foreign = urls.filter((u) => !u.startsWith(`https://${HOST}/`));
  if (foreign.length) fail('в sitemap есть адреса не с https://' + HOST + ':\n' + foreign.join('\n'));

  const payload = { host: HOST, key, keyLocation, urlList: urls };
  console.log(`Источник: ${source}`);
  console.log(`Адресов: ${urls.length}`);
  urls.forEach((u) => console.log('  ' + u));
  console.log(`Файл ключа: ${keyLocation}`);

  if (!send) {
    console.log('\nРежим проверки: ничего не отправлено. Для отправки добавьте --send');
    process.exit(0);
  }

  const keyRes = await fetch(keyLocation);
  const keyBody = keyRes.ok ? (await keyRes.text()).trim() : '';
  if (keyBody !== key) fail(`файл ключа ${keyLocation} не открывается или содержит другой текст (HTTP ${keyRes.status}). Сначала задеплойте сайт и сбросьте кэш CDN`);

  const res = await fetch(ENDPOINT, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json; charset=utf-8' },
    body: JSON.stringify(payload),
  });
  const meaning = { 200: 'принято', 202: 'принято, ключ будет проверен', 400: 'неверный запрос', 403: 'ключ не найден или не совпал', 422: 'адреса не относятся к хосту или неверный ключ', 429: 'слишком много запросов' };
  console.log(`\nОтвет Яндекса: HTTP ${res.status} (${meaning[res.status] ?? 'см. https://www.indexnow.org/documentation'})`);
  process.exit(res.status === 200 || res.status === 202 ? 0 : 1);
} catch (e) {
  fail(e.message);
}

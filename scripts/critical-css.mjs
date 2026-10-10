// Критический CSS: после сборки Hugo встраивает в каждую страницу стили, которые нужны её разметке,
// а полный файл стилей подключает без блокировки отрисовки (preload + onload, с <noscript> для браузеров без JS).
// Запуск: node scripts/critical-css.mjs public   (в CI — после `hugo --gc --minify`, см. .github/workflows/selectel.yaml)
import fs from 'node:fs/promises';
import path from 'node:path';
import Beasties from 'beasties';

const dir = path.resolve(process.argv[2] || 'public');

const beasties = new Beasties({
  path: dir,
  publicPath: '/',
  preload: 'swap',          // <link rel=preload as=style onload="this.rel='stylesheet'">
  noscriptFallback: true,
  pruneSource: false,       // файлы стилей остаются полными: их используют все страницы и кеширует браузер
  inlineFonts: true,        // правила @font-face — во встроенный CSS, иначе шрифты ждут полный файл стилей и текст «прыгает»
  preloadFonts: false,      // шрифты уже загружаются заранее (layouts/partials/head/fonts.html)
  reduceInlineStyles: false, // не трогать существующие <style> (в т.ч. внутри <noscript> в шапке — иначе меню раскрыто всегда)
  compress: true,
  logLevel: 'warn',
});

async function* htmlFiles(d) {
  for (const e of await fs.readdir(d, { withFileTypes: true })) {
    const p = path.join(d, e.name);
    if (e.isDirectory()) yield* htmlFiles(p);
    else if (e.name.endsWith('.html')) yield p;
  }
}

let count = 0;
for await (const file of htmlFiles(dir)) {
  const html = await fs.readFile(file, 'utf8');
  if (!html.includes('rel="stylesheet"') && !html.includes('rel=stylesheet')) continue;
  await fs.writeFile(file, await beasties.process(html));
  count++;
}
console.log(`critical-css: обработано страниц: ${count}`);

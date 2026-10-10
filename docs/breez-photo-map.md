# Фото для галерей моделей: откуда взяты

Фото взяты со страниц серий breez.ru (общедоступные страницы, вход в личный кабинет не использовался). На сайт попадают WebP-версии (основное фото 1200×900 и миниатюра 200×150) из `static/images/models/<бренд>/<модель>/`; исходные файлы лежат локально в `source-images/` (в репозиторий не входят). Список выбранных кадров и подписи: `scripts/gallery_manifest.json`; пересборка: `python scripts/fetch_breez_gallery.py`, затем `python scripts/build_gallery.py`.

| Модель на сайте | Страница | Серии на breez.ru | Найдено фото | В галерее |
|---|---|---|---|---|
| Hisense Sensation Slider Pro | `/projects/hisense-nastennye/sensation-slider-pro/` | `/products/sensation-slider-pro-superior-dc-inverter/`<br>`/products/sensation-slider-pro-carbon-superior-dc-inverter/` | 19 | 12 |
| Hisense Vision Pro 2.0 | `/projects/hisense-nastennye/vision-pro-2-0/` | `/products/vision-pro-2-0-superior-dc-inverter/`<br>`/products/vision-pro-2-0-carbon-superior-dc-inverter/` | 28 | 12 |
| Hisense Vibe Pro EU | `/projects/hisense-nastennye/vibe-pro-eu/` | `/products/vibe-pro-silver-eu-dc-inverter/`<br>`/products/vibe-pro-carbon-eu-dc-inverter/`<br>`/products/vibe-pro-champagne-eu-dc-inverter/` | 13 | 11 |
| Hisense Expert Pro 2.0 EU | `/projects/hisense-nastennye/expert-pro-2-0-eu/` | `/products/expert-pro-2-0-eu-dc-inverter/` | 8 | 8 |
| Hisense Goal 2.0 | `/projects/hisense-nastennye/goal-2-0/` | `/products/split-system-goal-2-0-dc-inverter-wi-fi/`<br>`/products/split-system-goal-2-0-classic-a-wi-fi/` | 18 | 12 |
| Hisense Кассетные | `/projects/promyshlennye/kassetnye/` | `/products/heavy-2-0-classic-casset/`<br>`/products/split-sistem-kasset-heavy-eu-dc-inverter-wi-fi/`<br>`/products/split-sistem-kasset-heavy-eu-dc-inverter/` | 11 | 7 |
| Hisense Канальные | `/projects/promyshlennye/kanalnye/` | `/products/heavy-2-0-classic-canal/`<br>`/products/split-sistem-kanal-heavy-eu-dc-inverter-r32-wi-fi/`<br>`/products/split-sistem-kanal-heavy-eu-dc-inverter-r32/` | 12 | 7 |
| Hisense Напольно-потолочные и консольные | `/projects/promyshlennye/napolno-potolochnye/` | `/products/heavy-2-0-classic-pol-potolok/`<br>`/products/split-sistem-pol-potolok-heavy-eu-dc-inverter-r32-wi-fi/`<br>`/products/split-sistem-konsol-eu-dc-inverter-r32-wi-fi/` | 11 | 8 |
| Hisense Колонные | `/projects/promyshlennye/kolonnye/` | `/products/heavy-2-0-classic-kolon/` | 2 | 2 |
| Hisense Наружные блоки | `/projects/hisense-multi-split/naruzhnye-bloki/` | `/products/multi-eu-dc-inverter/`<br>`/products/multi-eu-dc-inverter-lp/`<br>`/products/ultra-multi-dc-inverter/` | 3 | 3 |
| Hisense Внутренние блоки | `/projects/hisense-multi-split/vnutrennie-bloki/` | `/products/vision-pro-2-0-multi-superior-dc-inverter/`<br>`/products/sensation-pro-multi-superior-dc-inverter/`<br>`/products/vibe-pro-multi-eu-dc-inverter/`<br>`/products/zoom-multi-eu-dc-inverter/`<br>`/products/multi-eu-dc-inverter-console/`<br>`/products/multi-eu-dc-inverter-canal/`<br>`/products/multi-eu-dc-inverter-casset/`<br>`/products/multi-eu-dc-inverter-pol-potolok/` | 40 | 12 |
| Hisense Серия V | `/projects/hisense-mobilnye/seriya-v/` | `/products/mob-cond-v/` | 7 | 7 |
| Hisense Серия W | `/projects/hisense-mobilnye/seriya-w/` | `/products/mob-cond-w/` | 5 | 5 |
| Hisense Серия C | `/projects/hisense-mobilnye/seriya-c/` | `/products/mob-cond-c/` | 4 | 4 |
| LG Deluxe Pro | `/projects/lg/deluxe-pro/` | `/products/invert-split-system-deluxe-pro-dual-inverter/` | 13 | 9 |
| LG ARTCOOL Mirror | `/projects/lg/artcool-mirror/` | `/products/invert-spit-system-artcool-mirror/` | 2 | 2 |
| LG ProCool | `/projects/lg/procool/` | `/products/procool/` | 10 | 9 |
| LG ProMulti 2.0 | `/projects/lg/promulti-2-0/` | `/products/lg-promult-2025/` | 3 | 3 |
| Royal Clima BREZZA RCB 150 LUX | `/projects/ventilyaciya/brizery/brezza-rcb-150-lux/` | `/products/brezza/` | 6 | 6 |
| Royal Clima BREZZA XS RCB 75 | `/projects/ventilyaciya/brizery/brezza-xs-rcb-75/` | `/products/brezza-xs/` | 4 | 4 |
| Royal Clima BREZZA LUNA RCB 80 LUX | `/projects/ventilyaciya/brizery/brezza-luna-rcb-80-lux/` | `/products/brezza-luna/` | 4 | 4 |
| Royal Clima VENTO RCV | `/projects/ventilyaciya/pritochnye/vento-rcv/` | `/products/kpy-vento/` | 2 | 2 |
| Royal Clima FIATO RCF 70 | `/projects/ventilyaciya/rekuperatory/fiato-rcf-70/` | `/products/energoeffektivniy-rekuperator-fiato/` | 10 | 10 |
| Royal Clima SOFFIO UNO | `/projects/ventilyaciya/rekuperatory/soffio-uno/` | `/products/soffio-uno/` | 2 | 2 |
| Royal Clima SOFFIO UNO 4.0 | `/projects/ventilyaciya/rekuperatory/soffio-uno-4-0/` | `/products/soffio-uno-4-0/` | 2 | 2 |
| Royal Clima SOFFIO PRIMO 3.0 | `/projects/ventilyaciya/rekuperatory/soffio-primo-3-0/` | `/products/soffio-primo-3-0/` | 2 | 2 |
| Royal Clima SOFFIO PRIMO 4.0 | `/projects/ventilyaciya/rekuperatory/soffio-primo-4-0/` | `/products/soffio-primo-4-0/` | 2 | 2 |
| Royal Clima CARISMA Studio | `/projects/osushiteli/bytovye/carisma-studio/` | `/products/carisma-studio-rd-cr/` | 8 | 8 |
| Royal Clima CARISMA Loft | `/projects/osushiteli/bytovye/carisma-loft/` | `/products/carisma-loft-rd-cr/` | 8 | 8 |
| Royal Clima CARISMA Villa | `/projects/osushiteli/bytovye/carisma-villa/` | `/products/carisma-villa-rd-cr/` | 8 | 8 |
| Royal Clima PACIFIC Studio | `/projects/osushiteli/bytovye/pacific-studio/` | `/products/osushit-pacific-studio/` | 5 | 5 |
| Royal Clima PACIFIC Loft | `/projects/osushiteli/bytovye/pacific-loft/` | `/products/osushit-pacific-loft/` | 5 | 5 |
| Royal Clima PACIFIC Villa | `/projects/osushiteli/bytovye/pacific-villa/` | `/products/pacific-villa/` | 4 | 4 |
| Royal Clima PACIFIC Palazzo | `/projects/osushiteli/bytovye/pacific-palazzo/` | `/products/pacific-palazzo/` | 5 | 5 |
| Hisense Air Go Pro | `/projects/osushiteli/bytovye/hisense-air-go-pro/` | `/products/osushit-vozd-air-go-pro/` | 5 | 5 |
| Royal Clima RIVIERA | `/projects/osushiteli/dlya-basseynov/riviera/` | `/products/riviera/` | 1 | 1 |
| Roland FAVORITE II | `/projects/favorite-ii/` | `/products/classic-favorite-2-2024/` | 6 | 6 |
| Roland FAVORITE II Inverter | `/projects/favorite-ii-inverter/` | `/products/invert-favorite-2-2024/` | 6 | 6 |
| Roland MAESTRO | `/projects/maestro/` | `/products/classic-split-system-maestro/` | 4 | 4 |

Итого: 39 моделей, найдено 308 фото, в галереи вошло 232.

Правила отбора: не больше 12 лучших на модель; порядок — внутренний блок спереди, под углом, наружный блок, пульт, остальное; варианты отделки (цвет, инвертор/классика) объединены в одну галерею, вариант указан в подписи фото; повторы пультов и наружных блоков из разных серий не дублируются.
Для мульти-сплит «Внутренние блоки» взято по одному-два кадра на тип блока (настенные Sensation/Vibe/Vision/Zoom, канальный, кассетный, консольный, напольно-потолочный).

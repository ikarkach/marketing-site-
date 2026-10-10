"""Какие серии breez.ru дают фото для галереи каждой модели сайта.

Ключ — путь страницы модели относительно /projects/ (для Roland — страница серии).
Значение — (папка бренда на сайте, [адреса серий на breez.ru без домена]).
Страницы серий на breez.ru публичные, вход не нужен. Решения по неоднозначным группам согласованы с владельцем сайта (2026-10-10).
"""

B = '/products/'

SOURCES = {
    # ---- Hisense: настенные
    'hisense-nastennye/sensation-slider-pro': ('hisense', [B + 'sensation-slider-pro-superior-dc-inverter/', B + 'sensation-slider-pro-carbon-superior-dc-inverter/']),
    'hisense-nastennye/vision-pro-2-0': ('hisense', [B + 'vision-pro-2-0-superior-dc-inverter/', B + 'vision-pro-2-0-carbon-superior-dc-inverter/']),
    'hisense-nastennye/vibe-pro-eu': ('hisense', [B + 'vibe-pro-silver-eu-dc-inverter/', B + 'vibe-pro-carbon-eu-dc-inverter/', B + 'vibe-pro-champagne-eu-dc-inverter/']),
    'hisense-nastennye/expert-pro-2-0-eu': ('hisense', [B + 'expert-pro-2-0-eu-dc-inverter/']),
    'hisense-nastennye/goal-2-0': ('hisense', [B + 'split-system-goal-2-0-dc-inverter-wi-fi/', B + 'split-system-goal-2-0-classic-a-wi-fi/']),
    # ---- Hisense: промышленные HEAVY (серии, соответствующие текущему прайсу: HEAVY 2.0 on/off и HEAVY EU DC Inverter)
    'promyshlennye/kassetnye': ('hisense', [B + 'heavy-2-0-classic-casset/', B + 'split-sistem-kasset-heavy-eu-dc-inverter-wi-fi/', B + 'split-sistem-kasset-heavy-eu-dc-inverter/']),
    'promyshlennye/kanalnye': ('hisense', [B + 'heavy-2-0-classic-canal/', B + 'split-sistem-kanal-heavy-eu-dc-inverter-r32-wi-fi/', B + 'split-sistem-kanal-heavy-eu-dc-inverter-r32/']),
    'promyshlennye/napolno-potolochnye': ('hisense', [B + 'heavy-2-0-classic-pol-potolok/', B + 'split-sistem-pol-potolok-heavy-eu-dc-inverter-r32-wi-fi/', B + 'split-sistem-konsol-eu-dc-inverter-r32-wi-fi/']),
    'promyshlennye/kolonnye': ('hisense', [B + 'heavy-2-0-classic-kolon/']),
    # ---- Hisense: мульти-сплит
    'hisense-multi-split/naruzhnye-bloki': ('hisense', [B + 'multi-eu-dc-inverter/', B + 'multi-eu-dc-inverter-lp/', B + 'ultra-multi-dc-inverter/']),
    # внутренние блоки: по одному фото на тип блока (первое фото каждой серии)
    'hisense-multi-split/vnutrennie-bloki': ('hisense', [B + 'vision-pro-2-0-multi-superior-dc-inverter/', B + 'sensation-pro-multi-superior-dc-inverter/', B + 'vibe-pro-multi-eu-dc-inverter/',
                                                         B + 'zoom-multi-eu-dc-inverter/', B + 'multi-eu-dc-inverter-console/', B + 'multi-eu-dc-inverter-canal/',
                                                         B + 'multi-eu-dc-inverter-casset/', B + 'multi-eu-dc-inverter-pol-potolok/']),
    # ---- Hisense: мобильные
    'hisense-mobilnye/seriya-v': ('hisense', [B + 'mob-cond-v/']),
    'hisense-mobilnye/seriya-w': ('hisense', [B + 'mob-cond-w/']),
    'hisense-mobilnye/seriya-c': ('hisense', [B + 'mob-cond-c/']),
    # ---- LG
    'lg/deluxe-pro': ('lg', [B + 'invert-split-system-deluxe-pro-dual-inverter/']),
    'lg/artcool-mirror': ('lg', [B + 'invert-spit-system-artcool-mirror/']),
    'lg/procool': ('lg', [B + 'procool/']),
    'lg/promulti-2-0': ('lg', [B + 'lg-promult-2025/']),
    # ---- Royal Clima: вентиляция
    'ventilyaciya/brizery/brezza-rcb-150-lux': ('royal-clima', [B + 'brezza/']),
    'ventilyaciya/brizery/brezza-xs-rcb-75': ('royal-clima', [B + 'brezza-xs/']),
    'ventilyaciya/brizery/brezza-luna-rcb-80-lux': ('royal-clima', [B + 'brezza-luna/']),
    'ventilyaciya/pritochnye/vento-rcv': ('royal-clima', [B + 'kpy-vento/']),
    'ventilyaciya/rekuperatory/fiato-rcf-70': ('royal-clima', [B + 'energoeffektivniy-rekuperator-fiato/']),
    'ventilyaciya/rekuperatory/soffio-uno': ('royal-clima', [B + 'soffio-uno/']),
    'ventilyaciya/rekuperatory/soffio-uno-4-0': ('royal-clima', [B + 'soffio-uno-4-0/']),
    'ventilyaciya/rekuperatory/soffio-primo-3-0': ('royal-clima', [B + 'soffio-primo-3-0/']),
    'ventilyaciya/rekuperatory/soffio-primo-4-0': ('royal-clima', [B + 'soffio-primo-4-0/']),
    # ---- осушители
    'osushiteli/bytovye/carisma-studio': ('royal-clima', [B + 'carisma-studio-rd-cr/']),
    'osushiteli/bytovye/carisma-loft': ('royal-clima', [B + 'carisma-loft-rd-cr/']),
    'osushiteli/bytovye/carisma-villa': ('royal-clima', [B + 'carisma-villa-rd-cr/']),
    'osushiteli/bytovye/pacific-studio': ('royal-clima', [B + 'osushit-pacific-studio/']),
    'osushiteli/bytovye/pacific-loft': ('royal-clima', [B + 'osushit-pacific-loft/']),
    'osushiteli/bytovye/pacific-villa': ('royal-clima', [B + 'pacific-villa/']),
    'osushiteli/bytovye/pacific-palazzo': ('royal-clima', [B + 'pacific-palazzo/']),
    'osushiteli/bytovye/hisense-air-go-pro': ('hisense', [B + 'osushit-vozd-air-go-pro/']),
    'osushiteli/dlya-basseynov/riviera': ('royal-clima', [B + 'riviera/']),
    # ---- Roland (на breez бренд лежит в папке rln)
    'favorite-ii': ('roland', [B + 'classic-favorite-2-2024/']),
    'favorite-ii-inverter': ('roland', [B + 'invert-favorite-2-2024/']),
    'maestro': ('roland', [B + 'classic-split-system-maestro/']),
}

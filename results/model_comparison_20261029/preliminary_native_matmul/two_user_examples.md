# Two-user comparison

Users are anonymized here; the private setup file preserves the source-ID mapping. Selection used training history only: Among template users with qualified training history: min/max distinct qualified programme count; ties ascending raw user ID. No held-out hits or scores used.

## History Poor

4 distinct programmes with soft training overlap; 1 with qualified training airings. Held-out target IDs: .

| Observed training programme | Title | Category | Qualified airings | Soft airing sum |
| --- | --- | --- | ---: | ---: |
| 90066849 | Х/ф 'Гангстер'. | Фильмы | 1 | 0.9141 |
| 10002064 | Т/с 'Во все тяжкие', 2 сезон, 10 с. 'Конец бизнеса'. | Сериалы | 0 | 2.4507 |
| 90056809 | Х/ф 'Национальная безопасность'. | Фильмы | 0 | 0.6011 |
| 90011097 | Х/ф 'Харлей Дэвидсон и ковбой Мальборо'. | Фильмы | 0 | 0.0142 |

| Method | Rank | Programme ID | Title | Category | Held-out hit | Seen in training |
| --- | ---: | --- | --- | --- | --- | --- |
| popularity | 1 | 2400480 | ТСН. | Инфо | no | no |
| popularity | 2 | 240081 | Факты. | Инфо | no | no |
| popularity | 3 | 2400467 | 'Викна-Новости'. | Инфо | no | no |
| popularity | 4 | 200344 | 'Чистоnews'. | Развлечения | no | no |
| popularity | 5 | 2400508 | Сегодня. | Инфо | no | no |
| personal | 1 | 90066849 | Х/ф 'Гангстер'. | Фильмы | no | yes |
| personal | 2 | 2400480 | ТСН. | Инфо | no | no |
| personal | 3 | 240081 | Факты. | Инфо | no | no |
| personal | 4 | 2400467 | 'Викна-Новости'. | Инфо | no | no |
| personal | 5 | 200344 | 'Чистоnews'. | Развлечения | no | no |
| cbf | 1 | 12003091 | М/с 'Приключения Ам Няма'. | Детям | no | no |
| cbf | 2 | 90018696 | Х/ф 'Крикуны'. | Фильмы | no | no |
| cbf | 3 | 900405 | Премьера. Х/ф 'Крутые стволы'. | Фильмы | no | no |
| cbf | 4 | 90047361 | Х/ф 'Ловушка для родителей'. | Фильмы | no | no |
| cbf | 5 | 90075859 | Х/ф 'Экипаж'. | Фильмы | no | no |
| als_f32_r0.1 | 1 | 90070560 | Х/ф '2012'. | Фильмы | no | no |
| als_f32_r0.1 | 2 | 10001072 | Т/с 'Побег', 3 сезон, 5 с. 'Помехи'. | Сериалы | no | no |
| als_f32_r0.1 | 3 | 10001085 | Т/с 'Как я встретил вашу маму', 5 сезон, 18 с. 'Улыбочку'. | Сериалы | no | no |
| als_f32_r0.1 | 4 | 90066849 | Х/ф 'Гангстер'. | Фильмы | no | yes |
| als_f32_r0.1 | 5 | 10001711 | Т/с 'Город хищниц', 6 сезон, 6 с. 'Не то, что стоит делать'. | Сериалы | no | no |

## History Rich

837 distinct programmes with soft training overlap; 183 with qualified training airings. Held-out target IDs: 240081, 12001734, 200352, 90049236, 90071741.

| Observed training programme | Title | Category | Qualified airings | Soft airing sum |
| --- | --- | --- | ---: | ---: |
| 2400480 | ТСН. | Инфо | 68 | 77.8222 |
| 240081 | Факты. | Инфо | 66 | 76.4886 |
| 12001682 | М/с 'Губка Боб Квадратные Штаны'. | Детям | 63 | 86.6989 |
| 20088 | 'Завтрак с 1+1'. Информационно-развлекательная программа. | Развлечения | 38 | 40.0924 |
| 2400508 | Сегодня. | Инфо | 35 | 46.1683 |

| Method | Rank | Programme ID | Title | Category | Held-out hit | Seen in training |
| --- | ---: | --- | --- | --- | --- | --- |
| popularity | 1 | 2400480 | ТСН. | Инфо | no | yes |
| popularity | 2 | 240081 | Факты. | Инфо | yes | yes |
| popularity | 3 | 2400467 | 'Викна-Новости'. | Инфо | no | yes |
| popularity | 4 | 200344 | 'Чистоnews'. | Развлечения | no | yes |
| popularity | 5 | 2400508 | Сегодня. | Инфо | no | yes |
| personal | 1 | 2400480 | ТСН. | Инфо | no | yes |
| personal | 2 | 240081 | Факты. | Инфо | yes | yes |
| personal | 3 | 12001682 | М/с 'Губка Боб Квадратные Штаны'. | Детям | no | yes |
| personal | 4 | 20088 | 'Завтрак с 1+1'. Информационно-развлекательная программа. | Развлечения | no | yes |
| personal | 5 | 2400508 | Сегодня. | Инфо | no | yes |
| cbf | 1 | 12002772 | М/с 'Робокар Поли и его друзья'. | Детям | no | yes |
| cbf | 2 | 12002926 | М/с 'Викинг Вик'. | Детям | no | no |
| cbf | 3 | 120078335 | М/ф 'Замбезия'. | Детям | no | no |
| cbf | 4 | 120079995 | М/ф 'Супергерой'. | Детям | no | no |
| cbf | 5 | 2400508 | Сегодня. | Инфо | no | yes |
| als_f32_r0.1 | 1 | 90047611 | Х/ф 'Лучше не бывает'. | Фильмы | no | no |
| als_f32_r0.1 | 2 | 90081973 | Х/ф 'Эволюция'. | Фильмы | no | yes |
| als_f32_r0.1 | 3 | 90012900 | Х/ф 'Шоссе в никуда'. | Фильмы | no | yes |
| als_f32_r0.1 | 4 | 90063383 | Х/ф 'Ночной рейс'. | Фильмы | no | no |
| als_f32_r0.1 | 5 | 90079986 | Х/ф 'Лев'. | Фильмы | no | yes |

# Архітектура Neo4j: чому графова база швидко обходить зв’язки

Neo4j — це **нативна графова база даних**.

Це означає, що вона не зберігає граф як набір таблиць, а фізично організовує дані навколо двох головних сутностей:

- `Node` — вузол
- `Relationship` — зв’язок

Головна ідея Neo4j:

> зв’язки не обчислюються під час запиту — вони вже фізично збережені в базі.

Саме тому Neo4j добре працює там, де потрібно багато разів переходити від одного об’єкта до іншого: маршрути, рекомендації, соціальні мережі, fraud detection, логістика, диспетчеризація таксі.


## 🧠 Neo4j Cypher — документація та базові запити

---

## 🔹 Що таке Cypher

Cypher — це декларативна мова запитів Neo4j.

Вона дозволяє описувати граф через патерни:

- вузли → `( )`
- зв’язки → `[ ]`
- напрям → `-->`

Приклад:

```cypher
(:Zone)-[:CONNECTED_TO]->(:Zone)
````

Це означає:

> зона пов’язана з іншою зоною

---

### 🔹 Основна логіка запиту

Будь-який запит у Cypher має структуру:

```text
MATCH → знайти
WHERE → відфільтрувати
RETURN → повернути
```

Приклад:

```cypher
MATCH (z:Zone)
RETURN z
LIMIT 10
```

---

### 🔍 1 Пошук даних (READ)

### MATCH

Головний оператор для пошуку.

```cypher
MATCH (z:Zone)
RETURN z
LIMIT 10
```

---

### MATCH з умовою

```cypher
MATCH (z:Zone {zone_id: 48})
RETURN z
```

---

### MATCH зі зв’язком

```cypher
MATCH (a:Zone)-[:CONNECTED_TO]->(b:Zone)
RETURN a, b
LIMIT 20
```

---

### WHERE

Фільтрація:

```cypher
MATCH (z:Zone)
WHERE z.zone_id > 100
RETURN z
```

---

### OPTIONAL MATCH

Аналог LEFT JOIN:

```cypher
MATCH (z:Zone)
OPTIONAL MATCH (z)-[:CONNECTED_TO]->(n:Zone)
RETURN z, n
```

---

### ORDER BY / LIMIT

```cypher
MATCH (z:Zone)-[r:CONNECTED_TO]->()
RETURN z, COUNT(r) AS connections
ORDER BY connections DESC
LIMIT 5
```

---

### ✍️ 2 Створення даних (WRITE)

### CREATE

```cypher
CREATE (:Zone {zone_id: 999})
```

---

### CREATE зв’язок

```cypher
MATCH (a:Zone {zone_id: 48}), (b:Zone {zone_id: 161})
CREATE (a)-[:CONNECTED_TO]->(b)
```

---

### MERGE (find or create)

```cypher
MERGE (z:Zone {zone_id: 48})
```

---

### MERGE зі зв’язком

```cypher
MATCH (a:Zone {zone_id: 48}), (b:Zone {zone_id: 161})
MERGE (a)-[:CONNECTED_TO]->(b)
```

---

### 🔄 3. Оновлення даних

### SET

```cypher
MATCH (z:Zone {zone_id: 48})
SET z.name = "Central Zone"
```

---

### REMOVE

```cypher
MATCH (z:Zone {zone_id: 48})
REMOVE z.name
```

---

### ❌ 4. Видалення

### DELETE

```cypher
MATCH (z:Zone {zone_id: 999})
DELETE z
```

---

### DETACH DELETE

```cypher
MATCH (z:Zone {zone_id: 48})
DETACH DELETE z
```

(видаляє разом зі зв’язками)

---

### 🔗 5. Робота з графом

### Показати граф

```cypher
MATCH p = (:Zone)-[:CONNECTED_TO]->(:Zone)
RETURN p
LIMIT 50
```

---

### Сусіди вузла

```cypher
MATCH p = (:Zone {zone_id: 48})-[:CONNECTED_TO]->(z:Zone)
RETURN p
LIMIT 30
```

---

### Багаторівневий обхід (BFS)

```cypher
MATCH p = (:Zone {zone_id: 48})-[:CONNECTED_TO*1..2]->(z:Zone)
RETURN p
LIMIT 50
```

---

### Ваговий маршрут

```cypher
MATCH p = (:Zone {zone_id: 48})-[r:CONNECTED_TO*1..3]->(z:Zone)
WITH z, p,
     REDUCE(cost = 0.0, rel IN r | cost + rel.avg_cost) AS total_cost
RETURN p, total_cost
ORDER BY total_cost ASC
LIMIT 10
```

---

### 📊 6. Агрегація

### COUNT

```cypher
MATCH (z:Zone)
RETURN COUNT(z)
```

---

### SUM

```cypher
MATCH ()-[r:CONNECTED_TO]->()
RETURN SUM(r.freq) AS total_trips
```

---

### AVG

```cypher
MATCH ()-[r:CONNECTED_TO]->()
RETURN AVG(r.avg_cost) AS avg_cost
```

---

### 🔁 7. WITH (pipeline)

```cypher
MATCH (z:Zone)-[r:CONNECTED_TO]->()
WITH z, COUNT(r) AS connections
WHERE connections > 10
RETURN z, connections
```

---

### 📦 8. UNWIND (робота зі списками)

```cypher
UNWIND [1,2,3,4] AS x
RETURN x
```

---

### 🧱 9. Constraints та індекси

### Constraint

```cypher
CREATE CONSTRAINT zone_id IF NOT EXISTS
FOR (z:Zone)
REQUIRE z.zone_id IS UNIQUE;
```

---

### Перевірка

```cypher
SHOW CONSTRAINTS;
```

---

### Index

```cypher
CREATE INDEX zone_idx IF NOT EXISTS
FOR (z:Zone)
ON (z.zone_id);
```

---

### 🧠 Висновок

Cypher — це мова для роботи з графами через патерни.

Основна ідея:

```text
SQL → працює з таблицями
Cypher → працює зі зв’язками
```

Neo4j дозволяє:

* швидко обходити граф
* знаходити зв’язки
* будувати маршрути
* аналізувати мережі

```text
дані → зв’язки → граф → система
```

---

## 1. Основна архітектурна ідея: Index-Free Adjacency

У реляційній базі, якщо нам потрібно знайти пов’язані записи, база часто виконує `JOIN`.

Наприклад:

```sql
SELECT *
FROM zones z
JOIN trips t ON z.id = t.pickup_zone
JOIN zones z2 ON t.dropoff_zone = z2.id;
````

Тобто база повинна зіставити записи між таблицями.

У Neo4j зв’язок уже існує фізично:

```cypher
(:Zone)-[:CONNECTED_TO]->(:Zone)
```

Тому запит виглядає як перехід:

```cypher
MATCH (a:Zone)-[:CONNECTED_TO]->(b:Zone)
RETURN a, b
```

Neo4j не “шукає” кожен раз, як ці зони пов’язані.
Він переходить від вузла до його зв’язків.

Це називається:

> **Index-Free Adjacency** — суміжність без індексів.

Тобто кожен вузол має прямі вказівники на свої зв’язки, а зв’язки мають вказівники на початковий і кінцевий вузол.

---


## 2. Фізична модель зберігання

Neo4j зберігає граф у спеціальних файлах на диску.

Ключова ідея:

> дані зберігаються у записах фіксованого розміру.

Це дозволяє Neo4j швидко знаходити фізичне місце запису за його внутрішнім ID.

У спрощеному вигляді:

```text
physical_address = record_id * record_size
```

Тобто замість довгого пошуку база може швидко перейти до потрібного запису.

---

## 3. Node Store — сховище вузлів

Файл:

```text
neostore.nodestore.db
```

Вузол у Neo4j дуже легкий.

Він не зберігає всі свої дані всередині себе.

Вузол містить:

* службовий прапорець: чи активний запис
* вказівник на перший зв’язок
* вказівник на першу властивість

Спрощено:

```text
Node
 ├── in_use
 ├── first_relationship_id
 └── first_property_id
```

Приклад у нашій задачі:

```cypher
(:Zone {zone_id: 48})
```

Цей вузол не зберігає весь список маршрутів напряму як масив.
Він має вказівник на перший relationship, а далі Neo4j переходить по ланцюжку зв’язків.

---

## 4. Relationship Store — сховище зв’язків

Файл:

```text
neostore.relationshipstore.db
```

Relationship — це головна сила Neo4j.

Зв’язок зберігає:

* ID початкового вузла
* ID кінцевого вузла
* тип зв’язку
* вказівники на попередні/наступні зв’язки для обох вузлів
* вказівник на властивості зв’язку

Спрощено:

```text
Relationship
 ├── start_node_id
 ├── end_node_id
 ├── relationship_type
 ├── start_prev_rel
 ├── start_next_rel
 ├── end_prev_rel
 ├── end_next_rel
 └── first_property_id
```

У нашому прикладі:

```cypher
(:Zone {zone_id: 48})-[:CONNECTED_TO {
    freq: 120,
    avg_cost: 18.5,
    avg_dist: 3.2,
    weight: 0.0083
}]->(:Zone {zone_id: 161})
```

Тут сам relationship є не просто “лінією”.

Він є повноцінним об’єктом, який має власні властивості:

* скільки поїздок було між зонами
* середня вартість
* середня дистанція
* вага для алгоритму

---

## 5. Двозв’язний список зв’язків

Зв’язки в Neo4j організовані як **двозв’язний список**.

Це означає, що relationship знає:

* попередній зв’язок
* наступний зв’язок

Для початкового вузла і для кінцевого вузла.

Спрощено:

```text
Zone 48
  |
  v
REL 1 <-> REL 2 <-> REL 3 <-> REL 4
  |       |        |        |
Zone 90  Zone 161 Zone 230 Zone 239
```

Саме тому Neo4j швидко відповідає на запити типу:

```cypher
MATCH (:Zone {zone_id: 48})-[:CONNECTED_TO]->(z:Zone)
RETURN z
```

База не сканує всі маршрути.

Вона бере вузол `48`, переходить до першого relationship, а потім іде по ланцюжку зв’язків.

---

## 6. Property Store — сховище властивостей

Файл:

```text
neostore.propertystore.db
```

Властивості зберігаються окремо від вузлів і зв’язків.

Наприклад:

```cypher
(:Zone {zone_id: 48})
```

або:

```cypher
[:CONNECTED_TO {freq: 120, avg_cost: 18.5}]
```

У Neo4j властивості — це key-value пари.

Спрощено:

```text
Property
 ├── key
 ├── value
 └── next_property_id
```

Невеликі значення можуть зберігатися прямо в property block.

Великі рядки або масиви можуть переноситися в окремі dynamic stores.

---

## 7. Як виконується graph traversal

Коли ми пишемо:

```cypher
MATCH p = (:Zone {zone_id: 48})-[:CONNECTED_TO*1..3]->(:Zone)
RETURN p
```

Neo4j виконує не табличний JOIN, а обхід графа.

Спрощений процес:

```text
1. Знайти вузол Zone 48
2. Взяти pointer на перший relationship
3. Перейти по CONNECTED_TO
4. Дістати сусідню Zone
5. Повторити до глибини 3
```

Це і є traversal.

---

## 8. Архітектура пам’яті Neo4j

Neo4j працює на JVM, тому пам’ять поділяється на кілька рівнів.

### 8.1 Page Cache

Page Cache кешує файли графа з диску.

Тобто часто використовувані вузли, relationships і properties можуть читатися не з диску, а з пам’яті.

```text
Disk Store → Page Cache → Query Engine
```

Це критично для продуктивності.

---

### 8.2 JVM Heap

JVM Heap використовується для:

* об’єктів запиту
* виконання Cypher
* транзакцій
* тимчасових результатів
* планування запитів

Якщо запит повертає занадто багато даних, heap може бути перевантажений.

---

### 8.3 Off-Heap Memory

Off-heap memory використовується поза JVM heap.

Вона допомагає зменшити тиск на Garbage Collector і використовується для внутрішніх структур та кешування.

---

## 9. Query Engine

Коли ми запускаємо Cypher-запит:

```cypher
MATCH (z:Zone)-[:CONNECTED_TO]->(n:Zone)
RETURN z, n
```

Neo4j проходить кілька етапів:

```text
Cypher Query
    ↓
Parser
    ↓
Logical Plan
    ↓
Query Optimizer
    ↓
Physical Execution Plan
    ↓
Graph Traversal
    ↓
Result
```

Neo4j вирішує:

* з якого вузла почати
* чи використати index
* який напрям traversal
* як обмежити кількість результатів
* як виконати aggregation

---

## 10. Індекси в Neo4j

Neo4j не використовує індекси для кожного переходу між сусідами.

Але індекси потрібні, щоб швидко знайти стартовий вузол.

Наприклад:

```cypher
MATCH (z:Zone {zone_id: 48})
RETURN z
```

Для цього потрібен constraint/index:

```cypher
CREATE CONSTRAINT zone_id IF NOT EXISTS
FOR (z:Zone)
REQUIRE z.zone_id IS UNIQUE;
```

Після того як стартовий вузол знайдено, Neo4j далі рухається по relationships.

Тобто:

```text
Index → знайти старт
Traversal → іти по зв’язках
```

---

## 11. Транзакції та ACID

Neo4j підтримує ACID:

* Atomicity — транзакція або виконується повністю, або не виконується
* Consistency — граф залишається в коректному стані
* Isolation — паралельні транзакції не ламають одна одну
* Durability — після commit дані не зникають

Перед змінами Neo4j записує інформацію у transaction log.

```text
Write Query
    ↓
Transaction Log
    ↓
Graph Store
    ↓
Commit
```

---

## 12. Архітектура нашого taxi graph

У цьому уроці ми моделюємо NYC Taxi як граф.

### Вузли

```cypher
(:Zone {zone_id: 48})
```

Кожна зона таксі — це вузол.

---

### Зв’язки

```cypher
(:Zone)-[:CONNECTED_TO]->(:Zone)
```

Зв’язок означає:

> між цими зонами реально були поїздки.

---

### Властивості зв’язку

```text
freq      — кількість поїздок
avg_cost  — середня вартість
avg_dist  — середня дистанція
weight    — вага для алгоритмів
```

---

## 13. Схема графа

```text
(:Zone {zone_id: 48})
      |
      | CONNECTED_TO
      | freq: 120
      | avg_cost: 18.5
      | avg_dist: 3.2
      v
(:Zone {zone_id: 161})
```

---

## 14. Чому це графова задача

Задача диспетчеризації таксі:

> отримати pickup zone і знайти найкращу доступну машину.

Це не просто сортування списку.

Це задача про зв’язки:

* які зони поруч
* які зони часто пов’язані
* які маршрути дешевші
* які маршрути швидші
* де зараз водії

Граф дозволяє мислити не рядками, а мережею.

---

# Практичні Cypher-запити для Neo4j Browser

---

## Запит 1. Побачити базовий граф

```cypher
MATCH p = (:Zone)-[:CONNECTED_TO]->(:Zone)
RETURN p
LIMIT 50
```

### Що показує

Цей запит показує перші 50 зв’язків між зонами.

Він потрібен для першого візуального ефекту:

> дані — це не таблиця, а мережа.

У Neo4j Browser треба перейти у вкладку `Graph`, і ви побачите вузли `Zone` та стрілки `CONNECTED_TO`.

---

## Запит 2. Показати одну центральну зону і її сусідів

```cypher
MATCH p = (:Zone {zone_id: 48})-[:CONNECTED_TO]->(:Zone)
RETURN p
LIMIT 40
```

### Що показує

Це показує всі напрямки руху з конкретної зони `48`.

Зона `48` стає центром локального графа.

Це добре для пояснення:

> один вузол може бути точкою входу в цілу мережу.

---

## Запит 3. Знайти найактивніші зони

```cypher
MATCH (z:Zone)-[r:CONNECTED_TO]->()
RETURN z, COUNT(r) AS outgoing_connections, SUM(r.freq) AS total_trips
ORDER BY total_trips DESC
LIMIT 10
```

### Що показує

Цей запит знаходить зони, з яких було найбільше руху.

Тут студенти бачать, що граф можна аналізувати не лише візуально, але й аналітично.

Ідея:

> чим більше зв’язків і поїздок — тим важливіший транспортний хаб.

---

## Запит 4. Найпопулярніші маршрути

```cypher
MATCH p = (a:Zone)-[r:CONNECTED_TO]->(b:Zone)
RETURN p, r.freq AS trips, r.avg_cost AS avg_cost, r.avg_dist AS avg_dist
ORDER BY r.freq DESC
LIMIT 15
```

### Що показує

Цей запит показує найбільш завантажені коридори між зонами.

Це вже не просто граф структури, а граф інтенсивності руху.

Тут можна пояснити:

> ребро в графі може мати вагу, силу, вартість і сенс.

---

## Запит 5. BFS-логіка: зони на 1–2 кроки від pickup zone

```cypher
MATCH p = (:Zone {zone_id: 48})-[:CONNECTED_TO*1..2]->(:Zone)
RETURN p
LIMIT 60
```

### Що показує

Цей запит показує хвилю пошуку від зони `48`.

* `*1..2` означає: пройти від 1 до 2 зв’язків
* це схоже на BFS
* спочатку прямі сусіди
* потім сусіди сусідів

Ідея для пояснення:

> BFS — це поширення хвилі по графу.

---

## Запит 6. Ваговий маршрут: cheapest path idea

```cypher
MATCH p = (:Zone {zone_id: 48})-[rels:CONNECTED_TO*1..3]->(z:Zone)
WITH z, p,
     REDUCE(cost = 0.0, r IN rels | cost + r.avg_cost) AS total_cost
RETURN p, ROUND(total_cost, 2) AS total_cost
ORDER BY total_cost ASC
LIMIT 10
```

### Що показує

Цей запит шукає маршрути до 3 кроків і рахує їхню сумарну вартість.

Це демонструє ідею Dijkstra:

> не всі маршрути однакові; у кожного шляху є вартість.

---

## Запит 7. Показати маршрути з підписами

```cypher
MATCH p = (a:Zone {zone_id: 48})-[r:CONNECTED_TO]->(b:Zone)
RETURN 
    a.zone_id AS from_zone,
    b.zone_id AS to_zone,
    r.freq AS trips,
    r.avg_cost AS avg_cost,
    r.avg_dist AS avg_dist
ORDER BY r.freq DESC
LIMIT 15
```

### Що показує

Це табличний варіант 

```text
Graph view → інтуїція
Table view → аналітика
```

---

# Фінальна ідея


Neo4j потрібен не тому, що це “модна база”.

Neo4j потрібен тоді, коли головне питання звучить так:

> не “де лежать дані?”, а “як вони пов’язані?”

У задачі taxi dispatch це означає:

```text
pickup zone
    ↓
сусідні зони
    ↓
доступні водії
    ↓
найкращий маршрут
    ↓
рішення диспетчера
```

Граф перетворює дані з таблиці на систему.

___

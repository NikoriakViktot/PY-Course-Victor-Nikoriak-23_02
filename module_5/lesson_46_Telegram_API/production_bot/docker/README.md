# docker/ — допоміжні файли для контейнерів

## Структура

```
docker/
└── ssl/          ← SSL-сертифікати для Nginx (НЕ комітити в git!)
    ├── fullchain.pem
    └── privkey.pem
```

## Чому docker-compose.yml не тут?

`docker-compose.yml` знаходиться в корені проєкту (`production_bot/`) — це **стандартне** розміщення.  
Docker автоматично знаходить його при запуску `docker compose up` з директорії проєкту.

## Де знаходиться docker-compose.yml?

```
production_bot/
├── docker-compose.yml    ← ТУТ (корінь проєкту)
├── Dockerfile
├── docker/
│   └── ssl/              ← сюди кладемо сертифікати
├── nginx/
│   └── default.conf
└── ...
```

## Як отримати SSL-сертифікати

### Варіант 1: Let's Encrypt (production)

```bash
# Встановити certbot
sudo apt install certbot

# Отримати сертифікат (домен має вказувати на сервер)
sudo certbot certonly --standalone -d yourdomain.com

# Скопіювати у docker/ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem docker/ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem docker/ssl/
sudo chmod 644 docker/ssl/*.pem
```

### Варіант 2: Self-signed (розробка / тестування)

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout docker/ssl/privkey.pem \
    -out docker/ssl/fullchain.pem \
    -subj "/CN=localhost"
```

## Після отримання сертифікатів

```bash
# Запустити весь стек
docker compose up -d

# Перевірити стан
docker compose ps
docker compose logs nginx
```

## Важливо

- Файли `*.pem` і `*.key` **ніколи не комітити** в git (додані до .gitignore)
- `.gitkeep` в `ssl/` — технічний файл, щоб git відслідковував порожню папку
- Nginx читає сертифікати з `/etc/nginx/ssl/` всередині контейнера (volume: `./docker/ssl:/etc/nginx/ssl:ro`)

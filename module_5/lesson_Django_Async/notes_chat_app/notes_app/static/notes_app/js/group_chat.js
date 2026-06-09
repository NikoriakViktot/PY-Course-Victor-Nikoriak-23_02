/**
 * group_chat.js — WebSocket чат клієнт (vanilla JavaScript)
 *
 * ЯК ПРАЦЮЄ WebSocket API БРАУЗЕРА:
 * ───────────────────────────────────
 *
 * HTTP (класичний):
 *   Browser ──── GET /page ────► Server ──── Response ────► (з'єднання закрито)
 *   Кожен запит — нове TCP з'єднання. Сервер НЕ може ініціювати запит.
 *
 * WebSocket (цей файл):
 *   Browser ══ PERSISTENT TCP CONNECTION ══ Server
 *   Будь-яка сторона може надіслати дані в будь-який момент.
 *   Один раз відкрити — і тримати відкритим весь час.
 *
 * WebSocket API браузера (вбудований, не потребує бібліотек):
 *
 *   const ws = new WebSocket('ws://host/ws/groups/7/chat/')
 *              ↑ відкриває TCP з'єднання + HTTP Upgrade handshake
 *              ↑ ws:// для HTTP, wss:// для HTTPS (аналог http/https)
 *
 *   ws.onopen    = () => {...}    — з'єднання встановлено
 *   ws.onmessage = (event) => {...} — сервер надіслав дані (event.data = JSON рядок)
 *   ws.onerror   = (event) => {...} — помилка з'єднання
 *   ws.onclose   = (event) => {...} — з'єднання закрито (event.code = причина)
 *
 *   ws.send(JSON.stringify({content: "Привіт!"}))  — надіслати дані
 *   ws.close()                                      — закрити з'єднання
 *   ws.readyState === WebSocket.OPEN                — перевірка стану
 *
 * ЧОМУ ОДИН EVENT LOOP ТРИМАЄ ТИСЯЧІ З'ЄДНАНЬ?
 * ──────────────────────────────────────────────
 * На сервері кожне WebSocket з'єднання — це Consumer об'єкт у пам'яті.
 * Коли жодних повідомлень немає — Consumer просто "спить" у event loop.
 * CPU зайнятий тільки коли є що обробляти (нове повідомлення, connect/disconnect).
 * 10 000 відкритих з'єднань ≈ стільки ж RAM скільки 10 000 Python об'єктів.
 * Це і є перевага async: не "один потік на з'єднання", а "одна coroutine на з'єднання".
 */

// IIFE (Immediately Invoked Function Expression):
// Огортаємо весь код у функцію щоб уникнути глобальних змінних.
// (function() { ... })() — стандартна практика для vanilla JS модулів.
(function () {
    'use strict';

    // ── Config (з data-атрибутів HTML) ────────────────────────────────────────
    // Читаємо group_pk і username з #chat-config (div в group_chat.html).
    // dataset.groupPk ← data-group-pk (camelCase автоконверсія браузером).
    const config    = document.getElementById('chat-config');
    const GROUP_PK  = config.dataset.groupPk;
    const USERNAME  = config.dataset.username;

    // ── DOM refs ──────────────────────────────────────────────────────────────
    const messagesEl  = document.getElementById('chat-messages');
    const placeholderEl = document.getElementById('chat-placeholder');
    const inputEl     = document.getElementById('chat-input');
    const formEl      = document.getElementById('chat-form');
    const sendBtnEl   = document.getElementById('chat-send-btn');
    const statusDotEl = document.getElementById('status-dot');
    const statusTextEl = document.getElementById('status-text');

    // ── WebSocket URL ─────────────────────────────────────────────────────────
    // ws:// для HTTP, wss:// для HTTPS — аналог http/https.
    // location.host = "127.0.0.1:8001" (включає порт).
    // Важливо: використовуємо location.host щоб URL автоматично
    // підхоплював поточний хост (localhost, staging, production).
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const WS_URL   = `${protocol}://${window.location.host}/ws/groups/${GROUP_PK}/chat/`;

    let socket = null;
    let historyLoaded = false;

    // ── CONNECT ───────────────────────────────────────────────────────────────

    function connect() {
        setStatus('connecting');

        // new WebSocket(url):
        //   1. Браузер відкриває TCP з'єднання до сервера
        //   2. Надсилає HTTP GET з заголовком "Upgrade: websocket"
        //   3. Сервер відповідає HTTP 101 Switching Protocols
        //   4. З цього моменту — двосторонній WebSocket протокол
        //
        // Django Channels обробляє крок 2-3 автоматично через AuthMiddlewareStack.
        socket = new WebSocket(WS_URL);

        socket.onopen = function () {
            // З'єднання встановлено. Тепер можна надсилати/отримувати повідомлення.
            setStatus('connected');
            inputEl.disabled = false;
            sendBtnEl.disabled = false;
            inputEl.focus();
        };

        socket.onmessage = function (event) {
            // Сервер надіслав JSON рядок.
            // event.data — рядок (завжди, для текстових WS фреймів).
            let data;
            try {
                data = JSON.parse(event.data);
            } catch (e) {
                console.error('[chat] Невалідний JSON від сервера:', event.data);
                return;
            }

            // type='history' — повідомлення з БД при connect() (load_history у consumer)
            // type='message' — нове повідомлення в real-time (chat_message у consumer)
            if (data.type === 'history' || data.type === 'message') {
                if (!historyLoaded) {
                    // Перше повідомлення після connect → прибираємо placeholder
                    placeholderEl.style.display = 'none';
                    historyLoaded = true;
                }
                appendMessage(data);
            }
        };

        socket.onerror = function (event) {
            console.error('[chat] WebSocket помилка:', event);
            setStatus('error');
        };

        socket.onclose = function (event) {
            // event.code:
            //   1000 — нормальне закриття (браузер закрив вкладку або сервер відхилив)
            //   1001 — сторінка закривається
            //   1006 — аварійне (інтернет обірвався, сервер впав)
            setStatus('disconnected');
            inputEl.disabled = true;
            sendBtnEl.disabled = true;

            // Автоперепідключення через 3 секунди при аварійному закритті.
            // Не перепідключаємось при 1000/1001 (навмисне закриття).
            if (event.code !== 1000 && event.code !== 1001) {
                setTimeout(connect, 3000);
            }
        };
    }

    // ── SEND ──────────────────────────────────────────────────────────────────

    formEl.addEventListener('submit', function (event) {
        event.preventDefault(); // НЕ надсилати HTTP POST форму

        const content = inputEl.value.trim();
        if (!content) return;

        // Перевіряємо що з'єднання активне
        if (!socket || socket.readyState !== WebSocket.OPEN) return;

        // Надсилаємо JSON на сервер.
        // Сервер: consumer.receive(text_data) → json.loads(text_data)
        socket.send(JSON.stringify({ content: content }));

        inputEl.value = '';
        inputEl.focus();
    });

    // Enter → submit (Shift+Enter → новий рядок)
    inputEl.addEventListener('keydown', function (event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            formEl.dispatchEvent(new Event('submit'));
        }
    });

    // ── RENDER MESSAGE ────────────────────────────────────────────────────────

    function appendMessage(data) {
        // isMine: чи це наше власне повідомлення?
        // Свої → правіше (justify-content-end), чужі → лівіше (justify-content-start).
        const isMine = data.author === USERNAME;

        // Форматуємо час із ISO рядка (напр. "2024-06-07T14:23:05.123456+00:00")
        const time = new Date(data.timestamp).toLocaleTimeString('uk-UA', {
            hour: '2-digit',
            minute: '2-digit',
        });

        // Bootstrap flex layout: wrapper розташовує бульбашку ліворуч або праворуч
        const wrapper = document.createElement('div');
        wrapper.className = `d-flex mb-2 ${isMine ? 'justify-content-end' : 'justify-content-start'}`;
        if (data.message_id) {
            wrapper.dataset.messageId = data.message_id;
        }

        // ВАЖЛИВО: escapeHtml() перед будь-яким user content!
        // Без цього зловмисник може ввести <script>alert('XSS')</script>
        // і браузер його виконає.
        wrapper.innerHTML = `
          <div class="chat-bubble ${isMine ? 'chat-mine' : 'chat-other'}">
            ${!isMine ? `<div class="chat-author">${escapeHtml(data.author)}</div>` : ''}
            <div class="chat-content">${escapeHtml(data.content)}</div>
            <div class="chat-time">${time}</div>
          </div>`;

        messagesEl.appendChild(wrapper);

        // Автоскрол до останнього повідомлення.
        // scrollTop = scrollHeight → прокручує до самого низу.
        messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    // ── STATUS INDICATOR ─────────────────────────────────────────────────────

    const STATUS_CONFIG = {
        connecting:   { color: '#ffc107', text: 'Підключення...' },
        connected:    { color: '#198754', text: 'Підключено' },
        disconnected: { color: '#6c757d', text: 'Відключено. Перепідключення через 3 сек...' },
        error:        { color: '#dc3545', text: 'Помилка з\'єднання' },
    };

    function setStatus(key) {
        const cfg = STATUS_CONFIG[key] || STATUS_CONFIG.error;
        statusDotEl.style.background = cfg.color;
        statusTextEl.textContent = cfg.text;
    }

    // ── XSS PREVENTION ───────────────────────────────────────────────────────

    /**
     * Екранує HTML спецсимволи.
     *
     * НІКОЛИ не вставляти user content через innerHTML без цієї функції!
     * Інакше зловмисник може надіслати повідомлення:
     *   <img src=x onerror="document.cookie → зовнішній сервер">
     * і отримати cookie інших користувачів (XSS атака).
     *
     * textContent безпечний (не парсить HTML), але ми використовуємо
     * innerHTML для flex-layout бульбашок, тому escapeHtml() обов'язковий.
     */
    function escapeHtml(str) {
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    // ── START ─────────────────────────────────────────────────────────────────

    // Відключити input до встановлення з'єднання
    inputEl.disabled = true;
    sendBtnEl.disabled = true;

    // Відкрити WebSocket з'єднання
    connect();

}());

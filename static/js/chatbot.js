(function () {
    const configEl = document.getElementById('agro-chatbot-config');
    if (!configEl) return;

    const config = {
        url: configEl.dataset.url,
        userName: configEl.dataset.userName || 'utilizador',
        userRole: configEl.dataset.userRole || 'Visitante',
        csrf: configEl.dataset.csrf,
    };

    const state = {
        open: false,
        voiceEnabled: localStorage.getItem('agro_chat_voice') === 'on',
        history: [],
    };

    function cleanSpeechText(text) {
        return (text || '')
            .replace(/https?:\/\/\S+/gi, '')
            .replace(/[*#_\x60]/g, ' ')
            .replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1')
            .replace(/[\[\]{}()<>|~^=+]/g, ' ')
            .replace(/[•●▪►▶✓✔✅⚠️🌱🌾@©®™§¶]/g, ' ')
            .replace(/[\u{1F000}-\u{1FAFF}]/gu, ' ')
            .replace(/[-–—]{2,}/g, '. ')
            .replace(/°\s*C/gi, ' graus Celsius')
            .replace(/km\s*\/\s*h/gi, ' quilómetros por hora')
            .replace(/(\d+(?:[.,]\d+)?)%/g, '$1 por cento')
            .replace(/\s+/g, ' ')
            .trim();
    }

    function createEl(tag, className, text) {
        const el = document.createElement(tag);
        if (className) el.className = className;
        if (text) el.textContent = text;
        return el;
    }

    function speak(text, force = false) {
        text = cleanSpeechText(text);
        if (!text) return;
        if ((!force && !state.voiceEnabled) || !('speechSynthesis' in window)) return;
        if (window.AgroVisionVoice) {
            window.AgroVisionVoice.speak(text, { rate: 0.9, pitch: 1.08, silent: true });
            return;
        }
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = 'pt-PT';
        utterance.rate = 0.9;
        utterance.pitch = 1.08;
        window.speechSynthesis.speak(utterance);
    }

    function addMessage(list, text, type) {
        const item = createEl('div', `agro-chat-message ${type}`);
        const content = createEl('span', '', text);
        item.appendChild(content);
        if (type === 'bot') {
            const listen = createEl('button', 'agro-chat-listen');
            listen.type = 'button';
            listen.title = 'Ouvir esta resposta';
            listen.innerHTML = '<i class="fas fa-volume-high"></i>';
            listen.addEventListener('click', () => {
                const previous = state.voiceEnabled;
                state.voiceEnabled = true;
                speak(text);
                state.voiceEnabled = previous;
            });
            item.appendChild(listen);
        }
        list.appendChild(item);
        list.scrollTop = list.scrollHeight;
    }

    async function ask(message, list) {
        addMessage(list, message, 'user');
        state.history.push('Utilizador: ' + message);
        state.history = state.history.slice(-6);
        try {
            const response = await fetch(config.url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': config.csrf,
                },
                body: JSON.stringify({ mensagem: message, historico: state.history }),
            });
            const data = await response.json();
            const answer = data.resposta || 'Não consegui responder agora.';
            addMessage(list, answer, 'bot');
            state.history.push('Assistente: ' + answer);
            state.history = state.history.slice(-6);
            speak(answer);
        } catch (error) {
            const fallback = 'Não foi possível contactar o assistente interno.';
            addMessage(list, fallback, 'bot');
            speak(fallback);
        }
    }

    function buildWidget() {
        const root = createEl('div', 'agro-chatbot');
        const toggle = createEl('button', 'agro-chat-toggle');
        toggle.type = 'button';
        toggle.innerHTML = '<i class="fas fa-comments"></i>';

        const panel = createEl('section', 'agro-chat-panel');
        panel.innerHTML = `
            <div class="agro-chat-header">
                <div>
                    <strong>Assistente AgroVision</strong>
                    <small>${config.userRole}</small>
                </div>
                <button type="button" class="agro-chat-close" aria-label="Fechar"><i class="fas fa-times"></i></button>
            </div>
            <div class="agro-chat-messages"></div>
            <div class="agro-chat-suggestions">
                <button type="button" data-question="Como funciona o meu perfil?">Perfil</button>
                <button type="button" data-question="Mostra o meu resumo">Resumo</button>
                <button type="button" data-question="Como usar meteorologia?">Meteorologia</button>
                <button type="button" data-question="Ajuda-me a começar uma tarefa desta área">Guia da área</button>
            </div>
            <form class="agro-chat-form">
                <button type="button" class="agro-chat-voice" title="Falar pergunta"><i class="fas fa-microphone"></i></button>
                <input type="text" placeholder="Pergunte ao assistente..." autocomplete="off">
                <button type="submit" title="Enviar"><i class="fas fa-paper-plane"></i></button>
            </form>
            <button type="button" class="agro-chat-sound"></button>
        `;

        root.appendChild(toggle);
        root.appendChild(panel);
        document.body.appendChild(root);

        const messages = panel.querySelector('.agro-chat-messages');
        const form = panel.querySelector('.agro-chat-form');
        const input = form.querySelector('input');
        const soundButton = panel.querySelector('.agro-chat-sound');
        const voiceButton = panel.querySelector('.agro-chat-voice');

        function updateSoundLabel() {
            soundButton.innerHTML = state.voiceEnabled
                ? '<i class="fas fa-volume-high"></i> Voz automática ligada'
                : '<i class="fas fa-volume-high"></i> Ativar respostas por voz';
        }
        updateSoundLabel();

        toggle.addEventListener('click', () => {
            state.open = true;
            root.classList.add('is-open');
            input.focus();
        });

        panel.querySelector('.agro-chat-close').addEventListener('click', () => {
            state.open = false;
            root.classList.remove('is-open');
        });

        form.addEventListener('submit', (event) => {
            event.preventDefault();
            const message = input.value.trim();
            if (!message) return;
            input.value = '';
            ask(message, messages);
        });

        panel.querySelectorAll('[data-question]').forEach((button) => {
            button.addEventListener('click', () => ask(button.dataset.question, messages));
        });

        soundButton.addEventListener('click', () => {
            state.voiceEnabled = !state.voiceEnabled;
            localStorage.setItem('agro_chat_voice', state.voiceEnabled ? 'on' : 'off');
            updateSoundLabel();
            if (state.voiceEnabled) speak('Voz do assistente ativada.');
            else window.speechSynthesis && window.speechSynthesis.cancel();
        });

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (SpeechRecognition) {
            const recognition = new SpeechRecognition();
            recognition.lang = 'pt-PT';
            recognition.interimResults = false;
            recognition.maxAlternatives = 1;

            voiceButton.addEventListener('click', () => recognition.start());
            recognition.addEventListener('result', (event) => {
                input.value = event.results[0][0].transcript;
                form.requestSubmit();
            });
        } else {
            voiceButton.disabled = true;
            voiceButton.title = 'Reconhecimento de voz indisponível neste navegador.';
        }

        const agricultor = config.userRole.toLowerCase().includes('agricultor');
        const apoio = agricultor ? ' Também posso conversar consigo sobre plantio, solo, rega, culturas e prevenção de doenças. Para orientar melhor, diga a cultura, o local e o que está a observar.' : '';
        const hello = 'Olá, ' + config.userName + '. Como posso ajudar hoje? Sou o assistente da AgroVision e reconheci o seu perfil como ' + config.userRole + '. Posso explicar o seu painel e acompanhar as suas dúvidas passo a passo.' + apoio;
        state.history.push('Assistente: ' + hello);
        addMessage(messages, hello, 'bot');

        const key = `agro_voice_greeted_${config.userName}_${config.userRole}`;
        if (!sessionStorage.getItem(key)) {
            setTimeout(() => speak(hello, true), 700);
            sessionStorage.setItem(key, '1');
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', buildWidget);
    } else {
        buildWidget();
    }
})();

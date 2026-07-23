(function () {
    const supportsVoice = 'speechSynthesis' in window;
    const synth = supportsVoice ? window.speechSynthesis : null;
    let selectedVoice = null;

    const preferredNames = [
        'maria', 'francisca', 'joana', 'catarina', 'inês', 'ines',
        'fernanda', 'luciana', 'helia', 'google português', 'google portugues'
    ];
    const lessNaturalNames = ['desktop', 'male', 'masculino', 'daniel', 'duarte', 'antonio', 'antónio'];

    function scoreVoice(voice) {
        const name = (voice.name || '').toLowerCase();
        const lang = (voice.lang || '').toLowerCase();
        let score = 0;
        if (lang === 'pt-pt') score += 80;
        else if (lang === 'pt-br') score += 70;
        else if (lang.startsWith('pt')) score += 55;
        if (preferredNames.some((item) => name.includes(item))) score += 45;
        if (name.includes('natural') || name.includes('online')) score += 30;
        if (name.includes('microsoft') || name.includes('google')) score += 12;
        if (voice.localService === false) score += 8;
        if (lessNaturalNames.some((item) => name.includes(item))) score -= 35;
        return score;
    }

    function chooseVoice() {
        if (!supportsVoice) return null;
        const voices = synth.getVoices();
        selectedVoice = voices
            .filter((voice) => (voice.lang || '').toLowerCase().startsWith('pt'))
            .sort((a, b) => scoreVoice(b) - scoreVoice(a))[0] || voices[0] || null;
        return selectedVoice;
    }

    function cleanText(text) {
        return (text || '')
            .replace(/https?:\/\/\S+/gi, '')
            .replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1')
            .replace(/[*#_\x60~|^=+<>{}\[\]]/g, ' ')
            .replace(/[\u{1F000}-\u{1FAFF}]/gu, ' ')
            .replace(/°\s*C/gi, ' graus Celsius')
            .replace(/\bC\b(?=\s*[;,.])/g, ' graus Celsius')
            .replace(/km\s*\/\s*h/gi, ' quilómetros por hora')
            .replace(/\bmm\b/gi, ' milímetros')
            .replace(/\bha\b/gi, ' hectares')
            .replace(/(\d+(?:[.,]\d+)?)%/g, '$1 por cento')
            .replace(/\s+/g, ' ')
            .replace(/[✅⚙️]/g, '')
            .replace(/([.!?])\s*/g, '$1 ')
            .trim();
    }

    function speak(text, options = {}) {
        if (!supportsVoice) {
            if (!options.silent) alert('A leitura por voz não está disponível neste navegador.');
            return;
        }
        const content = cleanText(text);
        if (!content) return;
        synth.cancel();
        const utterance = new SpeechSynthesisUtterance(content);
        const voice = selectedVoice || chooseVoice();
        if (voice) {
            utterance.voice = voice;
            utterance.lang = voice.lang || 'pt-PT';
        } else {
            utterance.lang = 'pt-PT';
        }
        utterance.rate = options.rate || 0.89;
        utterance.pitch = options.pitch || 1.08;
        utterance.volume = 1;
        synth.speak(utterance);
    }

    function areaExplanation(fallback) {
        if ((fallback || '').includes('Encontrei a meteorologia')) return fallback;
        const path = window.location.pathname.toLowerCase();
        const areas = [
            [['meteorologia', 'previsao'], 'Nesta área pode pesquisar uma localidade, consultar a condição atual e a previsão de sete dias, ouvir a análise agrícola e identificar riscos para rega, pulverização, calor, chuva e doenças.'],
            [['alertas'], 'Nesta área pode consultar alertas meteorológicos e agrícolas, filtrar por severidade e marcar cada alerta como lido depois de o analisar.'],
            [['recomend'], 'Nesta área pode gerar recomendações agronómicas automáticas por talhão, rever o diagnóstico, definir a prioridade, acompanhar o estado e exportar o resultado em PDF.'],
            [['visita'], 'Nesta área pode planear e registar visitas técnicas, descrever observações de campo e anexar fotografias como evidência.'],
            [['praga'], 'Nesta área pode registar pragas e doenças por talhão, indicar a severidade, anexar fotografias, acompanhar o tratamento e confirmar a resolução.'],
            [['talh'], 'Nesta área pode organizar os talhões de cada propriedade, indicar área, cultura, solo, estado fenológico e fotografia atual.'],
            [['propriedad'], 'Nesta área pode registar e consultar propriedades, localização, coordenadas, proprietário, consultor responsável e fotografia da fazenda.'],
            [['cultura'], 'Nesta área pode gerir as culturas agrícolas usadas nos talhões e as respetivas informações de referência.'],
            [['relatorio'], 'Nesta área pode consultar indicadores, gráficos, produção registada, riscos e previsões usadas na análise e na apresentação do sistema.'],
            [['utilizador'], 'Nesta área o administrador pode consultar utilizadores, perfis, estados de aprovação e permissões de acesso.'],
            [['config'], 'Nesta área o administrador pode configurar os provedores meteorológicos e a inteligência artificial, testar ligações e controlar quais integrações estão ativas.'],
            [['mensagen', 'atendimento'], 'Nesta área pode enviar pedidos ou reclamações, acompanhar respostas e manter o histórico de comunicação com a administração.'],
            [['dashboard'], 'Esta é a área principal. Aqui pode ver um resumo das informações e abrir os módulos permitidos para o seu perfil.']
        ];
        for (const [keys, explanation] of areas) {
            if (keys.some((key) => path.includes(key))) return explanation;
        }
        return fallback;
    }

    function controlPurpose(label) {
        const name = label.toLowerCase();
        const purposes = [
            [['propriedade'], 'seleciona a fazenda relacionada com este registo'],
            [['talhão', 'talhao'], 'seleciona a área específica da propriedade que será analisada'],
            [['cultura'], 'identifica o produto ou planta cultivada'],
            [['solo'], 'regista as características do terreno usadas na análise agrícola'],
            [['localização', 'localizacao', 'cidade'], 'indica o local usado nas consultas e previsões'],
            [['temperatura'], 'informa o nível de calor considerado na análise'],
            [['humidade'], 'mostra a quantidade de humidade do ar'],
            [['vento'], 'indica a velocidade do vento e possíveis riscos operacionais'],
            [['quantidade'], 'regista o volume produzido, disponível ou pretendido'],
            [['data'], 'define quando o acontecimento ocorreu ou deverá ocorrer'],
            [['prioridade'], 'indica a urgência com que o assunto deve ser tratado'],
            [['estado', 'status'], 'mostra a fase atual do processo'],
            [['foto', 'imagem', 'ficheiro'], 'permite anexar evidência visual para análise'],
            [['observa'], 'recebe informações adicionais importantes'],
            [['mensagem', 'descrição', 'descricao'], 'permite explicar a situação com detalhes'],
            [['contacto', 'telefone', 'email', 'e-mail'], 'informa como o responsável poderá responder'],
            [['senha', 'password'], 'permite autenticar a conta e nunca será lida em voz alta'],
        ];
        for (const [keys, purpose] of purposes) if (keys.some((key) => name.includes(key))) return purpose;
        return 'serve para preencher a informação indicada antes de continuar';
    }

    function explainVisibleControls() {
        const parts = [];
        const seen = new Set();
        document.querySelectorAll('main label').forEach((label) => {
            if (parts.length >= 12 || label.offsetParent === null) return;
            const text = cleanText(label.innerText || label.textContent).replace(/\s*\*\s*$/, '');
            if (!text || seen.has(text.toLowerCase())) return;
            seen.add(text.toLowerCase());
            parts.push('O campo ' + text + ' ' + controlPurpose(text) + '.');
        });
        const buttons = [];
        document.querySelectorAll('main button, main a.btn').forEach((button) => {
            if (buttons.length >= 8 || button.offsetParent === null || button.hasAttribute('data-speech-stop')) return;
            const text = cleanText(button.innerText || button.textContent);
            if (text && !buttons.includes(text) && !/ouvir|explicar esta área/i.test(text)) buttons.push(text);
        });
        if (buttons.length) parts.push('As ações disponíveis nesta página são: ' + buttons.join(', ') + '.');
        const table = document.querySelector('main table');
        if (table && table.offsetParent !== null) {
            const heads = [...table.querySelectorAll('thead th')].map((item) => cleanText(item.innerText)).filter(Boolean).slice(0, 10);
            if (heads.length) parts.push('A tabela organiza as informações pelas colunas: ' + heads.join(', ') + '.');
        }
        return parts.join(' ');
    }

    function textFromTarget(button) {
        const direct = button.dataset.speech;
        if (direct) return direct;
        const selector = button.dataset.speechTarget;
        if (!selector) return '';
        const target = document.querySelector(selector);
        const content = target ? (target.innerText || target.textContent) : '';
        if (selector === '#explicacao-contextual') {
            const heading = document.querySelector('.page-header h1');
            const area = heading ? cleanText(heading.innerText || heading.textContent) : '';
            const explanation = areaExplanation(content);
            const controls = explainVisibleControls();
            const complete = controls ? explanation + ' Agora vou explicar os elementos desta página. ' + controls : explanation;
            return area ? ('Área ' + area + '. ' + complete) : complete;
        }
        return content;
    }

    function initVoiceButtons() {
        chooseVoice();
        document.querySelectorAll('[data-speech], [data-speech-target]').forEach((button) => {
            button.addEventListener('click', () => speak(textFromTarget(button)));
        });
        document.querySelectorAll('[data-speech-stop]').forEach((button) => {
            button.addEventListener('click', () => supportsVoice && synth.cancel());
        });
        const automatic = document.querySelector('[data-speech-auto]');
        if (automatic && sessionStorage.getItem('agrovision-explain-weather') === 'yes') {
            sessionStorage.removeItem('agrovision-explain-weather');
            setTimeout(() => speak(textFromTarget({ dataset: { speechTarget: '#explicacao-contextual' } }), { rate: 0.91 }), 450);
        }
        document.querySelectorAll('[data-weather-search]').forEach((form) => {
            form.addEventListener('submit', () => sessionStorage.setItem('agrovision-explain-weather', 'yes'));
        });
    }

    if (supportsVoice) {
        synth.addEventListener('voiceschanged', chooseVoice);
        setTimeout(chooseVoice, 250);
    }

    window.AgroVisionVoice = {
        speak,
        stop: () => supportsVoice && synth.cancel(),
        refresh: chooseVoice,
        getVoiceName: () => selectedVoice ? selectedVoice.name : '',
    };

    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initVoiceButtons);
    else initVoiceButtons();
})();

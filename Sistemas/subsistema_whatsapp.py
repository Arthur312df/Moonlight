import os
import time
import queue
import threading
import logging
import unicodedata
from playwright.sync_api import sync_playwright

class SubsistemaWhatsApp:
    def __init__(self, callback_alerta=None):
        self.callback_alerta = callback_alerta
        self.ativo = False
        self.thread_monitor = None
        
        self.estado_whatsapp = {
            "carregado": False,
            "total_badge_global": 0,
            "conversas_nao_lidas": [],
            "topo_da_lista": []
        }
        
        self.lock_estado = threading.Lock()
        self.fila_comandos = queue.Queue()
        self.ultimas_nao_lidas_conhecidas = {}
        
        self.diretorio_sessao = os.path.abspath("./whatsapp_session")
        logging.info("📱 [Subsistema WhatsApp]: Módulo inicializado.")

    def iniciar(self):
        if self.ativo:
            return
        self.ativo = True
        self.thread_monitor = threading.Thread(target=self._loop_monitoramento_web, daemon=True)
        self.thread_monitor.start()
        print("📱 [Subsistema WhatsApp]: Monitoramento proativo em tempo real iniciado em background.")

    def parar(self):
        self.ativo = False
        print("📱 [Subsistema WhatsApp]: Parando monitoramento...")

    def solicitar_leitura_contato(self, contato_alvo=None):
        with self.lock_estado:
            carregado = self.estado_whatsapp["carregado"]
            nao_lidas = list(self.estado_whatsapp["conversas_nao_lidas"])
            total_global = self.estado_whatsapp["total_badge_global"]

        if not carregado:
            return ("Ainda estou conectando ao WhatsApp Web em segundo plano, Arthur. Me dê mais alguns segundos.", [])

        if contato_alvo and contato_alvo.lower() not in ["whatsapp", "zap", "todos", "nao lidas", "não lidas"]:
            print(f"🔍 [Subsistema WhatsApp]: Consultando conversa específica de '{contato_alvo}'...")
            evento_concluido = threading.Event()
            resultado_container = {"texto": "", "mensagens": []}
            
            self.fila_comandos.put(("ler_contato", contato_alvo, resultado_container, evento_concluido))
            if evento_concluido.wait(timeout=15.0):
                return (resultado_container["texto"], resultado_container["mensagens"])
            return (f"Demorei muito para abrir a conversa de {contato_alvo}, Arthur.", [])

        print("⚡ [Subsistema WhatsApp]: A consultar estado instantâneo da cache...")
        if not nao_lidas:
            if total_global > 0:
                return (f"Arthur, o WhatsApp indica {total_global} conversas não lidas arquivadas ou mais antigas na lista.", [])
            return ("Não encontrei nenhuma mensagem não lida no momento, Arthur.", [])

        total = max(len(nao_lidas), total_global)
        detalhes = ", ".join([f"de {nome} dizendo: {msg}" for nome, msg in nao_lidas])
        resposta_texto = f"Arthur, você tem {total} conversas não lidas: {detalhes}."
        return (resposta_texto, nao_lidas)

    def enviar_mensagem(self, contato_alvo, texto_mensagem):
        with self.lock_estado:
            if not self.estado_whatsapp["carregado"]:
                return False
        self.fila_comandos.put(("enviar", contato_alvo, texto_mensagem, None))
        return True

    def marcar_como_lida(self, contato_alvo):
        self.fila_comandos.put(("marcar_lida", contato_alvo, None, None))
        return True

    def _injetar_bypass_visibilidade(self, page):
        try:
            page.evaluate("""
            () => {
                Object.defineProperty(document, 'hidden', { get: () => false, configurable: true });
                Object.defineProperty(document, 'visibilityState', { get: () => 'visible', configurable: true });
                document.hasFocus = () => true;
                window.dispatchEvent(new Event('focus'));
                document.dispatchEvent(new Event('visibilitychange'));
            }
            """)
        except Exception:
            pass

    def _limpar_pesquisa(self, page):
        try:
            page.evaluate("""
            () => {
                const btnCancel = document.querySelector('#side button[aria-label*="Cancelar" i], #side button[aria-label*="Cancel" i], #side span[data-icon="x-alt"], #side span[data-icon="back"]');
                if (btnCancel) {
                    btnCancel.click();
                } else {
                    const side = document.querySelector('#side');
                    if (side) {
                        const box = side.querySelector('div[contenteditable="true"], input[type="text"]');
                        if (box) {
                            box.focus();
                            document.execCommand('selectAll', false, null);
                            document.execCommand('delete', false, null);
                        }
                    }
                }
            }
            """)
            time.sleep(0.3)
        except Exception:
            pass

    def _abrir_conversa_por_pesquisa(self, page, contato_alvo):
        if page.is_closed():
            raise Exception("A página do navegador foi fechada.")

        try:
            page.bring_to_front()
        except Exception:
            pass
        self._injetar_bypass_visibilidade(page)

        print(f"   ↳ [Passo 1/4]: Focando na barra de pesquisa para buscar '{contato_alvo}'...")
        coord_pesquisa = page.evaluate("""
        () => {
            const botoes = Array.from(document.querySelectorAll('div[role="button"], button, span'));
            const abaTudo = botoes.find(el => el.innerText && el.innerText.trim() === 'Tudo');
            if (abaTudo) abaTudo.click();

            const side = document.querySelector('#side');
            if (!side) return null;

            const searchIcon = side.querySelector('span[data-icon="search"], button[aria-label*="Pesquisar" i], button[aria-label*="Search" i]');
            if (searchIcon) searchIcon.click();

            const editables = Array.from(side.querySelectorAll('div[contenteditable="true"], input[type="text"]'));
            if (editables.length > 0) {
                const searchBox = editables[0];
                searchBox.focus();
                const rect = searchBox.getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0) {
                    return { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 };
                }
            }
            return null;
        }
        """)

        if coord_pesquisa:
            page.mouse.click(coord_pesquisa["x"], coord_pesquisa["y"])
        else:
            page.keyboard.press("Control+Alt+Slash")
        
        time.sleep(0.2)
        page.keyboard.press("Control+A")
        page.keyboard.press("Backspace")
        time.sleep(0.1)

        print(f"   ↳ [Passo 2/4]: Digitando '{contato_alvo}' na busca...")
        # Usa APENAS insert_text nativo do Playwright (sem duplicar com InputEvent)
        page.keyboard.insert_text(contato_alvo)
        time.sleep(1.0)

        print(f"   ↳ [Passo 3/4]: Selecionando contato '{contato_alvo}' na lista...")
        coordenadas = page.evaluate("""
        (alvo) => {
            const normalizar = (str) => str.normalize('NFD').replace(/[\\u0300-\\u036f]/g, '').toLowerCase().trim();
            const alvoNorm = normalizar(alvo);
            const ignorar = ['tudo', 'nao lidas', 'favoritas', 'grupos', 'canais', 'status', 'comunidades', 'mensagens', 'contatos', 'conversas'];

            const pane = document.querySelector('#pane-side');
            if (!pane) return null;

            const spans = Array.from(pane.querySelectorAll('span[title]'));
            let melhorElemento = null;

            for (let sp of spans) {
                const titulo = sp.getAttribute('title') || '';
                const tNorm = normalizar(titulo);
                if (!tNorm || ignorar.includes(tNorm)) continue;
                if (tNorm === alvoNorm || tNorm.startsWith(alvoNorm)) {
                    melhorElemento = sp;
                    break;
                }
            }

            if (!melhorElemento) {
                for (let sp of spans) {
                    const titulo = sp.getAttribute('title') || '';
                    const tNorm = normalizar(titulo);
                    if (!tNorm || ignorar.includes(tNorm)) continue;
                    if (tNorm.includes(alvoNorm)) {
                        melhorElemento = sp;
                        break;
                    }
                }
            }

            if (melhorElemento) {
                const row = melhorElemento.closest('div[role="listitem"], div[role="row"], div[tabindex="-1"]') || melhorElemento;
                row.scrollIntoView({ behavior: 'instant', block: 'center' });
                const rect = row.getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0) {
                    return { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2, nome: melhorElemento.getAttribute('title') };
                }
            }
            return null;
        }
        """, contato_alvo)

        if coordenadas:
            print(f"   ↳ [Contato Encontrado]: Clicando em '{coordenadas['nome']}' nas coordenadas ({int(coordenadas['x'])}, {int(coordenadas['y'])})...")
            page.mouse.click(coordenadas["x"], coordenadas["y"])
        else:
            print("   ↳ [Aviso]: Nome exato não listado nos spans, pressionando Enter na busca...")
            page.keyboard.press("ArrowDown")
            time.sleep(0.2)
            page.keyboard.press("Enter")

        time.sleep(1.0)

    def _executar_envio_seguro(self, page, contato_alvo, texto_mensagem):
        print(f"📱 [Subsistema WhatsApp]: Abrindo conversa de '{contato_alvo}' para enviar: '{texto_mensagem}'")
        try:
            if page.is_closed():
                print("❌ [Erro]: O navegador do WhatsApp está fechado.")
                return

            if contato_alvo:
                self._abrir_conversa_por_pesquisa(page, contato_alvo)

            print("   ↳ [Passo 4/4]: Inserindo mensagem única e disparando envio...")
            coord_caixa = None
            for _ in range(15):
                coord_caixa = page.evaluate("""
                () => {
                    const main = document.querySelector('#main');
                    if (!main) return null;
                    const box = main.querySelector('footer div[contenteditable="true"], div[contenteditable="true"][data-tab="10"], div[contenteditable="true"]');
                    if (!box) return null;
                    box.focus();
                    const rect = box.getBoundingClientRect();
                    if (rect.width > 0 && rect.height > 0) {
                        return { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 };
                    }
                    return null;
                }
                """)
                if coord_caixa:
                    break
                time.sleep(0.25)

            if not coord_caixa:
                print(f"❌ [Erro]: O chat de '{contato_alvo}' não abriu a caixa de mensagem.")
                self._limpar_pesquisa(page)
                return

            # 1. Clica fisicamente na caixa de texto do chat e limpa qualquer rascunho
            page.mouse.click(coord_caixa["x"], coord_caixa["y"])
            time.sleep(0.15)
            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")
            time.sleep(0.15)

            # 2. Insere o texto UMA ÚNICA VEZ via API nativa do Playwright (não duplica no Lexical!)
            page.keyboard.insert_text(texto_mensagem)
            time.sleep(0.3)

            # 3. Aperta Enter para enviar
            page.keyboard.press("Enter")
            time.sleep(0.5)

            # 4. Só clica no botão de Enviar se o texto AINDA estiver preso na caixa (evita duplo envio)
            page.evaluate("""
            () => {
                const main = document.querySelector('#main');
                if (!main) return;
                const box = main.querySelector('footer div[contenteditable="true"], div[contenteditable="true"][data-tab="10"]');
                if (box && box.innerText && box.innerText.trim().length > 0) {
                    const btnSend = main.querySelector('button[aria-label*="Enviar" i], button[aria-label*="Send" i], span[data-icon="send"]');
                    if (btnSend) {
                        const clickable = btnSend.closest('button') || btnSend;
                        clickable.click();
                    }
                }
            }
            """)

            time.sleep(0.5)
            self._limpar_pesquisa(page)
            print(f"✅ [Subsistema WhatsApp]: Mensagem enviada com sucesso para '{contato_alvo}'!")

        except Exception as e:
            print(f"❌ [Erro ao enviar mensagem no WhatsApp para '{contato_alvo}']: {e}")
            self._limpar_pesquisa(page)

    def _executar_marcar_lida(self, page, contato_alvo):
        print(f"👁️ [Subsistema WhatsApp]: Forçando 2 tracinhos azuis (leitura real) para '{contato_alvo}'...")
        try:
            if page.is_closed():
                return

            self._abrir_conversa_por_pesquisa(page, contato_alvo)
            self._injetar_bypass_visibilidade(page)
            
            page.evaluate("""
            () => {
                const mainPanel = document.querySelector('#main');
                if (mainPanel) {
                    const scrollables = mainPanel.querySelectorAll('div');
                    for (let d of scrollables) {
                        if (d.scrollHeight > d.clientHeight) {
                            d.scrollTop = d.scrollHeight;
                        }
                    }
                    const msgs = mainPanel.querySelectorAll('div.message-in');
                    if (msgs.length > 0) {
                        const lastMsg = msgs[msgs.length - 1];
                        lastMsg.scrollIntoView({ behavior: 'instant', block: 'end' });
                        lastMsg.click();
                    }
                    const box = mainPanel.querySelector('footer div[contenteditable="true"], div[contenteditable="true"]');
                    if (box) box.focus();
                }
            }
            """)
            
            page.mouse.wheel(0, 500)
            time.sleep(1.2)
            self._limpar_pesquisa(page)
            
            with self.lock_estado:
                self.estado_whatsapp["conversas_nao_lidas"] = [
                    (r, m) for r, m in self.estado_whatsapp["conversas_nao_lidas"]
                    if contato_alvo.lower() not in r.lower()
                ]
                
            print(f"✅ [Subsistema WhatsApp]: Leitura confirmada e 2 tracinhos azuis enviados para '{contato_alvo}'!")
        except Exception as e:
            print(f"❌ [Erro ao marcar como lida]: {e}")
            self._limpar_pesquisa(page)

    def _executar_leitura_especifica(self, page, contato_alvo, resultado_container):
        try:
            if page.is_closed():
                return

            self._injetar_bypass_visibilidade(page)
            self._abrir_conversa_por_pesquisa(page, contato_alvo)
            self._limpar_pesquisa(page)

            dados_chat = page.evaluate("""
            () => {
                const headerTitle = document.querySelector('#main header span[title]');
                const nomeChat = headerTitle ? headerTitle.getAttribute('title') : "Contato";
                
                const rows = Array.from(document.querySelectorAll('#main div.message-in, #main div.message-out'));
                if (rows.length === 0) return { nome: nomeChat, ultimas: [], ultima_foi_dela: false };
                
                const ultimas = [];
                rows.slice(-4).forEach(r => {
                    const isIn = r.classList.contains('message-in');
                    const textEls = Array.from(r.querySelectorAll('span.selectable-text, span.selectable-text span, span[dir="ltr"]'));
                    let texto = textEls.map(e => e.innerText ? e.innerText.trim() : "").filter(Boolean).join(' ');
                    
                    if (!texto) {
                        const docEl = r.querySelector('span[title$=".pdf"], span[title$=".docx"], span[title$=".png"], span[title$=".jpg"]');
                        if (docEl) {
                            texto = "Documento ou arquivo: " + docEl.getAttribute('title');
                        } else {
                            texto = "Figurinha, áudio ou mídia recebida";
                        }
                    }
                    
                    if (texto) {
                        ultimas.push({ autor: isIn ? nomeChat : 'Você', texto: texto, recebida: isIn });
                    }
                });
                
                const ultima_foi_dela = ultimas.length > 0 ? ultimas[ultimas.length - 1].recebida : false;
                return { nome: nomeChat, ultimas: ultimas, ultima_foi_dela: ultima_foi_dela };
            }
            """)

            nome_real = dados_chat.get("nome", contato_alvo)
            ultimas = dados_chat.get("ultimas", [])
            ultima_foi_dela = dados_chat.get("ultima_foi_dela", False)

            if not ultimas:
                resultado_container["texto"] = f"Abri a conversa com {nome_real}, Arthur, mas não encontrei mensagens de texto recentes."
                return

            ultima_msg = ultimas[-1]["texto"]
            if ultima_foi_dela:
                resultado_container["texto"] = f"Arthur, na conversa com {nome_real}, a última mensagem diz: {ultima_msg}."
                resultado_container["mensagens"] = [(nome_real, ultima_msg)]
            else:
                msg_dela = next((m["texto"] for m in reversed(ultimas) if m["recebida"]), None)
                if msg_dela:
                    resultado_container["texto"] = f"Arthur, você já respondeu {nome_real}. A última mensagem recebida tinha sido: '{msg_dela}', e você respondeu: '{ultima_msg}'."
                    resultado_container["mensagens"] = [(nome_real, msg_dela)]
                else:
                    resultado_container["texto"] = f"Arthur, não há nada pendente de {nome_real}. A última mensagem lá é sua dizendo: {ultima_msg}."

        except Exception as e:
            print(f"❌ [Erro ao ler contato específico]: {e}")
            resultado_container["texto"] = f"Tive um problema ao tentar ler a conversa de {contato_alvo}, Arthur."

    def _extrair_painel_js(self, page):
        script_js = """
        () => {
            const pane = document.querySelector('#pane-side');
            if (!pane) return { nao_lidas: [], topo: [], total_global: 0 };
            
            let total_global = 0;
            const globalBadges = Array.from(document.querySelectorAll('[aria-label*="não lida"], [aria-label*="unread"]'));
            for (let gb of globalBadges) {
                const label = gb.getAttribute('aria-label') || "";
                const match = label.match(/(\\d+)\\s*(conversa|chat)/i);
                if (match) {
                    total_global = parseInt(match[1]);
                    break;
                }
            }

            let items = Array.from(pane.querySelectorAll('div[role="listitem"]'));
            if (items.length === 0) {
                items = Array.from(pane.querySelectorAll('div[role="row"]'));
            }

            const nao_lidas = [];
            const topo = [];
            const nomes_vistos = new Set();
            const ignorar = ["Tudo", "Não lidas", "Favoritas", "Grupos", "Canais", "Status", "Comunidades"];

            items.forEach((item) => {
                const titleEl = item.querySelector('span[title]');
                if (!titleEl) return;
                
                const nome = titleEl.getAttribute('title').trim();
                if (!nome || ignorar.includes(nome) || nomes_vistos.has(nome)) return;
                nomes_vistos.add(nome);

                const spans = Array.from(item.querySelectorAll('span[dir="ltr"], span.selectable-text'));
                let preview = "";
                for (let s of spans.reverse()) {
                    const txt = s.innerText ? s.innerText.trim() : "";
                    if (txt && txt !== nome && !/^\\d{1,2}:\\d{2}/.test(txt) && !/^Ontem$/i.test(txt)) {
                        preview = txt.split('\\n')[0].substring(0, 110);
                        break;
                    }
                }

                if (!preview) {
                    const docEl = item.querySelector('span[title$=".pdf"], span[title$=".docx"], span[title$=".png"], span[title$=".jpg"]');
                    if (docEl) {
                        preview = "Arquivo: " + docEl.getAttribute('title');
                    } else {
                        preview = "Nova mensagem ou arquivo recebido";
                    }
                }

                if (topo.length < 5) {
                    topo.push([nome, preview]);
                }

                let isUnread = false;
                const badgeAria = item.querySelector('[aria-label*="não lida" i], [aria-label*="nao lida" i], [aria-label*="unread" i]');
                if (badgeAria) {
                    isUnread = true;
                } else {
                    const allSpans = Array.from(item.querySelectorAll('span'));
                    for (let sp of allSpans) {
                        const t = sp.innerText ? sp.innerText.trim() : "";
                        if (/^\\d{1,4}$/.test(t) && parseInt(t) > 0 && sp.children.length === 0) {
                            isUnread = true;
                            break;
                        }
                    }
                }

                if (isUnread) {
                    nao_lidas.push([nome, preview]);
                }
            });

            return { nao_lidas, topo, total_global };
        }
        """
        return page.evaluate(script_js)

    def _loop_monitoramento_web(self):
        while self.ativo:
            try:
                with sync_playwright() as p:
                    os.makedirs(self.diretorio_sessao, exist_ok=True)
                    
                    browser_context = p.chromium.launch_persistent_context(
                        user_data_dir=self.diretorio_sessao,
                        headless=False,
                        args=[
                            "--disable-gpu",
                            "--no-sandbox",
                            "--disable-dev-shm-usage",
                            "--disable-background-timer-throttling",
                            "--disable-backgrounding-occluded-windows",
                            "--disable-renderer-backgrounding",
                            "--window-position=0,0"
                        ]
                    )
                    
                    browser_context.add_init_script("""
                        Object.defineProperty(document, 'hidden', { get: () => false, configurable: true });
                        Object.defineProperty(document, 'visibilityState', { get: () => 'visible', configurable: true });
                        document.hasFocus = () => true;
                    """)
                    
                    page = browser_context.pages[0] if browser_context.pages else browser_context.new_page()
                    
                    print("📱 [Subsistema WhatsApp]: A ligar ao WhatsApp Web (Sessão Única)...")
                    page.goto("https://web.whatsapp.com", timeout=60000)
                    
                    for _ in range(60):
                        if not self.ativo:
                            break
                        try:
                            if page.evaluate("() => !!document.querySelector('#pane-side')"):
                                break
                        except Exception:
                            pass
                        time.sleep(1)

                    self._injetar_bypass_visibilidade(page)
                    with self.lock_estado:
                        self.estado_whatsapp["carregado"] = True
                    print("✅ [Subsistema WhatsApp]: Pronto! Cache proativa em tempo real ativa.")

                    try:
                        dados_iniciais = self._extrair_painel_js(page)
                        for r, m in dados_iniciais.get("nao_lidas", []):
                            self.ultimas_nao_lidas_conhecidas[r] = m
                    except Exception:
                        pass

                    while self.ativo:
                        if page.is_closed():
                            raise Exception("Janela do WhatsApp Web foi fechada.")

                        executou_comando = False
                        while not self.fila_comandos.empty():
                            executou_comando = True
                            acao, arg1, arg2, evento = self.fila_comandos.get()
                            try:
                                if acao == "enviar":
                                    self._executar_envio_seguro(page, arg1, arg2)
                                elif acao == "ler_contato":
                                    self._executar_leitura_especifica(page, arg1, arg2)
                                elif acao == "marcar_lida":
                                    self._executar_marcar_lida(page, arg1)
                            finally:
                                if evento:
                                    evento.set()
                                self.fila_comandos.task_done()

                        if executou_comando:
                            time.sleep(1.0)

                        try:
                            dados = self._extrair_painel_js(page)
                            nao_lidas = dados.get("nao_lidas", [])
                            topo = dados.get("topo", [])
                            total_global = dados.get("total_global", 0)

                            novas_detectadas = []
                            for remetente, preview in nao_lidas:
                                if remetente not in self.ultimas_nao_lidas_conhecidas or self.ultimas_nao_lidas_conhecidas[remetente] != preview:
                                    novas_detectadas.append((remetente, preview))
                                self.ultimas_nao_lidas_conhecidas[remetente] = preview

                            if novas_detectadas and self.callback_alerta:
                                for rem, msg in novas_detectadas:
                                    try:
                                        self.callback_alerta(rem, msg)
                                    except Exception as ex:
                                        print(f"❌ [Erro no callback de alerta]: {ex}")

                            with self.lock_estado:
                                self.estado_whatsapp["conversas_nao_lidas"] = nao_lidas
                                self.estado_whatsapp["topo_da_lista"] = topo
                                self.estado_whatsapp["total_badge_global"] = max(total_global, len(nao_lidas))

                        except Exception:
                            pass

                        time.sleep(1.5)

            except Exception as e:
                print(f"⚠️ [Subsistema WhatsApp]: Conexão reiniciada ({e}). Reconectando em 5s...")
                with self.lock_estado:
                    self.estado_whatsapp["carregado"] = False
                time.sleep(5)
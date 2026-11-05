import time
import threading
import logging
import psutil
import ctypes

class SubsistemaTracking:
    def __init__(self, callback_alerta=None, callback_avaliar_prioridade=None, intervalo_verificacao=3, intervalo_sistema=10):
        self.callback_alerta = callback_alerta
        self.callback_avaliar_prioridade = callback_avaliar_prioridade
        self.intervalo_verificacao = intervalo_verificacao
        self.intervalo_sistema = intervalo_sistema
        self.ativo = False
        self.thread_monitor = None
        self.ultimo_aviso_cpu = 0
        self.ultimo_estado_notificacao = ""
        self.ultima_mensagem_capturada = ""  # Armazena o último estado detetado para consulta isolada
        
        # Contatos prioritários
        self.contatos_importantes = ["jô", "Mila Mamys", "Marcelo Frigo", "amor"]
        
        logging.info("👁️ [Subsistema Tracking]: Módulo de rastreamento isolado ativado.")

    def iniciar(self):
        if self.ativo:
            return
        self.ativo = True
        self.thread_monitor = threading.Thread(target=self._loop_monitoramento, daemon=True)
        self.thread_monitor.start()
        print("👁️ [Subsistema Tracking]: Monitoramento em segundo plano ativo.")

    def parar(self):
        self.ativo = False
        if self.thread_monitor:
            self.thread_monitor.join(timeout=1.0)
        print("👁️ [Subsistema Tracking]: Monitoramento desativado.")

    def _obter_todos_titulos_janelas_windows(self):
        titulos = []
        EnumWindows = ctypes.windll.user32.EnumWindows
        EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
        GetWindowTextW = ctypes.windll.user32.GetWindowTextW
        GetWindowTextLengthW = ctypes.windll.user32.GetWindowTextLengthW

        def foreach_window(hwnd, lParam):
            length = GetWindowTextLengthW(hwnd)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                GetWindowTextW(hwnd, buff, length + 1)
                titulo = buff.value.strip()
                if titulo:
                    titulos.append(titulo)
            return True

        EnumWindows(EnumWindowsProc(foreach_window), 0)
        return titulos

    def obter_ultima_mensagem_lida(self):
        """Método isolado para o Cérebro consultar o que o tracking detetou por último."""
        if self.ultima_mensagem_capturada:
            return f"A última atividade detetada no WhatsApp foi: {self.ultima_mensagem_capturada}"
        return "Não há novas mensagens registadas pelo tracking no momento."

    def _loop_monitoramento(self):
        contador_sistema = 0

        while self.ativo:
            try:
                titulos = self._obter_todos_titulos_janelas_windows()
                for titulo in titulos:
                    titulo_lower = titulo.lower()
                    
                    # Rastreia exclusivamente o WhatsApp ignorando lixo de sistema
                    if "whatsapp" in titulo_lower and "gdi+" not in titulo_lower:
                        
                        # Se houver indicador de nova mensagem não lida
                        if "(" in titulo and ")" in titulo:
                            if titulo != self.ultimo_estado_notificacao:
                                self.ultimo_estado_notificacao = titulo
                                self.ultima_mensagem_capturada = titulo  # Salva o estado internamente no tracking
                                print(f"💬 [Tracking WhatsApp Ativo]: {titulo}")
                                
                                if self.callback_alerta:
                                    self.callback_alerta(f"Arthur, detetei nova mensagem no WhatsApp: {titulo}")
                                    
                        elif titulo == "WhatsApp":
                            self.ultimo_estado_notificacao = ""

                # Verificação de recursos do sistema (CPU) a cada 10s
                contador_sistema += self.intervalo_verificacao
                if contador_sistema >= self.intervalo_sistema:
                    contador_sistema = 0
                    uso_cpu = psutil.cpu_percent(interval=None)
                    tempo_atual = time.time()
                    
                    if uso_cpu > 95 and (tempo_atual - self.ultimo_aviso_cpu > 60):
                        self.ultimo_aviso_cpu = tempo_atual
                        if self.callback_alerta:
                            self.callback_alerta(f"Atenção Arthur, o uso de CPU atingiu {int(uso_cpu)} por cento.")

            except Exception as e:
                logging.error(f"Erro no loop de tracking: {e}")

            time.sleep(self.intervalo_verificacao)
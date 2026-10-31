import os
import json
import ollama

class StarLightCore:
    def __init__(self):
        self.modelo_ia = "mistral"
        self.brain_file = "starlight_brain.json"
        self.dataset_file = "starlight_dataset.jsonl"
        self.brain = self.carregar_cerebro()

    def carregar_cerebro(self):
        if os.path.exists(self.brain_file):
            try:
                with open(self.brain_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "camada_base": {"neuronios": []},
            "nucleo_nivel_2": {"grupos": []},
            "nucleo_nivel_3": {"arquitetura": []},
            "pontes_cruzadas": []
        }

    def guardar_cerebro(self):
        with open(self.brain_file, "w", encoding="utf-8") as f:
            json.dump(self.brain, f, ensure_ascii=False, indent=4)

    def relatorio_terminal(self):
        """Imprime um relatório detalhado do estado neural diretamente no terminal."""
        total_base = len(self.brain.get("camada_base", {}).get("neuronios", []))
        total_nivel2 = len(self.brain.get("nucleo_nivel_2", {}).get("grupos", []))
        total_nivel3 = len(self.brain.get("nucleo_nivel_3", {}).get("arquitetura", []))
        total_sinapses = len(self.brain.get("pontes_cruzadas", []))
        
        print("\n" + "="*40)
        print("🧠 RELATÓRIO DO ESTADO NEURAL (STARLIGHT)")
        print("="*40)
        print(f"• Camada Base (Nível 1): {total_base} neurónios")
        print(f"• Núcleos Nível 2:        {total_nivel2} grupos")
        print(f"• Super-Núcleos Nível 3:  {total_nivel3} estruturas")
        print(f"• Pontes Cruzadas (Sinapses): {total_sinapses}")
        print("="*40 + "\n")

    def registar_dataset(self, prompt, resposta):
        registro = {"prompt": prompt, "resposta": resposta, "uso": 1}
        with open(self.dataset_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(registro, ensure_ascii=False) + "\n")

    def evoluir_rede_hierarquica(self, conceito):
        base = self.brain["camada_base"]["neuronios"]
        base.append({"termo": conceito[:30], "peso": 1})
        
        if len(base) >= 20:
            self.brain["nucleo_nivel_2"]["grupos"].append({
                "id": len(self.brain["nucleo_nivel_2"]["grupos"]) + 1,
                "conteudo_resumido": f"Bloco Consolidado {len(self.brain['nucleo_nivel_2']['grupos']) + 1}"
            })
            self.brain["camada_base"]["neuronios"] = base[20:]
            
        if len(self.brain["nucleo_nivel_2"]["grupos"]) >= 2:
            self.brain["nucleo_nivel_3"]["arquitetura"].append(f"Super-Núcleo Global {len(self.brain['nucleo_nivel_3']['arquitetura']) + 1}")
            self.brain["nucleo_nivel_2"]["grupos"] = []

        self.brain["pontes_cruzadas"].append(f"Sinapse_{len(self.brain['pontes_cruzadas'])+1}")
        self.guardar_cerebro()
        
        # Mostra o relatório atualizado no terminal de forma elegante
        self.relatorio_terminal()

    def podas_sinapticas(self):
        if os.path.exists(self.dataset_file):
            try:
                with open(self.dataset_file, "r", encoding="utf-8") as f:
                    linhas = f.readlines()
                if len(linhas) > 500:
                    with open(self.dataset_file, "w", encoding="utf-8") as f:
                        f.writelines(linhas[-500:])
            except:
                pass

    def procurar_memoria_parcial(self, mensagem_limpa):
        if not os.path.exists(self.dataset_file):
            return None
        
        historico_relevante = []
        palavras_chave_msg = set(mensagem_limpa.split())

        try:
            with open(self.dataset_file, "r", encoding="utf-8") as f:
                for linha in f:
                    dados = json.loads(linha)
                    p_cadastrado = dados["prompt"].strip().lower()
                    
                    if p_cadastrado == mensagem_limpa:
                        return {"tipo": "exata", "resposta": dados['resposta']}
                    
                    palavras_cadastradas = set(p_cadastrado.split())
                    intersecao = palavras_chave_msg.intersection(palavras_cadastradas)
                    if len(intersecao) >= 2:
                        historico_relevante.append(f"Pergunta: {dados['prompt']} | Resposta Anterior: {dados['resposta']}")
        except:
            pass

        if historico_relevante:
            return {"tipo": "parcial", "contexto": "\n".join(historico_relevante[-3:])}
            
        return None

    def processar_mensagem(self, mensagem):
        mensagem_limpa = mensagem.strip().lower()
        self.podas_sinapticas()

        chars_validos = "0123456789+-*/(). "
        expressao_limpa = "".join([c for c in mensagem if c in chars_validos]).strip()
        if any(op in expressao_limpa for op in "+-*/") and len(expressao_limpa) > 2:
            try:
                resultado = eval(expressao_limpa)
                resposta_calc = f"🧮 [Cálculo Lógico Direto]: {expressao_limpa} = {resultado}"
                self.evoluir_rede_hierarquica(mensagem)
                self.registar_dataset(mensagem, resposta_calc)
                return resposta_calc
            except:
                pass

        memoria = self.procurar_memoria_parcial(mensagem_limpa)
        if memoria and memoria["tipo"] == "exata":
            return f"🧠 [Memória Interna Direta - 0 Custo]:\n\n{memoria['resposta']}"

        prompt_sistema = (
            "Você é a StarLight, uma inteligência artificial cognitiva autônoma, "
            "profunda, elegante e analítica. Responda de forma rica, detalhada e estruturada em português."
        )

        if memoria and memoria["tipo"] == "parcial":
            prompt_completo = (
                f"{prompt_sistema}\n\n"
                f"Contexto prévio na tua hierarquia de núcleos:\n{memoria['contexto']}\n\n"
                f"Novo estímulo: {mensagem}\n"
                f"Instrução: Evolui a partir do conhecimento prévio, expandindo e refinando os conceitos."
            )
            origem_tag = "🔄 [Evolução Hierárquica Incremental via Mistral Local]"
        else:
            prompt_completo = f"{prompt_sistema}\n\nUtilizador: {mensagem}"
            origem_tag = "🌟 [Aprendizado Novo via Mistral Local]"

        try:
            resposta_ia = ollama.chat(model=self.modelo_ia, messages=[
                {"role": "user", "content": prompt_completo}
            ])
            
            resposta_final = resposta_ia['message']['content'].strip()
            
            self.evoluir_rede_hierarquica(mensagem)
            self.registar_dataset(mensagem, resposta_final)
            
            return f"{origem_tag}:\n\n{resposta_final}"

        except Exception as e:
            return f"⚠️ [Erro no Motor Local]: Certifique-se de que o Ollama está a correr no PC. Detalhe: {str(e)}"
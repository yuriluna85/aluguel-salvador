"""
Buscador de Imóveis para Aluguel - Salvador e Região Metropolitana / Cidades de Comutação Diária
Desenvolvido por: YLuna85 LABs
Execução Autônoma via GitHub Actions e Local
"""

import os
import json
import csv
import urllib.parse
import urllib.request
from datetime import datetime
from typing import List, Dict, Any
from dataclasses import dataclass, asdict

PATH_BANCO_JSON = "data/anuncios_imoveis_salvador.json"
PATH_HISTORICO_CSV = "data/historico_imoveis.csv"
PATH_RELATORIO_MD = "README.md"

# Mapeamento de Cidades e Prioridades de Comutação Diária
CIDADES_PRIORITARIAS = {
    "Salvador": 1,              # Prioridade Máxima (Capital e Bairros)
    "Lauro de Freitas": 2,      # Comutação Diária Direta (Vizinha)
    "Simões Filho": 2,          # Comutação Diária Direta
    "Camaçari": 2,              # Comutação Diária (Pólo / Orla)
    "Santo Amaro": 2,           # Comutação Diária (Recôncavo / Acesso BR-324)
    "Candeias": 2,              # Comutação Diária
    "São Francisco do Conde": 2,# Comutação Diária
    "Dias d'Ávila": 2           # Comutação Diária
}

@dataclass
class ImovelAnuncio:
    id: str
    titulo: str
    plataforma: str
    preco_aluguel: float
    cidade: str
    bairro: str
    quartos: int
    area_m2: float
    link: str
    data_descoberta: str
    status: str = "ativo"        # "ativo", "alugado", "indisponivel"
    data_atualizacao: str = ""   # Data da última verificação de status
    prioridade: int = 1         # 1: Salvador (Capital), 2: Cidades de Comutação Diária

class BuscadorImoveisSalvador:
    def __init__(self):
        self.serper_api_key = os.getenv("SERPER_API_KEY_IMOVEIS") or os.getenv("SERPER_API_KEY")
        self.scraper_api_key = os.getenv("SCRAPER_API_KEY_IMOVEIS") or os.getenv("SCRAPER_API_KEY")
        self.anuncios_existentes: Dict[str, Dict[str, Any]] = self._carregar_banco_dados()

    def _carregar_banco_dados(self) -> Dict[str, Dict[str, Any]]:
        """Carrega banco JSON existente estruturado."""
        if os.path.exists(PATH_BANCO_JSON):
            try:
                with open(PATH_BANCO_JSON, "r", encoding="utf-8") as f:
                    content = json.load(f)
                    # Se estiver na estrutura nova com metadados
                    if isinstance(content, dict) and "ativos" in content:
                        todos = {}
                        for item in content.get("ativos", []):
                            todos[item["id"]] = item
                        for item in content.get("indisponiveis", []):
                            todos[item["id"]] = item
                        return todos
                    elif isinstance(content, dict):
                        return content
            except Exception as e:
                print(f"Aviso: Não foi possível ler banco JSON existente: {e}")
        return {}

    def _salvar_banco_json_e_csv(self):
        """Salva o JSON estruturado para HTML e exporta histórico completo em CSV."""
        os.makedirs("data", exist_ok=True)
        hoje_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        ativos = []
        indisponiveis = []

        for item in self.anuncios_existentes.values():
            if item.get("status") == "ativo":
                ativos.append(item)
            else:
                indisponiveis.append(item)

        # 1. Estrutura JSON otimizada para o HTML
        json_payload = {
            "metadados": {
                "ultima_atualizacao": hoje_str,
                "total_ativos": len(ativos),
                "total_indisponiveis": len(indisponiveis),
                "total_historico": len(self.anuncios_existentes)
            },
            "ativos": ativos,
            "indisponiveis": indisponiveis
        }

        with open(PATH_BANCO_JSON, "w", encoding="utf-8") as f:
            json.dump(json_payload, f, ensure_ascii=False, indent=2)
        print(f"JSON otimizado atualizado em: {PATH_BANCO_JSON}")

        # 2. Exportação para Histórico CSV
        fieldnames = [
            "id", "plataforma", "cidade", "bairro", "titulo", "preco_aluguel", 
            "quartos", "area_m2", "status", "data_descoberta", "data_atualizacao", "link"
        ]

        with open(PATH_HISTORICO_CSV, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            for item in sorted(self.anuncios_existentes.values(), key=lambda x: x.get("data_descoberta", ""), reverse=True):
                writer.writerow(item)
        print(f"Histórico CSV exportado em: {PATH_HISTORICO_CSV}")

    def processar_resultados_e_salvar(self, novos_anuncios: List[ImovelAnuncio]):
        hoje_data = datetime.now().strftime("%Y-%m-%d")
        count_novos = 0
        ids_capturados = set()

        for item in novos_anuncios:
            ids_capturados.add(item.id)
            item.prioridade = CIDADES_PRIORITARIAS.get(item.cidade, 2)
            item.data_atualizacao = hoje_data

            if item.id not in self.anuncios_existentes:
                self.anuncios_existentes[item.id] = asdict(item)
                count_novos += 1
            else:
                # Se já existe, atualiza informações mantendo histórico
                self.anuncios_existentes[item.id].update(asdict(item))

        # Verificar se algum imóvel ativo antigo não apareceu e marcar como indisponível/alugado se necessário
        # (Em varredura real completa via Scraper)
        self._salvar_banco_json_e_csv()
        self.atualizar_readme()

    def atualizar_readme(self):
        """Atualiza o README.md com lista ativa e estatísticas."""
        hoje = datetime.now().strftime("%d/%m/%Y")
        ativos = [i for i in self.anuncios_existentes.values() if i.get("status") == "ativo"]
        indisponiveis = [i for i in self.anuncios_existentes.values() if i.get("status") != "ativo"]
        
        header = f"""# 🏡 Busca Imóveis Salvador & Cidades Próximas (Comutação Diária)
> **Projeto desenvolvido sob a chancela 🔬 YLuna85 LABs**

Aplicação automatizada para raspagem, consolidação, histórico CSV e monitoramento de anúncios de aluguel.

### 🎯 Diretrizes Geográficas
* **Prioridade 1 (Capital)**: Salvador/BA e seus bairros.
* **Prioridade 2 (Comutação Diária)**: Lauro de Freitas, Santo Amaro, Simões Filho, Camaçari, Candeias, São Francisco do Conde e Dias d'Ávila.

---

## 📍 Anúncios Ativos Monitorados ({hoje})

| Prioridade | Plataforma | Cidade / Bairro | Título / Descrição | Preço Aluguel | Status | Link do Anúncio |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
"""
        linhas = []
        anuncios_ordenados = sorted(
            ativos,
            key=lambda x: (x.get('prioridade', 1), x['data_descoberta'], x['preco_aluguel']),
            reverse=False
        )

        for anc in anuncios_ordenados:
            prio_tag = "⭐ Capital" if anc.get('prioridade', 1) == 1 else "🚗 Comutação"
            preco_fmt = f"R$ {anc['preco_aluguel']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if anc['preco_aluguel'] > 0 else "Sob Consulta"
            localizacao = f"{anc['cidade']} - {anc['bairro']}" if anc['bairro'] else anc['cidade']
            link_markdown = f"[Acessar Anúncio 🔗]({anc['link']})"
            status_badge = "🟢 Disponível" if anc.get("status") == "ativo" else "🔴 Indisponível/Alugado"
            linhas.append(f"| {prio_tag} | {anc['plataforma']} | {localizacao} | {anc['titulo']} | {preco_fmt} | {status_badge} | {link_markdown} |")

        footer = f"""

---

## 📊 Histórico e Arquivos Gerados
* **JSON Estruturado para HTML**: `data/anuncios_imoveis_salvador.json`
* **Histórico Completo em CSV**: `data/historico_imoveis.csv` ({len(self.anuncios_existentes)} registros totais)

---

## 📜 Log de Atualizações (Changelog)
* **28/06/2026**: Implementação da exportação automática de histórico em CSV (`historico_imoveis.csv`), controle de ciclo de vida do anúncio (Ativo vs. Alugado/Indisponível) e JSON otimizado para o frontend.
"""

        conteudo_completo = header + "\n".join(linhas) + footer
        with open(PATH_RELATORIO_MD, "w", encoding="utf-8") as f:
            f.write(conteudo_completo)
        print("README.md atualizado com sucesso!")


def executar():
    print("Iniciando rotina de busca de imóveis - YLuna85 LABs com Histórico CSV...")
    buscador = BuscadorImoveisSalvador()
    hoje = datetime.now().strftime("%Y-%m-%d")

    # Amostra demonstrativa incluindo um imóvel marcado como alugado/indisponível para teste de histórico
    dados_iniciais = [
        ImovelAnuncio("olx_salvador_pituba_01", "Casa duplex 3 quartos com suíte e garagem privativa", "OLX", 2800.00, "Salvador", "Pituba", 3, 120.0, "https://ba.olx.com.br/grande-salvador/imoveis/aluguel-casa-pituba-3-quartos-12345678", hoje, "ativo", hoje, 1),
        ImovelAnuncio("vivareal_salvador_imbui_01", "Casa térrea com quintal amplo e 2 vagas de garagem", "VivaReal", 2300.00, "Salvador", "Imbuí", 3, 110.0, "https://www.vivareal.com.br/imovel/casa-3-quartos-imbui-salvador-110m2-id-456789/", hoje, "ativo", hoje, 1),
        ImovelAnuncio("chavena_mao_lauro_01", "Casa em condomínio fechado perto da praia de Buraquinho", "Chave na Mão", 3200.00, "Lauro de Freitas", "Buraquinho", 4, 150.0, "https://www.chavenamao.com.br/imovel/aluguel-casa-lauro-de-freitas-4-quartos/id-987654/", hoje, "ativo", hoje, 2),
        ImovelAnuncio("olx_santo_amaro_centro_01", "Casa espaçosa 3 quartos próxima ao centro histórico", "OLX", 1600.00, "Santo Amaro", "Centro", 3, 130.0, "https://ba.olx.com.br/regiao-de-feira-de-santana-e-santo-amaro/imoveis/casa-aluguel-santo-amaro-3-quartos-777888/", hoje, "ativo", hoje, 2),
        ImovelAnuncio("olx_salvador_barra_antigo", "Apartamento vista mar 2 quartos (Alugado)", "OLX", 3500.00, "Salvador", "Barra", 2, 85.0, "https://ba.olx.com.br/grande-salvador/imoveis/aluguel-barra-2-quartos-old", "2026-06-15", "alugado", hoje, 1)
    ]

    buscador.processar_resultados_e_salvar(dados_iniciais)

if __name__ == "__main__":
    executar()

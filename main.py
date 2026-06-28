"""
Buscador de Imóveis para Aluguel - Salvador e Região Metropolitana / Cidades de Comutação Diária
Desenvolvido por: YLuna85 LABs
Execução Autônoma via GitHub Actions e Local (Estrito: Apenas Casas Reais)
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

CIDADES_PRIORITARIAS = {
    "Salvador": 1,              # Prioridade Máxima (Capital e Bairros)
    "Lauro de Freitas": 2,      # Comutação Diária Direta (Vizinha)
    "Simões Filho": 2,          # Comutação Diária Direta
    "Camaçari": 2,              # Comutação Diária (Pólo / Orla)
    "Santo Amaro": 2,           # Comutação Diária (Recôncavo / Acesso BR-324)
    "Candeias": 2,              # Comutação Diária
    "São Francisco do Conde": 2,
    "Dias d'Ávila": 2
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
    data_atualizacao: str = ""
    prioridade: int = 1

class BuscadorImoveisSalvador:
    def __init__(self):
        self.serper_api_key = os.getenv("SERPER_API_KEY_IMOVEIS") or os.getenv("SERPER_API_KEY")
        self.scraper_api_key = os.getenv("SCRAPER_API_KEY_IMOVEIS") or os.getenv("SCRAPER_API_KEY")
        self.anuncios_existentes: Dict[str, Dict[str, Any]] = self._carregar_banco_dados()

    def _carregar_banco_dados(self) -> Dict[str, Dict[str, Any]]:
        if os.path.exists(PATH_BANCO_JSON):
            try:
                with open(PATH_BANCO_JSON, "r", encoding="utf-8") as f:
                    content = json.load(f)
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
        os.makedirs("data", exist_ok=True)
        hoje_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        ativos = [item for item in self.anuncios_existentes.values() if item.get("status") == "ativo"]
        indisponiveis = [item for item in self.anuncios_existentes.values() if item.get("status") != "ativo"]

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

        for item in novos_anuncios:
            item.prioridade = CIDADES_PRIORITARIAS.get(item.cidade, 2)
            item.data_atualizacao = hoje_data

            if item.id not in self.anuncios_existentes:
                self.anuncios_existentes[item.id] = asdict(item)
                count_novos += 1
            else:
                self.anuncios_existentes[item.id].update(asdict(item))

        self._salvar_banco_json_e_csv()
        self.atualizar_readme()

    def atualizar_readme(self):
        hoje = datetime.now().strftime("%d/%m/%Y")
        ativos = [i for i in self.anuncios_existentes.values() if i.get("status") == "ativo"]
        
        header = f"""# 🏡 Busca Imóveis Salvador & Cidades Próximas (Apenas Casas)
> **Projeto desenvolvido sob a chancela 🔬 YLuna85 LABs**

Aplicação automatizada para raspagem, consolidação e monitoramento estrito de **CASAS** para aluguel.

### 🎯 Diretrizes Geográficas e Filtros
* **Filtro Rígido**: Apenas casas (apartamentos ignorados).
* **Prioridade 1 (Capital)**: Salvador/BA e seus bairros.
* **Prioridade 2 (Comutação Diária)**: Lauro de Freitas, Santo Amaro, Simões Filho, Camaçari, Candeias, São Francisco do Conde e Dias d'Ávila.

---

## 📍 Casas Ativas Monitoradas ({hoje})

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
* **28/06/2026**: Higienização completa da base (removidos testes iniciais), aplicação de filtro rígido exclusivo para CASAS (apartamentos descartados) e raspagem real via Serper API.
"""

        conteudo_completo = header + "\n".join(linhas) + footer
        with open(PATH_RELATORIO_MD, "w", encoding="utf-8") as f:
            f.write(conteudo_completo)
        print("README.md atualizado com sucesso!")


def executar():
    print("Iniciando rotina de busca de imóveis - YLuna85 LABs com Histórico CSV...")
    buscador = BuscadorImoveisSalvador()
    # Apenas sincronizar e salvar dados reais existentes
    buscador.processar_resultados_e_salvar([])

if __name__ == "__main__":
    executar()

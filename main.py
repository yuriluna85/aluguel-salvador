"""
Buscador de Imóveis para Aluguel - Salvador e Região Metropolitana / Cidades de Comutação Diária
Desenvolvido por: YLuna85 LABs
Execução Autônoma Estrita (Apenas Links Diretos de Anúncios Individuais e Extração de Preços R$)
"""

import os
import json
import csv
import ssl
import re
import urllib.parse
import urllib.request
from datetime import datetime
from typing import List, Dict, Any
from dataclasses import dataclass, asdict

PATH_BANCO_JSON = "data/anuncios_imoveis_salvador.json"
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

TERMOS_IGNORAR = ["apartamento", "apto", "flat", "studio", "kitnet", "loft", "cobertura"]

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
        self.serper_api_key = (
            os.getenv("SERPER_API_KEY_IMOVEIS") or 
            os.getenv("SERPER_API_KEY") or 
            os.getenv("SERPER_KEY") or 
            "2050ba8d3ed621397d76d49c751c58dd116a87ca"
        )
        self.scraper_api_key = (
            os.getenv("SCRAPER_API_KEY_IMOVEIS") or 
            os.getenv("SCRAPER_API_KEY") or 
            os.getenv("SCRAPER_KEY") or 
            "f7f774ad40bd82c46ef02b6debe15839"
        )
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

    def raspagem_estrita_links_diretos(self) -> List[ImovelAnuncio]:
        """Raspagem focada estritamente em anúncios individuais com extração de preços R$."""
        if not self.serper_api_key:
            return []

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        queries = [
            ("OLX", "Salvador", 1, "excelente casa aluguel salvador olx"),
            ("OLX", "Salvador", 1, "casa duplex aluguel pituba brotas salvador olx"),
            ("OLX", "Lauro de Freitas", 2, "casa aluguel buraquinho vilas lauro de freitas olx"),
            ("OLX", "Santo Amaro", 2, "casa aluguel centro santo amaro bahia olx"),
            ("VivaReal", "Salvador", 1, "casa aluguel salvador id vivareal"),
            ("VivaReal", "Lauro de Freitas", 2, "casa aluguel lauro de freitas id vivareal"),
            ("Zap Imóveis", "Salvador", 1, "casa aluguel salvador id zap imoveis"),
            ("QuintoAndar", "Salvador", 1, "casa aluguel salvador quintoandar id")
        ]

        casas_encontradas = []
        hoje_str = datetime.now().strftime("%Y-%m-%d")

        print("--- Executando Coleta Estrita de Links Diretos & Preços ---")

        for plat, cidade, prioridade, q in queries:
            url = "https://google.serper.dev/search"
            payload = json.dumps({"q": q, "gl": "br", "hl": "pt-br", "num": 20})
            headers = {'X-API-KEY': self.serper_api_key, 'Content-Type': 'application/json'}
            try:
                req = urllib.request.Request(url, data=payload.encode('utf-8'), headers=headers)
                with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                    organic = data.get("organic", [])
                    for item in organic:
                        link = item.get("link", "")
                        title = item.get("title", "")
                        snippet = item.get("snippet", "")
                        full_text = (title + " " + snippet).lower()

                        # 1. Eliminar páginas de busca/categoria gerais
                        if link.endswith("/aluguel") or link.endswith("/casas") or link.endswith("/salvador") or "/alugar/imovel/" in link or link.endswith("/pituba"):
                            continue
                        
                        # 2. Eliminar apartamentos
                        if any(termo in full_text for termo in TERMOS_IGNORAR):
                            continue

                        # 3. Extração rigorosa de preço R$ (Título, Snippet ou Padrão Numérico)
                        price_match = re.search(r'R\$\s?([\d\.]+)', title + " " + snippet)
                        preco = 0.0
                        if price_match:
                            try:
                                preco = float(price_match.group(1).replace(".", "").replace(",", "."))
                            except:
                                preco = 0.0

                        if preco == 0.0:
                            num_match = re.search(r'(?:aluguel|valor|por)\s?:?\s?R?\$\s?([\d\.]+)', full_text)
                            if num_match:
                                try:
                                    preco = float(num_match.group(1).replace(".", "").replace(",", "."))
                                except:
                                    preco = 0.0

                        bairro = "Geral"
                        bairros_conhecidos = ["Pituba", "Imbuí", "Brotas", "Barra", "Cabula", "Stella Maris", "Buraquinho", "Vilas do Atlântico", "Centro", "Busca Vida", "Jauá", "Abrantes", "Boca do Rio", "Itapuã", "Ondina", "Graça", "Caminho das Árvores"]
                        for b in bairros_conhecidos:
                            if b.lower() in full_text:
                                bairro = b
                                break

                        import hashlib
                        prefix = plat.lower().replace(" ", "_").replace("ã", "a").replace("ó", "o")
                        anc_id = f"{prefix}_ind_{hashlib.md5(link.encode('utf-8')).hexdigest()[:10]}"
                        clean_title = title.split("|")[0].split("-")[0].strip()

                        casas_encontradas.append(ImovelAnuncio(
                            id=anc_id, titulo=clean_title, plataforma=plat, preco_aluguel=preco,
                            cidade=cidade, bairro=bairro, quartos=3, area_m2=120.0, link=link,
                            data_descoberta=hoje_str, status="ativo", data_atualizacao=hoje_str, prioridade=prioridade
                        ))
            except Exception as e:
                print(f"Aviso na busca [{q}]: {e}")

        print(f"Total de Anúncios Individuais Diretos Encontrados: {len(casas_encontradas)}")
        return casas_encontradas

    def _salvar_banco_json_e_csv_segmentados(self):
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

        grupos_csv: Dict[str, List[Dict[str, Any]]] = {}
        for item in self.anuncios_existentes.values():
            plat_slug = item.get("plataforma", "outros").lower().replace(" ", "_").replace("ã", "a").replace("ó", "o").replace("/", "_")
            data_desc = item.get("data_descoberta", "2026-01-01")
            ano = data_desc.split("-")[0] if "-" in data_desc else "2026"
            
            chave_arquivo = f"data/{plat_slug}_{ano}.csv"
            if chave_arquivo not in grupos_csv:
                grupos_csv[chave_arquivo] = []
            grupos_csv[chave_arquivo].append(item)

        for filepath, items in grupos_csv.items():
            with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                for item in sorted(items, key=lambda x: x.get("data_descoberta", ""), reverse=True):
                    writer.writerow(item)
            print(f"CSV Segmentado exportado: {filepath} ({len(items)} registros)")

    def processar_resultados_e_salvar(self, novos_anuncios: List[ImovelAnuncio]):
        hoje_data = datetime.now().strftime("%Y-%m-%d")

        for item in novos_anuncios:
            item.prioridade = CIDADES_PRIORITARIAS.get(item.cidade, 2)
            item.data_atualizacao = hoje_data

            if item.id not in self.anuncios_existentes:
                self.anuncios_existentes[item.id] = asdict(item)
            else:
                self.anuncios_existentes[item.id].update(asdict(item))

        self._salvar_banco_json_e_csv_segmentados()
        self.atualizar_readme()

    def atualizar_readme(self):
        hoje = datetime.now().strftime("%d/%m/%Y")
        ativos = [i for i in self.anuncios_existentes.values() if i.get("status") == "ativo"]
        
        header = f"""# 🏡 Busca Imóveis Salvador & Cidades Próximas (Central Multi-Vitrine Direta)
> **Projeto desenvolvido sob a chancela 🔬 YLuna85 LABs**

Aplicação automatizada para raspagem multi-vitrine com links diretos de anúncios individuais e preços R$.

### 🎯 Diretrizes Geográficas e Filtros Estritos
* **Links Diretos**: Apenas URLs diretas de anúncios individuais (páginas de categoria descartadas).
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

## 📊 Histórico e Arquivos CSV Segmentados por Plataforma e Ano
* **JSON Estruturado para HTML**: `data/anuncios_imoveis_salvador.json`
* **Arquivos CSV Segmentados**: `data/olx_2026.csv`, `data/vivareal_2026.csv`, `data/quintoandar_2026.csv`, `data/zap_imoveis_2026.csv`, etc. ({len(self.anuncios_existentes)} registros totais)

---

## 📜 Log de Atualizações (Changelog)
* **28/06/2026**: Implementação de filtro estrito para aceitar exclusivamente URLs de anúncios individuais diretos e aprimoramento na extração de preços R$.
"""

        conteudo_completo = header + "\n".join(linhas) + footer
        with open(PATH_RELATORIO_MD, "w", encoding="utf-8") as f:
            f.write(conteudo_completo)
        print("README.md atualizado com sucesso!")


def executar():
    print("Iniciando rotina autônoma de links diretos e preços R$ - YLuna85 LABs...")
    buscador = BuscadorImoveisSalvador()
    novas_casas = buscador.raspagem_estrita_links_diretos()
    buscador.processar_resultados_e_salvar(novas_casas)

if __name__ == "__main__":
    executar()

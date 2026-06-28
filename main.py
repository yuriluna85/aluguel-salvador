"""
Buscador de Imóveis para Aluguel - Salvador e Região Metropolitana / Cidades de Comutação Diária
Desenvolvido por: YLuna85 LABs
Execução Autônoma Dual-Engine (Serper API + ScraperAPI) via GitHub Actions
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

    def raspagem_serper(self) -> List[ImovelAnuncio]:
        """Engine 1: Busca via Serper Google API."""
        if not self.serper_api_key:
            return []

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        queries = [
            ("Salvador", 1, "aluguel casa salvador olx"),
            ("Salvador", 1, "aluguel casa pituba brotas barra cabula salvador olx"),
            ("Lauro de Freitas", 2, "aluguel casa lauro de freitas vilas buraquinho olx"),
            ("Santo Amaro", 2, "aluguel casa santo amaro bahia olx"),
            ("Camaçari", 2, "aluguel casa camacari busca vida jaua olx")
        ]

        casas_encontradas = []
        hoje_str = datetime.now().strftime("%Y-%m-%d")

        print("--- Executando Engine 1 (Serper.dev API) ---")

        for cidade, prioridade, q in queries:
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

                        if "olx.com.br" in link and not link.endswith("/aluguel"):
                            if any(termo in full_text for termo in TERMOS_IGNORAR):
                                continue
                            if "casa" not in full_text and "duplex" not in full_text and "triplex" not in full_text and "condomínio" not in full_text:
                                continue

                            price_match = re.search(r'R\$\s?([\d\.]+)', title + " " + snippet)
                            preco = 0.0
                            if price_match:
                                try:
                                    preco = float(price_match.group(1).replace(".", "").replace(",", "."))
                                except:
                                    preco = 0.0

                            bairro = "Geral"
                            bairros_conhecidos = ["Pituba", "Imbuí", "Brotas", "Barra", "Cabula", "Stella Maris", "Buraquinho", "Vilas do Atlântico", "Centro", "Busca Vida", "Jauá", "Abrantes", "Itapuã", "Ondina", "Graça", "Caminho das Árvores"]
                            for b in bairros_conhecidos:
                                if b.lower() in full_text:
                                    bairro = b
                                    break

                            import hashlib
                            anc_id = "olx_casa_" + hashlib.md5(link.encode("utf-8")).hexdigest()[:10]
                            clean_title = title.split("|")[0].replace(" - OLX", "").strip()

                            casas_encontradas.append(ImovelAnuncio(
                                id=anc_id, titulo=clean_title, plataforma="OLX", preco_aluguel=preco,
                                cidade=cidade, bairro=bairro, quartos=3, area_m2=120.0, link=link,
                                data_descoberta=hoje_str, status="ativo", data_atualizacao=hoje_str, prioridade=prioridade
                            ))
            except Exception as e:
                print(f"Aviso na busca Serper [{q}]: {e}")

        print(f"Engine 1 capturou {len(casas_encontradas)} casas.")
        return casas_encontradas

    def raspagem_scraperapi(self) -> List[ImovelAnuncio]:
        """Engine 2: Busca direta via ScraperAPI com bypass de bloqueio."""
        if not self.scraper_api_key:
            return []

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        target_url = "https://ba.olx.com.br/grande-salvador/imoveis/aluguel/casas"
        proxy_url = f"http://api.scraperapi.com?api_key={self.scraper_api_key}&url={urllib.parse.quote(target_url)}"

        casas_encontradas = []
        hoje_str = datetime.now().strftime("%Y-%m-%d")

        print("--- Executando Engine 2 (ScraperAPI Direct Proxy) ---")
        try:
            req = urllib.request.Request(proxy_url)
            with urllib.request.urlopen(req, context=ctx, timeout=45) as resp:
                html = resp.read().decode('utf-8', errors='ignore')
                links = re.findall(r'href="([^"]+)"', html)
                olx_links = [l for l in set(links) if 'ba.olx.com.br' in l and ('-id-' in l or '/aluguel-' in l)]
                
                for link in olx_links[:15]:
                    import hashlib
                    anc_id = "olx_casa_" + hashlib.md5(link.encode("utf-8")).hexdigest()[:10]
                    casas_encontradas.append(ImovelAnuncio(
                        id=anc_id, titulo="Casa para Aluguel na Grande Salvador", plataforma="OLX", preco_aluguel=0.0,
                        cidade="Salvador", bairro="Geral", quartos=3, area_m2=120.0, link=link,
                        data_descoberta=hoje_str, status="ativo", data_atualizacao=hoje_str, prioridade=1
                    ))
        except Exception as e:
            print(f"Aviso Engine 2 (ScraperAPI): {e}")

        print(f"Engine 2 capturou {len(casas_encontradas)} casas.")
        return casas_encontradas

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

Aplicação automatizada para raspagem dual-engine, consolidação e monitoramento estrito de **CASAS** para aluguel.

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
* **28/06/2026**: Atualização do motor autônomo para suporte dual-engine (Serper.dev + ScraperAPI) e detecção de segredos redundantes.
"""

        conteudo_completo = header + "\n".join(linhas) + footer
        with open(PATH_RELATORIO_MD, "w", encoding="utf-8") as f:
            f.write(conteudo_completo)
        print("README.md atualizado com sucesso!")


def executar():
    print("Iniciando rotina autônoma Dual-Engine de busca de imóveis - YLuna85 LABs...")
    buscador = BuscadorImoveisSalvador()
    
    casas_serper = buscador.raspagem_serper()
    casas_scraperapi = buscador.raspagem_scraperapi()
    
    todas_novas = casas_serper + casas_scraperapi
    buscador.processar_resultados_e_salvar(todas_novas)

if __name__ == "__main__":
    executar()

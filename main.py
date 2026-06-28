"""
Buscador de Imóveis para Aluguel - Salvador e Região Metropolitana / Cidades de Comutação Diária
Desenvolvido por: YLuna85 LABs
Execução Autônoma via GitHub Actions e Local
"""

import os
import json
import urllib.parse
import urllib.request
from datetime import datetime
from typing import List, Dict, Any
from dataclasses import dataclass, asdict

PATH_BANCO_DADOS = "data/anuncios_imoveis_salvador.json"
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
    prioridade: int = 1         # 1: Salvador (Capital), 2: Cidades de Comutação Diária

class BuscadorImoveisSalvador:
    def __init__(self):
        self.serper_api_key = os.getenv("SERPER_API_KEY_IMOVEIS") or os.getenv("SERPER_API_KEY")
        self.scraper_api_key = os.getenv("SCRAPER_API_KEY_IMOVEIS") or os.getenv("SCRAPER_API_KEY")
        self.anuncios_existentes = self._carregar_banco_dados()

    def _carregar_banco_dados(self) -> Dict[str, Dict[str, Any]]:
        if os.path.exists(PATH_BANCO_DADOS):
            try:
                with open(PATH_BANCO_DADOS, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Aviso: Não foi possível ler banco de dados existente: {e}")
        return {}

    def _salvar_banco_dados(self):
        os.makedirs(os.path.dirname(PATH_BANCO_DADOS), exist_ok=True)
        with open(PATH_BANCO_DADOS, "w", encoding="utf-8") as f:
            json.dump(self.anuncios_existentes, f, ensure_ascii=False, indent=2)

    def processar_resultados_e_salvar(self, novos_anuncios: List[ImovelAnuncio]):
        count_novos = 0
        for item in novos_anuncios:
            item.prioridade = CIDADES_PRIORITARIAS.get(item.cidade, 2)
            if item.id not in self.anuncios_existentes:
                self.anuncios_existentes[item.id] = asdict(item)
                count_novos += 1
            else:
                self.anuncios_existentes[item.id].update(asdict(item))

        self._salvar_banco_dados()
        self.atualizar_readme()

    def atualizar_readme(self):
        """Atualiza o README.md mantendo a lista de imóveis organizada por prioridade geográfica e selo YLuna85 LABs."""
        hoje = datetime.now().strftime("%d/%m/%Y")
        
        header = f"""# 🏡 Busca Imóveis Salvador & Cidades Próximas (Comutação Diária)
> **Projeto desenvolvido sob a chancela 🔬 YLuna85 LABs**

Aplicação automatizada para raspagem, consolidação e monitoramento diário de casas e apartamentos para aluguel.

### 🎯 Diretrizes de Busca Geográfica
* **Prioridade 1 (Máxima)**: Salvador/BA e seus bairros (Pituba, Imbuí, Brotas, Cabula, Barra, etc.).
* **Prioridade 2 (Comutação Diária)**: Cidades com raio de fácil acesso diário de ir e voltar (Lauro de Freitas, Santo Amaro, Simões Filho, Camaçari, Candeias, São Francisco do Conde e Dias d'Ávila).

---

## 📍 Anúncios Monitorados (Atualizado em {hoje})

| Prioridade | Plataforma | Cidade / Bairro | Título / Descrição | Preço Aluguel | Link do Anúncio |
| :--- | :--- | :--- | :--- | :--- | :--- |
"""
        linhas = []
        anuncios_ordenados = sorted(
            self.anuncios_existentes.values(),
            key=lambda x: (x.get('prioridade', 1), x['data_descoberta'], x['preco_aluguel']),
            reverse=False
        )

        for anc in anuncios_ordenados:
            prio_tag = "⭐ Capital (Salvador)" if anc.get('prioridade', 1) == 1 else "🚗 Comutação Diária"
            preco_fmt = f"R$ {anc['preco_aluguel']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if anc['preco_aluguel'] > 0 else "Sob Consulta"
            localizacao = f"{anc['cidade']} - {anc['bairro']}" if anc['bairro'] else anc['cidade']
            link_markdown = f"[Acessar Anúncio 🔗]({anc['link']})"
            linhas.append(f"| {prio_tag} | {anc['plataforma']} | {localizacao} | {anc['titulo']} | {preco_fmt} | {link_markdown} |")

        footer = f"""

---

## 🛠️ Configuração de Secrets no GitHub

Para execução automatizada via GitHub Actions, configure as seguintes variáveis no repositório (**Settings -> Secrets and variables -> Actions**):

* `SCRAPER_API_KEY_IMOVEIS`: Chave do ScraperAPI cadastrada com `yluna85.imoveis.ba@gmail.com`.
* `SERPER_API_KEY_IMOVEIS`: Chave do Serper.dev cadastrada com `yluna85.imoveis.ba@gmail.com`.

---

## 📜 Log de Atualizações (Changelog)
* **28/06/2026**: Adicionada a chancela oficial **YLuna85 LABs** no projeto e atualizada a hierarquia geográfica de buscas.
"""

        conteudo_completo = header + "\n".join(linhas) + footer
        with open(PATH_RELATORIO_MD, "w", encoding="utf-8") as f:
            f.write(conteudo_completo)
        print("README.md atualizado com sucesso!")


def executar():
    print("Iniciando rotina de busca de imóveis - YLuna85 LABs...")
    buscador = BuscadorImoveisSalvador()
    hoje = datetime.now().strftime("%Y-%m-%d")

    dados_iniciais = [
        ImovelAnuncio("olx_salvador_pituba_01", "Casa duplex 3 quartos com suíte e garagem privativa", "OLX", 2800.00, "Salvador", "Pituba", 3, 120.0, "https://ba.olx.com.br/grande-salvador/imoveis/aluguel-casa-pituba-3-quartos-12345678", hoje, 1),
        ImovelAnuncio("vivareal_salvador_imbui_01", "Casa térrea com quintal amplo e 2 vagas de garagem", "VivaReal", 2300.00, "Salvador", "Imbuí", 3, 110.0, "https://www.vivareal.com.br/imovel/casa-3-quartos-imbui-salvador-110m2-id-456789/", hoje, 1),
        ImovelAnuncio("chavena_mao_lauro_01", "Casa em condomínio fechado perto da praia de Buraquinho", "Chave na Mão", 3200.00, "Lauro de Freitas", "Buraquinho", 4, 150.0, "https://www.chavenamao.com.br/imovel/aluguel-casa-lauro-de-freitas-4-quartos/id-987654/", hoje, 2),
        ImovelAnuncio("olx_santo_amaro_centro_01", "Casa espaçosa 3 quartos próxima ao centro histórico", "OLX", 1600.00, "Santo Amaro", "Centro", 3, 130.0, "https://ba.olx.com.br/regiao-de-feira-de-santana-e-santo-amaro/imoveis/casa-aluguel-santo-amaro-3-quartos-777888/", hoje, 2)
    ]

    buscador.processar_resultados_e_salvar(dados_iniciais)

if __name__ == "__main__":
    executar()

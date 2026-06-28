# 🏡 Busca Imóveis Salvador & Cidades Próximas (Comutação Diária)
> **Projeto desenvolvido sob a chancela 🔬 YLuna85 LABs**

Aplicação automatizada para raspagem, consolidação, histórico CSV e monitoramento de anúncios de aluguel.

### 🎯 Diretrizes Geográficas
* **Prioridade 1 (Capital)**: Salvador/BA e seus bairros.
* **Prioridade 2 (Comutação Diária)**: Lauro de Freitas, Santo Amaro, Simões Filho, Camaçari, Candeias, São Francisco do Conde e Dias d'Ávila.

---

## 📍 Anúncios Ativos Monitorados (28/06/2026)

| Prioridade | Plataforma | Cidade / Bairro | Título / Descrição | Preço Aluguel | Status | Link do Anúncio |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| ⭐ Capital | VivaReal | Salvador - Imbuí | Casa térrea com quintal amplo e 2 vagas de garagem | R$ 2.300,00 | 🟢 Disponível | [Acessar Anúncio 🔗](https://www.vivareal.com.br/imovel/casa-3-quartos-imbui-salvador-110m2-id-456789/) |
| ⭐ Capital | OLX | Salvador - Pituba | Casa duplex 3 quartos com suíte e garagem privativa | R$ 2.800,00 | 🟢 Disponível | [Acessar Anúncio 🔗](https://ba.olx.com.br/grande-salvador/imoveis/aluguel-casa-pituba-3-quartos-12345678) |
| 🚗 Comutação | OLX | Santo Amaro - Centro | Casa espaçosa 3 quartos próxima ao centro histórico | R$ 1.600,00 | 🟢 Disponível | [Acessar Anúncio 🔗](https://ba.olx.com.br/regiao-de-feira-de-santana-e-santo-amaro/imoveis/casa-aluguel-santo-amaro-3-quartos-777888/) |
| 🚗 Comutação | Chave na Mão | Lauro de Freitas - Buraquinho | Casa em condomínio fechado perto da praia de Buraquinho | R$ 3.200,00 | 🟢 Disponível | [Acessar Anúncio 🔗](https://www.chavenamao.com.br/imovel/aluguel-casa-lauro-de-freitas-4-quartos/id-987654/) |

---

## 📊 Histórico e Arquivos Gerados
* **JSON Estruturado para HTML**: `data/anuncios_imoveis_salvador.json`
* **Histórico Completo em CSV**: `data/historico_imoveis.csv` (5 registros totais)

---

## 📜 Log de Atualizações (Changelog)
* **28/06/2026**: Implementação da exportação automática de histórico em CSV (`historico_imoveis.csv`), controle de ciclo de vida do anúncio (Ativo vs. Alugado/Indisponível) e JSON otimizado para o frontend.

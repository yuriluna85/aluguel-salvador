# 🏡 Busca Imóveis Salvador & Cidades Próximas (Comutação Diária)
> **Projeto desenvolvido sob a chancela 🔬 YLuna85 LABs**

Aplicação automatizada para raspagem, consolidação e monitoramento diário de casas e apartamentos para aluguel.

### 🎯 Diretrizes de Busca Geográfica
* **Prioridade 1 (Máxima)**: Salvador/BA e seus bairros (Pituba, Imbuí, Brotas, Cabula, Barra, etc.).
* **Prioridade 2 (Comutação Diária)**: Cidades com raio de fácil acesso diário de ir e voltar (Lauro de Freitas, Santo Amaro, Simões Filho, Camaçari, Candeias, São Francisco do Conde e Dias d'Ávila).

---

## 📍 Anúncios Monitorados (Atualizado em 28/06/2026)

| Prioridade | Plataforma | Cidade / Bairro | Título / Descrição | Preço Aluguel | Link do Anúncio |
| :--- | :--- | :--- | :--- | :--- | :--- |
| ⭐ Capital (Salvador) | VivaReal | Salvador - Imbuí | Casa térrea com quintal amplo e 2 vagas de garagem | R$ 2.300,00 | [Acessar Anúncio 🔗](https://www.vivareal.com.br/imovel/casa-3-quartos-imbui-salvador-110m2-id-456789/) |
| ⭐ Capital (Salvador) | OLX | Salvador - Pituba | Casa duplex 3 quartos com suíte e garagem privativa | R$ 2.800,00 | [Acessar Anúncio 🔗](https://ba.olx.com.br/grande-salvador/imoveis/aluguel-casa-pituba-3-quartos-12345678) |
| 🚗 Comutação Diária | OLX | Santo Amaro - Centro | Casa espaçosa 3 quartos próxima ao centro histórico | R$ 1.600,00 | [Acessar Anúncio 🔗](https://ba.olx.com.br/regiao-de-feira-de-santana-e-santo-amaro/imoveis/casa-aluguel-santo-amaro-3-quartos-777888/) |
| 🚗 Comutação Diária | Chave na Mão | Lauro de Freitas - Buraquinho | Casa em condomínio fechado perto da praia de Buraquinho | R$ 3.200,00 | [Acessar Anúncio 🔗](https://www.chavenamao.com.br/imovel/aluguel-casa-lauro-de-freitas-4-quartos/id-987654/) |

---

## 🛠️ Configuração de Secrets no GitHub

Para execução automatizada via GitHub Actions, configure as seguintes variáveis no repositório (**Settings -> Secrets and variables -> Actions**):

* `SCRAPER_API_KEY_IMOVEIS`: Chave do ScraperAPI cadastrada com `yluna85.imoveis.ba@gmail.com`.
* `SERPER_API_KEY_IMOVEIS`: Chave do Serper.dev cadastrada com `yluna85.imoveis.ba@gmail.com`.

---

## 📜 Log de Atualizações (Changelog)
* **28/06/2026**: Adicionada a chancela oficial **YLuna85 LABs** no projeto e atualizada a hierarquia geográfica de buscas.

/**
 * App.js - Lógica Interativa do Buscador de Imóveis (YLuna85 LABs)
 * Suporte a Histórico, Status Alugado/Indisponível e Carga via JSON/CSV
 */

document.addEventListener("DOMContentLoaded", () => {
    // Estado da Aplicação
    let imoveisAtivos = [];
    let imoveisIndisponiveis = [];
    let currentTab = "ativos"; // "ativos" ou "indisponiveis"
    let currentFontSize = 16;

    // Elementos DOM
    const gridEl = document.getElementById("imoveis-grid");
    const noResultsEl = document.getElementById("no-results");
    const countEl = document.getElementById("results-count");
    const statsBoxEl = document.getElementById("header-stats-box");
    
    // Abas e Badges
    const tabAtivosBtn = document.getElementById("tab-ativos");
    const tabIndisponiveisBtn = document.getElementById("tab-indisponiveis");
    const badgeAtivosEl = document.getElementById("count-badge-ativos");
    const badgeIndisponiveisEl = document.getElementById("count-badge-indisponiveis");

    // Filtros
    const searchInput = document.getElementById("search-input");
    const selectCidade = document.getElementById("select-cidade");
    const selectPlataforma = document.getElementById("select-plataforma");
    const selectOrdem = document.getElementById("select-ordem");

    // A11y
    const btnFontDecrease = document.getElementById("btn-font-decrease");
    const btnFontReset = document.getElementById("btn-font-reset");
    const btnFontIncrease = document.getElementById("btn-font-increase");
    const btnContrastToggle = document.getElementById("btn-contrast-toggle");

    // 1. Inicializar Aplicação
    async function init() {
        setupA11y();
        setupEventListeners();

        try {
            const response = await fetch("data/anuncios_imoveis_salvador.json");
            if (response.ok) {
                const data = await response.json();
                if (data.ativos && data.indisponiveis) {
                    imoveisAtivos = data.ativos;
                    imoveisIndisponiveis = data.indisponiveis;
                } else if (Array.isArray(data)) {
                    imoveisAtivos = data.filter(i => i.status === "ativo");
                    imoveisIndisponiveis = data.filter(i => i.status !== "ativo");
                } else {
                    const list = Object.values(data);
                    imoveisAtivos = list.filter(i => i.status === "ativo" || !i.status);
                    imoveisIndisponiveis = list.filter(i => i.status && i.status !== "ativo");
                }
            }
        } catch (error) {
            console.log("Modo offline ou leitura local.");
        }

        updateBadgesAndStats();
        renderImoveis();
    }

    // 2. Atualizar Badges e Estatísticas
    function updateBadgesAndStats() {
        badgeAtivosEl.textContent = imoveisAtivos.length;
        badgeIndisponiveisEl.textContent = imoveisIndisponiveis.length;

        const totalHistorico = imoveisAtivos.length + imoveisIndisponiveis.length;
        const somaValores = imoveisAtivos.reduce((acc, curr) => acc + (curr.preco_aluguel || 0), 0);
        const mediaPreco = imoveisAtivos.length > 0 ? somaValores / imoveisAtivos.length : 0;

        statsBoxEl.innerHTML = `
            <div class="stat-card">
                <div class="stat-value">${imoveisAtivos.length}</div>
                <div class="stat-label">Disponíveis</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">R$ ${Math.round(mediaPreco).toLocaleString("pt-BR")}</div>
                <div class="stat-label">Média Aluguel</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${totalHistorico}</div>
                <div class="stat-label">Histórico CSV</div>
            </div>
        `;
    }

    // 3. Filtrar e Ordenar
    function getFilteredAndSortedData() {
        const sourceData = currentTab === "ativos" ? imoveisAtivos : imoveisIndisponiveis;
        const term = searchInput.value.toLowerCase().trim();
        const cidadeFiltro = selectCidade.value;
        const platFiltro = selectPlataforma.value;
        const ordem = selectOrdem.value;

        let filtered = sourceData.filter(item => {
            const matchTerm = !term || 
                item.titulo.toLowerCase().includes(term) ||
                item.cidade.toLowerCase().includes(term) ||
                item.bairro.toLowerCase().includes(term);

            let matchCidade = true;
            if (cidadeFiltro === "salvador") {
                matchCidade = item.cidade === "Salvador";
            } else if (cidadeFiltro === "comutacao") {
                matchCidade = item.cidade !== "Salvador";
            } else if (cidadeFiltro !== "todas") {
                matchCidade = item.cidade === cidadeFiltro;
            }

            const matchPlat = platFiltro === "todas" || item.plataforma === platFiltro;
            return matchTerm && matchCidade && matchPlat;
        });

        filtered.sort((a, b) => {
            if (ordem === "prioridade") {
                return (a.prioridade || 1) - (b.prioridade || 1) || a.preco_aluguel - b.preco_aluguel;
            } else if (ordem === "preco-asc") {
                return a.preco_aluguel - b.preco_aluguel;
            } else if (ordem === "preco-desc") {
                return b.preco_aluguel - a.preco_aluguel;
            } else if (ordem === "recentes") {
                return new Date(b.data_descoberta) - new Date(a.data_descoberta);
            }
            return 0;
        });

        return filtered;
    }

    // 4. Renderizar
    function renderImoveis() {
        const list = getFilteredAndSortedData();
        countEl.textContent = `(${list.length})`;

        if (list.length === 0) {
            gridEl.innerHTML = "";
            noResultsEl.classList.remove("hidden");
            return;
        }

        noResultsEl.classList.add("hidden");
        gridEl.innerHTML = list.map(item => {
            const isCapital = item.cidade === "Salvador";
            const prioTag = isCapital 
                ? `<span class="tag tag-prio-1">⭐ Capital</span>` 
                : `<span class="tag tag-prio-2">🚗 Comutação</span>`;

            const isAlugado = item.status && item.status !== "ativo";
            const statusTag = isAlugado 
                ? `<span class="tag tag-status-alugado">🔴 Alugado / Indisponível</span>`
                : `<span class="tag tag-prio-1">🟢 Disponível</span>`;

            const precoFmt = item.preco_aluguel > 0 
                ? `R$ ${item.preco_aluguel.toLocaleString("pt-BR", {minimumFractionDigits: 2})}` 
                : "Sob Consulta";

            return `
                <article class="imovel-card ${isAlugado ? 'card-indisponivel' : ''}" aria-label="Anúncio: ${item.titulo}">
                    <div>
                        <div class="card-tags">
                            ${statusTag}
                            ${prioTag}
                            <span class="tag tag-platform">${item.plataforma}</span>
                        </div>
                        <h3 class="card-title">${item.titulo}</h3>
                        <div class="card-location">
                            <span>📍</span>
                            <span><strong>${item.cidade}</strong> - ${item.bairro}</span>
                        </div>
                        <div class="card-specs">
                            <div class="spec-item">🛏️ <strong>${item.quartos}</strong> qts</div>
                            <div class="spec-item">📐 <strong>${item.area_m2}</strong> m²</div>
                        </div>
                    </div>
                    <div class="card-footer">
                        <div class="price-box">
                            <span class="price-label">Valor Aluguel</span>
                            <span class="price-value">${precoFmt}</span>
                        </div>
                        <a href="${item.link}" target="_blank" rel="noopener noreferrer" class="btn-link" aria-label="Ver anúncio na plataforma ${item.plataforma}">
                            ${isAlugado ? 'Ver Histórico 🔗' : 'Ver Anúncio 🔗'}
                        </a>
                    </div>
                </article>
            `;
        }).join("");
    }

    // 5. Event Listeners
    function setupEventListeners() {
        tabAtivosBtn.addEventListener("click", () => {
            currentTab = "ativos";
            tabAtivosBtn.classList.add("active");
            tabIndisponiveisBtn.classList.remove("active");
            tabAtivosBtn.setAttribute("aria-selected", "true");
            tabIndisponiveisBtn.setAttribute("aria-selected", "false");
            renderImoveis();
        });

        tabIndisponiveisBtn.addEventListener("click", () => {
            currentTab = "indisponiveis";
            tabIndisponiveisBtn.classList.add("active");
            tabAtivosBtn.classList.remove("active");
            tabIndisponiveisBtn.setAttribute("aria-selected", "true");
            tabAtivosBtn.setAttribute("aria-selected", "false");
            renderImoveis();
        });

        searchInput.addEventListener("input", renderImoveis);
        selectCidade.addEventListener("change", renderImoveis);
        selectPlataforma.addEventListener("change", renderImoveis);
        selectOrdem.addEventListener("change", renderImoveis);
    }

    // 6. A11y
    function setupA11y() {
        btnFontDecrease.addEventListener("click", () => {
            if (currentFontSize > 12) {
                currentFontSize -= 2;
                document.documentElement.style.fontSize = `${currentFontSize}px`;
            }
        });

        btnFontReset.addEventListener("click", () => {
            currentFontSize = 16;
            document.documentElement.style.fontSize = "16px";
        });

        btnFontIncrease.addEventListener("click", () => {
            if (currentFontSize < 24) {
                currentFontSize += 2;
                document.documentElement.style.fontSize = `${currentFontSize}px`;
            }
        });

        btnContrastToggle.addEventListener("click", () => {
            document.body.classList.toggle("high-contrast");
        });
    }

    init();
});

<!DOCTYPE html>
<html lang="pt-BR" class="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>ProEstudos - Concursos 2.0</title>
    
    <!-- 👇 Ícone da aba do navegador (Favicon de Chapéu de Formatura) -->
    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🎓</text></svg>">
    
    <script>
        if (localStorage.getItem('theme') === 'dark' || (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }
    </script>
    
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/@phosphor-icons/web"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
    
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    fontFamily: { sans: ['Inter', 'sans-serif'] },
                    colors: { brand: { 500: '#4f46e5', 600: '#4338ca' } }
                }
            }
        }
    </script>
    
    <style>
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 10px; }
        .dark ::-webkit-scrollbar-thumb { background: #475569; }
        ::-webkit-scrollbar-thumb:hover { background: #94a3b8; }

        .ai-brain {
            background: linear-gradient(135deg, #4f46e5, #ec4899);
            background-clip: text;
            -webkit-background-clip: text;
            color: transparent;
            -webkit-text-fill-color: transparent;
        }

        mark {
            background-color: #fde047;
            color: #0f172a;
            border-radius: 4px;
            padding: 0 4px;
        }

        /* ESTILOS DE IMPRESSÃO - SIMULADO CLÁSSICO */
        @media print {
            @page { margin: 1.5cm; }
            html, body, main, #main-scroll, #conteudo-principal { 
                height: auto !important; min-height: auto !important;
                overflow: visible !important; width: 100% !important; position: static !important;
                display: block !important; background: #fff !important; padding: 0 !important; margin: 0 !important;
            }
            * { box-shadow: none !important; text-shadow: none !important; color: #000 !important; }
            #sidebar, #overlay, header, .no-print, [id^="loading-"], .chat-container, .anotacao-container { display: none !important; }
            
            [id^="card_questao_"] { 
                page-break-inside: avoid; break-inside: avoid; margin-bottom: 25px !important; 
                border: none !important; border-bottom: 1px dashed #ccc !important; padding: 0 0 20px 0 !important;
                display: block !important; background-color: transparent !important; border-radius: 0 !important;
            }
            [id^="card_questao_"] .flex.flex-col.gap-2 { flex-direction: row !important; flex-wrap: wrap !important; gap: 8px !important; margin-bottom: 10px !important; }
            [id^="card_questao_"] span.bg-indigo-50, [id^="card_questao_"] span.bg-slate-100, [id^="card_questao_"] span.bg-emerald-50 {
                background: transparent !important; border: 1px solid #000 !important; padding: 2px 6px !important; font-size: 9pt !important; font-weight: bold !important;
            }
            [id^="card_questao_"] p { font-size: 11pt !important; line-height: 1.4 !important; text-align: justify !important; margin-bottom: 15px !important; }
            
            /* A mágica do layout limpo e junto nas alternativas */
            [id^="alts_"] { margin-bottom: 5px !important; }
            [id^="alts_"] button { 
                border: none !important; margin-bottom: 6px !important; padding: 0 !important; 
                break-inside: avoid; display: flex !important; align-items: flex-start !important; 
                background-color: transparent !important; opacity: 1 !important; 
            }
            [id^="check_"] { 
                border: 1px solid #000 !important; background-color: transparent !important; 
                width: 14px !important; height: 14px !important; min-width: 14px !important; 
                margin-top: 3px !important; margin-right: 10px !important; border-radius: 50% !important; 
            }
            [id^="alts_"] span.flex-1 { font-size: 10.5pt !important; line-height: 1.3 !important; }
        }
    </style>
</head>
<body class="bg-slate-50 dark:bg-slate-950 text-slate-800 dark:text-slate-200 font-sans h-[100dvh] flex overflow-hidden transition-colors duration-300">

    <div id="overlay" onclick="toggleSidebar()" class="fixed inset-0 bg-slate-900/60 dark:bg-black/80 z-30 hidden md:hidden backdrop-blur-sm transition-opacity"></div>

    <aside id="sidebar" class="w-72 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 flex flex-col fixed md:relative h-[100dvh] z-40 transform -translate-x-full md:translate-x-0 transition-transform duration-300 shrink-0">
        <div class="p-6 border-b border-slate-200 dark:border-slate-800 shrink-0 flex justify-between items-center">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center text-white shadow-lg shadow-indigo-200 dark:shadow-none shrink-0">
                    <i class="ph-bold ph-student text-2xl"></i>
                </div>
                <div class="min-w-0">
                    <h1 class="text-xl font-black tracking-tight text-slate-900 dark:text-white truncate">ProEstudos</h1>
                    <p class="text-[10px] uppercase font-bold text-indigo-500 tracking-wider">Concursos 2.0</p>
                </div>
            </div>
            <!-- Botão de fechar só aparece no celular -->
            <button onclick="toggleSidebar()" class="md:hidden text-slate-400 hover:text-slate-700 dark:hover:text-white p-2">
                <i class="ph-bold ph-x text-xl"></i>
            </button>
        </div>

        <div class="flex-1 overflow-y-auto p-4 space-y-1" id="menu-disciplinas">
            <button onclick="carregarPainel()" class="w-full flex items-center gap-3 px-4 py-3 bg-indigo-50 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-400 font-bold rounded-xl transition-colors">
                <i class="ph-bold ph-chart-pie-slice text-xl"></i> Dashboards
            </button>
            <button onclick="iniciarCadernoDeErros()" class="w-full flex items-center gap-3 px-4 py-3 hover:bg-rose-50 dark:hover:bg-rose-900/20 text-slate-700 hover:text-rose-600 dark:text-slate-400 dark:hover:text-rose-400 font-bold rounded-xl transition-colors mt-2 border border-slate-200 dark:border-slate-800 hover:border-rose-200 dark:hover:border-rose-800">
                <i class="ph-bold ph-book-open text-xl text-rose-500"></i> Caderno de Erros
            </button>
            <div class="pt-4 pb-2 px-2 text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider flex justify-between items-center">
                <span>Disciplinas</span>
                <button onclick="abrirModalNovaDisciplina()" class="hover:text-indigo-600 transition" title="Adicionar Disciplina"><i class="ph-bold ph-plus text-lg"></i></button>
            </div>
            <div id="lista-disciplinas-menu" class="space-y-1"></div>
        </div>

        <div class="p-4 border-t border-slate-200 dark:border-slate-800 space-y-2 shrink-0 bg-white dark:bg-slate-900">
            <button onclick="abrirModalIA()" class="w-full flex items-center justify-center gap-2 px-4 py-3.5 bg-slate-900 dark:bg-indigo-600 text-white font-bold rounded-xl hover:bg-slate-800 dark:hover:bg-indigo-700 transition shadow-md active:scale-[0.98]">
                <i class="ph-fill ph-magic-wand text-xl text-yellow-400"></i> Gerar via IA
            </button>
            <div class="flex gap-2">
                <button onclick="abrirModalConfig()" class="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-bold rounded-xl hover:bg-slate-200 dark:hover:bg-slate-700 transition">
                    <i class="ph-bold ph-gear"></i> Config
                </button>
            </div>
        </div>
    </aside>

    <main class="flex-1 flex flex-col h-[100dvh] min-w-0 overflow-hidden relative bg-slate-50 dark:bg-slate-950">
        
        <header class="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 px-4 py-3 flex items-center justify-between sticky top-0 z-20 shrink-0 shadow-sm no-print">
            <div class="flex items-center gap-3 min-w-0 flex-1 pr-2">
                <button onclick="toggleSidebar()" class="md:hidden w-10 h-10 flex items-center justify-center text-slate-700 dark:text-slate-200 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 rounded-xl transition-colors shrink-0">
                    <i class="ph-bold ph-list text-2xl"></i>
                </button>
                <h2 id="header-title" class="text-lg md:text-xl font-black text-slate-900 dark:text-white truncate">Painel Geral</h2>
            </div>
            
            <div class="flex items-center gap-2 shrink-0">
                <div class="flex items-center gap-1.5 bg-gradient-to-r from-orange-500 to-amber-500 text-white px-3 py-2 rounded-xl shadow-md font-bold text-sm shrink-0">
                    <i class="ph-fill ph-fire text-lg animate-pulse"></i>
                    <span id="streak-counter" class="hidden sm:inline">0 dias</span>
                </div>
                <button onclick="toggleTheme()" class="w-10 h-10 flex items-center justify-center bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 font-bold rounded-xl hover:bg-slate-200 dark:hover:bg-slate-700 transition shrink-0">
                    <i id="theme-icon" class="ph-bold ph-moon text-lg"></i>
                </button>
                <button onclick="window.print()" title="Imprimir PDF" class="w-10 h-10 sm:w-auto sm:px-3 sm:py-2 flex items-center justify-center gap-1.5 bg-indigo-50 dark:bg-indigo-900/40 border border-indigo-200 dark:border-indigo-800 rounded-xl text-indigo-700 dark:text-indigo-400 hover:bg-indigo-100 transition-colors shrink-0">
                    <i class="ph-bold ph-printer text-lg"></i>
                    <span class="text-sm font-bold hidden sm:inline">PDF</span>
                </button>
            </div>
        </header>

        <div id="barra-pressao" class="hidden bg-slate-900 text-white p-3 flex justify-between items-center shadow-lg z-10 shrink-0 border-b-4 border-rose-500 sticky top-0 no-print">
            <div class="flex items-center gap-2 font-black text-rose-400 animate-pulse">
                <i class="ph-fill ph-timer text-2xl"></i> <span id="timer-display" class="text-xl tracking-widest">00:00:00</span>
            </div>
            <div class="text-sm font-bold bg-white/20 px-3 py-1 rounded-lg">Modo Simulado Ativo</div>
            <button onclick="finalizarModoPressao()" class="bg-rose-500 hover:bg-rose-600 text-white px-4 py-2 rounded-xl font-bold transition">Finalizar Prova</button>
        </div>

        <div class="flex-1 overflow-y-auto p-4 md:p-8" id="main-scroll">
            <div class="max-w-4xl mx-auto" id="conteudo-principal"></div>
        </div>
        
        <div id="loading-ia" class="hidden absolute inset-0 bg-white/95 dark:bg-slate-950/95 backdrop-blur-md z-50 flex flex-col items-center justify-center">
            <i class="ph-fill ph-brain text-7xl ai-brain animate-pulse mb-6"></i>
            <h3 class="text-2xl font-black text-slate-900 dark:text-white mb-2">Trabalhando...</h3>
            <p class="text-slate-500 dark:text-slate-400 font-medium text-center px-4">Conectando ao modelo de Inteligência Artificial.</p>
        </div>
    </main>

    <!-- Modal Gerar IA -->
    <div id="modal-ia" class="fixed inset-0 bg-slate-900/60 dark:bg-black/80 z-50 hidden items-center justify-center p-4 backdrop-blur-sm">
        <div class="bg-white dark:bg-slate-900 rounded-3xl shadow-2xl w-full max-w-md border border-slate-200 dark:border-slate-800 flex flex-col max-h-[90dvh]">
            <div class="p-5 border-b border-slate-100 dark:border-slate-800 flex justify-between items-center shrink-0">
                <h3 class="font-extrabold text-lg flex items-center gap-2 dark:text-white"><i class="ph-fill ph-magic-wand text-indigo-500"></i> Gerador IA</h3>
                <button onclick="fecharModal('modal-ia')" class="text-slate-400 hover:text-slate-700 dark:hover:text-white p-2"><i class="ph-bold ph-x text-xl"></i></button>
            </div>
            
            <div class="p-6 space-y-4 overflow-y-auto flex-1">
                <div class="grid grid-cols-2 gap-2 mb-4 bg-slate-100 dark:bg-slate-800 p-1 rounded-xl shrink-0">
                    <button onclick="mudarAbaIA('disciplina')" id="aba-disciplina" class="py-2.5 bg-white dark:bg-slate-700 shadow text-indigo-600 dark:text-white font-bold text-sm rounded-lg transition-all">Foco Específico</button>
                    <button onclick="mudarAbaIA('simulado')" id="aba-simulado" class="py-2.5 text-slate-500 dark:text-slate-400 hover:text-slate-700 font-bold text-sm rounded-lg transition-all">Simulado Geral</button>
                </div>

                <div id="form-disciplina">
                    <label class="block text-sm font-bold text-slate-700 dark:text-slate-300 mb-1">Origem das Questões</label>
                    <select id="ia-tipo" class="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3 outline-none focus:border-indigo-500 dark:text-white mb-4">
                        <option value="reais">Questões REAIS (Provas Anteriores)</option>
                        <option value="ineditas">Questões Inéditas (Criadas pela IA)</option>
                    </select>

                    <label class="block text-sm font-bold text-slate-700 dark:text-slate-300 mb-1">Disciplina</label>
                    <select id="ia-disciplina" class="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3 outline-none focus:border-indigo-500 dark:text-white mb-4"></select>
                    
                    <div class="grid grid-cols-2 gap-3 mb-4">
                        <div>
                            <label class="block text-sm font-bold text-slate-700 dark:text-slate-300 mb-1">Nível</label>
                            <select id="ia-nivel" class="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3 outline-none focus:border-indigo-500 dark:text-white">
                                <option>Médio</option>
                                <option>Superior</option>
                                <option>Magistratura</option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-sm font-bold text-slate-700 dark:text-slate-300 mb-1">Quantidade</label>
                            <select id="ia-qtd" class="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3 outline-none focus:border-indigo-500 dark:text-white">
                                <option value="5">5 Questões</option>
                                <option value="10" selected>10 Questões</option>
                                <option value="20">20 Questões</option>
                            </select>
                        </div>
                    </div>
                    
                    <label class="block text-sm font-bold text-slate-700 dark:text-slate-300 mb-1">Banca Específica</label>
                    <select id="ia-banca" class="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3 outline-none focus:border-indigo-500 dark:text-white mb-4">
                        <option value="">Qualquer Banca</option>
                        <option value="CEBRASPE (CESPE)">CEBRASPE (CESPE)</option>
                        <option value="FGV (Fundação Getulio Vargas)">FGV</option>
                        <option value="VUNESP">VUNESP</option>
                        <option value="FCC (Fundação Carlos Chagas)">FCC</option>
                        <option value="Cesgranrio">Cesgranrio</option>
                        <option value="Instituto AOCP">Instituto AOCP</option>
                        <option value="IBFC">IBFC</option>
                        <option value="IDECAN">IDECAN</option>
                    </select>
                    
                    <label class="block text-sm font-bold text-slate-700 dark:text-slate-300 mb-1">Qual Concurso? (Órgão / Cargo Alvo)</label>
                    <select id="ia-orgao" class="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 border-indigo-400 dark:border-indigo-500 rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-indigo-500 dark:text-white mb-4">
                        <option value="">Qualquer Concurso (Geral)</option>
                        <optgroup label="🎓 Carreiras Educacionais">
                            <option value="SEDUC-PA - Professor">SEDUC-PA - Professor</option>
                            <option value="SEDUC-PA - Especialista em Educação">SEDUC-PA - Especialista em Educação</option>
                            <option value="SEDUC-PA - Assistente Administrativo">SEDUC-PA - Assistente Administrativo</option>
                            <option value="SEMEC - Professor / Pedagogo">SEMEC - Professor / Pedagogo</option>
                            <option value="Universidades Federais (TAE)">Universidades Federais (TAE)</option>
                        </optgroup>
                        <optgroup label="🚓 Segurança Pública">
                            <option value="Polícia Civil (PC-PA) - Investigador">Polícia Civil (PC-PA) - Investigador</option>
                            <option value="Polícia Civil (PC-PA) - Escrivão">Polícia Civil (PC-PA) - Escrivão</option>
                            <option value="Polícia Civil (PC-PA) - Papiloscopista">Polícia Civil (PC-PA) - Papiloscopista</option>
                            <option value="Polícia Civil (PC-PA) - Delegado">Polícia Civil (PC-PA) - Delegado</option>
                            <option value="Polícia Militar (PM-PA) - Soldado">Polícia Militar (PM-PA) - Soldado</option>
                            <option value="Polícia Militar (PM-PA) - Oficial">Polícia Militar (PM-PA) - Oficial</option>
                            <option value="Polícia Penal (SEAP-PA)">Polícia Penal (SEAP-PA)</option>
                            <option value="Polícia Federal (PF)">Polícia Federal (PF)</option>
                            <option value="Polícia Rodoviária Federal (PRF)">Polícia Rodoviária Federal (PRF)</option>
                            <option value="Corpo de Bombeiros (CBMPA)">Corpo de Bombeiros (CBMPA)</option>
                        </optgroup>
                        <optgroup label="⚖️ Tribunais e Jurídicas">
                            <option value="Tribunal de Justiça (TJ-PA)">Tribunal de Justiça (TJ-PA)</option>
                            <option value="Justiça Eleitoral (TRE / TSE Unificado)">Justiça Eleitoral (TRE / TSE Unificado)</option>
                            <option value="Tribunal Regional do Trabalho (TRT)">Tribunal Regional do Trabalho (TRT)</option>
                            <option value="Tribunal Regional Federal (TRF)">Tribunal Regional Federal (TRF)</option>
                            <option value="Ministério Público (MP-PA / MPU)">Ministério Público (MP-PA / MPU)</option>
                            <option value="Defensoria Pública (DPE-PA)">Defensoria Pública (DPE-PA)</option>
                        </optgroup>
                        <optgroup label="🏢 Administrativas, Fiscais e Controle">
                            <option value="INSS - Técnico / Analista">INSS - Técnico / Analista</option>
                            <option value="SEFA-PA (Auditor / Fiscal)">SEFA-PA (Auditor / Fiscal)</option>
                            <option value="TCE-PA (Tribunal de Contas)">TCE-PA (Tribunal de Contas)</option>
                            <option value="Banco do Brasil / Caixa Econômica">Banco do Brasil / Caixa Econômica</option>
                            <option value="Correios">Correios</option>
                            <option value="Assembleia Legislativa (ALEPA)">Assembleia Legislativa (ALEPA)</option>
                        </optgroup>
                        <optgroup label="🏥 Carreiras da Saúde">
                            <option value="Secretaria de Saúde (SESPA)">Secretaria de Saúde (SESPA)</option>
                            <option value="Hospitais Universitários (EBSERH)">Hospitais Universitários (EBSERH)</option>
                        </optgroup>
                    </select>

                    <label class="block text-sm font-bold text-slate-700 dark:text-slate-300 mb-1">Filtro Cirúrgico (Subtópico)</label>
                    <input type="text" id="ia-topico" placeholder="Ex: Habeas Corpus, Crase..." class="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3 outline-none focus:border-indigo-500 dark:text-white mb-6">

                    <button onclick="gerarQuestoes()" class="w-full py-4 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl transition shadow-md flex items-center justify-center gap-2">
                        <i class="ph-bold ph-check-circle text-lg"></i> Iniciar Busca
                    </button>
                </div>

                <div id="form-simulado" class="hidden">
                    <label class="block text-sm font-bold text-slate-700 dark:text-slate-300 mb-1">Modo Prova (Cronometrado)</label>
                    <select id="sim-pressao" class="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3 outline-none focus:border-indigo-500 dark:text-white mb-4 font-bold text-rose-500">
                        <option value="0">Desativado (Modo Normal)</option>
                        <option value="30">30 Minutos (Sem gabarito na hora)</option>
                        <option value="60">1 Hora (Sem gabarito na hora)</option>
                        <option value="120">2 Horas (Sem gabarito na hora)</option>
                    </select>

                    <label class="block text-sm font-bold text-slate-700 dark:text-slate-300 mb-1">Origem das Questões</label>
                    <select id="sim-tipo" class="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3 outline-none focus:border-indigo-500 dark:text-white mb-4">
                        <option value="reais">Questões REAIS (Provas Anteriores)</option>
                        <option value="ineditas">Questões Inéditas (Criadas pela IA)</option>
                    </select>
                    
                    <div class="grid grid-cols-2 gap-3 mb-4">
                        <div>
                            <label class="block text-sm font-bold text-slate-700 dark:text-slate-300 mb-1">Banca Específica</label>
                            <select id="sim-banca" class="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3 outline-none focus:border-indigo-500 dark:text-white">
                                <option value="">Qualquer Banca</option>
                                <option value="CEBRASPE (CESPE)">CEBRASPE</option>
                                <option value="FGV">FGV</option>
                                <option value="VUNESP">VUNESP</option>
                                <option value="FCC">FCC</option>
                                <option value="Cesgranrio">Cesgranrio</option>
                                <option value="Instituto AOCP">AOCP</option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-sm font-bold text-slate-700 dark:text-slate-300 mb-1">Qual Concurso?</label>
                            <select id="sim-orgao" class="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 border-indigo-400 dark:border-indigo-500 rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-indigo-500 dark:text-white">
                                <option value="">Qualquer Concurso (Geral)</option>
                                <optgroup label="🎓 Carreiras Educacionais">
                                    <option value="SEDUC-PA - Professor">SEDUC-PA - Professor</option>
                                    <option value="SEDUC-PA - Especialista em Educação">SEDUC-PA - Especialista em Educação</option>
                                    <option value="SEDUC-PA - Assistente Administrativo">SEDUC-PA - Assistente Administrativo</option>
                                    <option value="SEMEC - Professor / Pedagogo">SEMEC - Professor / Pedagogo</option>
                                </optgroup>
                                <optgroup label="🚓 Segurança Pública">
                                    <option value="Polícia Civil (PC-PA) - Investigador">Polícia Civil (PC-PA) - Investigador</option>
                                    <option value="Polícia Civil (PC-PA) - Escrivão">Polícia Civil (PC-PA) - Escrivão</option>
                                    <option value="Polícia Civil (PC-PA) - Papiloscopista">Polícia Civil (PC-PA) - Papiloscopista</option>
                                    <option value="Polícia Militar (PM-PA)">Polícia Militar (PM-PA)</option>
                                    <option value="Polícia Penal (SEAP-PA)">Polícia Penal (SEAP-PA)</option>
                                    <option value="Polícia Federal (PF)">Polícia Federal (PF)</option>
                                    <option value="Polícia Rodoviária Federal (PRF)">Polícia Rodoviária Federal (PRF)</option>
                                </optgroup>
                                <optgroup label="⚖️ Tribunais e Jurídicas">
                                    <option value="Tribunal de Justiça (TJ-PA)">Tribunal de Justiça (TJ-PA)</option>
                                    <option value="Justiça Eleitoral (TRE / TSE Unificado)">Justiça Eleitoral (TRE / TSE Unificado)</option>
                                    <option value="Tribunal Regional do Trabalho (TRT)">Tribunal Regional do Trabalho (TRT)</option>
                                    <option value="Ministério Público (MP-PA / MPU)">Ministério Público (MP-PA / MPU)</option>
                                </optgroup>
                                <optgroup label="🏢 Administrativas, Fiscais e Bancárias">
                                    <option value="INSS - Técnico / Analista">INSS - Técnico / Analista</option>
                                    <option value="SEFA-PA (Auditor / Fiscal)">SEFA-PA (Auditor / Fiscal)</option>
                                    <option value="Banco do Brasil / Caixa Econômica">Banco do Brasil / Caixa Econômica</option>
                                    <option value="Correios">Correios</option>
                                </optgroup>
                            </select>
                        </div>
                    </div>

                    <div class="grid grid-cols-2 gap-3 mb-6">
                        <div>
                            <label class="block text-sm font-bold text-slate-700 dark:text-slate-300 mb-1">Nível</label>
                            <select id="sim-nivel" class="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3 outline-none focus:border-indigo-500 dark:text-white">
                                <option>Médio</option><option>Superior</option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-sm font-bold text-slate-700 dark:text-slate-300 mb-1">Total</label>
                            <select id="sim-qtd" class="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3 outline-none focus:border-indigo-500 dark:text-white">
                                <option value="10">10 Questões</option>
                                <option value="20" selected>20 Questões</option>
                                <option value="50">50 Questões</option>
                            </select>
                        </div>
                    </div>
                    
                    <button onclick="gerarSimulado()" class="w-full py-4 bg-slate-900 dark:bg-indigo-600 hover:bg-slate-800 text-white font-bold rounded-xl transition shadow-md flex items-center justify-center gap-2">
                        <i class="ph-bold ph-rocket-launch text-lg"></i> Iniciar Simulado
                    </button>
                </div>
            </div>
        </div>
    </div>

    <!-- Modais Genéricos -->
    <div id="modal-disciplina" class="fixed inset-0 bg-slate-900/60 dark:bg-black/80 z-50 hidden items-center justify-center p-4 backdrop-blur-sm">
        <div class="bg-white dark:bg-slate-900 rounded-3xl shadow-2xl w-full max-w-sm overflow-hidden p-6 border border-slate-200 dark:border-slate-800">
            <h3 class="font-extrabold text-lg mb-4 dark:text-white">Nova Disciplina</h3>
            <input type="text" id="nova-disciplina-nome" placeholder="Ex: Direito Penal" class="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3 outline-none focus:border-indigo-500 dark:text-white mb-4">
            <div class="flex gap-2">
                <button onclick="fecharModal('modal-disciplina')" class="flex-1 py-3 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-bold rounded-xl">Cancelar</button>
                <button onclick="salvarDisciplina()" class="flex-1 py-3 bg-indigo-600 text-white font-bold rounded-xl">Salvar</button>
            </div>
        </div>
    </div>

    <div id="modal-config" class="fixed inset-0 bg-slate-900/60 dark:bg-black/80 z-50 hidden items-center justify-center p-4 backdrop-blur-sm">
        <div class="bg-white dark:bg-slate-900 rounded-3xl shadow-2xl w-full max-w-md overflow-hidden p-6 border border-slate-200 dark:border-slate-800">
            <div class="flex justify-between items-center mb-4">
                <h3 class="font-extrabold text-lg flex items-center gap-2 dark:text-white"><i class="ph-fill ph-gear text-slate-500"></i> Configurações</h3>
                <button onclick="fecharModal('modal-config')" class="text-slate-400 hover:text-slate-700 p-1"><i class="ph-bold ph-x text-xl"></i></button>
            </div>
            <div class="mb-6">
                <label class="block text-sm font-bold text-slate-700 dark:text-slate-300 mb-1">Chave API (Groq)</label>
                <input type="password" id="config-groq" placeholder="gsk_..." class="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3 outline-none focus:border-indigo-500 dark:text-white mb-2">
                <p class="text-xs text-slate-500 dark:text-slate-400">Pegue sua chave gratuita em <a href="https://console.groq.com" target="_blank" class="text-indigo-500 font-bold">console.groq.com</a></p>
            </div>
            <div class="grid grid-cols-2 gap-3 mb-6 pt-4 border-t border-slate-200 dark:border-slate-800">
                <button onclick="resetarBanco()" class="w-full py-3 bg-rose-50 dark:bg-rose-900/20 text-rose-600 dark:text-rose-400 font-bold rounded-xl transition flex items-center justify-center gap-2 text-sm border border-rose-200 dark:border-rose-900/50">
                    <i class="ph-bold ph-trash"></i> Resetar
                </button>
                <button onclick="window.location.href=API_BASE_URL+'/api/backup'" class="w-full py-3 bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400 font-bold rounded-xl transition flex items-center justify-center gap-2 text-sm border border-emerald-200 dark:emerald-900/50">
                    <i class="ph-bold ph-download-simple"></i> Backup DB
                </button>
            </div>
            <button onclick="salvarConfig()" class="w-full py-3 bg-indigo-600 text-white font-bold rounded-xl shadow-md">Salvar</button>
        </div>
    </div>

    <script>
        // 👇 AQUI FOI FEITA A ALTERAÇÃO: Este é o link oficial do seu servidor gerado pelo Render!
        const API_BASE_URL = 'https://proestudos-api.onrender.com'; 
        
        let state = {
            disciplinas: [], disciplinaAtual: null, filtroAtual: 'todas', questoes: [], stats: {},
            modoPressao: false, respostasPressao: {}, tempoRestante: 0, timerInterval: null,
            isCadernoErros: false
        };

        let chartEvolucao = null;
        let chartPizza = null;

        async function api(endpoint, method = 'GET', body = null) {
            try {
                const options = { method, headers: { 'Content-Type': 'application/json' } };
                if (body) options.body = JSON.stringify(body);
                const res = await fetch(`${API_BASE_URL}${endpoint}`, options);
                if (!res.ok) throw new Error(await res.text());
                return await res.json();
            } catch (e) {
                alert("Erro de conexão com o servidor! Verifique se o Python está rodando."); return null;
            }
        }

        function toggleTheme() {
            const html = document.documentElement;
            if (html.classList.contains('dark')) { html.classList.remove('dark'); localStorage.setItem('theme', 'light'); document.getElementById('theme-icon').classList.replace('ph-sun', 'ph-moon'); } 
            else { html.classList.add('dark'); localStorage.setItem('theme', 'dark'); document.getElementById('theme-icon').classList.replace('ph-moon', 'ph-sun'); }
        }
        if(document.documentElement.classList.contains('dark')) document.getElementById('theme-icon').classList.replace('ph-moon', 'ph-sun');

        function toggleSidebar() {
            document.getElementById('sidebar').classList.toggle('-translate-x-full');
            document.getElementById('overlay').classList.toggle('hidden');
        }
        function fecharSidebarMobile() { 
            if (window.innerWidth < 768) { 
                document.getElementById('sidebar').classList.add('-translate-x-full'); 
                document.getElementById('overlay').classList.add('hidden'); 
            } 
        }

        function abrirModal(id) { document.getElementById(id).classList.replace('hidden', 'flex'); }
        function fecharModal(id) { document.getElementById(id).classList.replace('flex', 'hidden'); }
        
        function abrirModalNovaDisciplina() { fecharSidebarMobile(); abrirModal('modal-disciplina'); }
        function abrirModalConfig() { fecharSidebarMobile(); api('/api/config').then(data => { if(data) document.getElementById('config-groq').value = data.groq_key; }); abrirModal('modal-config'); }
        
        function abrirModalIA() { 
            fecharSidebarMobile();
            const sel = document.getElementById('ia-disciplina');
            sel.innerHTML = state.disciplinas.map(d => `<option value="${d.id}">${d.nome}</option>`).join('');
            if(state.disciplinaAtual) sel.value = state.disciplinaAtual;
            abrirModal('modal-ia');
        }

        function mudarAbaIA(aba) {
            if(aba === 'disciplina') {
                document.getElementById('form-disciplina').classList.remove('hidden'); document.getElementById('form-simulado').classList.add('hidden');
                document.getElementById('aba-disciplina').className = 'py-2.5 bg-white dark:bg-slate-700 shadow text-indigo-600 dark:text-white font-bold text-sm rounded-lg transition-all';
                document.getElementById('aba-simulado').className = 'py-2.5 text-slate-500 dark:text-slate-400 hover:text-slate-700 font-bold text-sm rounded-lg transition-all';
            } else {
                document.getElementById('form-disciplina').classList.add('hidden'); document.getElementById('form-simulado').classList.remove('hidden');
                document.getElementById('aba-disciplina').className = 'py-2.5 text-slate-500 dark:text-slate-400 hover:text-slate-700 font-bold text-sm rounded-lg transition-all';
                document.getElementById('aba-simulado').className = 'py-2.5 bg-white dark:bg-slate-700 shadow text-indigo-600 dark:text-white font-bold text-sm rounded-lg transition-all';
            }
        }

        function showLoading(show) { document.getElementById('loading-ia').classList.toggle('hidden', !show); }

        async function salvarDisciplina() {
            const nome = document.getElementById('nova-disciplina-nome').value;
            if(!nome) return; await api('/api/disciplina', 'POST', {nome}); fecharModal('modal-disciplina'); document.getElementById('nova-disciplina-nome').value = ''; init();
        }
        async function salvarConfig() { await api('/api/config', 'POST', {groq_key: document.getElementById('config-groq').value}); fecharModal('modal-config'); }
        async function resetarBanco() { if(confirm('Tem certeza? Apagará TUDO!')){ await api('/api/reset_db', 'POST'); fecharModal('modal-config'); init(); } }

        async function gerarQuestoes() {
            const id = document.getElementById('ia-disciplina').value; if(!id) return;
            fecharModal('modal-ia'); showLoading(true);
            await api('/api/gerar', 'POST', {
                disciplina_id: parseInt(id), nivel: document.getElementById('ia-nivel').value, quantidade: parseInt(document.getElementById('ia-qtd').value),
                banca: document.getElementById('ia-banca').value, orgao: document.getElementById('ia-orgao').value, topico: document.getElementById('ia-topico').value, tipo: document.getElementById('ia-tipo').value 
            });
            showLoading(false); carregarMateria(parseInt(id));
        }

        async function gerarSimulado() {
            fecharModal('modal-ia'); showLoading(true);
            const pressaoVal = parseInt(document.getElementById('sim-pressao').value);
            
            await api('/api/gerar_simulado', 'POST', {
                nivel: document.getElementById('sim-nivel').value, quantidade: parseInt(document.getElementById('sim-qtd').value), banca: document.getElementById('sim-banca').value, orgao: document.getElementById('sim-orgao').value, tipo: document.getElementById('sim-tipo').value 
            });
            showLoading(false); 
            
            if(pressaoVal > 0) {
                iniciarModoPressao(pressaoVal * 60);
            } else {
                carregarPainel();
            }
        }

        // --- MODO PRESSÃO ---
        function iniciarModoPressao(segundos) {
            state.modoPressao = true;
            state.respostasPressao = {};
            state.tempoRestante = segundos;
            document.getElementById('barra-pressao').classList.remove('hidden');
            atualizarTimer();
            state.timerInterval = setInterval(() => {
                state.tempoRestante--;
                atualizarTimer();
                if(state.tempoRestante <= 0) finalizarModoPressao();
            }, 1000);
            
            state.disciplinaAtual = null; state.filtroAtual = 'pendentes'; state.isCadernoErros = false;
            atualizarVistaAtual();
        }

        function atualizarTimer() {
            const h = Math.floor(state.tempoRestante / 3600).toString().padStart(2, '0');
            const m = Math.floor((state.tempoRestante % 3600) / 60).toString().padStart(2, '0');
            const s = (state.tempoRestante % 60).toString().padStart(2, '0');
            document.getElementById('timer-display').innerText = `${h}:${m}:${s}`;
        }

        async function finalizarModoPressao() {
            clearInterval(state.timerInterval);
            state.modoPressao = false;
            document.getElementById('barra-pressao').classList.add('hidden');
            
            if(Object.keys(state.respostasPressao).length > 0) {
                showLoading(true);
                await api('/api/responder_lote', 'POST', {respostas: state.respostasPressao});
                showLoading(false);
                alert("Simulado finalizado! Veja seu desempenho no Painel.");
            }
            carregarPainel();
        }

        // --- CADERNO DE ERROS ---
        async function iniciarCadernoDeErros() {
            fecharSidebarMobile();
            state.isCadernoErros = true;
            state.disciplinaAtual = null;
            state.filtroAtual = 'erros';
            state.questoes = await api(`/api/questoes?apenas_erros=true&limit=100`) || [];
            
            const html = `
                <div class="bg-rose-50 dark:bg-rose-900/20 rounded-3xl p-8 mb-8 border border-rose-200 dark:border-rose-800 flex items-center justify-between no-print">
                    <div>
                        <h2 class="text-3xl font-black text-rose-600 dark:text-rose-400 mb-2"><i class="ph-bold ph-book-open"></i> Caderno de Erros</h2>
                        <p class="text-slate-700 dark:text-slate-300 font-medium">Revisão espaçada: O sistema isolou ${state.questoes.length} questões que você errou. Refaça-as para fixar o conhecimento!</p>
                    </div>
                    ${state.questoes.length > 0 ? `<button onclick="limparEIniciarErros()" class="bg-rose-600 hover:bg-rose-700 text-white font-bold px-6 py-4 rounded-xl shadow-lg transition">Limpar e Refazer Tudo</button>` : ''}
                </div>
                <div id="lista-questoes">${renderListaQuestoes()}</div>
            `;
            document.getElementById('conteudo-principal').innerHTML = html;
        }

        async function limparEIniciarErros() {
            if(!confirm("Isso apagará o status de 'Errado' destas questões para você tentar de novo. Confirmar?")) return;
            const ids = state.questoes.map(q => q.id);
            await api('/api/refazer_lote', 'POST', {ids: ids});
            state.filtroAtual = 'pendentes';
            state.questoes = await api(`/api/questoes?limit=100`) || [];
            state.questoes = state.questoes.filter(q => ids.includes(q.id));
            
            const html = `
                <div class="bg-indigo-50 dark:bg-indigo-900/20 rounded-3xl p-8 mb-8 border border-indigo-200 dark:border-indigo-800 no-print">
                    <h2 class="text-2xl font-black text-indigo-600 dark:text-indigo-400 mb-2">Simulado de Correção</h2>
                    <p class="text-slate-700 dark:text-slate-300">As questões foram zeradas. Mostre que você aprendeu!</p>
                </div>
                <div id="lista-questoes">${renderListaQuestoes()}</div>
            `;
            document.getElementById('conteudo-principal').innerHTML = html;
        }

        // --- FUNCIONALIDADES DE QUESTÃO ---
        function lerQuestao(btn, qId) {
            const q = state.questoes.find(x => x.id === qId); if (!q) return;
            window.speechSynthesis.cancel();
            const texto = `Questão. ${q.enunciado}. Alternativas. ${q.alternativas.join('. ')}`;
            const utt = new SpeechSynthesisUtterance(texto); utt.lang = 'pt-BR'; utt.rate = 1.1;
            const icone = btn.querySelector('i'); icone.classList.replace('ph-speaker-high', 'ph-stop'); btn.classList.add('text-indigo-600');
            utt.onend = () => { icone.classList.replace('ph-stop', 'ph-speaker-high'); btn.classList.remove('text-indigo-600'); };
            window.speechSynthesis.speak(utt);
        }

        async function abrirChatDuvida(qId) {
            const chatDiv = document.getElementById(`chat_${qId}`);
            chatDiv.classList.toggle('hidden');
        }

        async function enviarDuvida(qId) {
            const input = document.getElementById(`chat_input_${qId}`);
            const msg = input.value; if(!msg) return;
            const chatHist = document.getElementById(`chat_historico_${qId}`);
            
            chatHist.innerHTML += `<div class="bg-indigo-100 dark:bg-indigo-900/50 text-indigo-900 dark:text-indigo-100 p-3 rounded-lg text-sm mb-2 w-fit ml-auto max-w-[85%]">${msg}</div>`;
            input.value = ''; input.disabled = true;
            chatHist.innerHTML += `<div id="chat_loading_${qId}" class="text-slate-400 text-xs italic mb-2">Professor IA digitando...</div>`;
            
            const res = await api('/api/chat_duvida', 'POST', {questao_id: qId, mensagem: msg});
            document.getElementById(`chat_loading_${qId}`).remove();
            
            if(res && res.resposta) {
                chatHist.innerHTML += `<div class="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 p-3 rounded-lg text-sm mb-2 w-fit mr-auto max-w-[90%] whitespace-pre-wrap"><i class="ph-fill ph-student text-indigo-500 mr-1"></i> ${res.resposta}</div>`;
            }
            input.disabled = false; input.focus();
        }

        function toggleAnotacao(qId) { document.getElementById(`anotacao_${qId}`).classList.toggle('hidden'); }
        async function salvarAnotacao(qId) {
            const txt = document.getElementById(`anotacao_text_${qId}`).value;
            await api('/api/questao/anotacao', 'POST', {questao_id: qId, anotacao: txt});
            alert('Anotação salva!');
        }

        function grifarTexto(qId) {
            const selection = window.getSelection();
            if(selection.rangeCount > 0 && selection.toString().trim().length > 0) {
                const range = selection.getRangeAt(0);
                const mark = document.createElement('mark');
                try {
                    range.surroundContents(mark);
                    const novoHtml = document.getElementById(`enunciado_text_${qId}`).innerHTML;
                    api('/api/questao/html', 'POST', {questao_id: qId, html: novoHtml});
                    const q = state.questoes.find(x => x.id === qId); if(q) q.enunciado_html = novoHtml;
                } catch(e) { alert("Não é possível cruzar o grifo com outros blocos. Tente selecionar um trecho menor."); }
            } else {
                alert("Selecione um pedaço de texto do enunciado primeiro!");
            }
        }

        // --- RENDERIZAÇÃO CENTRAL ---
        async function init() {
            const data = await api('/api/dados');
            if(!data) return;
            state.disciplinas = data.disciplinas; state.stats = data.stats;
            document.getElementById('streak-counter').innerText = `${state.stats.streak} dias`;
            renderMenu(); carregarPainel();
        }

        function renderMenu() {
            const container = document.getElementById('lista-disciplinas-menu');
            container.innerHTML = state.disciplinas.map(d => `
                <button onclick="carregarMateria(${d.id})" class="w-full text-left px-4 py-2.5 rounded-xl font-bold transition flex justify-between items-center group ${state.disciplinaAtual === d.id ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'}">
                    <span class="truncate pr-2">${d.nome}</span>
                    <i class="ph-bold ph-caret-right opacity-0 group-hover:opacity-100 transition-opacity"></i>
                </button>
            `).join('');
        }

        function renderPainelGeral() {
            state.isCadernoErros = false;
            document.getElementById('header-title').innerText = 'Dashboards de Desempenho';
            
            const html = `
                <div class="grid grid-cols-3 gap-3 md:gap-4 mb-6">
                    <div class="bg-white dark:bg-slate-900 p-4 md:p-6 rounded-2xl md:rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col items-center justify-center">
                        <span class="text-slate-400 text-[10px] md:text-xs font-bold uppercase tracking-widest mb-1">Total Resolvidas</span>
                        <span class="text-2xl md:text-4xl font-black text-slate-900 dark:text-white">${state.stats.total}</span>
                    </div>
                    <div class="bg-white dark:bg-slate-900 p-4 md:p-6 rounded-2xl md:rounded-3xl border border-emerald-100 dark:border-emerald-900/50 shadow-sm flex flex-col items-center justify-center">
                        <span class="text-emerald-500 text-[10px] md:text-xs font-bold uppercase tracking-widest mb-1">Acertos</span>
                        <span class="text-2xl md:text-4xl font-black text-emerald-600 dark:text-emerald-400">${state.stats.acertos}</span>
                    </div>
                    <div class="bg-white dark:bg-slate-900 p-4 md:p-6 rounded-2xl md:rounded-3xl border border-rose-100 dark:border-rose-900/50 shadow-sm flex flex-col items-center justify-center">
                        <span class="text-rose-500 text-[10px] md:text-xs font-bold uppercase tracking-widest mb-1">Erros</span>
                        <span class="text-2xl md:text-4xl font-black text-rose-600 dark:text-rose-400">${state.stats.erros}</span>
                    </div>
                </div>
                
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                    <div class="bg-white dark:bg-slate-900 rounded-3xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col">
                        <h4 class="text-slate-800 dark:text-white font-black uppercase tracking-widest text-sm mb-4"><i class="ph-bold ph-trend-up text-indigo-500"></i> Evolução de Estudos (7 dias)</h4>
                        <div class="flex-1 relative min-h-[200px]"><canvas id="chartLine"></canvas></div>
                    </div>

                    <div class="bg-white dark:bg-slate-900 rounded-3xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col items-center">
                        <h4 class="text-slate-800 dark:text-white font-black uppercase tracking-widest text-sm mb-4 self-start"><i class="ph-bold ph-chart-pie-slice text-indigo-500"></i> Balanço Geral</h4>
                        <div class="relative w-48 h-48 mb-2"><canvas id="chartPie"></canvas></div>
                        <div class="text-3xl font-black text-slate-900 dark:text-white">${state.stats.aproveitamento}% <span class="text-sm font-medium text-slate-400">Taxa de Acerto</span></div>
                    </div>
                </div>

                <div class="flex items-center gap-3 mb-6">
                    <i class="ph-fill ph-stack text-2xl text-slate-400"></i>
                    <h3 class="text-xl font-extrabold text-slate-900 dark:text-white">Últimas Questões</h3>
                </div>
                ${renderFiltros()}
                <div id="lista-questoes">${renderListaQuestoes()}</div>
            `;
            document.getElementById('conteudo-principal').innerHTML = html;
            initCharts();
        }

        function initCharts() {
            if(chartEvolucao) chartEvolucao.destroy();
            if(chartPizza) chartPizza.destroy();

            const isDark = document.documentElement.classList.contains('dark');
            const textColor = isDark ? '#94a3b8' : '#64748b';
            const gridColor = isDark ? '#334155' : '#e2e8f0';

            const ctxL = document.getElementById('chartLine').getContext('2d');
            const labels = state.stats.historico.map(d => d.data.substring(5).replace('-','/'));
            const dataAcertos = state.stats.historico.map(d => d.acertos);
            const dataErros = state.stats.historico.map(d => d.erros);
            
            chartEvolucao = new Chart(ctxL, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [
                        { label: 'Acertos', data: dataAcertos, borderColor: '#10b981', backgroundColor: '#10b98120', tension: 0.4, fill: true },
                        { label: 'Erros', data: dataErros, borderColor: '#f43f5e', backgroundColor: 'transparent', tension: 0.4 }
                    ]
                },
                options: {
                    responsive: true, maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: { 
                        y: { beginAtZero: true, grid: { color: gridColor }, ticks: { color: textColor } },
                        x: { grid: { display: false }, ticks: { color: textColor } }
                    }
                }
            });

            const ctxP = document.getElementById('chartPie').getContext('2d');
            chartPizza = new Chart(ctxP, {
                type: 'doughnut',
                data: {
                    labels: ['Acertos', 'Erros'],
                    datasets: [{ data: [state.stats.acertos, state.stats.erros], backgroundColor: ['#10b981', '#f43f5e'], borderWidth: 0, cutout: '75%' }]
                },
                options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
            });
        }

        function renderMateriaInfo() {
            const d = state.disciplinas.find(x => x.id === state.disciplinaAtual);
            document.getElementById('header-title').innerText = d ? d.nome : 'Disciplina';
            
            const html = `
                <div class="relative bg-slate-900 dark:bg-indigo-950 rounded-3xl p-8 mb-8 overflow-hidden shadow-xl shadow-slate-200 dark:shadow-none no-print">
                    <div class="absolute top-0 right-0 p-8 opacity-10 text-white"><i class="ph-fill ph-books text-9xl"></i></div>
                    <div class="relative z-10">
                        <span class="bg-white/20 text-white text-xs font-bold px-3 py-1 rounded-full uppercase tracking-widest backdrop-blur-md border border-white/20 mb-4 inline-block">Caderno de Estudos</span>
                        <h2 class="text-3xl md:text-4xl font-black text-white mb-2 leading-tight">${d ? d.nome : ''}</h2>
                    </div>
                </div>
                ${renderFiltros()}
                <div id="lista-questoes">${renderListaQuestoes()}</div>
            `;
            document.getElementById('conteudo-principal').innerHTML = html;
        }

        function renderFiltros() {
            const f = state.filtroAtual;
            const btnClass = "px-4 py-2.5 rounded-xl font-bold text-sm transition shrink-0 ";
            const ativo = btnClass + "bg-slate-900 dark:bg-indigo-600 text-white shadow-md";
            const inativo = btnClass + "bg-white dark:bg-slate-900 text-slate-500 dark:text-slate-400 border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800";
            return `
                <div class="flex gap-2 overflow-x-auto pb-4 no-scrollbar mb-4 no-print">
                    <button onclick="setFiltro('todas')" class="${f==='todas'?ativo:inativo}">Todas</button>
                    <button onclick="setFiltro('pendentes')" class="${f==='pendentes'?ativo:inativo} flex gap-1.5 items-center"><i class="ph-bold ph-circle-dashed"></i> Pendentes</button>
                    <button onclick="setFiltro('erros')" class="${f==='erros'?ativo:inativo} flex gap-1.5 items-center text-rose-500"><i class="ph-bold ph-x"></i> Errei</button>
                    <button onclick="setFiltro('acertos')" class="${f==='acertos'?ativo:inativo} flex gap-1.5 items-center text-emerald-500"><i class="ph-bold ph-check"></i> Acertei</button>
                </div>
            `;
        }

        function renderListaQuestoes() {
            if(state.questoes.length === 0) return `<div class="text-center py-12 bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 border-dashed"><i class="ph-fill ph-empty text-5xl text-slate-300 dark:text-slate-700 mb-3"></i><p class="text-slate-500 dark:text-slate-400 font-bold">Nenhuma questão encontrada.</p></div>`;
            
            return state.questoes.map(q => {
                const nomeBanca = q.banca ? q.banca : 'Inédita';
                const anoQuestao = q.ano ? q.ano : new Date().getFullYear();
                const nomeConcurso = q.concurso ? q.concurso : 'Simulado';
                
                const respondidaNaPressao = state.modoPressao && state.respostasPressao[q.id];
                const exibirFeedback = q.respondida && !state.modoPressao;
                
                const textoEnunciado = (q.enunciado_html && q.enunciado_html.trim() !== '') ? q.enunciado_html : q.enunciado;

                return `
                <div class="bg-white dark:bg-slate-900 rounded-2xl md:rounded-3xl shadow-sm border border-slate-200 dark:border-slate-800 overflow-hidden mb-6 transition-all" id="card_questao_${q.id}">
                    <div class="p-5 md:p-8 relative">
                        <div class="flex justify-between items-start gap-4 mb-6 z-10 relative">
                            <div class="flex flex-col gap-2 flex-1 min-w-0">
                                <div class="flex flex-wrap gap-2">
                                    <span class="bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-400 text-[10px] md:text-xs font-bold px-3 py-1.5 rounded-lg uppercase tracking-wider border border-indigo-100 dark:border-indigo-800">${q.disciplina}</span>
                                    ${q.topico_especifico ? `<span class="bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 text-[10px] md:text-xs font-bold px-3 py-1.5 rounded-lg uppercase tracking-wider border border-emerald-100 dark:border-emerald-800"><i class="ph-bold ph-target"></i> ${q.topico_especifico}</span>` : ''}
                                </div>
                                <span class="bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 text-[10px] md:text-xs font-bold px-3 py-1.5 rounded-lg uppercase tracking-wider border border-slate-200 dark:border-slate-700 flex items-center gap-1.5 w-fit"><i class="ph-fill ph-bank"></i> ${nomeBanca} - ${nomeConcurso} (${anoQuestao})</span>
                            </div>

                            <div class="flex gap-1.5 shrink-0 no-print">
                                <button onclick="grifarTexto(${q.id})" class="text-slate-400 hover:text-yellow-500 bg-slate-50 dark:bg-slate-800 hover:bg-yellow-50 dark:hover:bg-yellow-900/20 rounded-lg p-2 transition" title="Selecione um texto e clique para grifar">
                                    <i class="ph-bold ph-highlighter text-xl"></i>
                                </button>
                                <button onclick="toggleAnotacao(${q.id})" class="text-slate-400 hover:text-indigo-500 bg-slate-50 dark:bg-slate-800 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 rounded-lg p-2 transition" title="Anotações">
                                    <i class="ph-bold ph-note-pencil text-xl"></i>
                                </button>
                                <button onclick="lerQuestao(this, ${q.id})" class="text-slate-400 hover:text-indigo-500 bg-slate-50 dark:bg-slate-800 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 rounded-lg p-2 transition" title="Ouvir">
                                    <i class="ph-bold ph-speaker-high text-xl"></i>
                                </button>
                            </div>
                        </div>

                        <p id="enunciado_text_${q.id}" class="text-slate-900 dark:text-slate-100 font-medium leading-relaxed mb-6 text-sm md:text-base whitespace-pre-wrap">${textoEnunciado}</p>
                        
                        <div class="space-y-3 mb-6" id="alts_${q.id}">
                            ${q.alternativas.map(alt => {
                                const letra = alt.charAt(0);
                                let btnClass = "w-full text-left p-4 md:p-5 rounded-xl border border-slate-200 dark:border-slate-700 transition flex items-start gap-3 bg-white dark:bg-slate-900 hover:border-indigo-400 cursor-pointer text-slate-700 dark:text-slate-300 text-sm md:text-base font-medium";
                                let checkClass = "w-5 h-5 md:w-6 md:h-6 rounded-full border-2 border-slate-300 dark:border-slate-600 shrink-0 mt-0.5 transition";
                                
                                if(exibirFeedback) {
                                    btnClass += " opacity-70 cursor-default pointer-events-none";
                                    if(letra === q.gabarito) {
                                        btnClass = "w-full text-left p-4 md:p-5 rounded-xl border flex items-start gap-3 text-sm md:text-base font-medium bg-emerald-50 dark:bg-emerald-900/20 border-emerald-500 text-emerald-900 dark:text-emerald-100 opacity-100";
                                        checkClass = "w-5 h-5 md:w-6 md:h-6 rounded-full border-2 border-emerald-500 bg-emerald-500 shrink-0 mt-0.5 flex items-center justify-center text-white before:content-['✓'] before:text-xs md:before:text-sm";
                                    } else if (!q.acertou && letra === q.resposta_usuario) {
                                        btnClass = "w-full text-left p-4 md:p-5 rounded-xl border flex items-start gap-3 text-sm md:text-base font-medium bg-rose-50 dark:bg-rose-900/20 border-rose-500 text-rose-900 dark:text-rose-100 opacity-100";
                                        checkClass = "w-5 h-5 md:w-6 md:h-6 rounded-full border-2 border-rose-500 bg-rose-500 shrink-0 mt-0.5 flex items-center justify-center text-white before:content-['✕'] before:text-xs md:before:text-sm";
                                    }
                                } else if (state.modoPressao && state.respostasPressao[q.id] === letra) {
                                    btnClass = "w-full text-left p-4 md:p-5 rounded-xl border flex items-start gap-3 text-sm md:text-base font-bold bg-indigo-50 dark:bg-indigo-900/30 border-indigo-500 text-indigo-900 dark:text-indigo-100 shadow-sm";
                                    checkClass = "w-5 h-5 md:w-6 md:h-6 rounded-full border-4 border-indigo-600 dark:border-indigo-400 bg-white dark:bg-slate-900 shrink-0 mt-0.5";
                                }
                                
                                return `<button onclick="selecionarAlt(${q.id}, '${letra}')" id="btn_${q.id}_${letra}" class="${btnClass}"><div id="check_${q.id}_${letra}" class="${checkClass}"></div><span class="flex-1">${alt}</span></button>`;
                            }).join('')}
                        </div>

                        <div id="anotacao_${q.id}" class="hidden anotacao-container mb-6 bg-yellow-50 dark:bg-slate-800 p-4 rounded-xl border border-yellow-200 dark:border-slate-700 no-print">
                            <label class="text-xs font-bold uppercase text-yellow-600 dark:text-slate-400 mb-2 flex items-center gap-1"><i class="ph-fill ph-note-pencil"></i> Meu Bloco de Notas</label>
                            <textarea id="anotacao_text_${q.id}" class="w-full bg-transparent outline-none text-slate-800 dark:text-slate-200 text-sm resize-y min-h-[80px]" placeholder="Escreva seu mnemônico ou resumo aqui...">${q.anotacao || ''}</textarea>
                            <div class="flex justify-end mt-2"><button onclick="salvarAnotacao(${q.id})" class="text-xs bg-yellow-200 dark:bg-slate-700 text-yellow-800 dark:text-slate-300 font-bold px-3 py-1.5 rounded hover:bg-yellow-300 transition">Salvar Anotação</button></div>
                        </div>

                        ${(!q.respondida && !state.modoPressao) ? 
                            `<button onclick="responder(${q.id})" class="w-full py-4 bg-indigo-600 hover:bg-indigo-700 active:scale-[0.98] transition-all text-white font-bold rounded-xl shadow-md text-sm md:text-base flex items-center justify-center gap-2 no-print">
                                <i class="ph-bold ph-check-circle text-xl"></i> Confirmar Resposta
                            </button>` 
                            : ''
                        }
                        
                        ${exibirFeedback ? 
                            `<div class="bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 md:p-6 shadow-sm no-print mt-4">
                                <div class="flex items-center gap-2 mb-3">
                                    ${q.acertou 
                                        ? `<i class="ph-fill ph-check-circle text-emerald-500 text-xl"></i> <span class="font-black text-emerald-600 dark:text-emerald-400">Você Acertou!</span>` 
                                        : `<i class="ph-fill ph-x-circle text-rose-500 text-xl"></i> <span class="font-black text-rose-600 dark:text-rose-400">Você Errou. O correto era a letra ${q.gabarito}</span>`}
                                </div>
                                <div class="text-sm text-slate-700 dark:text-slate-300 leading-relaxed mb-4"><strong>Explicação:</strong> ${q.explicacao}</div>
                                
                                <div class="flex flex-wrap gap-2">
                                    <button onclick="abrirChatDuvida(${q.id})" class="text-xs font-bold text-indigo-700 dark:text-indigo-400 bg-indigo-100 dark:bg-indigo-900/40 px-4 py-2.5 rounded-xl hover:bg-indigo-200 transition flex items-center gap-1"><i class="ph-fill ph-chat-teardrop-text"></i> Dúvida c/ IA</button>
                                    <a href="${q.video_url}" target="_blank" class="text-xs font-bold text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 border border-red-100 dark:border-red-900/30 px-4 py-2.5 rounded-xl hover:bg-red-100 transition flex items-center gap-1"><i class="ph-fill ph-youtube-logo text-lg"></i> Videoaula</a>
                                </div>

                                <div id="chat_${q.id}" class="hidden chat-container mt-4 border-t border-slate-200 dark:border-slate-800 pt-4">
                                    <div id="chat_historico_${q.id}" class="mb-3 max-h-60 overflow-y-auto pr-2">
                                        <div class="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 p-3 rounded-lg text-sm mb-2 w-fit max-w-[90%]"><i class="ph-fill ph-student text-indigo-500 mr-1"></i> Olá! Ficou com dúvida na explicação acima? Me pergunte!</div>
                                    </div>
                                    <div class="flex gap-2">
                                        <input type="text" id="chat_input_${q.id}" placeholder="Ex: Por que não é peculato?" class="flex-1 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-2 text-sm outline-none focus:border-indigo-500">
                                        <button onclick="enviarDuvida(${q.id})" class="bg-indigo-600 text-white p-2 rounded-xl hover:bg-indigo-700"><i class="ph-bold ph-paper-plane-right"></i></button>
                                    </div>
                                </div>
                            </div>` : ''
                        }
                    </div>
                </div>`;
            }).join('') + `<div class="text-center py-6 text-slate-400 font-bold text-sm no-print">Fim da lista</div>`;
        }

        window.respostasTmp = {};
        function selecionarAlt(qId, letra) {
            if(state.modoPressao) {
                state.respostasPressao[qId] = letra;
                atualizarVistaAtual(); 
                return;
            }
            
            window.respostasTmp[qId] = letra;
            const alts = ['A','B','C','D','E'];
            alts.forEach(l => {
                const btn = document.getElementById(`btn_${qId}_${l}`); const chk = document.getElementById(`check_${qId}_${l}`);
                if(btn && chk) {
                    if(l === letra) {
                        btn.className = "w-full text-left p-4 md:p-5 rounded-xl border border-indigo-500 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-900 dark:text-indigo-100 transition flex items-start gap-3 text-sm md:text-base font-bold shadow-sm";
                        chk.className = "w-5 h-5 md:w-6 md:h-6 rounded-full border-4 border-indigo-600 dark:border-indigo-400 bg-white dark:bg-slate-900 shrink-0 mt-0.5 transition";
                    } else {
                        btn.className = "w-full text-left p-4 md:p-5 rounded-xl border border-slate-200 dark:border-slate-700 transition flex items-start gap-3 bg-white dark:bg-slate-900 hover:border-indigo-400 text-slate-700 dark:text-slate-300 text-sm md:text-base font-medium";
                        chk.className = "w-5 h-5 md:w-6 md:h-6 rounded-full border-2 border-slate-300 dark:border-slate-600 shrink-0 mt-0.5 transition";
                    }
                }
            });
        }

        async function responder(qId) {
            const resp = window.respostasTmp[qId]; if(!resp) { alert('Selecione uma alternativa.'); return; }
            await api('/api/responder', 'POST', {questao_id: qId, resposta: resp});
            atualizarVistaAtual();
        }

        async function carregarPainel() {
            state.disciplinaAtual = null; state.isCadernoErros = false;
            renderMenu(); fecharSidebarMobile();
            let query = `/api/questoes?limit=50`;
            if(state.filtroAtual === 'pendentes') query += `&apenas_pendentes=true`;
            if(state.filtroAtual === 'erros') query += `&apenas_erros=true`;
            if(state.filtroAtual === 'acertos') query += `&apenas_acertos=true`;
            state.questoes = await api(query) || [];
            const data = await api('/api/dados'); if(data) state.stats = data.stats;
            renderPainelGeral();
        }

        async function carregarMateria(id) {
            state.disciplinaAtual = id; state.isCadernoErros = false;
            renderMenu(); fecharSidebarMobile();
            let query = `/api/questoes?disciplina_id=${id}&limit=50`;
            if(state.filtroAtual === 'pendentes') query += `&apenas_pendentes=true`;
            if(state.filtroAtual === 'erros') query += `&apenas_erros=true`;
            if(state.filtroAtual === 'acertos') query += `&apenas_acertos=true`;
            state.questoes = await api(query) || [];
            renderMateriaInfo();
        }

        function setFiltro(f) {
            state.filtroAtual = f;
            if(state.isCadernoErros) iniciarCadernoDeErros(); 
            else atualizarVistaAtual();
        }

        function atualizarVistaAtual() {
            if(state.isCadernoErros) {
                document.getElementById('lista-questoes').innerHTML = renderListaQuestoes();
            }
            else if(state.modoPressao) {
                if(state.disciplinaAtual) {
                    const html = `<div class="bg-rose-50 dark:bg-rose-900/20 p-6 rounded-2xl mb-6"><h2 class="text-2xl font-black text-rose-600">Simulado em Andamento...</h2></div> <div id="lista-questoes">${renderListaQuestoes()}</div>`;
                    document.getElementById('conteudo-principal').innerHTML = html;
                } else {
                    const html = `<div class="bg-rose-50 dark:bg-rose-900/20 p-6 rounded-2xl mb-6"><h2 class="text-2xl font-black text-rose-600">Simulado Geral em Andamento...</h2></div> <div id="lista-questoes">${renderListaQuestoes()}</div>`;
                    document.getElementById('conteudo-principal').innerHTML = html;
                }
            }
            else if(state.disciplinaAtual) carregarMateria(state.disciplinaAtual);
            else carregarPainel();
        }

        init();
    </script>
</body>
</html>

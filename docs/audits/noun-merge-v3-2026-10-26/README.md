# noun-merge/v3: what newly shares a card (measured, not staged)

Rule: a feminine form is an inflection like a plural; only the noun's own entries are compared (a participle's verb on the menu no longer blocks it); a noun and an adjective of the same headword are one word; a feminine form whose senses differ is refused alone. Other words on a form are left to decision 0033's 3-example, 10% bar.

Reproduce: `PYTHONPATH=src python3 recompute.py <dir>` then `node measure_noun.cjs <language> <dir>/<language>-nounv3.json`.

## Portuguese: 1073 forms join 813 cards; 0 split

| Card | Newly joined | Card now holds | Was blocked by |
|---|---|---|---|
| coisa | coisa, coisas | coisa / coisas | ambiguous_headwords |
| casa | casa, casas | casa / casas | ambiguous_headwords |
| vez | vez | vez | ambiguous_headwords |
| vida | vida, vidas | vida / vidas | ambiguous_headwords |
| mãe | mãe, mães | mãe / mães | ambiguous_headwords |
| trabalho | trabalho, trabalhos | trabalho / trabalhos | ambiguous_headwords |
| parte | parte | parte | ambiguous_headwords |
| carro | carro, carros | carro / carros | ambiguous_headwords |
| querido | querida, querido | querida / querido / queridos | ambiguous_headwords, not_a_plural_relationship |
| forma | forma, formas | forma / formas | ambiguous_headwords |
| minuto | minutos, minuto | minutos / minuto | ambiguous_headwords |
| maneira | maneira, maneiras | maneira / maneiras | ambiguous_headwords |
| arma | arma, armas | arma / armas | ambiguous_headwords |
| conta | conta, contas | conta / contas | ambiguous_headwords |
| porta | porta | porta | ambiguous_headwords |
| caminho | caminho, caminhos | caminho / caminhos | ambiguous_headwords |
| quarto | quarto | quarto | ambiguous_headwords |
| causa | causa, causas | causa / causas | ambiguous_headwords |
| pessoal | pessoal | pessoal / pessoais | multiple_dictionary_entries |
| olho | olhos | olhos | ambiguous_headwords |
| jogo | jogo, jogos | jogo / jogos | ambiguous_headwords |
| número | número, números | número / números | ambiguous_headwords |
| idiota | idiota, idiotas | idiota / idiotas | multiple_dictionary_entries |
| suficiente | suficiente | suficiente / suficientes | multiple_dictionary_entries |
| festa | festa, festas | festa / festas | ambiguous_headwords |
| culpa | culpa | culpa | ambiguous_headwords |
| comida | comida, comidas | comida / comidas | ambiguous_headwords |
| pergunta | pergunta, perguntas | pergunta / perguntas | ambiguous_headwords |
| falta | falta | falta | ambiguous_headwords |
| esposa | esposa, esposas | esposa / esposas | ambiguous_headwords |
| telefone | telefone, telefones | telefone / telefones | ambiguous_headwords |
| equipa | equipa, equipas | equipa / equipas | ambiguous_headwords |
| raio | raio, raios | raio / raios | ambiguous_headwords |
| solo | solo, solos | solo / solos | ambiguous_headwords |
| plano | plano, planos | plano / planos | ambiguous_headwords |
| resto | resto, restos | resto / restos | ambiguous_headwords |
| puta | puta | puta | ambiguous_headwords |
| sexo | sexo | sexo | ambiguous_headwords |
| música | música, músicas | música / músicas | ambiguous_headwords |
| livro | livro, livros | livro / livros | ambiguous_headwords |
| sentido | sentido, sentidos | sentido / sentidos | ambiguous_headwords |
| ar | ar, ares | ar / ares | ambiguous_headwords |
| filme | filme, filmes | filme / filmes | ambiguous_headwords |
| final | final, finais | final / finais | ambiguous_headwords |
| local | local, locais | local / locais | ambiguous_headwords |
| rei | rei | rei | ambiguous_headwords |
| campo | campo | campo | ambiguous_headwords |
| futuro | futuro | futuro / futura / futuros / futuras | ambiguous_headwords |
| lista | lista, listas | lista / listas | ambiguous_headwords |
| vista | vista | vista | ambiguous_headwords |
| assassino | assassino, assassinos, assassina | assassino / assassinos / assassina | ambiguous_headwords, not_a_plural_relationship |
| respeito | respeito | respeito | ambiguous_headwords |
| mente | mente | mente | ambiguous_headwords |
| ataque | ataque, ataques | ataque / ataques | ambiguous_headwords |
| programa | programa, programas | programa / programas | ambiguous_headwords |
| chão | chão | chão | multiple_dictionary_entries |
| uno | uno | uno | ambiguous_headwords |
| banco | banco, bancos | banco / bancos | ambiguous_headwords |
| avião | avião, aviões | avião / aviões | ambiguous_headwords |
| banho | banho | banho | ambiguous_headwords |
| emprego | emprego, empregos | emprego / empregos | ambiguous_headwords |
| carta | carta, cartas | carta / cartas | ambiguous_headwords |
| presente | presente, presentes | presente / presentes | multiple_dictionary_entries |
| bocado | bocado, bocados | bocado / bocados | ambiguous_headwords |
| governo | governo, governos | governo / governos | ambiguous_headwords |
| centro | centro, centros | centro / centros | ambiguous_headwords |
| espaço | espaço, espaços | espaço / espaços | ambiguous_headwords |
| sonho | sonho, sonhos | sonho / sonhos | ambiguous_headwords |
| escolha | escolha | escolha | ambiguous_headwords |
| erro | erro, erros | erro / erros | ambiguous_headwords |
| advogado | advogado, advogados, advogada | advogado / advogados / advogada | ambiguous_headwords, not_a_plural_relationship |
| par | par | par | ambiguous_headwords |
| prova | provas | provas | ambiguous_headwords |
| bebida | bebida, bebidas | bebida / bebidas | ambiguous_headwords |
| chave | chave | chave | ambiguous_headwords |
| céu | céu | céu | ambiguous_headwords |
| vestido | vestido, vestidos | vestido / vestidos / vestida | ambiguous_headwords |
| destino | destino | destino | ambiguous_headwords |
| humano | humano, humanos | humano / humanos / humana / humanas | ambiguous_headwords |
| esquerda | esquerda | esquerda | ambiguous_headwords |
| oficial | oficial, oficiais | oficial / oficiais | ambiguous_headwords |
| namorada | namorada, namoradas | namorada / namoradas | ambiguous_headwords |
| bomba | bomba, bombas | bomba / bombas | ambiguous_headwords |
| direita | direita | direita | ambiguous_headwords |
| papai | papai | papai | ambiguous_headwords |
| mar | mar, mares | mar / mares | ambiguous_headwords |
| motivo | motivo, motivos | motivo / motivos | ambiguous_headwords |
| saída | saída, saídas | saída / saídas | ambiguous_headwords |
| perigo | perigo, perigos | perigo / perigos | ambiguous_headwords |
| namorado | namorado | namorado | ambiguous_headwords |
| teste | teste, testes | teste / testes | ambiguous_headwords |
| animal | animais, animal | animais / animal | ambiguous_headwords |
| aniversário | aniversário | aniversário | multiple_dictionary_entries |
| entrada | entrada, entradas | entrada / entradas | ambiguous_headwords |
| honra | honra | honra | ambiguous_headwords |
| comando | comando, comandos | comando / comandos | ambiguous_headwords |
| piada | piada, piadas | piada / piadas | ambiguous_headwords |
| mestre | mestre, mestres | mestre / mestres | ambiguous_headwords |
| contacto | contacto, contactos | contacto / contactos | ambiguous_headwords |
| diferença | diferença, diferenças | diferença / diferenças | ambiguous_headwords |
| zona | zona | zona | ambiguous_headwords |
| janela | janela, janelas | janela / janelas | ambiguous_headwords |
| saco | saco, sacos | saco / sacos | ambiguous_headwords |
| controlo | controlo | controlo | ambiguous_headwords |
| paciente | paciente, pacientes | paciente / pacientes | multiple_dictionary_entries |
| avó | avó | avó | ambiguous_headwords |
| pele | pele | pele | ambiguous_headwords |
| bala | bala, balas | bala / balas | ambiguous_headwords |
| risco | risco, riscos | risco / riscos | ambiguous_headwords |
| lixo | lixo | lixo | ambiguous_headwords |
| busca | busca | busca | ambiguous_headwords |
| buraco | buraco, buracos | buraco / buracos | ambiguous_headwords |
| almoço | almoço | almoço | ambiguous_headwords |
| corte | corte | corte | ambiguous_headwords |
| visita | visita | visita | ambiguous_headwords |
| gelo | gelo | gelo | ambiguous_headwords |
| cozinha | cozinha | cozinha | ambiguous_headwords |
| soldado | soldado, soldados | soldado / soldados | ambiguous_headwords |
| major | major | major | multiple_dictionary_entries |
| equipe | equipe, equipes | equipe / equipes | ambiguous_headwords |
| cheiro | cheiro | cheiro | ambiguous_headwords |
| acesso | acesso | acesso | ambiguous_headwords |
| bordo | bordo | bordo | ambiguous_headwords |
| flor | flores, flor | flores / flor | ambiguous_headwords |
| parede | parede, paredes | parede / paredes | ambiguous_headwords |
| dente | dentes, dente | dentes / dente | ambiguous_headwords |
| tamanho | tamanho | tamanho | multiple_dictionary_entries |
| valor | valor, valores | valor / valores | ambiguous_headwords |
| inglês | inglês, ingleses | inglês / ingleses | ambiguous_headwords |
| queda | queda, quedas | queda / quedas | ambiguous_headwords |
| processo | processo, processos | processo / processos | ambiguous_headwords |
| data | data, datas | data / datas | ambiguous_headwords |
| cor | cor | cor | ambiguous_headwords |
| calor | calor | calor | multiple_dictionary_entries |
| americano | americanos | americano / americanos / americana / americanas | multiple_dictionary_entries |
| peixe | peixe, peixes | peixe / peixes | ambiguous_headwords |
| saudade | saudades, saudade | saudades / saudade | ambiguous_headwords |
| baile | baile | baile | ambiguous_headwords |
| apoio | apoio | apoio | ambiguous_headwords |
| jovem | jovens | jovem / jovens | multiple_dictionary_entries |
| dança | dança | dança | ambiguous_headwords |
| interior | interior | interior | multiple_dictionary_entries |
| cadeia | cadeia | cadeia | ambiguous_headwords |
| director | director, directora | director / directora | multiple_dictionary_entries, not_a_plural_relationship |
| juiz | juiz, juízes, juíza | juiz / juízes / juíza | ambiguous_headwords, not_a_plural_relationship |
| movimento | movimento, movimentos | movimento / movimentos | ambiguous_headwords |
| comboio | comboio, comboios | comboio / comboios | ambiguous_headwords |
| aula | aula, aulas | aula / aulas | ambiguous_headwords |
| mercado | mercado | mercado | ambiguous_headwords |
| material | material, materiais | material / materiais | multiple_dictionary_entries |
| resultado | resultado, resultados | resultado / resultados | ambiguous_headwords |
| corrida | corrida, corridas | corrida / corridas | ambiguous_headwords |
| beijo | beijo, beijos | beijo / beijos | ambiguous_headwords |
| milhão | milhão | milhão | ambiguous_headwords |
| testemunha | testemunha, testemunhas | testemunha / testemunhas | ambiguous_headwords |
| nota | nota, notas | nota / notas | ambiguous_headwords |
| floresta | floresta, florestas | floresta / florestas | ambiguous_headwords |
| vento | vento, ventos | vento / ventos | ambiguous_headwords |
| noiva | noiva | noiva | ambiguous_headwords |
| rato | rato, ratos, ratas | rato / ratos / ratas | ambiguous_headwords |
| notícia | notícia | notícia | ambiguous_headwords |
| curso | curso | curso | ambiguous_headwords |
| porco | porco, porcos | porco / porcos | multiple_dictionary_entries |
| contrato | contrato, contratos | contrato / contratos | ambiguous_headwords |
| voo | voo | voo | ambiguous_headwords |
| peito | peito, peitos | peito / peitos | ambiguous_headwords |
| corredor | corredor, corredores | corredor / corredores | multiple_dictionary_entries |
| policial | policial | policial / policiais | multiple_dictionary_entries |
| crédito | crédito | crédito | ambiguous_headwords |
| assistente | assistente | assistente | multiple_dictionary_entries |
| primo | primo, primos | primo / primos | ambiguous_headwords |
| imprensa | imprensa | imprensa | ambiguous_headwords |
| ouvido | ouvidos | ouvidos | ambiguous_headwords |
| olhada | olhada | olhada | ambiguous_headwords |
| patrão | patrão | patrão | ambiguous_headwords |
| rede | rede, redes | rede / redes | ambiguous_headwords |
| companheiro | companheiro, companheiros | companheiro / companheiros | ambiguous_headwords |
| pesquisa | pesquisa | pesquisa | ambiguous_headwords |
| piloto | piloto, pilotos | piloto / pilotos | ambiguous_headwords |
| cheque | cheque | cheque | ambiguous_headwords |
| direito | direitos | direito / direitos | multiple_dictionary_entries |
| detalhe | detalhes, detalhe | detalhes / detalhe | ambiguous_headwords |
| funeral | funeral | funeral | multiple_dictionary_entries |
| original | original, originais | original / originais | ambiguous_headwords |
| revista | revista, revistas | revista / revistas | ambiguous_headwords |
| disco | disco, discos | disco / discos | ambiguous_headwords |
| motor | motor, motores | motor / motores | multiple_dictionary_entries |
| neve | neve | neve | ambiguous_headwords |
| torre | torre | torre | ambiguous_headwords |
| obra | obra, obras | obra / obras | ambiguous_headwords |
| venda | venda, vendas | venda / vendas | ambiguous_headwords |
| entrevista | entrevista, entrevistas | entrevista / entrevistas | ambiguous_headwords |
| reino | reino | reino | ambiguous_headwords |
| transporte | transporte, transportes | transporte / transportes | ambiguous_headwords |
| discurso | discurso, discursos | discurso / discursos | ambiguous_headwords |
| tentativa | tentativa, tentativas | tentativa / tentativas | ambiguous_headwords |
| treino | treino, treinos | treino / treinos | ambiguous_headwords |
| choque | choque | choque | ambiguous_headwords |
| topo | topo | topo | ambiguous_headwords |
| fita | fita, fitas | fita / fitas | ambiguous_headwords |
| deserto | deserto | deserto | ambiguous_headwords |
| passeio | passeio | passeio | ambiguous_headwords |
| fila | fila, filas | fila / filas | ambiguous_headwords |
| anjo | anjo, anjos | anjo / anjos | ambiguous_headwords |
| casal | casal, casais | casal / casais | ambiguous_headwords |
| boleia | boleia | boleia | ambiguous_headwords |
| quadro | quadro, quadros | quadro / quadros | ambiguous_headwords |
| truque | truque, truques | truque / truques | ambiguous_headwords |
| projecto | projecto, projectos | projecto / projectos | ambiguous_headwords |
| treta | treta | treta | ambiguous_headwords |
| dano | danos, dano | danos / dano | ambiguous_headwords |
| francês | francês, franceses | francês / franceses / francesa | multiple_dictionary_entries |
| documento | documentos, documento | documentos / documento | ambiguous_headwords |
| pânico | pânico | pânico | multiple_dictionary_entries |
| alcance | alcance | alcance | ambiguous_headwords |
| chamada | chamadas | chamadas | ambiguous_headwords |
| regra | regra | regra | ambiguous_headwords |
| sola | sola, solas | sola / solas | ambiguous_headwords |
| diário | diário, diários | diário / diários | multiple_dictionary_entries |
| peça | peças | peças | ambiguous_headwords |
| aposta | aposta, apostas | aposta / apostas | ambiguous_headwords |
| amante | amante, amantes | amante / amantes | ambiguous_headwords |
| tesouro | tesouro, tesouros | tesouro / tesouros | ambiguous_headwords |
| desafio | desafio, desafios | desafio / desafios | ambiguous_headwords |
| vaca | vaca, vacas | vaca / vacas | ambiguous_headwords |
| traseiro | traseiro | traseiro | multiple_dictionary_entries |
| telhado | telhado | telhado | ambiguous_headwords |
| ambiente | ambiente | ambiente | ambiguous_headwords |
| milagre | milagre, milagres | milagre / milagres | ambiguous_headwords |
| pulso | pulso, pulsos | pulso / pulsos | ambiguous_headwords |
| macaco | macaco, macacos | macaco / macacos | ambiguous_headwords |
| professor | professora | professor / professora / professores | not_a_plural_relationship |
| estranho | estranhos | estranho / estranha / estranhos / estranhas | ambiguous_headwords |
| sede | sede | sede | ambiguous_headwords |
| registo | registos, registo | registos / registo | ambiguous_headwords |
| papa | papa, papas | papa / papas | ambiguous_headwords |
| vidro | vidro, vidros | vidro / vidros | ambiguous_headwords |
| alarme | alarme, alarmes | alarme / alarmes | ambiguous_headwords |
| morada | morada | morada | ambiguous_headwords |
| terrorista | terroristas, terrorista | terroristas / terrorista | multiple_dictionary_entries |
| tema | tema | tema | ambiguous_headwords |
| celular | celular, celulares | celular / celulares | multiple_dictionary_entries |
| espelho | espelho, espelhos | espelho / espelhos | ambiguous_headwords |
| proposta | proposta | proposta | ambiguous_headwords |
| terreno | terreno | terreno | multiple_dictionary_entries |
| marinha | marinha | marinha | ambiguous_headwords |
| alternativa | alternativa | alternativa | ambiguous_headwords |
| dispositivo | dispositivo, dispositivos | dispositivo / dispositivos | multiple_dictionary_entries |
| mina | mina, minas | mina / minas | ambiguous_headwords |
| esquina | esquina | esquina | ambiguous_headwords |
| gelado | gelado, gelados | gelado / gelada / gelados | ambiguous_headwords |
| atirador | atirador, atiradores | atirador / atiradores | multiple_dictionary_entries |
| piso | piso | piso | ambiguous_headwords |
| vizinho | vizinhos, vizinho, vizinha | vizinhos / vizinho / vizinha | multiple_dictionary_entries, not_a_plural_relationship |
| amostra | amostra, amostras | amostra / amostras | ambiguous_headwords |
| alemão | alemães, alemão | alemães / alemão / alemã | multiple_dictionary_entries |
| endereço | endereço | endereço | ambiguous_headwords |
| dama | dama | dama | ambiguous_headwords |
| limite | limite, limites | limite / limites | ambiguous_headwords |
| areia | areia | areia | ambiguous_headwords |
| aluno | alunos, aluno | alunos / aluno | ambiguous_headwords |
| ferro | ferro | ferro | ambiguous_headwords |
| inverno | inverno | inverno | ambiguous_headwords |
| castigo | castigo | castigo | ambiguous_headwords |
| doce | doces | doce / doces | ambiguous_headwords |
| milha | milhas, milha | milhas / milha | ambiguous_headwords |
| medida | medida, medidas | medida / medidas | ambiguous_headwords |
| noivo | noivo, noivos | noivo / noivos | ambiguous_headwords |
| passo | passos | passos | ambiguous_headwords |
| russo | russo, russos | russo / russos / russa | multiple_dictionary_entries |
| gerente | gerente | gerente | multiple_dictionary_entries |
| doutor | doutora | doutor / doutora | not_a_plural_relationship |
| esforço | esforço, esforços | esforço / esforços | ambiguous_headwords |
| resgate | resgate | resgate | ambiguous_headwords |
| abrigo | abrigo | abrigo | ambiguous_headwords |
| maricas | maricas | maricas | multiple_dictionary_entries |
| significado | significado | significado | ambiguous_headwords |
| aliança | aliança | aliança | ambiguous_headwords |
| recompensa | recompensa, recompensas | recompensa / recompensas | ambiguous_headwords |
| exterior | exterior | exterior | multiple_dictionary_entries |
| pássaro | pássaro, pássaros | pássaro / pássaros | ambiguous_headwords |
| tolo | tolo, tolos | tolo / tola / tolos | multiple_dictionary_entries |
| uniforme | uniforme, uniformes | uniforme / uniformes | multiple_dictionary_entries |
| ministro | ministro | ministro | ambiguous_headwords |
| atraso | atraso | atraso | ambiguous_headwords |
| bastardo | bastardo, bastardos | bastardo / bastardos | multiple_dictionary_entries |
| bota | botas, bota | botas / bota | ambiguous_headwords |
| incidente | incidente, incidentes | incidente / incidentes | multiple_dictionary_entries |
| vampiro | vampiros, vampiro | vampiros / vampiro | ambiguous_headwords |
| tanque | tanque, tanques | tanque / tanques | ambiguous_headwords |
| rota | rota | rota | ambiguous_headwords |
| romance | romance, romances | romance / romances | multiple_dictionary_entries |
| tinta | tinta, tintas | tinta / tintas | ambiguous_headwords |
| lata | lata, latas | lata / latas | ambiguous_headwords |
| empregado | empregado, empregados | empregado / empregados | ambiguous_headwords |
| combustível | combustível | combustível | multiple_dictionary_entries |
| mama | mama | mama | ambiguous_headwords |
| adulto | adultos, adulto | adultos / adulto / adulta | multiple_dictionary_entries |
| fantasia | fantasia | fantasia | ambiguous_headwords |
| regresso | regresso | regresso | ambiguous_headwords |
| queixa | queixa, queixas | queixa / queixas | ambiguous_headwords |
| arquivo | arquivos, arquivo | arquivos / arquivo | ambiguous_headwords |
| traidor | traidor, traidores | traidor / traidores | multiple_dictionary_entries |
| voto | voto, votos | voto / votos | ambiguous_headwords |
| imposto | impostos, imposto | impostos / imposto | ambiguous_headwords |
| pecado | pecado, pecados | pecado / pecados | ambiguous_headwords |
| suspeito | suspeitos | suspeitos | ambiguous_headwords |
| impacto | impacto | impacto | ambiguous_headwords |
| traje | traje, trajes | traje / trajes | ambiguous_headwords |
| aventura | aventura, aventuras | aventura / aventuras | ambiguous_headwords |
| capa | capa | capa | ambiguous_headwords |
| pau | pau | pau | ambiguous_headwords |
| lance | lance | lance | ambiguous_headwords |
| guia | guia | guia | ambiguous_headwords |
| comprimido | comprimidos, comprimido | comprimidos / comprimido | ambiguous_headwords |
| chegada | chegada | chegada | ambiguous_headwords |
| foda | foda | foda | ambiguous_headwords |
| cave | cave | cave | ambiguous_headwords |
| conjunto | conjunto | conjunto | multiple_dictionary_entries |
| desgraçado | desgraçado, desgraçados | desgraçado / desgraçados | ambiguous_headwords |
| plástico | plástico | plástico / plástica | multiple_dictionary_entries |
| folga | folga | folga | ambiguous_headwords |
| costume | costume | costume | ambiguous_headwords |
| golfe | golfe | golfe | ambiguous_headwords |
| inspector | inspector | inspector | multiple_dictionary_entries |
| pausa | pausa | pausa | ambiguous_headwords |
| molho | molho | molho | ambiguous_headwords |
| concerto | concerto | concerto | ambiguous_headwords |
| pasta | pasta | pasta | ambiguous_headwords |
| letra | letra | letra | ambiguous_headwords |
| asa | asas, asa | asas / asa | ambiguous_headwords |
| velhote | velhote | velhote | multiple_dictionary_entries |
| roda | rodas, roda | rodas / roda | ambiguous_headwords |
| figura | figura, figuras | figura / figuras | ambiguous_headwords |
| potencial | potencial | potencial | multiple_dictionary_entries |
| patrulha | patrulha | patrulha | ambiguous_headwords |
| brinde | brinde | brinde | ambiguous_headwords |
| esposo | esposo | esposo | ambiguous_headwords |
| cambio | cambio | cambio | ambiguous_headwords |
| desejo | desejos | desejos | ambiguous_headwords |
| aumento | aumento | aumento | ambiguous_headwords |
| adolescente | adolescente | adolescente / adolescentes | multiple_dictionary_entries |
| condicional | condicional | condicional | multiple_dictionary_entries |
| planta | plantas, planta | plantas / planta | ambiguous_headwords |
| estudo | estudos | estudos | ambiguous_headwords |
| placa | placa, placas | placa / placas | ambiguous_headwords |
| bateria | bateria, baterias | bateria / baterias | ambiguous_headwords |
| tecido | tecido, tecidos | tecido / tecidos | ambiguous_headwords |
| italiano | italiano, italianos | italiano / italianos / italiana | multiple_dictionary_entries |
| fraude | fraude | fraude | ambiguous_headwords |
| firma | firma | firma | ambiguous_headwords |
| sumo | sumo | sumo / suma | ambiguous_headwords |
| capital | capital | capital | multiple_dictionary_entries |
| agenda | agenda | agenda | ambiguous_headwords |
| tiroteio | tiroteio | tiroteio | ambiguous_headwords |
| civil | civis | civil / civis | multiple_dictionary_entries |
| marcha | marcha | marcha | ambiguous_headwords |
| dose | dose | dose | ambiguous_headwords |
| reforço | reforços, reforço | reforços / reforço | ambiguous_headwords |
| horário | horário, horários | horário / horários | multiple_dictionary_entries |
| explosivo | explosivos | explosivos / explosivo | multiple_dictionary_entries |
| unha | unhas, unha | unhas / unha | ambiguous_headwords |
| condutor | condutor | condutor | multiple_dictionary_entries |
| besta | besta | besta | ambiguous_headwords |
| vendedor | vendedor, vendedores | vendedor / vendedores | multiple_dictionary_entries |
| aço | aço | aço | multiple_dictionary_entries |
| bunda | bunda | bunda | ambiguous_headwords |
| renda | renda | renda | ambiguous_headwords |
| espanhol | espanhol | espanhol / espanhola | ambiguous_headwords |
| dobro | dobro | dobro | ambiguous_headwords |
| vela | velas, vela | velas / vela | ambiguous_headwords |
| ficha | ficha, fichas | ficha / fichas | ambiguous_headwords |
| cretino | cretino | cretino | multiple_dictionary_entries |
| estrutura | estrutura | estrutura | ambiguous_headwords |
| rumo | rumo | rumo | ambiguous_headwords |
| coroa | coroa | coroa | ambiguous_headwords |
| muro | muro, muros | muro / muros | ambiguous_headwords |
| abraço | abraço | abraço | ambiguous_headwords |
| ensaio | ensaio, ensaios | ensaio / ensaios | ambiguous_headwords |
| grito | gritos, grito | gritos / grito | ambiguous_headwords |
| ramo | ramo | ramo | ambiguous_headwords |
| disfarce | disfarce | disfarce | ambiguous_headwords |
| desenho | desenho, desenhos | desenho / desenhos | ambiguous_headwords |
| folha | folha, folhas | folha / folhas | ambiguous_headwords |
| termo | termo | termo | ambiguous_headwords |
| cal | cal | cal | ambiguous_headwords |
| prática | prática | prática | ambiguous_headwords |
| luxo | luxo | luxo | ambiguous_headwords |
| tortura | tortura | tortura | ambiguous_headwords |
| complexo | complexo | complexo | ambiguous_headwords |
| palpite | palpite | palpite | ambiguous_headwords |
| receita | receita, receitas | receita / receitas | ambiguous_headwords |
| caminhão | caminhão | caminhão | ambiguous_headwords |
| laranja | laranja | laranja | multiple_dictionary_entries |
| manual | manual | manual | multiple_dictionary_entries |
| creme | creme | creme | ambiguous_headwords |
| torta | torta | torta | ambiguous_headwords |
| principio | principio | principio | ambiguous_headwords |
| consulta | consulta | consulta | ambiguous_headwords |
| estrangeiro | estrangeiro | estrangeiro / estrangeiros / estrangeira | multiple_dictionary_entries |
| escudo | escudos, escudo | escudos / escudo | ambiguous_headwords |
| encontro | encontros | encontros | ambiguous_headwords |
| inveja | inveja | inveja | ambiguous_headwords |
| argumento | argumento, argumentos | argumento / argumentos | ambiguous_headwords |
| perfume | perfume | perfume | ambiguous_headwords |
| mistura | mistura | mistura | ambiguous_headwords |
| rebelde | rebeldes | rebeldes / rebelde | multiple_dictionary_entries |
| gado | gado | gado | multiple_dictionary_entries |
| regalo | regalo | regalo | ambiguous_headwords |
| secretário | secretário | secretário | ambiguous_headwords |
| macho | macho, machos | macho / machos | multiple_dictionary_entries |
| recorde | recorde | recorde | ambiguous_headwords |
| político | políticos | político / políticos | ambiguous_headwords |
| bobo | bobo | bobo / boba | multiple_dictionary_entries |
| perspectiva | perspectiva | perspectiva | ambiguous_headwords |
| superior | superiores | superior / superiores | multiple_dictionary_entries |
| feitiço | feitiço | feitiço | multiple_dictionary_entries |
| fruta | fruta, frutas | fruta / frutas | ambiguous_headwords |
| milho | milho | milho | ambiguous_headwords |
| submarino | submarino | submarino | multiple_dictionary_entries |
| frigorífico | frigorífico | frigorífico | multiple_dictionary_entries |
| enfermaria | enfermaria | enfermaria | ambiguous_headwords |
| duche | duche | duche | ambiguous_headwords |
| pato | pato | pato | ambiguous_headwords |
| tomada | tomada | tomada | ambiguous_headwords |
| grana | grana | grana | ambiguous_headwords |
| taco | taco, tacos | taco / tacos | ambiguous_headwords |
| candidato | candidato, candidatos | candidato / candidatos | ambiguous_headwords |
| cumprimento | cumprimentos | cumprimentos | ambiguous_headwords |
| tenda | tenda | tenda | ambiguous_headwords |
| taxa | taxa, taxas | taxa / taxas | ambiguous_headwords |
| curva | curva, curvas | curva / curvas | ambiguous_headwords |
| viúva | viúva | viúva | ambiguous_headwords |
| desgraça | desgraça | desgraça | ambiguous_headwords |
| histórico | histórico | histórico | multiple_dictionary_entries |
| vaga | vaga | vaga | ambiguous_headwords |
| susto | susto | susto | ambiguous_headwords |
| ensino | ensino | ensino | ambiguous_headwords |
| testemunho | testemunho | testemunho | ambiguous_headwords |
| torneio | torneio | torneio | ambiguous_headwords |
| luto | luto | luto | ambiguous_headwords |
| custo | custo, custos | custo / custos | ambiguous_headwords |
| editor | editor | editor | ambiguous_headwords |
| ácido | ácido | ácido | multiple_dictionary_entries |
| líquido | líquido | líquido | multiple_dictionary_entries |
| ato | ato | ato | ambiguous_headwords |
| pervertido | pervertido | pervertido | ambiguous_headwords |
| cicatriz | cicatriz, cicatrizes | cicatriz / cicatrizes | ambiguous_headwords |
| tarado | tarado | tarado | ambiguous_headwords |
| objecto | objecto, objectos | objecto / objectos | ambiguous_headwords |
| tela | tela | tela | ambiguous_headwords |
| mergulho | mergulho | mergulho | ambiguous_headwords |
| lucro | lucro, lucros | lucro / lucros | ambiguous_headwords |
| rapto | rapto | rapto | ambiguous_headwords |
| conflito | conflito, conflitos | conflito / conflitos | ambiguous_headwords |
| biscoito | biscoitos, biscoito | biscoitos / biscoito | ambiguous_headwords |
| gay | gays | gay / gays | multiple_dictionary_entries |
| retrato | retrato | retrato | ambiguous_headwords |
| perito | perito, peritos | perito / peritos | multiple_dictionary_entries |
| distintivo | distintivo | distintivo | multiple_dictionary_entries |
| garantia | garantia, garantias | garantia / garantias | ambiguous_headwords |
| mandato | mandato | mandato | ambiguous_headwords |
| gesto | gesto | gesto | ambiguous_headwords |
| colapso | colapso | colapso | ambiguous_headwords |
| diagnóstico | diagnóstico | diagnóstico | multiple_dictionary_entries |
| encomenda | encomenda | encomenda | ambiguous_headwords |
| calibre | calibre | calibre | ambiguous_headwords |
| borracha | borracha | borracha | ambiguous_headwords |
| disciplina | disciplina | disciplina | ambiguous_headwords |
| novato | novato | novato | multiple_dictionary_entries |
| aliado | aliados, aliado | aliados / aliado | ambiguous_headwords |
| multa | multa, multas | multa / multas | ambiguous_headwords |
| desfile | desfile | desfile | ambiguous_headwords |
| gerador | gerador | gerador | multiple_dictionary_entries |
| suporte | suporte | suporte | ambiguous_headwords |
| testa | testa | testa | ambiguous_headwords |
| representante | representante, representantes | representante / representantes | multiple_dictionary_entries |
| perdedor | perdedor, perdedores | perdedor / perdedores | multiple_dictionary_entries |
| derrota | derrota | derrota | ambiguous_headwords |
| porão | porão | porão | ambiguous_headwords |
| fracasso | fracasso | fracasso | ambiguous_headwords |
| indivíduo | indivíduo, indivíduos | indivíduo / indivíduos | multiple_dictionary_entries |
| gripe | gripe | gripe | ambiguous_headwords |
| surpresa | surpresas | surpresas | ambiguous_headwords |
| reforma | reforma | reforma | ambiguous_headwords |
| visitante | visitantes, visitante | visitantes / visitante | multiple_dictionary_entries |
| brilho | brilho | brilho | ambiguous_headwords |
| conselheiro | conselheiro | conselheiro / conselheira | multiple_dictionary_entries |
| gigante | gigantes | gigante / gigantes | multiple_dictionary_entries |
| volante | volante | volante | multiple_dictionary_entries |
| grego | grego, gregos | grego / gregos / grega | ambiguous_headwords |
| instrumento | instrumento, instrumentos | instrumento / instrumentos | ambiguous_headwords |
| tampa | tampa | tampa | ambiguous_headwords |
| casco | casco | casco | ambiguous_headwords |
| desconto | desconto | desconto | ambiguous_headwords |
| psicopata | psicopata | psicopata | multiple_dictionary_entries |
| postal | postal | postal | multiple_dictionary_entries |
| vagabundo | vagabundo, vagabundos | vagabundo / vagabundos | ambiguous_headwords |
| urina | urina | urina | ambiguous_headwords |
| apelido | apelido | apelido | ambiguous_headwords |
| relva | relva | relva | ambiguous_headwords |
| martelo | martelo | martelo | ambiguous_headwords |
| oposto | oposto | oposto | ambiguous_headwords |
| sonda | sonda | sonda | ambiguous_headwords |
| fada | fadas, fada | fadas / fada | ambiguous_headwords |
| terminal | terminal | terminal | multiple_dictionary_entries |
| mosca | mosca, moscas | mosca / moscas | ambiguous_headwords |
| arco | arco | arco | ambiguous_headwords |
| conforto | conforto | conforto | ambiguous_headwords |
| circuito | circuito, circuitos | circuito / circuitos | ambiguous_headwords |
| copa | copa | copa | ambiguous_headwords |
| abuso | abuso | abuso | ambiguous_headwords |
| mortal | mortais | mortal / mortais | multiple_dictionary_entries |
| debate | debate | debate | ambiguous_headwords |
| xadrez | xadrez | xadrez | multiple_dictionary_entries |
| pirata | pirata | pirata | multiple_dictionary_entries |
| lésbica | lésbica, lésbicas | lésbica / lésbicas | ambiguous_headwords |
| cúmplice | cúmplice | cúmplice | multiple_dictionary_entries |
| arca | arca | arca | ambiguous_headwords |
| emboscada | emboscada | emboscada | ambiguous_headwords |
| monitor | monitor, monitores | monitor / monitores | ambiguous_headwords |
| químico | químicos | químicos / químico | ambiguous_headwords |
| elogio | elogio | elogio | ambiguous_headwords |
| desespero | desespero | desespero | ambiguous_headwords |
| gata | gata | gata | ambiguous_headwords |
| morgue | morgue | morgue | ambiguous_headwords |
| fêmea | fêmea, fêmeas | fêmea / fêmeas | ambiguous_headwords |
| seda | seda | seda | ambiguous_headwords |
| aborto | aborto | aborto | ambiguous_headwords |
| alimento | alimentos | alimentos | ambiguous_headwords |
| borracho | borracho | borracho | multiple_dictionary_entries |
| protector | protector | protector | multiple_dictionary_entries |
| balde | balde | balde | ambiguous_headwords |
| bloqueio | bloqueio | bloqueio | ambiguous_headwords |
| delegado | delegado | delegado | ambiguous_headwords |
| nazi | nazis | nazis / nazi | multiple_dictionary_entries |
| parceiro | parceira | parceiro / parceiros / parceira | not_a_plural_relationship |
| romano | romanos | romano / romanos | ambiguous_headwords |
| coitado | coitado | coitado | ambiguous_headwords |
| madrugada | madrugada | madrugada | ambiguous_headwords |
| quarentena | quarentena | quarentena | ambiguous_headwords |
| substituto | substituto | substituto | multiple_dictionary_entries |
| baleia | baleia, baleias | baleia / baleias | ambiguous_headwords |
| avanço | avanço | avanço | ambiguous_headwords |
| coro | coro | coro | ambiguous_headwords |
| árabe | árabe | árabe | multiple_dictionary_entries |
| bicho | bicho, bichos | bicho / bichos | ambiguous_headwords |
| massacre | massacre | massacre | ambiguous_headwords |
| fugitivo | fugitivo, fugitivos | fugitivo / fugitivos | multiple_dictionary_entries |
| pacto | pacto | pacto | ambiguous_headwords |
| disparo | disparos | disparos | ambiguous_headwords |
| caminhada | caminhada | caminhada | ambiguous_headwords |
| isco | isco | isco | ambiguous_headwords |
| entusiasmo | entusiasmo | entusiasmo | ambiguous_headwords |
| culto | culto | culto | multiple_dictionary_entries |
| bico | bico | bico | ambiguous_headwords |
| encanto | encanto | encanto | ambiguous_headwords |
| peso | pesos | pesos | ambiguous_headwords |
| artilharia | artilharia | artilharia | ambiguous_headwords |
| plasma | plasma | plasma | ambiguous_headwords |
| colete | colete | colete | ambiguous_headwords |
| mecânico | mecânico | mecânico / mecânica | ambiguous_headwords |
| ruído | ruído | ruído | ambiguous_headwords |
| legado | legado | legado | ambiguous_headwords |
| escova | escova | escova | ambiguous_headwords |
| assento | assento | assento | ambiguous_headwords |
| churrasco | churrasco | churrasco | ambiguous_headwords |
| missa | missa | missa | ambiguous_headwords |
| escolta | escolta | escolta | ambiguous_headwords |
| caçada | caçada | caçada | ambiguous_headwords |
| noivado | noivado | noivado | ambiguous_headwords |
| proprietário | proprietário | proprietário | multiple_dictionary_entries |
| chumbo | chumbo | chumbo | ambiguous_headwords |
| rodada | rodada | rodada | ambiguous_headwords |
| britânico | britânicos | britânico / britânicos / britânica | multiple_dictionary_entries |
| esgoto | esgoto, esgotos | esgoto / esgotos | ambiguous_headwords |
| soco | soco | soco | ambiguous_headwords |
| estrago | estragos | estragos | ambiguous_headwords |
| carroça | carroça | carroça | ambiguous_headwords |
| cadastro | cadastro | cadastro | ambiguous_headwords |
| garra | garras, garra | garras / garra | ambiguous_headwords |
| pilha | pilha, pilhas | pilha / pilhas | ambiguous_headwords |
| iniciativa | iniciativa | iniciativa | ambiguous_headwords |
| terno | terno | terno | multiple_dictionary_entries |
| reflexo | reflexo | reflexo | multiple_dictionary_entries |
| incómodo | incómodo | incómodo | multiple_dictionary_entries |
| técnico | técnicos | técnico / técnicos | multiple_dictionary_entries |
| cinta | cinta | cinta | ambiguous_headwords |
| ética | ética | ética | ambiguous_headwords |
| selo | selo, selos | selo / selos | ambiguous_headwords |
| fragmento | fragmentos, fragmento | fragmentos / fragmento | ambiguous_headwords |
| bagunça | bagunça | bagunça | ambiguous_headwords |
| fardo | fardo | fardo | ambiguous_headwords |
| bicha | bicha | bicha | ambiguous_headwords |
| mexicano | mexicanos | mexicano / mexicanos / mexicana | multiple_dictionary_entries |
| lote | lote | lote | ambiguous_headwords |
| veia | veias | veias | ambiguous_headwords |
| bacano | bacano | bacano | multiple_dictionary_entries |
| feriado | feriado | feriado | multiple_dictionary_entries |
| mago | mago | mago | multiple_dictionary_entries |
| cristão | cristãos | cristão / cristãos / cristã | multiple_dictionary_entries |
| enterro | enterro | enterro | ambiguous_headwords |
| borda | borda | borda | ambiguous_headwords |
| profeta | profeta | profeta | multiple_dictionary_entries |
| rolo | rolo | rolo | ambiguous_headwords |
| poste | poste | poste | ambiguous_headwords |
| brisa | brisa | brisa | ambiguous_headwords |
| músico | músico, músicos | músico / músicos | multiple_dictionary_entries |
| dinamite | dinamite | dinamite | ambiguous_headwords |
| manobra | manobra, manobras | manobra / manobras | ambiguous_headwords |
| abismo | abismo | abismo | ambiguous_headwords |
| galo | galo | galo | ambiguous_headwords |
| residente | residente, residentes | residente / residentes | multiple_dictionary_entries |
| autógrafo | autógrafo | autógrafo | multiple_dictionary_entries |
| réu | réu | réu | multiple_dictionary_entries |
| oral | oral | oral | multiple_dictionary_entries |
| vacina | vacina | vacina | ambiguous_headwords |
| grade | grades, grade | grades / grade | ambiguous_headwords |
| hipoteca | hipoteca | hipoteca | ambiguous_headwords |
| transplante | transplante | transplante | ambiguous_headwords |
| acompanhante | acompanhante | acompanhante | multiple_dictionary_entries |
| mobília | mobília | mobília | ambiguous_headwords |
| etiqueta | etiqueta | etiqueta | ambiguous_headwords |
| duelo | duelo | duelo | ambiguous_headwords |
| precisão | precisão | precisão | ambiguous_headwords |
| contentor | contentor | contentor | multiple_dictionary_entries |
| fatia | fatia | fatia | ambiguous_headwords |
| asilo | asilo | asilo | ambiguous_headwords |
| fenda | fenda | fenda | ambiguous_headwords |
| polegar | polegar | polegar | multiple_dictionary_entries |
| cimento | cimento | cimento | ambiguous_headwords |
| atentado | atentado | atentado | ambiguous_headwords |
| coral | coral | coral | multiple_dictionary_entries |
| detonador | detonador | detonador | multiple_dictionary_entries |
| gaita | gaita | gaita | ambiguous_headwords |
| hipócrita | hipócrita | hipócrita | multiple_dictionary_entries |
| aluna | aluna | aluna | ambiguous_headwords |
| conto | contos | contos | ambiguous_headwords |
| ditado | ditado | ditado | ambiguous_headwords |
| canto | cantos | cantos | ambiguous_headwords |
| pano | pano | pano | ambiguous_headwords |
| mana | mana | mana | ambiguous_headwords |
| grama | grama, gramas | grama / gramas | ambiguous_headwords |
| cantor | cantora | cantor / cantora | not_a_plural_relationship |
| orquestra | orquestra | orquestra | ambiguous_headwords |
| espuma | espuma | espuma | ambiguous_headwords |
| insulto | insulto | insulto | ambiguous_headwords |
| pátria | pátria | pátria | ambiguous_headwords |
| preservativo | preservativo, preservativos | preservativo / preservativos | multiple_dictionary_entries |
| chulo | chulo | chulo | ambiguous_headwords |
| consumo | consumo | consumo | ambiguous_headwords |
| demanda | demanda | demanda | ambiguous_headwords |
| lunático | lunático | lunático | multiple_dictionary_entries |
| farda | farda | farda | ambiguous_headwords |
| fractura | fractura | fractura | ambiguous_headwords |
| tango | tango | tango | ambiguous_headwords |
| certificado | certificado | certificado | ambiguous_headwords |
| saliva | saliva | saliva | ambiguous_headwords |
| comunicado | comunicado | comunicado | ambiguous_headwords |
| leito | leito | leito | ambiguous_headwords |
| desempenho | desempenho | desempenho | ambiguous_headwords |
| fruto | frutos, fruto | frutos / fruto | ambiguous_headwords |
| refrigerante | refrigerante | refrigerante | multiple_dictionary_entries |
| atalho | atalho | atalho | ambiguous_headwords |
| tesoura | tesoura | tesoura | ambiguous_headwords |
| limonada | limonada | limonada | ambiguous_headwords |
| estaca | estaca | estaca | ambiguous_headwords |
| recolha | recolha | recolha | ambiguous_headwords |
| espinha | espinha | espinha | ambiguous_headwords |
| berço | berço | berço | ambiguous_headwords |
| diploma | diploma | diploma | ambiguous_headwords |
| experimento | experimento | experimento | ambiguous_headwords |
| mijo | mijo | mijo | ambiguous_headwords |
| escuta | escutas | escutas | ambiguous_headwords |
| patife | patife | patife | multiple_dictionary_entries |
| recipiente | recipiente | recipiente | multiple_dictionary_entries |
| foco | foco | foco | ambiguous_headwords |
| administrador | administrador | administrador | multiple_dictionary_entries |
| golfo | golfo | golfo | ambiguous_headwords |
| tosse | tosse | tosse | ambiguous_headwords |
| estreia | estreia | estreia | ambiguous_headwords |
| cova | cova | cova | ambiguous_headwords |
| descida | descida | descida | ambiguous_headwords |
| cardeal | cardeal | cardeal | multiple_dictionary_entries |
| cunhado | cunhado | cunhado | ambiguous_headwords |
| português | português | português | multiple_dictionary_entries |
| aparte | aparte | aparte | ambiguous_headwords |
| trigo | trigo | trigo | ambiguous_headwords |
| roubo | roubos | roubos | ambiguous_headwords |
| vara | vara | vara | ambiguous_headwords |
| prego | prego | prego | ambiguous_headwords |
| punk | punk | punk | multiple_dictionary_entries |
| relâmpago | relâmpago | relâmpago | multiple_dictionary_entries |
| penteado | penteado | penteado | ambiguous_headwords |
| brinco | brincos | brincos | ambiguous_headwords |
| maníaco | maníaco | maníaco | multiple_dictionary_entries |
| quadrado | quadrado, quadrados | quadrado / quadrados | ambiguous_headwords |
| surra | surra | surra | ambiguous_headwords |
| fera | fera | fera | multiple_dictionary_entries |
| game | game | game | ambiguous_headwords |
| veterinário | veterinário | veterinário | multiple_dictionary_entries |
| terço | terço | terço | multiple_dictionary_entries |
| rival | rival | rival | multiple_dictionary_entries |
| tormenta | tormenta | tormenta | ambiguous_headwords |
| manada | manada | manada | ambiguous_headwords |
| paquete | paquete | paquete | multiple_dictionary_entries |
| parasita | parasita, parasitas | parasita / parasitas | ambiguous_headwords |
| desconhecido | desconhecidos | desconhecido / desconhecida / desconhecidos | ambiguous_headwords |
| pegada | pegada | pegada | ambiguous_headwords |
| católico | católico | católica / católico | multiple_dictionary_entries |
| raptor | raptor | raptor | multiple_dictionary_entries |
| bonitão | bonitão | bonitão | ambiguous_headwords |
| lotaria | lotaria | lotaria | ambiguous_headwords |
| senador | senadora | senador / senadora | not_a_plural_relationship |
| descoberta | descobertas | descobertas | ambiguous_headwords |
| esquilo | esquilo | esquilo | ambiguous_headwords |
| prensa | prensa | prensa | ambiguous_headwords |
| jacto | jacto | jacto | ambiguous_headwords |
| acelerador | acelerador | acelerador | multiple_dictionary_entries |
| ginástica | ginástica | ginástica | ambiguous_headwords |
| consolo | consolo | consolo | ambiguous_headwords |
| cubo | cubo | cubo | ambiguous_headwords |
| tese | tese | tese | ambiguous_headwords |
| cozinheiro | cozinheira | cozinheiro / cozinheira | not_a_plural_relationship |
| gole | gole | gole | ambiguous_headwords |
| vilão | vilão | vilão | multiple_dictionary_entries |
| tonto | tontos | tonto / tonta / tontos | multiple_dictionary_entries |
| anestesia | anestesia | anestesia | ambiguous_headwords |
| faia | faia | faia | ambiguous_headwords |
| veterano | veteranos, veterano | veteranos / veterano | multiple_dictionary_entries |
| escritor | escritora | escritor / escritores / escritora | not_a_plural_relationship |
| emenda | emenda | emenda | ambiguous_headwords |
| banca | banca | banca | ambiguous_headwords |
| matador | matador | matador | multiple_dictionary_entries |
| suborno | suborno | suborno | ambiguous_headwords |
| drogado | drogados | drogado / drogada / drogados | ambiguous_headwords |
| velhota | velhota | velhota | ambiguous_headwords |
| acordo | acordos | acordos | ambiguous_headwords |
| tacada | tacada | tacada | ambiguous_headwords |
| broche | broche | broche | ambiguous_headwords |
| malandro | malandro | malandro | ambiguous_headwords |
| livraria | livraria | livraria | ambiguous_headwords |
| alcunha | alcunha | alcunha | ambiguous_headwords |
| grão | grão | grão | multiple_dictionary_entries |
| soma | soma | soma | ambiguous_headwords |
| espertinho | espertinho | espertinho | multiple_dictionary_entries |
| expediente | expediente | expediente | multiple_dictionary_entries |
| sequestro | sequestro | sequestro | ambiguous_headwords |
| vigilante | vigilante | vigilante | multiple_dictionary_entries |
| trilha | trilha | trilha | ambiguous_headwords |
| embarque | embarque | embarque | ambiguous_headwords |
| filtro | filtro | filtro | ambiguous_headwords |
| tanga | tanga | tanga | ambiguous_headwords |
| documentário | documentário | documentário | multiple_dictionary_entries |
| verso | verso | verso | ambiguous_headwords |
| afecto | afecto | afecto | ambiguous_headwords |
| morena | morena | morena | ambiguous_headwords |
| admirador | admirador | admirador | multiple_dictionary_entries |
| baba | baba | baba | ambiguous_headwords |
| ceia | ceia | ceia | ambiguous_headwords |
| receptor | receptor | receptor | multiple_dictionary_entries |
| roxo | roxo | roxo | multiple_dictionary_entries |
| dentada | dentada | dentada | ambiguous_headwords |
| vencedor | vencedora | vencedor / vencedores / vencedora | not_a_plural_relationship |
| restante | restante | restantes / restante | multiple_dictionary_entries |
| subconsciente | subconsciente | subconsciente | multiple_dictionary_entries |
| morango | morango | morango | ambiguous_headwords |
| injustiça | injustiça | injustiça | ambiguous_headwords |
| reformado | reformado | reformado | ambiguous_headwords |
| secretaria | secretaria | secretaria | ambiguous_headwords |
| sova | sova | sova | ambiguous_headwords |
| prisioneiro | prisioneira | prisioneiros / prisioneiro / prisioneira | not_a_plural_relationship |
| aleijado | aleijado | aleijado | ambiguous_headwords |
| chapa | chapa | chapa | ambiguous_headwords |
| implante | implantes, implante | implantes / implante | ambiguous_headwords |
| campa | campa | campa | ambiguous_headwords |
| descendente | descendente | descendente | multiple_dictionary_entries |
| leitor | leitor | leitor | multiple_dictionary_entries |
| funerária | funerária | funerária | ambiguous_headwords |
| assalto | assaltos | assaltos | ambiguous_headwords |
| defensiva | defensiva | defensiva | ambiguous_headwords |
| inimigo | inimiga | inimigo / inimigos / inimiga | not_a_plural_relationship |
| clone | clone | clone | ambiguous_headwords |
| pia | pia | pia | ambiguous_headwords |
| reboque | reboque | reboque | ambiguous_headwords |
| totó | totó | totó | multiple_dictionary_entries |
| patente | patente | patente | multiple_dictionary_entries |
| republicano | republicano | republicano | multiple_dictionary_entries |
| oponente | oponente | oponente | multiple_dictionary_entries |
| irlandês | irlandeses | irlandês / irlandeses | multiple_dictionary_entries |
| encargo | encargo | encargo | ambiguous_headwords |
| viciado | viciados | viciado / viciada / viciados | ambiguous_headwords |
| ale | ale | ale | ambiguous_headwords |
| estufa | estufa | estufa | ambiguous_headwords |
| associado | associados | associado / associados | ambiguous_headwords |
| barro | barro | barro | ambiguous_headwords |
| alce | alce | alce | ambiguous_headwords |
| desgosto | desgosto | desgosto | ambiguous_headwords |
| abandono | abandono | abandono | ambiguous_headwords |
| pretexto | pretexto | pretexto | ambiguous_headwords |
| sobrenatural | sobrenatural | sobrenatural | multiple_dictionary_entries |
| confronto | confronto | confronto | ambiguous_headwords |
| cafeína | cafeína | cafeína | ambiguous_headwords |
| empate | empate | empate | ambiguous_headwords |
| liberal | liberal | liberal | multiple_dictionary_entries |
| cubano | cubanos | cubano / cubanos | multiple_dictionary_entries |
| memorando | memorando | memorando | ambiguous_headwords |
| porte | porte | porte | ambiguous_headwords |
| cómoda | cómoda | cómoda | ambiguous_headwords |
| mutante | mutante | mutante | multiple_dictionary_entries |
| canalizador | canalizador | canalizador | multiple_dictionary_entries |
| escritura | escritura | escritura | ambiguous_headwords |
| palestra | palestra | palestra | ambiguous_headwords |

## Spanish: 6 forms join 6 cards; 0 split

| Card | Newly joined | Card now holds | Was blocked by |
|---|---|---|---|
| compañero | compañera | compañero / compañeros / compañera | not_a_plural_relationship |
| secretario | secretaria | secretario / secretaria | not_a_plural_relationship |
| profesor | profesora | profesor / profesora / profesores | not_a_plural_relationship |
| senador | senadora | senador / senadora | not_a_plural_relationship |
| cocinero | cocinera | cocinero / cocinera | not_a_plural_relationship |
| operador | operadora | operadora / operador | not_a_plural_relationship |


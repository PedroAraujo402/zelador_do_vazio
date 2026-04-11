# O Zelador do Vacuo

Um jogo de terror claustrofobico feito em **Python + Pygame**. Voce e o unico zelador de uma estacao isolada no vacuo. Sua unica conexao com o exterior: um radio de cinturao que precisa permanecer sintonizado. Mantenha os sistemas da capsula operacionais, monitore o radar e sobreviva ate o fim do turno.

---

## Requisitos

- **Python 3.10+**
- **Pygame CE** (pygame-community edition)

## Instalacao e Execucao

```bash
# Instalar dependencia
pip install pygame-ce

# Rodar o jogo
python main.py
```

## Controles

| Acao | Controle |
|------|----------|
| Sintonizar radio | **Arraste horizontalmente** sobre o painel de radio |
| Reparar sistemas | **Segure o clique** nos botoes de manutencao |
| Fechar | `ESC` ou feche a janela |

## Mecanicas

### Radio e Sintonia
- Uma **frequencia alvo** e exibida como dica sutil em `ALVO: XX.X MHz` (canto inferior esquerdo)
- Arraste o mouse sobre o painel de radio para ajustar a frequencia
- Quando **sintonizado**, a barra de status muda e mensagens misteriosas comecam a aparecer
- Fora de sintonia, a sanidade cai gradualmente

### Radar e Criatura
- O radar de varredura estilo sonar mostra uma **entidade** que se move em direcao ao centro
- A criatura so aparece quando o sweep do sonar passa por ela
- Quanto mais tempo passa, mais rapida ela se aproxima
- Se chegar muito perto, a **resistencia da capsula** comeca a cair

### Sanidade Mental
- Barra no canto inferior direito
- Caindo quando fora de sintonia, subindo quando sintonizado
- Sanidade baixa aumenta a **ameaca das entidades** e causa efeitos visuais (shake, vinheta, granulacao, dessaturacao)

### Manutencao dos Sistemas
- 3 sistemas falham ocasionalmente: **Ventilacao**, **Refrigeracao** e **Energia**
- Segure o clique no botao falho por **2 segundos** para reparar
- Sistemas com falha aumentam a ameaca das entidades

### Ciclo de Dias
- **7 dias** de ~8 minutos cada (56 minutos no total)
- A dificuldade escala a cada dia: estacoes trocam mais rapido, tolerancia do radio diminui, ameaca base sobe
- Transicao visual entre dias com mensagem narrativa

### Sistema de AP Oculto
- A criatura usa um sistema invisivel de **pontos de acao** (AP) baseado nas horas do dia
- A cada hora, ela rola um **d20 silencioso**: se o resultado for menor ou igual aos AP, ela se move
- Sanidade baixa **multiplica os AP** da criatura, tornando-a mais ativa e perigosa

### Game Over
- Ocorre quando a **resistencia da capsula** chega a zero
- Ou ao sobreviver os **7 dias completos**

## Estrutura do Projeto

```
zelador_do_vacuo_py/
├── main.py                      # Entry point, loop principal, render
├── README.md                    # Esta documentacao
├── managers/
│   ├── __init__.py
│   ├── game_manager.py          # Singleton: estado global (freq, sanidade, tempo, ameaca)
│   ├── sanity_manager.py        # Shake de camera e panic attacks
│   ├── maintenance_manager.py   # Botoes de manutencao com falha e reparo
│   └── day_manager.py           # Ciclo de 7 dias, transicoes, escalada
├── systems/
│   ├── __init__.py
│   ├── radio_system.py          # Painel de radio com interacao de arraste
│   ├── radar_system.py          # Radar vetorial com sweep e criatura
│   └── crt_effect.py            # Helpers de scanlines e granulacao
├── arts/                        # Artes conceituais / referencias visuais
└── assets/
    └── audio/                   # (Reservado para arquivos de audio futuros)
```

## Licenca

Projeto experimental / portfolio.

# MT5 Trading Helper

Un'applicazione Python per il trading automatico su MetaTrader 5 con tasti rapidi e interfaccia grafica.

## Funzionalità

- Connessione a MetaTrader 5
- Interfaccia grafica per gestire tutte le impostazioni
- Tasti rapidi personalizzabili per:
  - Piazzare un ordine BE (Break Even)
  - Muovere SL/TP
  - Chiudere parzialmente le posizioni
  - Attivare/Disattivare Trailing Stop
  - Attivare/Disattivare Protezione Trend
- Sistema di Trailing Stop automatico
- Sistema di Protezione Trend basato su media mobile

## Requisiti

- Python 3.8 o superiore
- MetaTrader 5 installato e in esecuzione
- Account MT5 attivo

## Installazione

1. Clona o scarica questo progetto
2. Installa le dipendenze:
   ```bash
   pip install -r requirements.txt
   ```

## Utilizzo

1. Avvia MetaTrader 5 e accedi al tuo account
2. Esegui l'applicazione:
   ```bash
   python mt5_trading_helper.py
   ```
3. Clicca su "Connetti a MT5" per collegarti
4. Configura simbolo e lot size
5. Personalizza i tasti rapidi se necessario
6. Usa i pulsanti o i tasti rapidi per operare

## Tasti Rapidi Predefiniti

- F1: Place BE
- F2: Muovi SL/TP
- F3: Chiudi Parziale
- F4: Attiva/Disattiva Trailing Stop
- F5: Attiva/Disattiva Protezione Trend

## Note

- Assicurati che MetaTrader 5 sia in esecuzione prima di avviare l'applicazione
- I tasti rapidi funzionano anche quando l'applicazione è in background
- Usa con cautela e fai test in demo prima di utilizzare con denaro reale

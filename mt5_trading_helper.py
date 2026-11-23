import sys
import json
import os
import MetaTrader5 as mt5
import keyboard
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QLineEdit, QComboBox, QGroupBox, 
                             QFormLayout, QMessageBox)
from PyQt5.QtCore import Qt, QTimer


class MT5TradingHelper(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MT5 Trading Helper")
        self.setGeometry(100, 100, 700, 550)
        
        self.connected = False
        self.trailing_stop_active = False
        self.trend_protection_active = False
        self.current_symbol = "XAUUSD.s"
        self.lot_size = 0.10
        
        self.hotkeys = {
            "place_be": "F1",
            "move_sl_tp": "F2",
            "partial_close": "F3",
            "toggle_trailing": "F4",
            "toggle_protection": "F5"
        }
        
        self.settings_file = "mt5_trading_helper_settings.json"
        
        self.init_ui()
        self.load_settings()
        self.init_hotkeys()
        
        # Timer per aggiornare mercato e funzionalità attive
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_market_data)
        self.timer.start(500)
    
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # === SEZIONE CONNESSIONE ===
        conn_group = QGroupBox("Connessione MT5")
        conn_layout = QFormLayout()
        
        self.txt_login = QLineEdit()
        self.txt_login.setPlaceholderText("Numero Conto (opzionale)")
        conn_layout.addRow("Login:", self.txt_login)
        
        self.txt_password = QLineEdit()
        self.txt_password.setPlaceholderText("Password (opzionale)")
        self.txt_password.setEchoMode(QLineEdit.Password)
        conn_layout.addRow("Password:", self.txt_password)
        
        self.txt_server = QLineEdit()
        self.txt_server.setPlaceholderText("Server (opzionale)")
        conn_layout.addRow("Server:", self.txt_server)
        
        self.btn_connect = QPushButton("Connetti")
        self.btn_connect.clicked.connect(self.connect_mt5)
        conn_layout.addRow(self.btn_connect)
        
        self.lbl_status = QLabel("Stato: ❌ Disconnesso")
        conn_layout.addRow(self.lbl_status)
        
        conn_group.setLayout(conn_layout)
        main_layout.addWidget(conn_group)
        
        # === SEZIONE IMPOSTAZIONI ===
        settings_group = QGroupBox("Impostazioni")
        settings_layout = QFormLayout()
        
        self.cmb_symbol = QComboBox()
        self.cmb_symbol.setEditable(True)
        self.cmb_symbol.addItems(["XAUUSD.s", "EURUSD", "GBPUSD", "USDJPY"])
        self.cmb_symbol.currentTextChanged.connect(self.on_setting_change)
        settings_layout.addRow("Simbolo:", self.cmb_symbol)
        
        self.txt_lot = QLineEdit(str(self.lot_size))
        self.txt_lot.textChanged.connect(self.on_setting_change)
        settings_layout.addRow("Lot Size:", self.txt_lot)
        
        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)
        
        # === SEZIONE TASTI VELOCI ===
        hotkeys_group = QGroupBox("Tasti Veloci")
        hotkeys_layout = QFormLayout()
        
        self.txt_hotkey_be = QLineEdit(self.hotkeys["place_be"])
        self.txt_hotkey_be.editingFinished.connect(self.on_setting_change)
        hotkeys_layout.addRow("🎯 Break-Even:", self.txt_hotkey_be)
        
        self.txt_hotkey_sl_tp = QLineEdit(self.hotkeys["move_sl_tp"])
        self.txt_hotkey_sl_tp.editingFinished.connect(self.on_setting_change)
        hotkeys_layout.addRow("🔄 Muovi SL/TP:", self.txt_hotkey_sl_tp)
        
        self.txt_hotkey_partial = QLineEdit(self.hotkeys["partial_close"])
        self.txt_hotkey_partial.editingFinished.connect(self.on_setting_change)
        hotkeys_layout.addRow("✂️ Chiudi Parziale:", self.txt_hotkey_partial)
        
        self.txt_hotkey_trailing = QLineEdit(self.hotkeys["toggle_trailing"])
        self.txt_hotkey_trailing.editingFinished.connect(self.on_setting_change)
        hotkeys_layout.addRow("📍 Trailing Stop:", self.txt_hotkey_trailing)
        
        self.txt_hotkey_protection = QLineEdit(self.hotkeys["toggle_protection"])
        self.txt_hotkey_protection.editingFinished.connect(self.on_setting_change)
        hotkeys_layout.addRow("🛡️ Protezione Trend:", self.txt_hotkey_protection)
        
        hotkeys_group.setLayout(hotkeys_layout)
        main_layout.addWidget(hotkeys_group)
        
        # === SEZIONE PULSANTI ===
        actions_group = QGroupBox("Azioni Rapide")
        actions_layout = QHBoxLayout()
        
        self.btn_be = QPushButton("🎯 Break-Even")
        self.btn_be.setStyleSheet("background-color: #3498db; color: white; padding: 10px;")
        self.btn_be.clicked.connect(self.place_be)
        actions_layout.addWidget(self.btn_be)
        
        self.btn_sl_tp = QPushButton("🔄 Muovi SL/TP")
        self.btn_sl_tp.clicked.connect(self.move_sl_tp)
        actions_layout.addWidget(self.btn_sl_tp)
        
        self.btn_partial = QPushButton("✂️ Chiudi Parziale")
        self.btn_partial.clicked.connect(self.partial_close)
        actions_layout.addWidget(self.btn_partial)
        
        self.btn_trailing = QPushButton("📍 Trailing")
        self.btn_trailing.clicked.connect(self.toggle_trailing_stop)
        actions_layout.addWidget(self.btn_trailing)
        
        self.btn_protection = QPushButton("🛡️ Protezione")
        self.btn_protection.clicked.connect(self.toggle_trend_protection)
        actions_layout.addWidget(self.btn_protection)
        
        actions_group.setLayout(actions_layout)
        main_layout.addWidget(actions_group)
        
        # === SEZIONE STATO ===
        self.lbl_market = QLabel("Dati di Mercato: Connetti a MT5")
        main_layout.addWidget(self.lbl_market)
        
        self.lbl_trailing = QLabel("Trailing Stop: ❌ Disattivo")
        main_layout.addWidget(self.lbl_trailing)
        
        self.lbl_protection = QLabel("Protezione Trend: ❌ Disattiva")
        main_layout.addWidget(self.lbl_protection)
    
    def save_settings(self):
        settings = {
            "login": self.txt_login.text(),
            "server": self.txt_server.text(),
            "symbol": self.cmb_symbol.currentText(),
            "lot_size": self.txt_lot.text(),
            "hotkeys": self.hotkeys
        }
        try:
            with open(self.settings_file, "w") as f:
                json.dump(settings, f)
        except Exception as e:
            print(f"Errore salvataggio: {e}")
    
    def load_settings(self):
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, "r") as f:
                    settings = json.load(f)
                
                self.txt_login.setText(settings.get("login", ""))
                self.txt_server.setText(settings.get("server", ""))
                self.cmb_symbol.setCurrentText(settings.get("symbol", "XAUUSD.s"))
                self.txt_lot.setText(settings.get("lot_size", "0.10"))
                
                loaded_hotkeys = settings.get("hotkeys", {})
                if loaded_hotkeys:
                    self.hotkeys = loaded_hotkeys
                    self.txt_hotkey_be.setText(self.hotkeys.get("place_be", "F1"))
                    self.txt_hotkey_sl_tp.setText(self.hotkeys.get("move_sl_tp", "F2"))
                    self.txt_hotkey_partial.setText(self.hotkeys.get("partial_close", "F3"))
                    self.txt_hotkey_trailing.setText(self.hotkeys.get("toggle_trailing", "F4"))
                    self.txt_hotkey_protection.setText(self.hotkeys.get("toggle_protection", "F5"))
            except Exception as e:
                print(f"Errore caricamento: {e}")
    
    def on_setting_change(self):
        self.save_settings()
        self.update_hotkeys()
    
    def init_hotkeys(self):
        try:
            keyboard.unhook_all_hotkeys()
            keyboard.add_hotkey(self.hotkeys["place_be"], self.place_be)
            keyboard.add_hotkey(self.hotkeys["move_sl_tp"], self.move_sl_tp)
            keyboard.add_hotkey(self.hotkeys["partial_close"], self.partial_close)
            keyboard.add_hotkey(self.hotkeys["toggle_trailing"], self.toggle_trailing_stop)
            keyboard.add_hotkey(self.hotkeys["toggle_protection"], self.toggle_trend_protection)
        except Exception as e:
            print(f"Errore hotkeys: {e}")
    
    def update_hotkeys(self):
        self.hotkeys["place_be"] = self.txt_hotkey_be.text()
        self.hotkeys["move_sl_tp"] = self.txt_hotkey_sl_tp.text()
        self.hotkeys["partial_close"] = self.txt_hotkey_partial.text()
        self.hotkeys["toggle_trailing"] = self.txt_hotkey_trailing.text()
        self.hotkeys["toggle_protection"] = self.txt_hotkey_protection.text()
        self.init_hotkeys()
        self.save_settings()
    
    def connect_mt5(self):
        login = self.txt_login.text()
        password = self.txt_password.text()
        server = self.txt_server.text()
        
        if login and password and server:
            try:
                login_int = int(login)
                if not mt5.initialize(login=login_int, password=password, server=server):
                    error = mt5.last_error()
                    QMessageBox.critical(self, "Errore", f"Connessione fallita!\nCodice: {error[0]}\nMessaggio: {error[1]}")
                    self.connected = False
                    self.lbl_status.setText("Stato: ❌ Disconnesso")
                    return
            except ValueError:
                QMessageBox.warning(self, "Attenzione", "Login deve essere un numero!")
                return
        else:
            if not mt5.initialize():
                QMessageBox.critical(self, "Errore", "MT5 non è aperto! Avvia MT5 e connettiti al tuo account.")
                self.connected = False
                self.lbl_status.setText("Stato: ❌ Disconnesso")
                return
        
        self.connected = True
        self.lbl_status.setText("Stato: ✅ Connesso!")
        
        # Carica tutti i simboli disponibili
        symbols = mt5.symbols_get()
        if symbols:
            symbol_names = [s.name for s in symbols]
            self.cmb_symbol.clear()
            self.cmb_symbol.addItems(symbol_names)
            if "XAUUSD.s" in symbol_names:
                self.cmb_symbol.setCurrentText("XAUUSD.s")
        
        QMessageBox.information(self, "OK", "Connesso a MT5!")
        self.save_settings()
    
    # === AZIONI PRINCIPALI ===
    def place_be(self):
        """Break-Even: sposta SL di TUTTE le posizioni al prezzo di entrata!"""
        if not self.connected:
            QMessageBox.warning(self, "Attenzione", "Prima connetti a MT5!")
            return
        
        positions = mt5.positions_get()
        if positions is None or len(positions) == 0:
            QMessageBox.information(self, "Info", "Nessuna posizione aperta!")
            return
        
        modified = 0
        for pos in positions:
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "position": pos.ticket,
                "sl": pos.price_open,
                "tp": pos.tp if pos.tp != 0 else 0.0
            }
            result = mt5.order_send(request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                modified += 1
        
        if modified > 0:
            QMessageBox.information(self, "OK", f"✅ Break-Even applicato a {modified} posizioni!")
        else:
            QMessageBox.warning(self, "Errore", "Nessuna posizione modificata!")
    
    def move_sl_tp(self):
        if not self.connected:
            QMessageBox.warning(self, "Attenzione", "Prima connetti a MT5!")
            return
        
        positions = mt5.positions_get()
        if positions is None or len(positions) == 0:
            QMessageBox.information(self, "Info", "Nessuna posizione aperta!")
            return
        
        modified = 0
        for pos in positions:
            symbol_info = mt5.symbol_info(pos.symbol)
            if not symbol_info:
                continue
            
            tick = mt5.symbol_info_tick(pos.symbol)
            if not tick:
                continue
            
            point = symbol_info.point
            if pos.type == mt5.ORDER_TYPE_BUY:
                new_sl = tick.bid - 30 * point
                new_tp = tick.bid + 50 * point
            else:
                new_sl = tick.ask + 30 * point
                new_tp = tick.ask - 50 * point
            
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "position": pos.ticket,
                "sl": new_sl,
                "tp": new_tp
            }
            
            result = mt5.order_send(request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                modified += 1
        
        if modified > 0:
            QMessageBox.information(self, "OK", f"✅ SL/TP aggiornati per {modified} posizioni!")
        else:
            QMessageBox.warning(self, "Errore", "Nessuna posizione modificata!")
    
    def partial_close(self):
        if not self.connected:
            QMessageBox.warning(self, "Attenzione", "Prima connetti a MT5!")
            return
        
        positions = mt5.positions_get()
        if positions is None or len(positions) == 0:
            QMessageBox.information(self, "Info", "Nessuna posizione aperta!")
            return
        
        closed = 0
        for pos in positions:
            close_volume = pos.volume / 2
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": pos.symbol,
                "volume": close_volume,
                "type": mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY,
                "position": pos.ticket,
                "deviation": 100,
                "magic": 123456,
                "comment": "Partial Close",
            }
            
            result = mt5.order_send(request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                closed += 1
        
        if closed > 0:
            QMessageBox.information(self, "OK", f"✅ Chiuse parzialmente {closed} posizioni!")
        else:
            QMessageBox.warning(self, "Errore", "Nessuna posizione chiusa!")
    
    def toggle_trailing_stop(self):
        self.trailing_stop_active = not self.trailing_stop_active
        if self.trailing_stop_active:
            self.lbl_trailing.setText("Trailing Stop: ✅ Attivo!")
            self.btn_trailing.setStyleSheet("background-color: #2ecc71; color: white; padding: 10px;")
            QMessageBox.information(self, "OK", "Trailing Stop attivato!")
        else:
            self.lbl_trailing.setText("Trailing Stop: ❌ Disattivo")
            self.btn_trailing.setStyleSheet("")
            QMessageBox.information(self, "OK", "Trailing Stop disattivato!")
    
    def toggle_trend_protection(self):
        self.trend_protection_active = not self.trend_protection_active
        if self.trend_protection_active:
            self.lbl_protection.setText("Protezione Trend: ✅ Attiva!")
            self.btn_protection.setStyleSheet("background-color: #2ecc71; color: white; padding: 10px;")
            QMessageBox.information(self, "OK", "Protezione Trend attivata!")
        else:
            self.lbl_protection.setText("Protezione Trend: ❌ Disattiva")
            self.btn_protection.setStyleSheet("")
            QMessageBox.information(self, "OK", "Protezione Trend disattivata!")
    
    # === AGGIORNAMENTO DATI MERCATO E FUNZIONALITA' ATTIVE ===
    def update_market_data(self):
        if not self.connected:
            return
        
        symbol = self.cmb_symbol.currentText()
        tick = mt5.symbol_info_tick(symbol)
        if tick:
            self.lbl_market.setText(f"Dati di Mercato: {symbol} | Bid: {tick.bid} | Ask: {tick.ask}")
        
        if self.trailing_stop_active:
            self.update_trailing_stop()
        if self.trend_protection_active:
            self.update_trend_protection()
    
    def update_trailing_stop(self):
        positions = mt5.positions_get()
        if positions is None:
            return
        
        for pos in positions:
            symbol_info = mt5.symbol_info(pos.symbol)
            if not symbol_info:
                continue
            point = symbol_info.point
            tick = mt5.symbol_info_tick(pos.symbol)
            if not tick:
                continue
            
            if pos.type == mt5.ORDER_TYPE_BUY:
                new_sl = tick.bid - 20 * point
                if pos.sl == 0 or new_sl > pos.sl:
                    request = {
                        "action": mt5.TRADE_ACTION_SLTP,
                        "position": pos.ticket,
                        "sl": new_sl,
                        "tp": pos.tp if pos.tp != 0 else 0.0
                    }
                    mt5.order_send(request)
            else:
                new_sl = tick.ask + 20 * point
                if pos.sl == 0 or new_sl < pos.sl:
                    request = {
                        "action": mt5.TRADE_ACTION_SLTP,
                        "position": pos.ticket,
                        "sl": new_sl,
                        "tp": pos.tp if pos.tp != 0 else 0.0
                    }
                    mt5.order_send(request)
    
    def update_trend_protection(self):
        positions = mt5.positions_get()
        if positions is None:
            return
        
        for pos in positions:
            symbol_info = mt5.symbol_info(pos.symbol)
            if not symbol_info:
                continue
            point = symbol_info.point
            rates = mt5.copy_rates_from_pos(pos.symbol, mt5.TIMEFRAME_M1, 0, 10)
            if rates is None or len(rates) < 10:
                continue
            
            closes = [r.close for r in rates]
            avg_price = sum(closes) / len(closes)
            
            tick = mt5.symbol_info_tick(pos.symbol)
            if not tick:
                continue
            
            if pos.type == mt5.ORDER_TYPE_BUY:
                if tick.bid > avg_price * 1.0001:
                    new_sl = tick.bid - 10 * point
                    if pos.sl == 0 or new_sl > pos.sl:
                        request = {
                            "action": mt5.TRADE_ACTION_SLTP,
                            "position": pos.ticket,
                            "sl": new_sl,
                            "tp": pos.tp if pos.tp != 0 else 0.0
                        }
                        mt5.order_send(request)
            else:
                if tick.ask < avg_price * 0.9999:
                    new_sl = tick.ask + 10 * point
                    if pos.sl == 0 or new_sl < pos.sl:
                        request = {
                            "action": mt5.TRADE_ACTION_SLTP,
                            "position": pos.ticket,
                            "sl": new_sl,
                            "tp": pos.tp if pos.tp != 0 else 0.0
                        }
                        mt5.order_send(request)
    
    def closeEvent(self, event):
        if self.connected:
            mt5.shutdown()
        try:
            keyboard.unhook_all_hotkeys()
        except:
            pass
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MT5TradingHelper()
    window.show()
    sys.exit(app.exec_())

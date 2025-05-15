# NASDAQ LUDP Halt Monitor with Smart Extension Logic
# GNU GPLv3 License
# Mike Ippolito 2025

import sys
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pytz
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer

EST = pytz.timezone('US/Eastern')

class FloatingHaltWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.halts = {}
        self.mouse_pos = None
        self.init_ui()
        self.init_timers()

    def init_ui(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("""
            background-color: rgba(45, 45, 45, 0.9);
            color: #ffffff;
            border-radius: 5px;
            padding: 10px;
            font-family: Segoe UI;
            font-size: 12px;
        """)

        self.layout = QVBoxLayout()
        self.title = QLabel("Stock Volitility Halts")
        self.title.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 8px;")
        self.layout.addWidget(self.title)

        self.content = QLabel()
        self.layout.addWidget(self.content)
        self.setLayout(self.layout)
        self.adjustSize()

        screen_geo = QApplication.primaryScreen().availableGeometry()
        self.move(screen_geo.right() - self.width() - 20, 20)

    def init_timers(self):
        self.fetch_timer = QTimer()
        self.fetch_timer.timeout.connect(self.fetch_halts)
        self.fetch_timer.start(15000)  # 15 seconds

        self.display_timer = QTimer()
        self.display_timer.timeout.connect(self.update_display)
        self.display_timer.start(1000)  # 1 second

        self.fetch_halts()

    def fetch_halts(self):
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'}
            response = requests.get(
                "https://www.nasdaqtrader.com/rss.aspx?feed=tradehalts",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'xml')
            current_symbols = set()
            now = datetime.now(EST)

            for item in soup.find_all('item'):
                if item.find('ResumptionTradeTime') and item.find('ResumptionTradeTime').text.strip():
                    continue

                reason = item.find('ReasonCode')
                symbol_tag = item.find('IssueSymbol')
                if not reason or not symbol_tag:
                    continue

                if reason.text.strip().upper() != 'LUDP':
                    continue

                symbol = symbol_tag.text.strip()
                current_symbols.add(symbol)

                try:
                    # Parse halt information
                    halt_date = datetime.strptime(item.find('HaltDate').text, "%m/%d/%Y").date()
                    halt_time = datetime.strptime(item.find('HaltTime').text, "%H:%M:%S").time()
                    halt_dt = EST.localize(datetime.combine(halt_date, halt_time))

                    res_date = datetime.strptime(item.find('ResumptionDate').text, "%m/%d/%Y").date()
                    res_time = datetime.strptime(item.find('ResumptionQuoteTime').text, "%H:%M:%S").time()
                    res_dt = EST.localize(datetime.combine(res_date, res_time))

                    # Initialize new entry
                    new_est_unhalt = res_dt + timedelta(minutes=5)
                    extensions = 0

                    # Handle existing entries
                    if symbol in self.halts:
                        existing = self.halts[symbol]
                        
                        if res_dt == existing['resumption_time']:
                            if existing['est_unhalt'] < now:
                                if existing['extensions'] < 2:
                                    new_est_unhalt = existing['est_unhalt'] + timedelta(minutes=5)
                                    extensions = existing['extensions'] + 1
                                else:
                                    new_est_unhalt = existing['est_unhalt']
                                    extensions = existing['extensions']
                            else:
                                new_est_unhalt = existing['est_unhalt']
                                extensions = existing['extensions']
                        else:
                            # Reset if resumption time changes
                            new_est_unhalt = res_dt + timedelta(minutes=5)
                            extensions = 0

                    self.halts[symbol] = {
                        'halt_time': halt_dt,
                        'resumption_time': res_dt,
                        'est_unhalt': new_est_unhalt,
                        'extensions': extensions,
                        'last_seen': now
                    }

                except Exception as e:
                    print(f"Error processing {symbol}: {str(e)}")
                    continue

            # Cleanup process
            for symbol in list(self.halts.keys()):
                data = self.halts[symbol]
                elapsed = now - data['est_unhalt']
                
                remove = False
                if symbol not in current_symbols:
                    remove = True
                elif data['extensions'] >= 2 and elapsed > timedelta(minutes=5):
                    remove = True  # 5 minutes past final extension
                elif (now - data['last_seen']) > timedelta(minutes=30):
                    remove = True  # Stale entry
                
                if remove:
                    del self.halts[symbol]

        except Exception as e:
            print(f"Fetch error: {str(e)}")

    def update_display(self):
        now = datetime.now(EST)
        display_lines = []

        for symbol, data in self.halts.items():
            delta = data['est_unhalt'] - now
            total_seconds = delta.total_seconds()

            # Determine status and color
            if total_seconds > 0:
                hours, remainder = divmod(total_seconds, 3600)
                mins, secs = divmod(remainder, 60)
                countdown = f"{int(hours):02}:{int(mins):02}:{int(secs):02}"
                
                if data['extensions'] >= 2:
                    color = "#FF4444"  # Red - final extension
                    countdown += " (FINAL)"
                elif data['extensions'] > 0:
                    color = "#FFD700"  # Gold - extended
                else:
                    color = "#FFFFFF"  # White - initial
            else:
                if data['extensions'] >= 2:
                    countdown = "FINALIZED"
                    color = "#FF4444"
                else:
                    countdown = "PENDING UPDATE"
                    color = "#00FF00"  # Green

            halt_time = data['halt_time'].strftime("%m/%d %H:%M:%S")
            est_unhalt = data['est_unhalt'].strftime("%H:%M:%S")

            display_lines.append(
                f"<span style='color: {color}'>"
                f"{symbol} | {halt_time} → {est_unhalt} | {countdown}"
                f"</span>"
            )

        self.content.setText("<br>".join(display_lines) if display_lines else "No active LUDP halts")
        self.adjustSize()

    def mousePressEvent(self, event):
        self.mouse_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.mouse_pos:
            delta = event.globalPosition().toPoint() - self.mouse_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.mouse_pos = event.globalPosition().toPoint()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = FloatingHaltWidget()
    widget.show()
    sys.exit(app.exec())

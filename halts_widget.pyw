# Halts_widget
# gnu v3 license to share
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
        self.setStyleSheet(
            """
            background-color: rgba(45, 45, 45, 0.9);
            color: #ffffff;
            border-radius: 5px;
            padding: 10px;
            font-family: Segoe UI;
            font-size: 12px;
            """
        )

        self.layout = QVBoxLayout()
        self.title = QLabel("NASDAQ LUDP Halts")
        self.title.setStyleSheet(
            "font-weight: bold; font-size: 14px; margin-bottom: 8px;"
        )
        self.layout.addWidget(self.title)

        self.content = QLabel()
        self.layout.addWidget(self.content)

        self.setLayout(self.layout)
        self.adjustSize()

        screen_geo = QApplication.primaryScreen().availableGeometry()
        self.move(screen_geo.right() - self.width() - 20, 20)

    def init_timers(self):
        # Data refresh every 15 seconds
        self.fetch_timer = QTimer()
        self.fetch_timer.timeout.connect(self.fetch_halts)
        self.fetch_timer.start(15000)

        # UI update every second for smooth countdown
        self.display_timer = QTimer()
        self.display_timer.timeout.connect(self.update_display)
        self.display_timer.start(1000)

        # Initial fetch
        self.fetch_halts()

    def fetch_halts(self):
        try:
            response = requests.get(
                "https://www.nasdaqtrader.com/rss.aspx?feed=tradehalts",
                timeout=10
            )
            soup = BeautifulSoup(response.content, 'xml')

            current_symbols = set()
            for item in soup.find_all('item'):
                if item.find('ndaq:ResumptionTradeTime').text.strip():
                    continue

                if item.find('ndaq:ReasonCode').text.strip().upper() != 'LUDP':
                    continue

                try:
                    symbol = item.find('ndaq:IssueSymbol').text.strip()
                    current_symbols.add(symbol)

                    halt_date = datetime.strptime(
                        item.find('ndaq:HaltDate').text, "%m/%d/%Y"
                    ).date()
                    halt_time = datetime.strptime(
                        item.find('ndaq:HaltTime').text, "%H:%M:%S"
                    ).time()
                    halt_dt = EST.localize(datetime.combine(halt_date, halt_time))

                    res_date = datetime.strptime(
                        item.find('ndaq:ResumptionDate').text, "%m/%d/%Y"
                    ).date()
                    res_time = datetime.strptime(
                        item.find('ndaq:ResumptionQuoteTime').text, "%H:%M:%S"
                    ).time()
                    res_dt = EST.localize(datetime.combine(res_date, res_time))

                    est_unhalt = res_dt + timedelta(minutes=5)

                    self.halts[symbol] = {
                        'halt_time': halt_dt,
                        'est_unhalt': est_unhalt,
                        'last_seen': datetime.now(EST)
                    }
                except Exception as e:
                    print(f"Parse error: {e}")

            # Remove old entries
            for symbol in list(self.halts.keys()):
                if symbol not in current_symbols:
                    del self.halts[symbol]

        except Exception as e:
            print(f"Fetch error: {e}")

    def update_display(self):
        now = datetime.now(EST)
        display_lines = []

        for symbol, data in self.halts.items():
            delta = data['est_unhalt'] - now
            total_seconds = delta.total_seconds()

            if total_seconds > 0:
                hours, remainder = divmod(total_seconds, 3600)
                mins, secs = divmod(remainder, 60)
                countdown = f"{int(mins):02}:{int(secs):02}"
                color = "#FFD700" if total_seconds < 300 else "#FFFFFF"
            else:
                countdown = "UNHALTED?"
                color = "#FF4444"

            halt_time = data['halt_time'].strftime("%H:%M:%S")
            est_unhalt = data['est_unhalt'].strftime("%H:%M:%S")

            display_lines.append(
                f"<span style='color: {color}'>"
                f"{symbol} | {halt_time} → {est_unhalt} | {countdown}"
                f"</span>"
            )

        if not display_lines:
            self.content.setText("No active LUDP halts")
        else:
            self.content.setText("<br>".join(display_lines))

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

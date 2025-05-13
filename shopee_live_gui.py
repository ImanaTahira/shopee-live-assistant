import sys
import json
import os
import requests
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                           QCheckBox, QSpinBox, QTextEdit, QGroupBox,
                           QProgressBar, QMessageBox, QTabWidget, QFileDialog,
                           QTableWidget, QTableWidgetItem, QHeaderView, QDialog)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
import requests
import threading
import importlib.util
import tempfile
from cryptography.fernet import Fernet
import time
import random

def load_encrypted_main():
    """Load encrypted main.py"""
    try:
        # Get encrypted content and key from GitHub
        enc_url = "https://raw.githubusercontent.com/ImanaTahira/shopee-live-assistant/main/main.enc"
        key_url = "https://raw.githubusercontent.com/ImanaTahira/shopee-live-assistant/main/main.key"
        
        response_enc = requests.get(enc_url)
        response_key = requests.get(key_url)
        response_enc.raise_for_status()
        response_key.raise_for_status()
        
        # Decrypt content
        cipher_suite = Fernet(response_key.content)
        decrypted_content = cipher_suite.decrypt(response_enc.content)
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False, mode='wb') as temp_file:
            temp_file.write(decrypted_content)
            temp_path = temp_file.name
        
        # Import module
        spec = importlib.util.spec_from_file_location("main", temp_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Clean up
        os.unlink(temp_path)
        
        print("✅ Berhasil memuat main script terenkripsi")
        return module
    except Exception as e:
        print(f"❌ Gagal memuat main script: {str(e)}")
        return None

# Load encrypted main.py
main_module = load_encrypted_main()
if not main_module:
    print("❌ Gagal memuat main script")
    sys.exit(1)

# Import functions from decrypted main
load_cookies_from_github = main_module.load_cookies_from_github
send_message = main_module.send_message
send_buy = main_module.send_buy
send_follow = main_module.send_follow
send_like = main_module.send_like
TokenBucket = main_module.TokenBucket

class WorkerThread(QThread):
    log = pyqtSignal(str)  # Signal untuk mengirim log ke GUI
    progress = pyqtSignal(int)  # Signal untuk update progress bar
    finished = pyqtSignal()  # Signal ketika thread selesai
    iteration_update = pyqtSignal(int)  # Signal untuk update nomor iterasi

    def __init__(self, cookies_list, actions, kwargs, bucket, parent=None):
        super().__init__(parent)
        self.cookies_list = cookies_list
        self.actions = actions
        self.kwargs = kwargs
        self.bucket = bucket
        self.is_running = True
        self.total_iterations = 0
        self.current_iteration = 0
        self.start_time = None

    def run(self):
        try:
            self.start_time = time.time()
            loop_count = self.kwargs.get("loop_count", 1)
            is_unlimited = loop_count == -1
            iteration = 0

            while self.is_running:
                if not is_unlimited and iteration >= loop_count:
                    self.log.emit(f"✅ Selesai melakukan {loop_count} pengulangan!")
                    break

                current_time = time.time()
                elapsed_time = current_time - self.start_time
                hours = int(elapsed_time // 3600)
                minutes = int((elapsed_time % 3600) // 60)
                seconds = int(elapsed_time % 60)

                self.log.emit(f"\n📍 Pengulangan ke-{iteration + 1}")
                self.log.emit(f"⏱️ Waktu berjalan: {hours:02d}:{minutes:02d}:{seconds:02d}")
                
                if is_unlimited:
                    self.log.emit("🔄 Mode: Pengulangan Tak Terbatas")
                else:
                    remaining = loop_count - iteration
                    self.log.emit(f"🔄 Sisa pengulangan: {remaining}")

                self.process_cookies(self.cookies_list, iteration)
                
                iteration += 1
                self.total_iterations = iteration
                self.iteration_update.emit(iteration)
                
                if self.is_running:
                    delay = self.kwargs.get("delay", 2)
                    self.log.emit(f"💤 Menunggu {delay} detik sebelum pengulangan berikutnya...")
                    time.sleep(delay)

        except Exception as e:
            self.log.emit(f"❌ Error: {str(e)}")
        finally:
            end_time = time.time()
            total_time = end_time - self.start_time
            hours = int(total_time // 3600)
            minutes = int((total_time % 3600) // 60)
            seconds = int(total_time % 60)
            
            self.log.emit("\n📊 Statistik:")
            self.log.emit(f"Total pengulangan: {self.total_iterations}")
            self.log.emit(f"Total waktu: {hours:02d}:{minutes:02d}:{seconds:02d}")
            self.log.emit(f"Total cookies digunakan: {len(self.cookies_list) * self.total_iterations}")
            
            if any(action in self.actions for action in ["send_message", "send_buy", "send_follow", "send_like"]):
                self.log.emit("\nDetail Aksi:")
                if "send_message" in self.actions:
                    self.log.emit(f"✉️ Total pesan terkirim: {len(self.cookies_list) * self.total_iterations}")
                if "send_buy" in self.actions:
                    self.log.emit(f"🛒 Total aksi beli: {len(self.cookies_list) * self.total_iterations}")
                if "send_follow" in self.actions:
                    self.log.emit(f"👥 Total aksi follow: {len(self.cookies_list) * self.total_iterations}")
                if "send_like" in self.actions:
                    self.log.emit(f"👍 Total aksi like: {len(self.cookies_list) * self.total_iterations}")
            
            self.finished.emit()

    def process_cookies(self, cookies_list, thread_id):
        total_cookies = len(cookies_list)
        success_count = 0
        error_count = 0
        
        for i, cookies in enumerate(cookies_list):
            if not self.is_running:
                self.log.emit(f"🛑 Thread {thread_id+1} dihentikan")
                return

            if self.bucket.consume():
                try:
                    if "send_message" in self.actions:
                        messages = self.kwargs.get("messages", [])
                        if messages and self.kwargs.get("uuid") and self.kwargs.get("usersig"):
                            content = random.choice(messages) if self.kwargs.get("use_random") else messages[0]
                            send_message(
                                self.kwargs["session_id"],
                                cookies,
                                self.kwargs["uuid"],
                                self.kwargs["usersig"],
                                content,
                                self.kwargs.get("delay", 2)
                            )
                            self.log.emit(f"✉️ Pesan terkirim: {content[:30]}..." if len(content) > 30 else f"✉️ Pesan terkirim: {content}")
                            success_count += 1

                    if "send_buy" in self.actions:
                        send_buy(
                            self.kwargs["session_id"],
                            cookies,
                            self.kwargs.get("delay", 2)
                        )
                        self.log.emit("🛒 Aksi beli terkirim")
                        success_count += 1

                    if "send_follow" in self.actions and self.kwargs.get("shop_id"):
                        send_follow(
                            self.kwargs["session_id"],
                            self.kwargs["shop_id"],
                            cookies,
                            self.kwargs.get("delay", 2)
                        )
                        self.log.emit("👥 Aksi follow terkirim")
                        success_count += 1

                    if "send_like" in self.actions:
                        send_like(
                            self.kwargs["session_id"],
                            cookies,
                            self.kwargs.get("delay", 2),
                            self.kwargs.get("like_count", 1)
                        )
                        self.log.emit("👍 Aksi like terkirim")
                        success_count += 1

                    # Update progress
                    progress = int((i + 1) / total_cookies * 100)
                    self.progress.emit(progress)

                except Exception as e:
                    self.log.emit(f"⚠️ Error pada cookies {i+1}: {str(e)}")
                    error_count += 1
            else:
                self.log.emit("⚠️ Rate limit tercapai. Menunggu token...")
                time.sleep(1)
        
        # Tampilkan ringkasan untuk pengulangan ini
        self.log.emit(f"\n📌 Ringkasan pengulangan ini:")
        self.log.emit(f"✅ Berhasil: {success_count} aksi")
        self.log.emit(f"❌ Gagal: {error_count} aksi")
        success_rate = (success_count / (success_count + error_count)) * 100 if (success_count + error_count) > 0 else 0
        self.log.emit(f"📊 Tingkat keberhasilan: {success_rate:.1f}%")

    def stop(self):
        self.is_running = False

class SessionConfig:
    def __init__(self, session_id="", thread_count=1, delay=2, actions=None, 
                 message_settings=None, follow_settings=None, like_settings=None):
        self.session_id = session_id
        self.thread_count = thread_count
        self.delay = delay
        self.actions = actions or {"message": False, "buy": False, "follow": False, "like": False}
        
        # Default message settings
        default_message_settings = {
            "uuid": "", 
            "usersig": "", 
            "messages": [""],  # List of messages
            "use_random": False,  # Flag untuk menggunakan pesan random
            "loop_count": 1,  # Jumlah pengulangan (1 = tidak ada pengulangan)
            "content": ""  # Single message content for backward compatibility
        }
        
        # Update dengan settings yang diberikan
        if message_settings:
            # Ensure messages is always a list
            if "messages" not in message_settings:
                message_settings["messages"] = [message_settings.get("content", "")]
            elif isinstance(message_settings["messages"], str):
                message_settings["messages"] = [message_settings["messages"]]
            default_message_settings.update(message_settings)
        self.message_settings = default_message_settings

        # Default follow settings
        default_follow_settings = {
            "shop_id": "",
            "loop_count": 1
        }
        if follow_settings:
            default_follow_settings.update(follow_settings)
        self.follow_settings = default_follow_settings

        # Default like settings
        default_like_settings = {
            "like_count": 1,
            "loop_count": 1
        }
        if like_settings:
            default_like_settings.update(like_settings)
        self.like_settings = default_like_settings

        # Default buy settings
        self.buy_settings = {
            "loop_count": 1
        }

        self.is_running = False
        self.worker = None

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Shopee Live Assistant Pro - Multi Session")
        self.setMinimumWidth(1200)
        self.setMinimumHeight(800)
        self.config_file = "config.json"
        self.sessions = []
        self.cookies_list = []  # Initialize cookies list
        self.bucket = TokenBucket(rate=1, capacity=5)  # Initialize rate limiter
        
        # Load cookies at startup
        try:
            self.cookies_list = load_cookies_from_github("https://raw.githubusercontent.com/ImanaTahira/my-cookies/main/cookies.txt")
            print(f"✅ Berhasil memuat {len(self.cookies_list)} cookies")
        except Exception as e:
            print(f"❌ Gagal memuat cookies: {str(e)}")
            QMessageBox.warning(self, "Error", "Gagal memuat cookies. Pastikan koneksi internet Anda aktif.")
        
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Add Multi Session Tab
        multi_session_tab = QWidget()
        multi_session_layout = QVBoxLayout(multi_session_tab)
        
        # Session Table
        self.session_table = QTableWidget()
        self.session_table.setColumnCount(8)
        self.session_table.setHorizontalHeaderLabels([
            "Session ID", "Thread", "Delay", "Actions", "Status", "Progress", "Controls", "Log"
        ])
        header = self.session_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        multi_session_layout.addWidget(self.session_table)

        # Add Session Controls
        controls_layout = QHBoxLayout()
        
        # Add Session Button
        add_session_button = QPushButton("Tambah Sesi")
        add_session_button.clicked.connect(self.add_session_to_table)
        controls_layout.addWidget(add_session_button)

        # Start All Button
        self.start_all_button = QPushButton("Mulai Semua")
        self.start_all_button.clicked.connect(self.start_all_sessions)
        controls_layout.addWidget(self.start_all_button)

        # Stop All Button
        self.stop_all_button = QPushButton("Stop Semua")
        self.stop_all_button.clicked.connect(self.stop_all_sessions)
        self.stop_all_button.setEnabled(False)
        controls_layout.addWidget(self.stop_all_button)

        multi_session_layout.addLayout(controls_layout)
        
        self.tab_widget.addTab(multi_session_tab, "Multi Session")

        # Add Help Tab
        help_tab = QWidget()
        help_layout = QVBoxLayout(help_tab)
        
        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setFont(QFont("Arial", 10))
        
        help_content = """
        <h2>Panduan Penggunaan Shopee Live Assistant Pro</h2>
        
        <h3>1. Fitur Utama</h3>
        <ul>
            <li>Multi-session: Menjalankan beberapa sesi Shopee Live sekaligus</li>
            <li>Manajemen thread: Mengatur jumlah thread per sesi</li>
            <li>Rate limiting: Mencegah pemblokiran dengan pengaturan delay</li>
            <li>Penyimpanan konfigurasi: Menyimpan dan memuat pengaturan</li>
        </ul>

        <h3>2. Cara Menambah Sesi Baru</h3>
        <ol>
            <li>Klik tombol "Tambah Sesi"</li>
            <li>Isi Session ID dari live streaming</li>
            <li>Atur jumlah thread (1-10)</li>
            <li>Atur delay antar aksi (1-60 detik)</li>
            <li>Pilih aksi yang diinginkan (Pesan, Beli, Follow, Like)</li>
        </ol>

        <h3>3. Pengaturan Per Aksi (⚙️)</h3>
        <ul>
            <li><b>Pengaturan Pesan:</b>
                <ul>
                    <li>UUID: ID unik dari sesi live</li>
                    <li>UserSig: Signature pengguna</li>
                    <li>Isi Pesan: Pesan yang akan dikirim</li>
                </ul>
            </li>
            <li><b>Pengaturan Follow:</b>
                <ul>
                    <li>Shop ID: ID toko yang akan di-follow</li>
                </ul>
            </li>
            <li><b>Pengaturan Like:</b>
                <ul>
                    <li>Jumlah Like: Berapa kali mengirim like</li>
                </ul>
            </li>
        </ul>

        <h3>4. Kontrol Sesi</h3>
        <ul>
            <li>▶️ (Mulai): Menjalankan sesi</li>
            <li>⏹️ (Stop): Menghentikan sesi</li>
            <li>⚙️ (Pengaturan): Mengatur detail aksi</li>
            <li>🗑️ (Hapus): Menghapus sesi</li>
        </ul>

        <h3>5. Kontrol Global</h3>
        <ul>
            <li>"Mulai Semua": Menjalankan semua sesi</li>
            <li>"Stop Semua": Menghentikan semua sesi</li>
            <li>"Simpan Config": Menyimpan pengaturan</li>
            <li>"Load Config": Memuat pengaturan</li>
        </ul>

        <h3>6. Monitoring</h3>
        <ul>
            <li>Status: Menampilkan status sesi (Siap/Berjalan/Selesai)</li>
            <li>Progress: Menunjukkan kemajuan proses</li>
            <li>Log: Menampilkan detail aktivitas dan error</li>
        </ul>

        <h3>7. Tips Penggunaan</h3>
        <ul>
            <li>Gunakan delay yang sesuai untuk menghindari pemblokiran</li>
            <li>Simpan konfigurasi setelah pengaturan selesai</li>
            <li>Pantau log untuk memastikan semua berjalan lancar</li>
            <li>Gunakan jumlah thread sesuai kebutuhan</li>
        </ul>

        <h3>8. Peringatan</h3>
        <ul>
            <li>Pastikan Session ID valid sebelum memulai</li>
            <li>Jangan menggunakan delay terlalu cepat</li>
            <li>Perhatikan penggunaan CPU dan memori</li>
            <li>Backup konfigurasi penting secara berkala</li>
        </ul>
        """
        
        help_text.setHtml(help_content)
        help_layout.addWidget(help_text)
        
        self.tab_widget.addTab(help_tab, "Bantuan")
        
        layout.addWidget(self.tab_widget)

        # Config Buttons Layout
        config_buttons_layout = QHBoxLayout()
        
        # Save Config Button
        self.save_config_button = QPushButton("Simpan Config")
        self.save_config_button.clicked.connect(self.save_config_dialog)
        config_buttons_layout.addWidget(self.save_config_button)

        # Load Config Button
        self.load_config_button = QPushButton("Load Config")
        self.load_config_button.clicked.connect(self.load_config_dialog)
        config_buttons_layout.addWidget(self.load_config_button)

        layout.addLayout(config_buttons_layout)

        self.load_config()  # Load config setelah UI diinisialisasi

    def update_ui_state(self):
        """Update status UI berdasarkan checkbox yang dipilih"""
        pass  # Tidak perlu mengupdate UI karena sudah menggunakan multi-session

    def log_message(self, message):
        self.log_area.append(message)
        # Auto-scroll to bottom
        scrollbar = self.log_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def process_finished(self):
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.log_message("✅ Proses selesai!")
        QMessageBox.information(self, "Selesai", "Semua tugas telah selesai dijalankan!")

    def stop_process(self):
        if hasattr(self, 'worker'):
            self.worker.stop()
            self.log_message("🔴 Menghentikan proses...")
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)

    def start_process(self):
        session_id = self.session_id_input.text().strip()
        if not session_id:
            QMessageBox.warning(self, "Peringatan", "Session ID tidak boleh kosong!")
            return

        actions = []
        if self.message_check.isChecked():
            if not all([self.uuid_input.text(), self.usersig_input.text(), self.content_input.toPlainText()]):
                QMessageBox.warning(self, "Peringatan", "UUID, UserSig, dan isi pesan harus diisi untuk mengirim pesan!")
                return
            actions.append("send_message")
            
        if self.buy_check.isChecked():
            actions.append("send_buy")
            
        if self.follow_check.isChecked():
            if not self.shop_id_input.text():
                QMessageBox.warning(self, "Peringatan", "Shop ID harus diisi untuk melakukan follow!")
                return
            actions.append("send_follow")

        if self.like_check.isChecked():
            actions.append("send_like")

        if not actions:
            QMessageBox.warning(self, "Peringatan", "Pilih minimal satu aksi!")
            return

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress_bar.setValue(0)
        self.log_area.clear()

        # Create and start worker thread
        self.worker = WorkerThread(
            cookies_list=self.sessions[self.session_table.currentRow()].message_settings["messages"],
            actions=actions,
            kwargs={
                "session_id": session_id,
                "uuid": self.sessions[self.session_table.currentRow()].message_settings["uuid"],
                "usersig": self.sessions[self.session_table.currentRow()].message_settings["usersig"],
                "content": self.sessions[self.session_table.currentRow()].message_settings["content"],
                "shop_id": self.sessions[self.session_table.currentRow()].follow_settings["shop_id"],
                "like_count": self.sessions[self.session_table.currentRow()].like_settings["like_count"],
                "loop_count": self.sessions[self.session_table.currentRow()].message_settings["loop_count"],
                "use_random": self.sessions[self.session_table.currentRow()].message_settings["use_random"],
                "messages": self.sessions[self.session_table.currentRow()].message_settings["messages"],
                "delay": self.sessions[self.session_table.currentRow()].delay
            },
            bucket=self.sessions[self.session_table.currentRow()].bucket
        )
        
        self.worker.progress.connect(self.update_progress)
        self.worker.log.connect(self.log_message)
        self.worker.finished.connect(self.process_finished)
        self.worker.iteration_update.connect(self.update_iteration)
        self.worker.start()

    def save_config_dialog(self):
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Simpan Konfigurasi",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        if file_name:
            self.save_config(file_name)

    def load_config_dialog(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Load Konfigurasi",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        if file_name:
            self.load_config(file_name)

    def save_config(self, file_path=None):
        """Menyimpan konfigurasi ke file JSON"""
        config = {
            "multi_sessions": []
        }

        # Save multi-session configurations
        for row in range(self.session_table.rowCount()):
            session_config = {
                "session_id": self.session_table.cellWidget(row, 0).text(),
                "thread_count": self.session_table.cellWidget(row, 1).value(),
                "delay": self.session_table.cellWidget(row, 2).value(),
                "actions": {
                    "message": self.session_table.cellWidget(row, 3).layout().itemAt(0).widget().isChecked(),
                    "buy": self.session_table.cellWidget(row, 3).layout().itemAt(1).widget().isChecked(),
                    "follow": self.session_table.cellWidget(row, 3).layout().itemAt(2).widget().isChecked(),
                    "like": self.session_table.cellWidget(row, 3).layout().itemAt(3).widget().isChecked()
                },
                "message_settings": self.sessions[row].message_settings,
                "follow_settings": self.sessions[row].follow_settings,
                "like_settings": self.sessions[row].like_settings
            }
            config["multi_sessions"].append(session_config)

        try:
            save_path = file_path if file_path else self.config_file
            with open(save_path, 'w') as f:
                json.dump(config, f, indent=4)
            QMessageBox.information(self, "Sukses", f"Konfigurasi berhasil disimpan ke {save_path}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Gagal menyimpan konfigurasi: {str(e)}")

    def load_config(self, file_path=None):
        """Memuat konfigurasi dari file JSON"""
        try:
            load_path = file_path if file_path else self.config_file
            if not os.path.exists(load_path):
                if file_path:
                    QMessageBox.warning(self, "Error", f"File konfigurasi tidak ditemukan: {load_path}")
                return

            with open(load_path, 'r') as f:
                config = json.load(f)

            # Load multi-session configurations
            if "multi_sessions" in config:
                # Clear existing sessions
                while self.session_table.rowCount() > 0:
                    self.session_table.removeRow(0)
                self.sessions.clear()

                # Add saved sessions
                for session_config in config["multi_sessions"]:
                    self.add_session_to_table()
                    row = self.session_table.rowCount() - 1

                    # Set basic settings
                    self.session_table.cellWidget(row, 0).setText(session_config["session_id"])
                    self.session_table.cellWidget(row, 1).setValue(session_config["thread_count"])
                    self.session_table.cellWidget(row, 2).setValue(session_config["delay"])

                    # Set actions
                    actions = session_config["actions"]
                    actions_widget = self.session_table.cellWidget(row, 3)
                    actions_widget.layout().itemAt(0).widget().setChecked(actions["message"])
                    actions_widget.layout().itemAt(1).widget().setChecked(actions["buy"])
                    actions_widget.layout().itemAt(2).widget().setChecked(actions["follow"])
                    actions_widget.layout().itemAt(3).widget().setChecked(actions["like"])

                    # Set advanced settings
                    self.sessions[row].message_settings = session_config["message_settings"]
                    self.sessions[row].follow_settings = session_config["follow_settings"]
                    self.sessions[row].like_settings = session_config["like_settings"]

            if file_path:
                QMessageBox.information(self, "Sukses", f"Konfigurasi berhasil dimuat dari {load_path}")
        except Exception as e:
            if file_path:
                QMessageBox.warning(self, "Error", f"Gagal memuat konfigurasi: {str(e)}")

    def add_session_to_table(self):
        """Menambahkan sesi baru ke tabel"""
        current_row = self.session_table.rowCount()
        self.session_table.insertRow(current_row)
        
        # Session ID
        session_id_input = QLineEdit()
        self.session_table.setCellWidget(current_row, 0, session_id_input)
        
        # Thread Count
        thread_count = QSpinBox()
        thread_count.setRange(1, 10)
        thread_count.setValue(1)
        self.session_table.setCellWidget(current_row, 1, thread_count)
        
        # Delay
        delay_input = QSpinBox()
        delay_input.setRange(1, 60)
        delay_input.setValue(2)
        self.session_table.setCellWidget(current_row, 2, delay_input)
        
        # Actions Container
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        
        message_check = QCheckBox("Pesan")
        buy_check = QCheckBox("Beli")
        follow_check = QCheckBox("Follow")
        like_check = QCheckBox("Like")
        
        actions_layout.addWidget(message_check)
        actions_layout.addWidget(buy_check)
        actions_layout.addWidget(follow_check)
        actions_layout.addWidget(like_check)
        
        self.session_table.setCellWidget(current_row, 3, actions_widget)
        
        # Status
        status_label = QLabel("Siap")
        self.session_table.setCellWidget(current_row, 4, status_label)
        
        # Progress
        progress = QProgressBar()
        self.session_table.setCellWidget(current_row, 5, progress)
        
        # Controls Container
        controls_widget = QWidget()
        controls_layout = QHBoxLayout(controls_widget)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        
        settings_button = QPushButton("⚙️")
        settings_button.setToolTip("Pengaturan")
        settings_button.clicked.connect(lambda: self.show_session_settings(current_row))
        
        start_button = QPushButton("▶️")
        start_button.setToolTip("Mulai")
        start_button.clicked.connect(lambda: self.start_session(current_row))
        
        stop_button = QPushButton("⏹️")
        stop_button.setToolTip("Stop")
        stop_button.setEnabled(False)
        stop_button.clicked.connect(lambda: self.stop_session(current_row))
        
        delete_button = QPushButton("🗑️")
        delete_button.setToolTip("Hapus")
        delete_button.clicked.connect(lambda: self.delete_session(current_row))
        
        controls_layout.addWidget(settings_button)
        controls_layout.addWidget(start_button)
        controls_layout.addWidget(stop_button)
        controls_layout.addWidget(delete_button)
        
        self.session_table.setCellWidget(current_row, 6, controls_widget)
        
        # Log
        log_text = QTextEdit()
        log_text.setReadOnly(True)
        self.session_table.setCellWidget(current_row, 7, log_text)

        # Create and store session configuration
        session_config = SessionConfig()
        self.sessions.append(session_config)

    def show_session_settings(self, row):
        """Menampilkan dialog pengaturan untuk sesi tertentu"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Pengaturan Sesi")
        dialog.setMinimumWidth(400)
        layout = QVBoxLayout(dialog)

        # Message Settings
        message_group = QGroupBox("Pengaturan Pesan")
        message_layout = QVBoxLayout()
        
        uuid_layout = QHBoxLayout()
        uuid_label = QLabel("UUID:")
        uuid_input = QLineEdit()
        uuid_input.setText(self.sessions[row].message_settings["uuid"])
        uuid_layout.addWidget(uuid_label)
        uuid_layout.addWidget(uuid_input)
        
        usersig_layout = QHBoxLayout()
        usersig_label = QLabel("UserSig:")
        usersig_input = QLineEdit()
        usersig_input.setText(self.sessions[row].message_settings["usersig"])
        usersig_layout.addWidget(usersig_label)
        usersig_layout.addWidget(usersig_input)
        
        content_label = QLabel("Isi Pesan:")
        content_input = QTextEdit()
        content_input.setPlainText(self.sessions[row].message_settings["content"])
        content_input.setMaximumHeight(100)
        
        message_layout.addLayout(uuid_layout)
        message_layout.addLayout(usersig_layout)
        message_layout.addWidget(content_label)
        message_layout.addWidget(content_input)
        message_group.setLayout(message_layout)
        layout.addWidget(message_group)

        # Follow Settings
        follow_group = QGroupBox("Pengaturan Follow")
        follow_layout = QVBoxLayout()
        
        shop_id_layout = QHBoxLayout()
        shop_id_label = QLabel("Shop ID:")
        shop_id_input = QLineEdit()
        shop_id_input.setText(self.sessions[row].follow_settings["shop_id"])
        shop_id_layout.addWidget(shop_id_label)
        shop_id_layout.addWidget(shop_id_input)
        
        follow_layout.addLayout(shop_id_layout)
        follow_group.setLayout(follow_layout)
        layout.addWidget(follow_group)

        # Like Settings
        like_group = QGroupBox("Pengaturan Like")
        like_layout = QVBoxLayout()
        
        like_count_layout = QHBoxLayout()
        like_count_label = QLabel("Jumlah Like:")
        like_count_input = QSpinBox()
        like_count_input.setRange(1, 100)
        like_count_input.setValue(self.sessions[row].like_settings["like_count"])
        like_count_layout.addWidget(like_count_label)
        like_count_layout.addWidget(like_count_input)
        
        like_layout.addLayout(like_count_layout)
        like_group.setLayout(like_layout)
        layout.addWidget(like_group)

        # Save Button
        save_button = QPushButton("Simpan")
        save_button.clicked.connect(lambda: self.save_session_settings(
            row, uuid_input.text(), usersig_input.text(), content_input.toPlainText(),
            shop_id_input.text(), like_count_input.value(), dialog
        ))
        layout.addWidget(save_button)

        dialog.exec()

    def save_session_settings(self, row, uuid, usersig, content, shop_id, like_count, dialog):
        """Menyimpan pengaturan sesi"""
        # Split content into messages if it contains newlines
        messages = [msg.strip() for msg in content.split('\n') if msg.strip()]
        if not messages:
            messages = [""]  # Ensure at least one empty message
            
        self.sessions[row].message_settings.update({
            "uuid": uuid,
            "usersig": usersig,
            "content": messages[0],  # Keep first message as content for backward compatibility
            "messages": messages,
            "use_random": len(messages) > 1  # Enable random if multiple messages
        })
        self.sessions[row].follow_settings.update({
            "shop_id": shop_id
        })
        self.sessions[row].like_settings.update({
            "like_count": like_count
        })
        dialog.accept()

    def start_session(self, row):
        """Memulai sesi tertentu"""
        session = self.sessions[row]
        if session.is_running:
            return

        # Get values from table
        session_id = self.session_table.cellWidget(row, 0).text()
        thread_count = self.session_table.cellWidget(row, 1).value()
        delay = self.session_table.cellWidget(row, 2).value()
        
        actions_widget = self.session_table.cellWidget(row, 3)
        actions = []
        if actions_widget.layout().itemAt(0).widget().isChecked():  # Message
            actions.append("send_message")
        if actions_widget.layout().itemAt(1).widget().isChecked():  # Buy
            actions.append("send_buy")
        if actions_widget.layout().itemAt(2).widget().isChecked():  # Follow
            actions.append("send_follow")
        if actions_widget.layout().itemAt(3).widget().isChecked():  # Like
            actions.append("send_like")

        if not session_id:
            QMessageBox.warning(self, "Peringatan", f"Session ID untuk baris {row + 1} tidak boleh kosong!")
            return

        if not actions:
            QMessageBox.warning(self, "Peringatan", f"Pilih minimal satu aksi untuk baris {row + 1}!")
            return

        if not self.cookies_list:
            QMessageBox.warning(self, "Peringatan", "Tidak ada cookies yang dimuat!")
            return

        # Create and start worker
        session.worker = WorkerThread(
            cookies_list=self.cookies_list,
            actions=actions,
            kwargs={
                "session_id": session_id,
                "uuid": session.message_settings["uuid"],
                "usersig": session.message_settings["usersig"],
                "messages": session.message_settings["messages"],
                "use_random": session.message_settings["use_random"],
                "loop_count": session.message_settings["loop_count"],
                "delay": delay,
                "shop_id": session.follow_settings["shop_id"],
                "like_count": session.like_settings["like_count"]
            },
            bucket=self.bucket
        )

        # Connect signals
        progress_bar = self.session_table.cellWidget(row, 5)
        log_text = self.session_table.cellWidget(row, 7)
        status_label = self.session_table.cellWidget(row, 4)
        
        session.worker.progress.connect(progress_bar.setValue)
        session.worker.log.connect(lambda msg: log_text.append(msg))
        session.worker.finished.connect(lambda: self.session_finished(row))
        session.worker.iteration_update.connect(lambda count: status_label.setText(f"Berjalan (Iterasi {count})"))

        # Update UI
        controls = self.session_table.cellWidget(row, 6)
        controls.layout().itemAt(1).widget().setEnabled(False)  # Start button
        controls.layout().itemAt(2).widget().setEnabled(True)   # Stop button
        status_label.setText("Berjalan")
        
        session.is_running = True
        session.worker.start()

        # Update global controls
        self.update_global_controls()

    def session_finished(self, row):
        """Callback ketika sesi selesai"""
        session = self.sessions[row]
        session.is_running = False
        
        # Update UI
        controls = self.session_table.cellWidget(row, 6)
        controls.layout().itemAt(1).widget().setEnabled(True)   # Start button
        controls.layout().itemAt(2).widget().setEnabled(False)  # Stop button
        
        status_label = self.session_table.cellWidget(row, 4)
        status_label.setText("Selesai")
        
        # Update global controls
        self.update_global_controls()

    def stop_session(self, row):
        """Menghentikan sesi tertentu"""
        session = self.sessions[row]
        if session.worker and session.is_running:
            session.worker.stop()
            session.is_running = False
            
            # Update UI
            controls = self.session_table.cellWidget(row, 6)
            controls.layout().itemAt(1).widget().setEnabled(True)   # Start button
            controls.layout().itemAt(2).widget().setEnabled(False)  # Stop button
            
            status_label = self.session_table.cellWidget(row, 4)
            status_label.setText("Dihentikan")
            
            # Update global controls
            self.update_global_controls()

    def delete_session(self, row):
        """Menghapus sesi dari tabel"""
        if self.sessions[row].is_running:
            QMessageBox.warning(self, "Peringatan", "Hentikan sesi terlebih dahulu sebelum menghapus!")
            return
            
        self.session_table.removeRow(row)
        del self.sessions[row]

    def start_all_sessions(self):
        """Memulai semua sesi"""
        for row in range(self.session_table.rowCount()):
            if not self.sessions[row].is_running:
                self.start_session(row)

    def stop_all_sessions(self):
        """Menghentikan semua sesi"""
        for row in range(self.session_table.rowCount()):
            if self.sessions[row].is_running:
                self.stop_session(row)

    def update_global_controls(self):
        """Update tombol global berdasarkan status sesi"""
        any_running = any(session.is_running for session in self.sessions)
        self.start_all_button.setEnabled(not any_running)
        self.stop_all_button.setEnabled(any_running)

    def update_iteration(self, iteration):
        self.iteration_label.setText(f"Iterasi ke-{iteration}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec()) 
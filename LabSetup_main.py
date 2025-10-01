import sys
import random
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTabWidget, QGroupBox, QPushButton, 
                             QLabel, QSlider, QSpinBox, QDoubleSpinBox, 
                             QTextEdit, QProgressBar, QComboBox, QCheckBox,
                             QTableWidget, QTableWidgetItem, QSplitter)
from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QFont
import pyqtgraph as pg
import numpy as np
from datetime import datetime
import json

class SerialSimulator:
    """Имитатор связи с Arduino"""
    def __init__(self):
        self.connected = False
        self.data_callbacks = []
        self.timer = QTimer()
        self.timer.timeout.connect(self.generate_data)
        self.experiment_running = False
        
    def connect(self):
        self.connected = True
        print("Подключено к Arduino (имитация)")
        return True
        
    def disconnect(self):
        self.connected = False
        self.timer.stop()
        print("Отключено от Arduino")
        
    def start_experiment(self):
        self.experiment_running = True
        self.timer.start(100)  # Данные каждые 100мс
        print("Эксперимент запущен")
        
    def stop_experiment(self):
        self.experiment_running = False
        self.timer.stop()
        print("Эксперимент остановлен")
        
    def add_data_callback(self, callback):
        self.data_callbacks.append(callback)
        
    def generate_data(self):
        if not self.experiment_running:
            return
            
        # Генерация имитационных данных
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        laser_power = random.uniform(95, 105)  # мВт
        temperature = random.uniform(22.5, 23.5)  #°C
        intensity = random.uniform(0.8, 1.2)  # относительная интенсивность
        exposure_time = random.randint(45, 55)  # сек
        
        data = {
            'timestamp': timestamp,
            'laser_power': laser_power,
            'temperature': temperature,
            'intensity': intensity,
            'exposure_time': exposure_time
        }
        
        for callback in self.data_callbacks:
            callback(data)

class EquipmentControlTab(QWidget):
    """Вкладка управления оборудованием"""
    def __init__(self, serial_sim):
        super().__init__()
        self.serial_sim = serial_sim
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout()
        
        # Левая панель - управление лазером
        laser_group = QGroupBox("Управление лазером")
        laser_layout = QVBoxLayout()
        
        self.laser_power_slider = QSlider(Qt.Orientation.Horizontal)
        self.laser_power_slider.setRange(0, 200)  # мВт
        self.laser_power_slider.setValue(100)
        self.laser_power_label = QLabel("Мощность: 100 мВт")
        
        self.laser_status_btn = QPushButton("Включить лазер")
        self.laser_status_btn.setCheckable(True)
        self.laser_status_btn.clicked.connect(self.toggle_laser)
        
        laser_layout.addWidget(QLabel("Мощность лазера:"))
        laser_layout.addWidget(self.laser_power_slider)
        laser_layout.addWidget(self.laser_power_label)
        laser_layout.addWidget(self.laser_status_btn)
        laser_group.setLayout(laser_layout)
        
        # Правая панель - управление экспозицией
        exposure_group = QGroupBox("Управление экспозицией")
        exposure_layout = QVBoxLayout()
        
        self.exposure_time_spin = QSpinBox()
        self.exposure_time_spin.setRange(1, 300)
        self.exposure_time_spin.setValue(60)
        self.exposure_time_spin.setSuffix(" сек")
        
        self.start_exposure_btn = QPushButton("Начать экспозицию")
        self.start_exposure_btn.clicked.connect(self.start_exposure)
        
        self.exposure_progress = QProgressBar()
        self.exposure_progress.setValue(0)
        
        exposure_layout.addWidget(QLabel("Время экспозиции:"))
        exposure_layout.addWidget(self.exposure_time_spin)
        exposure_layout.addWidget(self.start_exposure_btn)
        exposure_layout.addWidget(self.exposure_progress)
        exposure_group.setLayout(exposure_layout)
        
        layout.addWidget(laser_group)
        layout.addWidget(exposure_group)
        self.setLayout(layout)
        
    def toggle_laser(self, checked):
        if checked:
            self.laser_status_btn.setText("Выключить лазер")
            self.laser_status_btn.setStyleSheet("background-color: #ff4444; color: white;")
        else:
            self.laser_status_btn.setText("Включить лазер")
            self.laser_status_btn.setStyleSheet("")
            
    def start_exposure(self):
        exposure_time = self.exposure_time_spin.value()
        self.exposure_progress.setValue(0)
        
        # Имитация прогресса экспозиции
        self.exposure_timer = QTimer()
        self.exposure_timer.timeout.connect(self.update_exposure_progress)
        self.exposure_timer.start(1000)  # Обновление каждую секунду
        self.exposure_start_time = datetime.now()
        
    def update_exposure_progress(self):
        elapsed = (datetime.now() - self.exposure_start_time).total_seconds()
        total_time = self.exposure_time_spin.value()
        progress = int((elapsed / total_time) * 100)
        
        if progress >= 100:
            self.exposure_progress.setValue(100)
            self.exposure_timer.stop()
            print("Экспозиция завершена!")
        else:
            self.exposure_progress.setValue(progress)

class RealTimeMonitorTab(QWidget):
    """Вкладка мониторинга в реальном времени"""
    data_updated = pyqtSignal(dict)
    
    def __init__(self, serial_sim):
        super().__init__()
        self.serial_sim = serial_sim
        self.data_points = []
        self.setup_ui()
        self.setup_plots()
        
        # Подключаемся к имитатору данных
        self.serial_sim.add_data_callback(self.on_new_data)
        
    def setup_ui(self):
        main_layout = QHBoxLayout()
        
        # Левая часть - графики
        plots_widget = QWidget()
        plots_layout = QVBoxLayout()
        
        # График интенсивности
        self.intensity_plot = pg.PlotWidget(title="Интенсивность сигнала в реальном времени")
        self.intensity_curve = self.intensity_plot.plot(pen='y')
        
        # График температуры
        self.temp_plot = pg.PlotWidget(title="Температура")
        self.temp_curve = self.temp_plot.plot(pen='r')
        
        plots_layout.addWidget(self.intensity_plot)
        plots_layout.addWidget(self.temp_plot)
        plots_widget.setLayout(plots_layout)
        
        # Правая часть - цифровые показания
        readings_widget = QWidget()
        readings_layout = QVBoxLayout()
        
        # Показания в реальном времени
        readings_group = QGroupBox("Текущие показания")
        readings_inner_layout = QVBoxLayout()
        
        self.laser_power_label = QLabel("Мощность лазера: -- мВт")
        self.temperature_label = QLabel("Температура: -- °C")
        self.intensity_label = QLabel("Интенсивность: --")
        self.time_label = QLabel("Время: --")
        
        readings_inner_layout.addWidget(self.laser_power_label)
        readings_inner_layout.addWidget(self.temperature_label)
        readings_inner_layout.addWidget(self.intensity_label)
        readings_inner_layout.addWidget(self.time_label)
        
        readings_group.setLayout(readings_inner_layout)
        readings_layout.addWidget(readings_group)
        
        # Лог событий
        log_group = QGroupBox("Лог событий")
        log_layout = QVBoxLayout()
        self.event_log = QTextEdit()
        self.event_log.setMaximumHeight(200)
        log_layout.addWidget(self.event_log)
        log_group.setLayout(log_layout)
        
        readings_layout.addWidget(log_group)
        readings_layout.addStretch()
        readings_widget.setLayout(readings_layout)
        
        main_layout.addWidget(plots_widget, 2)
        main_layout.addWidget(readings_widget, 1)
        self.setLayout(main_layout)
        
    def setup_plots(self):
        # Настраиваем графики
        self.intensity_plot.setLabel('left', 'Интенсивность', units='a.u.')
        self.intensity_plot.setLabel('bottom', 'Время', units='сек')
        self.temp_plot.setLabel('left', 'Температура', units='°C')
        self.temp_plot.setLabel('bottom', 'Время', units='сек')
        
        self.time_data = []
        self.intensity_data = []
        self.temp_data = []
        
    def on_new_data(self, data):
        # Обновляем цифровые показания
        self.laser_power_label.setText(f"Мощность лазера: {data['laser_power']:.1f} мВт")
        self.temperature_label.setText(f"Температура: {data['temperature']:.1f} °C")
        self.intensity_label.setText(f"Интенсивность: {data['intensity']:.3f}")
        self.time_label.setText(f"Время: {data['timestamp']}")
        
        # Добавляем в лог
        if len(self.time_data) % 10 == 0:  # Логируем каждые 10 точек
            self.event_log.append(f"{data['timestamp']} - Интенсивность: {data['intensity']:.3f}")
            
        # Обновляем графики
        current_time = len(self.time_data) * 0.1  # 100мс между точками
        
        self.time_data.append(current_time)
        self.intensity_data.append(data['intensity'])
        self.temp_data.append(data['temperature'])
        
        # Ограничиваем количество точек на графике
        max_points = 100
        if len(self.time_data) > max_points:
            self.time_data = self.time_data[-max_points:]
            self.intensity_data = self.intensity_data[-max_points:]
            self.temp_data = self.temp_data[-max_points:]
            
        self.intensity_curve.setData(self.time_data, self.intensity_data)
        self.temp_curve.setData(self.time_data, self.temp_data)

class ExperimentManagerTab(QWidget):
    """Вкладка управления экспериментами"""
    def __init__(self, serial_sim):
        super().__init__()
        self.serial_sim = serial_sim
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Панель управления экспериментом
        control_group = QGroupBox("Управление экспериментом")
        control_layout = QHBoxLayout()
        
        self.experiment_name = QComboBox()
        self.experiment_name.addItems(["Калибровка", "Измерение поглощения", "Фотополимеризация"])
        
        self.start_experiment_btn = QPushButton("Запуск эксперимента")
        self.start_experiment_btn.clicked.connect(self.start_experiment)
        
        self.stop_experiment_btn = QPushButton("Остановить")
        self.stop_experiment_btn.clicked.connect(self.stop_experiment)
        self.stop_experiment_btn.setEnabled(False)
        
        control_layout.addWidget(QLabel("Тип эксперимента:"))
        control_layout.addWidget(self.experiment_name)
        control_layout.addWidget(self.start_experiment_btn)
        control_layout.addWidget(self.stop_experiment_btn)
        control_layout.addStretch()
        control_group.setLayout(control_layout)
        
        # Таблица параметров
        params_group = QGroupBox("Параметры эксперимента")
        params_layout = QVBoxLayout()
        
        self.params_table = QTableWidget()
        self.params_table.setColumnCount(3)
        self.params_table.setHorizontalHeaderLabels(["Параметр", "Значение", "Единицы"])
        self.setup_parameters_table()
        
        params_layout.addWidget(self.params_table)
        params_group.setLayout(params_layout)
        
        layout.addWidget(control_group)
        layout.addWidget(params_group)
        self.setLayout(layout)
        
    def setup_parameters_table(self):
        parameters = [
            ["Мощность лазера", "100", "мВт"],
            ["Время экспозиции", "60", "сек"],
            ["Температура", "23.0", "°C"],
            ["Частота дискретизации", "10", "Гц"]
        ]
        
        self.params_table.setRowCount(len(parameters))
        for i, (param, value, unit) in enumerate(parameters):
            self.params_table.setItem(i, 0, QTableWidgetItem(param))
            self.params_table.setItem(i, 1, QTableWidgetItem(value))
            self.params_table.setItem(i, 2, QTableWidgetItem(unit))
            
    def start_experiment(self):
        experiment_type = self.experiment_name.currentText()
        print(f"Запуск эксперимента: {experiment_type}")
        
        self.start_experiment_btn.setEnabled(False)
        self.stop_experiment_btn.setEnabled(True)
        
        # Запускаем имитатор
        self.serial_sim.start_experiment()
        
    def stop_experiment(self):
        print("Эксперимент остановлен")
        
        self.start_experiment_btn.setEnabled(True)
        self.stop_experiment_btn.setEnabled(False)
        
        self.serial_sim.stop_experiment()

class OpticalLabApp(QMainWindow):
    """Главное окно приложения"""
    def __init__(self):
        super().__init__()
        self.serial_sim = SerialSimulator()
        self.setup_ui()
        self.setup_serial()
        
    def setup_ui(self):
        self.setWindowTitle("Оптическая лаборатория - Система управления")
        self.setGeometry(100, 100, 1200, 800)
        
        # Центральный виджет с вкладками
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Панель статуса
        self.status_label = QLabel("Готов к работе")
        layout.addWidget(self.status_label)
        
        # Вкладки
        self.tabs = QTabWidget()
        
        self.equipment_tab = EquipmentControlTab(self.serial_sim)
        self.monitor_tab = RealTimeMonitorTab(self.serial_sim)
        self.experiment_tab = ExperimentManagerTab(self.serial_sim)
        
        self.tabs.addTab(self.equipment_tab, "Управление оборудованием")
        self.tabs.addTab(self.monitor_tab, "Мониторинг в реальном времени")
        self.tabs.addTab(self.experiment_tab, "Управление экспериментами")
        
        layout.addWidget(self.tabs)
        
        # Нижняя панель с кнопками
        bottom_layout = QHBoxLayout()
        
        self.connect_btn = QPushButton("Подключить оборудование")
        self.connect_btn.clicked.connect(self.toggle_connection)
        
        self.emergency_stop_btn = QPushButton("АВАРИЙНАЯ ОСТАНОВКА")
        self.emergency_stop_btn.setStyleSheet("background-color: red; color: white; font-weight: bold;")
        self.emergency_stop_btn.clicked.connect(self.emergency_stop)
        
        bottom_layout.addWidget(self.connect_btn)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.emergency_stop_btn)
        
        layout.addLayout(bottom_layout)
        
    def setup_serial(self):
        # Имитируем подключение к Arduino
        self.serial_sim.connect()
        self.status_label.setText("Оборудование подключено (имитация)")
        
    def toggle_connection(self):
        if self.serial_sim.connected:
            self.serial_sim.disconnect()
            self.connect_btn.setText("Подключить оборудование")
            self.status_label.setText("Оборудование отключено")
        else:
            if self.serial_sim.connect():
                self.connect_btn.setText("Отключить оборудование")
                self.status_label.setText("Оборудование подключено (имитация)")
                
    def emergency_stop(self):
        print("АВАРИЙНАЯ ОСТАНОВКА!")
        self.serial_sim.stop_experiment()
        self.status_label.setText("АВАРИЙНАЯ ОСТАНОВКА - Все системы отключены")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")

def main():
    app = QApplication(sys.argv)
    
    # Устанавливаем тёмную тему для научного приложения
    app.setStyle('Fusion')
    
    window = OpticalLabApp()
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
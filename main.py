# Эта программа моделирует полет реактивного снаряда, запущенного под 
# углом к поверхности Земли. Снаряд принимается за материальную точку.
# Учитывается влияние атмосферы.

# Для работы необходим pyqt5, matplotlib, python3.5.
# Стандартная библиотека.
import sys
import math

# Для работы pyqt.
from PyQt5.QtWidgets import (QWidget, QPushButton, QHBoxLayout, QApplication, QLabel, QLineEdit)

# Для рисования QT оболочки.
from PyQt5.QtWidgets import QApplication, QMainWindow, QMenu, QVBoxLayout, QSizePolicy, QMessageBox, QWidget, \
    QPushButton, QGridLayout, QTextEdit

from PyQt5.QtGui import QIntValidator
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtGui import QIcon

# Для построение графика.
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

#-----------------------------------------------------------------------------------------------------------------------
# Создаем поле для рисования графика.
#-----------------------------------------------------------------------------------------------------------------------
class plotCanvas(FigureCanvas):
    def __init__(self, width=4, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        FigureCanvas.__init__(self, fig)
        self.max_size = 300   # Чтобы график отображался адекватно, масштаб по осям должен быть одинаков. Тут хранится большая грань.
        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title('Flight path')
        self.ax.hold(True)                                  # Когда кидаем новые данные - старые стирать нельзя.
        self.ax.axis([0, self.max_size, 0, self.max_size])
        self.x_array = []
        self.y_array = []

    def add_point(self, x, y):
        # Вычисляем большую грань.
        if x>self.max_size:
            self.max_size = x
        if y>self.max_size:
            self.max_size = y
        self.x_array.append(x)
        self.y_array.append(y)


    def print_graph(self, color):
        self.ax.plot(self.x_array, self.y_array, color)
        self.ax.axis([0, self.max_size, 0, self.max_size])
        self.draw()

    # Метод очищает внутренний список для текущего графика (который планируем отрисовать или только отрисовали).
    def clear_array(self):
        self.x_array.clear()
        self.y_array.clear()

    # Очищаем ото всех графиков и ставим стандартный масштаб.
    def clear_grap(self):
        self.max_size = 300
        self.ax.axis([0, self.max_size, 0, self.max_size])
        self.ax.clear()
        self.draw()

#-----------------------------------------------------------------------------------------------------------------------
# Основной объект.
#-----------------------------------------------------------------------------------------------------------------------
# Класс основного окна QT.
class main_window(QWidget):
    # Конструктор класса.
    def __init__(self):
        super().__init__()

        # Объявляем все необходимые переменные.
        self.c = 0.2
        self.p = 1.29
        self.s = 0.25
        self.u = 300         # Скорость выхода газов.
        self.g = 9.8
        self.mt = 30         # Масса топлива.
        self.m0 = 50         # Масса снаряда без топлива.
        self.mr = 3          # Расход топлива в секунду, кг.

        self.m = 0          # Общая масса.
        self.dm = 0.0       # Производная массы снаряда.
        self.t = 0.0        # Время полета.
        self.v = 30         # Скорость полета.
        self.q = 45 * math.pi / 180
        self.x = 0.0        # Координаты полета.
        self.y = 0.0

        self.loop_color = 0 # С помощью этой переменной согласуем цвета между графиками и тестовым полем.

        self._init_widget()

    # Служебные методы для runge_kutt.
    def Fx(self, t, v, q):                              # Функция производной координаты X.
        return v*math.cos(q)

    def Fy(self, t, v, q):                              # Функция производной координаты Y.
        return v*math.sin(q)

    def Fv(self, t, v, q):                              # Функция производной скорости.
        if self.m > self.m0:
            self.m -= self.mr * self.h                   # Закон изменения массы снаряда.
            self.dm=-self.mr * self.h
        else:
            self.m=self.m0
            self.dm=0
        # Производная скорости.
        return 1/self.m*((-1)/2*self.c*self.p*self.s*math.pow(v, 2)-(self.u+v)*self.dm)-self.g*math.sin(q)

    def Fq(self, t, v, q):                              # Функция производной угла полета.
        if v == 0:
            return 0
        else:
            return -self.g/v*math.cos(q)

    # Метод вычисляет производные t, v, q, методом Рунге-Кутта.
    def runge_kutt(self, t, v, q):
        self.h = 0.05
        k1 = self.h * self.Fx(t, v, q)           # Вычисление первых коэффициентов для д.у.
        k2 = self.h * self.Fx(t+self.h/2, v, q)
        k3 = self.h * self.Fx(t+self.h/2, v, q)
        k4 = self.h * self.Fx(t+self.h, v, q)

        l1 = self.h * self.Fy(t, v, q)           # Вычисление вторых коэффициентов для д.у.
        l2 = self.h * self.Fy(t+self.h/2, v, q)
        l3 = self.h * self.Fy(t+self.h/2, v, q)
        l4 = self.h * self.Fy(t+self.h, v, q)

        m1 = self.h * self.Fv(t, v, q)           # Вычисление третьих коэффициентов для д.у.
        m2 = self.h * self.Fv(t+self.h/2, v+m1/2, q)
        m3 = self.h * self.Fv(t+self.h/2, v+m2/2, q)
        m4 = self.h * self.Fv(t+self.h, v+m3, q)

        n1 = self.h * self.Fq(t, v, q)           # Вычисление четвертых коэффициентов для д.у.
        n2 = self.h * self.Fq(t+self.h/2, v, q+n1/2)
        n3 = self.h * self.Fq(t+self.h/2, v, q+n2/2)
        n4 = self.h * self.Fq(t+self.h, v, q+n3)

        self.x += 1/6 * (k1+2*k2+2*k3+k4)   # Вычисление производных координат x, y, скорости, угла полета.
        self.y += 1/6 * (l1+2*l2+2*l3+l4)
        self.v += 1/6 * (m1+2*m2+2*m3+m4)
        self.q += 1/6 * (n1+2*n2+2*n3+n4)

        self.t += self.h

    def b_clear_handler(self):
        self.graph.clear_grap()
        self.q_log.clear()
        self.loop_color = 0

    # Проситываем график.
    if __name__ == '__main__':
        def b_calculation_handler(self):
            # Заполняем переменные выбранными пользователем параметрами.
            self.q = int(self.le_degrees.text()) * math.pi/180
            self.c = int(self.le_c.text()) / 1000
            self.p = int(self.le_p.text()) / 1000
            self.s = (math.pow(int(self.le_diam.text()) * math.pow(10, -3), 2) * math.pi) / 4
            self.u = int(self.le_u.text())
            self.g = int(self.le_g.text()) / 1000
            self.v = int(self.le_v.text())
            self.mt = int(self.le_mt.text())
            self.m0 = int(self.le_m0.text())
            self.m = self.m0 + self.mt
            self.mr = int(self.le_mrs.text())

            # Получаемые в ходе расчета переменные.
            x_end_fuel = 0                                          # Тут будет лежать точка по x, где закончится топливо.
            y_end_fuel = 0
            y_max_gr = 0                                            # Вершина графика.
            x_mex_y_grap = 0
            flag = False                                            # Просто чтобы в нужный момент захватить координаты
                                                                    # конца топлева.
            # Одинаковые в начале запуска параметры.
            self.x = 0
            self.y = 0
            self.t = 0
            self.graph.clear_array()                                # Чистим от предыдущих расчетов.

            while 1:
                self.graph.add_point(self.x, self.y)                # Старт в точка 0.0, а потом и остальные координаты.
                self.runge_kutt(self.t, self.v, self.q)
                if self.y <= 0:                                     # Если полши в минус - выходим.
                    break
                if self.y > y_max_gr:                               # Получаем самую высокую точку полета.
                    y_max_gr = self.y
                    x_mex_y_grap = self.x
                # Этот кусок выполнятся 1 раз.
                if (self.m <= self.m0) and flag == False:
                    flag = True
                    x_end_fuel = self.x
                    y_end_fuel = self.y

            # Выбираем цвет (предполагаем, что возможно до 7 графиков за раз.
            if self.loop_color == 0:
                plot_color = 'r'
                self.q_log.setTextColor(Qt.red)
            if self.loop_color == 1:
                plot_color = 'g'
                self.q_log.setTextColor(Qt.green)
            if self.loop_color == 2:
                plot_color = 'b'
                self.q_log.setTextColor(Qt.blue)
            if self.loop_color == 3:
                plot_color = 'c'
                self.q_log.setTextColor(Qt.cyan)
            if self.loop_color == 4:
                plot_color = 'm'
                self.q_log.setTextColor(Qt.magenta)
            if self.loop_color == 5:
                plot_color = 'y'
                self.q_log.setTextColor(Qt.yellow)
            if self.loop_color == 6:
                plot_color = 'w'
                self.q_log.setTextColor(Qt.black)

            self.graph.print_graph(plot_color)  # Выводим графику.

            #Исходные параметры в лог.
            self.q_log.insertPlainText('Исходный угол наклона:\t\t\t' + self.le_degrees.text() + ' градусов.\n')
            self.q_log.insertPlainText('Исходная масса ракеты без топлива:\t\t' + self.le_m0.text() + ' кг.\n')
            self.q_log.insertPlainText('Масса топлива при старте:\t\t\t' + self.le_mt.text() + ' кг.\n')
            self.q_log.insertPlainText('Коэффициент сопротивления воздуха:\t\t%.2f' % self.c + '.\n')
            self.q_log.insertPlainText('Плотность воздуха:\t\t\t\t%.2f' % self.p + ' кг/м^3.\n')
            self.q_log.insertPlainText('Площадь поперечного сечения:\t\t\t%.2f' % self.s + ' м^2.\n')
            self.q_log.insertPlainText('Скорость выхода газов:\t\t\t%.2f' % self.u + ' м/с.\n')
            self.q_log.insertPlainText('Ускорение свободного падения: \t\t\t%.2f' % self.g + ' м/с^2.\n')
            self.q_log.insertPlainText('Начальная скорость полета:\t\t\t%.2f' % self.v + ' м/с.\n')

            # Итоги расчета.
            self.q_log.insertPlainText('Топливо закончится в точке:\t\t\tX = %.2f метров,\tY = %.2f метров.\n' % (x_end_fuel, y_end_fuel))
            self.q_log.insertPlainText('Самая высокая точка имеет координаты:\t\tX = %.2f метров,\tY = %.2f метров.\n' % (x_mex_y_grap, y_max_gr))
            self.q_log.insertPlainText('Координата падения по оси X:\t\t\t%.2f метров.\n' % self.x)
            self.q_log.insertPlainText('Время полета:\t\t\t\t%.2f секунд.\n\n' % self.t)

            # Готовимся к новому цвету
            self.loop_color += 1
            if self.loop_color == 7:
                self.loop_color = 0

    # Инициализация основного окна.
    def _init_widget(self):
        self.graph = plotCanvas(width=5, height=4, dpi = 100)   # График.
        self.graph.move(0, 0)                           # Можно и не писать, но на всякий случай.

        # Пересчитываем график..
        self.b_calculation = QPushButton("Построить график")                    # Кнопка постройки графика.
        self.b_calculation.clicked.connect(self.b_calculation_handler)

        # Чистим график.
        self.b_clear = QPushButton("Очистить")
        self.b_clear.clicked.connect(self.b_clear_handler)

        l0 = QLabel('Угол в градусах на старте [1..89]:')
        self.le_degrees = QLineEdit('45')
        self.le_degrees.setValidator(QIntValidator(1, 89, self))

        l1 = QLabel('Масса ракеты без топлива, кг: ')
        self.le_m0 = QLineEdit('20')
        self.le_m0.setValidator(QIntValidator(0, 1000000, self))

        l2 = QLabel('Масса топлива, кг: ')
        self.le_mt = QLineEdit('30')
        self.le_mt.setValidator(QIntValidator(0, 1000000, self))

        l9 = QLabel('Расход топлива в секунду, кг: ')
        self.le_mrs = QLineEdit('3')
        self.le_mrs.setValidator(QIntValidator(0, 1000000, self))

        l3 = QLabel('Коэффициент сопротивления воздуха (10^-3): ')
        self.le_c = QLineEdit('200')
        self.le_c.setValidator(QIntValidator(0, 1000000, self))

        l4 = QLabel('Плотность воздуха (10^-3), кг/м^3: ')
        self.le_p = QLineEdit('1200')
        self.le_p.setValidator(QIntValidator(0, 1000000, self))

        l5 = QLabel('Диаметр ракеты, мм: ')
        self.le_diam = QLineEdit('250')
        self.le_diam.setValidator(QIntValidator(0, 1000000, self))

        l6 = QLabel('Скорость выхода газов, м/с: ')
        self.le_u = QLineEdit('300')
        self.le_u.setValidator(QIntValidator(0, 1000000, self))

        l7 = QLabel('Ускорение свободного падения (10^-3), м/с^2: ')
        self.le_g = QLineEdit('9800')
        self.le_g.setValidator(QIntValidator(0, 1000000, self))

        l8 = QLabel('Начальная скорость полета, м/с: ')
        self.le_v = QLineEdit('30')
        self.le_v.setValidator(QIntValidator(1, 1000000, self))

        # Кнопки.
        self.but_l = QHBoxLayout()
        self.but_l.addWidget(self.b_clear)
        self.but_l.addWidget(self.b_calculation)

        # Вертикальная полоса в левой части.
        l_meny = QVBoxLayout()
        l_meny.addWidget(l0)
        l_meny.addWidget(self.le_degrees)
        l_meny.addWidget(l1)
        l_meny.addWidget(self.le_m0)
        l_meny.addWidget(l2)
        l_meny.addWidget(self.le_mt)
        l_meny.addWidget(l9)
        l_meny.addWidget(self.le_mrs)
        l_meny.addWidget(l3)
        l_meny.addWidget(self.le_c)
        l_meny.addWidget(l4)
        l_meny.addWidget(self.le_p)
        l_meny.addWidget(l5)
        l_meny.addWidget(self.le_diam)
        l_meny.addWidget(l6)
        l_meny.addWidget(self.le_u)
        l_meny.addWidget(l7)
        l_meny.addWidget(self.le_g)
        l_meny.addWidget(l8)
        l_meny.addWidget(self.le_v)
        l_meny.addLayout(self.but_l)             # Кнопки.
        l_meny.addStretch(1)


        top_l = QHBoxLayout()
        top_l.addLayout(l_meny)
        top_l.addWidget(self.graph)

        self.q_log = QTextEdit()

        end_window = QVBoxLayout()
        end_window.addLayout(top_l)
        end_window.addWidget(self.q_log)

        # Компонуем слои и укладываем их в основной виджет.
        self.setLayout(end_window)
        self.setGeometry(100, 100, 900, 700)                    # Задаем размер окна.
        self.setWindowTitle('flight_calculation')               # Имя формы.
        self.show()  # Не забываем показать.


#-----------------------------------------------------------------------------------------------------------------------
# В основной функции создаем объект основного окна. Все остальное пероисходит внутри объекта.
#-----------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = main_window()
    sys.exit(app.exec_())

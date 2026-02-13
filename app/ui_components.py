"""
UI Components Module
Componentes personalizados para la interfaz de usuario
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, Rectangle
import matplotlib.pyplot as plt


class StatisticsCard(BoxLayout):
    """Tarjeta para mostrar una estadística"""
    
    def __init__(self, title: str, value: str, unit: str = "", **kwargs):
        super().__init__(orientation='vertical', size_hint_y=None, height=100, **kwargs)
        
        title_label = Label(text=title, font_size='14sp', color=(0.7, 0.7, 0.7, 1))
        self.value_label = Label(text=f'{value} {unit}', font_size='24sp', bold=True)
        
        self.add_widget(title_label)
        self.add_widget(self.value_label)
    
    def update_value(self, value: str, unit: str = ""):
        """Actualiza el valor mostrado"""
        self.value_label.text = f'{value} {unit}'


class SlopeIndicator(BoxLayout):
    """Indicador visual de pendiente"""
    
    def __init__(self, **kwargs):
        super().__init__(orientation='horizontal', size_hint_y=None, height=80, **kwargs)
        
        self.slope_value = 0
        
        # Indicador de color según pendiente
        self.color_box = BoxLayout(size_hint_x=0.3)
        self.label = Label(text='0%', font_size='32sp', bold=True)
        
        self.add_widget(self.color_box)
        self.add_widget(self.label)
        
        self.bind(size=self._update_canvas)
    
    def _update_canvas(self, instance, value):
        """Redibuja el canvas cuando cambia el tamaño"""
        self._draw_color()
    
    def set_slope(self, slope: float):
        """Establece el valor de pendiente y cambia color"""
        self.slope_value = slope
        self.label.text = f'{abs(slope):.1f}%'
        self._draw_color()
    
    def _draw_color(self):
        """Dibuja el color según la pendiente"""
        slope = self.slope_value
        
        # Color según intensidad de pendiente
        if slope < -5:  # Bajada fuerte
            color = (0, 0.8, 1, 1)  # Azul
        elif slope < 0:  # Bajada suave
            color = (0, 1, 0.5, 1)  # Verde claro
        elif slope < 5:  # Bajada muy suave / casi plano
            color = (0, 1, 0, 1)  # Verde
        elif slope < 10:  # Subida suave
            color = (1, 1, 0, 1)  # Amarillo
        elif slope < 15:  # Subida moderada
            color = (1, 0.5, 0, 1)  # Naranja
        else:  # Subida fuerte
            color = (1, 0, 0, 1)  # Rojo
        
        self.color_box.canvas.clear()
        with self.color_box.canvas:
            Color(*color)
            Rectangle(size=self.color_box.size, pos=self.color_box.pos)


class RouteStatistics(ScrollView):
    """Panel de estadísticas de ruta"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.stats_layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
        self.stats_layout.bind(minimum_height=self.stats_layout.setter('height'))
        
        self.add_widget(self.stats_layout)
    
    def update_statistics(self, stats: dict):
        """Actualiza las estadísticas mostradas"""
        self.stats_layout.clear_widgets()
        
        for key, value in stats.items():
            card = StatisticsCard(
                title=key.replace('_', ' ').title(),
                value=str(value),
                size_hint_y=None,
                height=100
            )
            self.stats_layout.add_widget(card)
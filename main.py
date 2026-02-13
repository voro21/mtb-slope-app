import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.image import Image
from kivy.garden.mapview import MapView
from kivy.clock import Clock
from plyer import gps
from app.gps_handler import GPSHandler
from app.ui_components import SlopeIndicator, StatisticsCard, ElevationChart
import threading

class MTBSlopeApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.gps_handler = GPSHandler()
        self.tracking = False
    
    def build(self):
        self.title = 'MTB Slope Tracker'
        
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Header
        header = Label(text='MTB SLOPE TRACKER', size_hint_y=0.1, bold=True, font_size='18sp')
        main_layout.add_widget(header)
        
        # Slope Indicator
        self.slope_indicator = SlopeIndicator(size_hint_y=0.15)
        main_layout.add_widget(self.slope_indicator)
        
        # Statistics Grid
        stats_layout = GridLayout(cols=3, spacing=10, size_hint_y=0.2)
        self.speed_card = StatisticsCard('Velocidad', '0', 'km/h')
        self.alt_card = StatisticsCard('Altitud', '0', 'm')
        self.dist_card = StatisticsCard('Distancia', '0', 'km')
        stats_layout.add_widget(self.speed_card)
        stats_layout.add_widget(self.alt_card)
        stats_layout.add_widget(self.dist_card)
        main_layout.add_widget(stats_layout)
        
        # Control Buttons
        button_layout = BoxLayout(size_hint_y=0.15, spacing=10)
        self.start_btn = Button(text='INICIAR RASTREO', background_color=(0, 0.7, 0, 1))
        self.stop_btn = Button(text='DETENER', background_color=(0.7, 0, 0, 1))
        self.save_btn = Button(text='GUARDAR RUTA', background_color=(0, 0.5, 0.7, 1))
        
        self.start_btn.bind(on_press=self.start_tracking)
        self.stop_btn.bind(on_press=self.stop_tracking)
        self.save_btn.bind(on_press=self.save_route)
        
        button_layout.add_widget(self.start_btn)
        button_layout.add_widget(self.stop_btn)
        button_layout.add_widget(self.save_btn)
        main_layout.add_widget(button_layout)
        
        # Status Label
        self.status_label = Label(text='Estado: Listo', size_hint_y=0.1)
        main_layout.add_widget(self.status_label)
        
        # Update GPS data
        Clock.schedule_interval(self.update_gps_data, 0.5)
        
        return main_layout
    
    def start_tracking(self, instance):
        if not self.tracking:
            self.tracking = True
            self.gps_handler.start_tracking()
            self.status_label.text = 'Estado: Rastreando...'
            self.start_btn.disabled = True
    
    def stop_tracking(self, instance):
        if self.tracking:
            self.tracking = False
            self.gps_handler.stop_tracking()
            self.status_label.text = 'Estado: Detenido'
            self.start_btn.disabled = False
    
    def save_route(self, instance):
        if self.gps_handler.route_points:
            filename = self.gps_handler.export_to_gpx()
            self.status_label.text = f'Ruta guardada: {filename}'
    
    def update_gps_data(self, dt):
        if self.tracking:
            data = self.gps_handler.get_current_data()
            if data:
                self.slope_indicator.set_slope(data['slope'])
                self.speed_card.update_value(f'{data["speed"]:.1f}', 'km/h')
                self.alt_card.update_value(f'{data["altitude"]:.0f}', 'm')
                self.dist_card.update_value(f'{data["distance"]:.2f}', 'km')

if __name__ == '__main__':
    MTBSlopeApp().run()
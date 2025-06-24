from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button

from attendance_fetcher import fetch_attendance_from_all_devices, fetch_attendance

class MainScreen(BoxLayout):
    def fetch_all(self, *args):
        fetch_attendance_from_all_devices()

    def fetch_custom(self, ip, name):
        if ip and name:
            fetch_attendance(ip, name)

class AttendanceApp(App):
    def build(self):
        root = MainScreen(orientation='vertical', padding=20, spacing=10)
        root.add_widget(Label(text='Attendance Manager', font_size=24, size_hint_y=None, height=40))
        btn_all = Button(text='Fetch All Branch Logs', size_hint_y=None, height=50)
        btn_all.bind(on_release=root.fetch_all)
        root.add_widget(btn_all)

        ip_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=5)
        ip_input = TextInput(hint_text='Custom IP')
        name_input = TextInput(hint_text='Device Name')
        btn_custom = Button(text='Fetch')
        btn_custom.bind(on_release=lambda instance: root.fetch_custom(ip_input.text, name_input.text))
        ip_box.add_widget(ip_input)
        ip_box.add_widget(name_input)
        ip_box.add_widget(btn_custom)
        root.add_widget(ip_box)

        return root

if __name__ == '__main__':
    AttendanceApp().run()

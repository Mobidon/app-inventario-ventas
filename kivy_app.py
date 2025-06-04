import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner

# Conexi\xc3\xb3n a Google Sheets
scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('perron2-f307892530b3.json', scope)
client = gspread.authorize(creds)
spreadsheet = client.open_by_key('19Rd4PzPrrzSZ8CXb98VDwdhys9r-owybmdtfbdfOx2U')

# Configuraci\xc3\xb3n por tipo de producto
configuraciones = {
    "Peluches": {
        "hoja": spreadsheet.worksheet("Inventario"),
        "producto": "peluches"
    },
    "Llaveros": {
        "hoja": spreadsheet.worksheet("Inverteros"),
        "producto": "llaveros"
    }
}

class InventarioLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=10, spacing=10, **kwargs)

        self.spinner_tipo = Spinner(text='Peluches', values=list(configuraciones.keys()))
        self.add_widget(self.spinner_tipo)

        self.cantidad_input = TextInput(hint_text='Cantidad', multiline=False)
        self.add_widget(self.cantidad_input)

        self.costo_input = TextInput(hint_text='Costo Total', multiline=False)
        self.add_widget(self.costo_input)

        self.modelo_input = TextInput(hint_text='Modelo', multiline=False)
        self.add_widget(self.modelo_input)

        self.boton_pedido = Button(text='Registrar Pedido')
        self.boton_pedido.bind(on_press=self.registrar_pedido)
        self.add_widget(self.boton_pedido)

        self.llegados_input = TextInput(hint_text='Llegaron', multiline=False)
        self.add_widget(self.llegados_input)

        self.boton_llegada = Button(text='Registrar Llegada')
        self.boton_llegada.bind(on_press=self.registrar_llegada)
        self.add_widget(self.boton_llegada)

        self.boton_resumen = Button(text='Ver Resumen')
        self.boton_resumen.bind(on_press=self.ver_resumen)
        self.add_widget(self.boton_resumen)

        self.result_label = Label(text='')
        self.add_widget(self.result_label)

    def registrar_pedido(self, instance):
        tipo = self.spinner_tipo.text
        hoja = configuraciones[tipo]["hoja"]
        cantidad = self.cantidad_input.text
        costo_total = self.costo_input.text
        try:
            cantidad_num = int(cantidad)
        except ValueError:
            cantidad_num = 0
        try:
            costo_total_num = float(costo_total)
        except ValueError:
            costo_total_num = 0.0
        costo_promedio = costo_total_num / cantidad_num if cantidad_num > 0 else 0
        fecha_actual = datetime.now().strftime("%Y-%m-%d")
        fecha_llegada = (datetime.now() + timedelta(weeks=2)).strftime("%Y-%m-%d")
        modelo = self.modelo_input.text
        hoja.append_row([
            fecha_actual, cantidad_num, costo_total_num, round(costo_promedio, 2),
            "En Camino", fecha_llegada, cantidad_num, 0
        ], value_input_option='USER_ENTERED')
        num_filas = len(hoja.get_all_values())
        hoja.update_cell(num_filas, 10, modelo)
        self.result_label.text = f"Pedido de {cantidad_num} {configuraciones[tipo]['producto']} registrado. Modelo: {modelo}"
        self.cantidad_input.text = ''
        self.costo_input.text = ''
        self.modelo_input.text = ''

    def registrar_llegada(self, instance):
        tipo = self.spinner_tipo.text
        hoja = configuraciones[tipo]["hoja"]
        llegados = self.llegados_input.text
        try:
            llegados_num = int(llegados)
        except ValueError:
            llegados_num = 0
        encabezados = ["Fecha", "Peluches Comprados" if tipo == "Peluches" else "Llaveros Comprados", "Costo Total", "Promedio", "Estado", "Fecha Llegada", "En camino", "Llegaron", "", "Modelo"]
        datos = hoja.get_all_records(expected_headers=encabezados)
        df = pd.DataFrame(datos)
        df["En camino"] = pd.to_numeric(df["En camino"], errors='coerce').fillna(0)
        df["Llegaron"] = pd.to_numeric(df["Llegaron"], errors='coerce').fillna(0)

        for index, row in df.iterrows():
            faltan = row["En camino"] - row["Llegaron"]
            if faltan > 0:
                fila = index + 2
                cantidad_a_registrar = min(faltan, llegados_num)
                hoja.update_cell(fila, 8, row["Llegaron"] + cantidad_a_registrar)
                llegados_num -= cantidad_a_registrar
                if llegados_num == 0:
                    break

        if llegados_num > 0:
            self.result_label.text = f"Quedaron {llegados_num} sin asignar."
        else:
            self.result_label.text = "Todos los productos registrados."
        self.llegados_input.text = ''

    def ver_resumen(self, instance):
        tipo = self.spinner_tipo.text
        hoja = configuraciones[tipo]["hoja"]
        encabezados = ["Fecha", "Peluches Comprados" if tipo == "Peluches" else "Llaveros Comprados", "Costo Total", "Promedio", "Estado", "Fecha Llegada", "En camino", "Llegaron", "", "Modelo"]
        df = pd.DataFrame(hoja.get_all_records(expected_headers=encabezados))
        df["En camino"] = pd.to_numeric(df["En camino"], errors='coerce').fillna(0)
        df["Llegaron"] = pd.to_numeric(df["Llegaron"], errors='coerce').fillna(0)
        total_en_camino = df["En camino"].sum()
        total_llegaron = df["Llegaron"].sum()
        total_faltan = total_en_camino - total_llegaron
        resumen = f"En camino: {int(total_en_camino)}\nLlegaron: {int(total_llegaron)}\nFaltan: {int(total_faltan)}"
        self.result_label.text = resumen

class InventarioApp(App):
    def build(self):
        return InventarioLayout()

if __name__ == '__main__':
    InventarioApp().run()

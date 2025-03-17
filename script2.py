import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import re
from datetime import datetime

# Caminho dos arquivos
file_txt = "dados_arduino_indefinido.txt"
file_xlsx = "dados_extraidos.xlsx"

# Variáveis para armazenar os dados
timestamps = []
temperatura = []
temperatura2 = []
voltage = []
current = []
power = []
frequency = []
pf = []
sensorporta = []

# Expressões regulares para capturar os dados
regex_patterns = {
    "timestamp": re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})"),
    "temperatura": re.compile(r"Temperatura: ([\d\.-]+) \*C"),
    "temperatura2": re.compile(r"Temperatura2: ([\d\.-]+) \*C"),
    "voltage": re.compile(r"Voltage: ([\d\.]+) V"),
    "current": re.compile(r"Current: ([\d\.]+) A"),
    "power": re.compile(r"Power: ([\d\.]+) W"),
    "frequency": re.compile(r"Frequency: ([\d\.]+) Hz"),
    "pf": re.compile(r"PF: ([\d\.]+)"),
    "sensorporta": re.compile(r"SensorPorta: ([\d\.]+)")
}

# Processar o arquivo TXT
try:
    with open(file_txt, "r", encoding="utf-8") as file:
        for line in file:
            try:
                match_timestamp = regex_patterns["timestamp"].search(line)
                if match_timestamp:
                    timestamps.append(datetime.strptime(match_timestamp.group(1), "%Y-%m-%d %H:%M:%S"))
                
                for key in ["temperatura", "temperatura2", "voltage", "current", "power", "frequency", "pf", "sensorporta"]:
                    match = regex_patterns[key].search(line)
                    if match:
                        value = float(match.group(1))
                        locals()[key].append(value)
            except Exception as e:
                print(f"Erro ao processar linha: {line.strip()} - Erro: {e}")
except FileNotFoundError:
    print("Arquivo TXT não encontrado! Verifique o caminho.")
except Exception as e:
    print(f"Erro inesperado no TXT: {e}")

# Garantir que todas as listas tenham o mesmo tamanho
min_length = min(len(timestamps), len(temperatura), len(temperatura2), len(voltage), len(current), len(power), len(frequency), len(pf), len(sensorporta))
timestamps = timestamps[:min_length]
temperatura = temperatura[:min_length]
temperatura2 = temperatura2[:min_length]
voltage = voltage[:min_length]
current = current[:min_length]
power = power[:min_length]
frequency = frequency[:min_length]
pf = pf[:min_length]
sensorporta = sensorporta[:min_length]

# Processar o arquivo XLSX
try:
    df = pd.read_excel(file_xlsx)
    df.fillna(0, inplace=True)  # Substituir valores nulos por 0
    
    # Criar gráficos para as colunas numéricas
    for column in df.select_dtypes(include=['number']).columns:
        plt.figure(figsize=(10, 5))
        plt.plot(df.index, df[column], linestyle='-')
        plt.title(column)
        plt.xlabel("Índice")
        plt.ylabel(column)
        plt.grid()
        plt.show()
except FileNotFoundError:
    print("Arquivo XLSX não encontrado! Verifique o caminho.")
except Exception as e:
    print(f"Erro inesperado no XLSX: {e}")

# Plotando os gráficos do TXT se houver dados
if timestamps:
    fig, axes = plt.subplots(4, 2, figsize=(10, 10))
    #titles = ["Temperatura", "Temperatura2", "Voltage", "Current", "Power", "Frequency", "Power Factor", "SensorPorta"]
    #data = [temperatura, temperatura2, voltage, current, power, frequency, pf, sensorporta]
    titles = ["Tensão", "Temperatura Ambiente", "Corrente", "Temperaturna Interna", "Potência Ativa", "Sensor de Porta", "Fator de Potência", "Frequência"]
    data = [voltage, temperatura, current, temperatura2, power, sensorporta, pf, frequency]
    

    for ax, title, values in zip(axes.flat, titles, data):
        if values:
            ax.plot(timestamps, values, linestyle='-')
            ax.set_title(title)
            ax.set_xlabel("Horário/Data")
            ax.set_ylabel(title)
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S\n%Y-%m-%d"))  # Exibir horário e data no eixo X
            ax.grid()
        else:
            ax.set_title(title)
            ax.text(0.5, 0.5, "Sem dados", ha='center', va='center', fontsize=12)
            ax.set_xticks([])
            ax.set_yticks([])
    
    plt.subplots_adjust(hspace=2)  # Aumenta a distância entre os gráficos
    plt.tight_layout()
    plt.show()
else:
    print("Nenhum dado válido encontrado no TXT.")
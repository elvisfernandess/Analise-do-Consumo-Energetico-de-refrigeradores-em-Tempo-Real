import matplotlib.pyplot as plt
import re
from datetime import datetime

# Caminho do arquivo
file_path = "dados_arduino_indefinido.txt"

# Variáveis para armazenar os dados
timestamps = []
temperatura = []
temperatura2 = []
voltage = []
current = []
power = []
frequency = []
pf = []

# Expressões regulares para capturar os dados
regex_patterns = {
    "timestamp": re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})"),
    "temperatura": re.compile(r"Temperatura: ([\d\.-]+) \\\*C"),
    "temperatura2": re.compile(r"Temperatura2: ([\d\.-]+) \\\*C"),
    "voltage": re.compile(r"Voltage: ([\d\.]+) V"),
    "current": re.compile(r"Current: ([\d\.]+) A"),
    "power": re.compile(r"Power: ([\d\.]+) W"),
    "frequency": re.compile(r"Frequency: ([\d\.]+) Hz"),
    "pf": re.compile(r"PF: ([\d\.]+)")
}

# Processar o arquivo
try:
    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            try:
                match_timestamp = regex_patterns["timestamp"].search(line)
                if match_timestamp:
                    timestamps.append(datetime.strptime(match_timestamp.group(1), "%Y-%m-%d %H:%M:%S"))
                
                for key in ["temperatura", "temperatura2", "voltage", "current", "power", "frequency", "pf"]:
                    match = regex_patterns[key].search(line)
                    if match:
                        value = float(match.group(1))
                        if key == "temperatura":
                            temperatura.append(value)
                        elif key == "temperatura2":
                            temperatura2.append(value)
                        elif key == "voltage":
                            voltage.append(value)
                        elif key == "current":
                            current.append(value)
                        elif key == "power":
                            power.append(value)
                        elif key == "frequency":
                            frequency.append(value)
                        elif key == "pf":
                            pf.append(value)
            except Exception as e:
                print(f"Erro ao processar linha: {line.strip()} - Erro: {e}")

    if not timestamps:
        print("Nenhum dado válido encontrado. Verifique o formato do arquivo.")
    else:
        # Plotando os gráficos
        fig, axes = plt.subplots(4, 2, figsize=(12, 12))
        titles = ["Temperatura", "Temperatura2", "Voltage", "Current", "Power", "Frequency", "Power Factor"]
        data = [temperatura, temperatura2, voltage, current, power, frequency, pf]

        for ax, title, values in zip(axes.flat, titles, data):
            if values:
                ax.plot(timestamps[:len(values)], values, marker='o', linestyle='-')
                ax.set_title(title)
                ax.set_xlabel("Tempo")
                ax.set_ylabel(title)
                ax.grid()
            else:
                ax.set_title(title)
                ax.text(0.5, 0.5, "Sem dados", ha='center', va='center', fontsize=12)
                ax.set_xticks([])
                ax.set_yticks([])

        plt.tight_layout()
        plt.show()
except FileNotFoundError:
    print("Arquivo não encontrado! Verifique o caminho.")
except Exception as e:
    print(f"Erro inesperado: {e}")
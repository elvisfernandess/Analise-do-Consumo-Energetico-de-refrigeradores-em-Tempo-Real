import matplotlib.pyplot as plt #biblioteca para criar e personalizar gráficos   
import matplotlib.dates as mdates #biblioteca para formatar e manipular datas em gráficos
import pandas as pd #biblioteca para os os dados tabelados
import re #biblioteca que extrai dados de arquivos
from datetime import datetime #biblioteca para poder utilizar datas e horários

#nome dos arquivos onde os dados serão extraídos
file_txt = "dados_arduino_indefinido.txt"
file_xlsx = "dados_extraidos.xlsx"

#listas para armazenar os dados do arquivo dados_arduino_indefinido.txt
timestamps = [] #lista que armazena os horários das medições
temperatura = [] #lista que armazena a temperatura ambiente
temperatura2 = [] #lista que armazena a temperatura interna do refrigerador
voltage = [] #lista que armazena a tensão
current = [] #lista que armazena a corrrente
power = [] #lista que armazena a potência ativa
frequency = [] #lista que armazena a frequência
pf = [] #lista que armazena o fator de potência
sensorporta = [] #lista que armazena o sinal do sensor de porta

#definir a sequência dos caracteres que serão capturados
regex_patterns = {
    "timestamp": re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})"), #sequência de caracteres de data e hora
    "temperatura": re.compile(r"Temperatura: ([\d\.-]+) \*C"), #sequência de caracteres de temperatura ambiente
    "temperatura2": re.compile(r"Temperatura2: ([\d\.-]+) \*C"), #sequência de caracteres de temperatura interna do refrigerador
    "voltage": re.compile(r"Voltage: ([\d\.]+) V"), #sequência de caracteres de tensão
    "current": re.compile(r"Current: ([\d\.]+) A"), #sequência de caracteres de corrente
    "power": re.compile(r"Power: ([\d\.]+) W"), #sequência de caracteres de potência ativa
    "frequency": re.compile(r"Frequency: ([\d\.]+) Hz"), #sequência de caracteres de frequência
    "pf": re.compile(r"PF: ([\d\.]+)"), #sequência de caracteres de fator de potência
    "sensorporta": re.compile(r"SensorPorta: ([\d\.]+)") #sequência de caracteres de sinal de sensor de porta
}


try: #tenta processar o arquivo dados_arduino_indefinido.txt
    with open(file_txt, "r", encoding="utf-8") as file: #abrir o arquivo em modo de leitura
        for line in file: #o arquivo deve ser lido linha por linha
            try:
                match_timestamp = regex_patterns["timestamp"].search(line) #tenta capturar a data e a hora da medição que está no arquivo
                if match_timestamp: #converte a data e a hora em um objeto que será armazenado na lista
                    timestamps.append(datetime.strptime(match_timestamp.group(1), "%Y-%m-%d %H:%M:%S"))
                
                for key in ["temperatura", "temperatura2", "voltage", "current", "power", "frequency", "pf", "sensorporta"]: #relaciona a sequencia dos caracteres para capturar os valores das medições
                    match = regex_patterns[key].search(line) #encontrar o valor correspondente na linha atual do arquivo
                    if match:
                        value = float(match.group(1)) #o valor correspondente é convertido para float
                        locals()[key].append(value) #adiciona o valor na lista
            except Exception as e:
                print(f"Erro ao processar linha: {line.strip()} - Erro: {e}") #mensagem parar verificar erro
except FileNotFoundError:
    print("Arquivo TXT não encontrado! Verificar o caminho.") #mensagem de que não existe o arquivo no diretório do script
except Exception as e:
    print(f"Erro inesperado no TXT: {e}") #mensagem de erro no arquivo dados_arduino_indefinido.txt

#pegar o comprimento mínimo de cada linha e truncar para o mesmo tamanho
min_length = min(len(timestamps), len(temperatura), len(temperatura2), len(voltage), len(current), len(power), len(frequency), len(pf), len(sensorporta))

#garantir que todas as linhas tenham o mesmo tamanho
timestamps = timestamps[:min_length]
temperatura = temperatura[:min_length]
temperatura2 = temperatura2[:min_length]
voltage = voltage[:min_length]
current = current[:min_length]
power = power[:min_length]
frequency = frequency[:min_length]
pf = pf[:min_length]
sensorporta = sensorporta[:min_length]

#tenta processar o arquivo dados_extraidos.xlsx
try:
    df = pd.read_excel(file_xlsx) #ler os dados do arquivo em um quadro de dados
    df.fillna(0, inplace=True)  #substituir valores nulos por 0
    
    
    for column in df.select_dtypes(include=['number']).columns: #criar gráficos para cada coluna
        plt.figure(figsize=(10, 5)) #definir o tamanho do gráfico
        plt.plot(df.index, df[column], linestyle='-') #plotar os dados no gráfico
        plt.title(column) #definir o título do gráfico
        plt.xlabel("Amostras") #definir a legenda do eixo x
        plt.ylabel(column) #definir a legenda do eixo y
        plt.grid() #adicionar grade ao gráfico
        plt.show() #exibir o gráfico
        
except FileNotFoundError:
    print("Arquivo XLSX não encontrado! Verificar o caminho.") #mensagem de que não existe o arquivo no diretório do script
except Exception as e:
    print(f"Erro inesperado no XLSX: {e}") #mensagem de erro no arquivo.xlsx

#se houver dados no arquivo dados_arduino_indefinido.txt plotar os gráficos 
if timestamps:
    fig, axes = plt.subplots(4, 2, figsize=(10, 10))  #definir o numero de linhas, de colunas e o tamanho de cada gráfico
    #titles = ["Temperatura", "Temperatura2", "Voltage", "Current", "Power", "Frequency", "Power Factor", "SensorPorta"]
    #data = [temperatura, temperatura2, voltage, current, power, frequency, pf, sensorporta]
    titles = ["Tensão", "Temperatura Ambiente", "Corrente", "Temperaturna Interna", "Potência Ativa", "Sensor de Porta", "Fator de Potência", "Frequência"] #definir os títulos de cada gráfico
    data = [voltage, temperatura, current, temperatura2, power, sensorporta, pf, frequency]  #definir os dados de cada gráfico
    

    for ax, title, values in zip(axes.flat, titles, data): #percorrer os subgráficos e associar os títulos e aos dados correspondentes
        if values: #se tiver valores
            ax.plot(timestamps, values, linestyle='-') #plotar os dados no gráfico
            ax.set_title(title) #associar o título do gráfico
            ax.set_xlabel("Horário/Data") #definir a legenda do eixo x
            ax.set_ylabel(title) #definir a legenda do eixo y
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S\n%Y-%m-%d"))  #exibir horário e data no eixo X
            ax.grid() #adicionar grade ao gráfico
        else:
            ax.set_title(title) #mensagem de erro se nao tiver dados no arquivo .txt
            ax.text(0.5, 0.5, "Sem dados", ha='center', va='center', fontsize=12)
            ax.set_xticks([])
            ax.set_yticks([])
    
    plt.subplots_adjust(hspace=2)  #aumentar a distância entre os gráficos
    plt.tight_layout() #organiza a disposição para evitar sobreposição
    plt.show() #exibir o gráfico
else:
    print("Nenhum dado válido encontrado no TXT.")
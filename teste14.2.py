import pandas as pd #biblioteca para os os dados tabelados
from openpyxl import Workbook, load_workbook #biblioteca para poder enviar dados para um arquivo .xlsx
import xlwings as xw  # biblioteca necessária para poder automatizar um arquivo .xlsx 
import serial #biblioteca para comunicação serial com o hardware (chip atmega328p)
import tkinter as tk #biblioteca necessária para janelas com interface gráfica
from tkinter import messagebox  # biblioteca para emitir alertas e mensagens na tela
from tkinter.scrolledtext import ScrolledText #biblioteca para poder usar barra de rolagem na tela onde são exibidos os dados vindos do hardware
import math #biblioteca para poder utilizar funções da matemática avançadas
from datetime import datetime, timedelta #biblioteca para poder utilizar datas e horários, para ver a diferença entre dois horários ou datas
import json #biblioteca necessário para poder salvar e carregar os dados que usam a estrutura no formato JSON
import os #biblioteca necessária para interação com o sistema operacional e seus diretórios
import re #biblioteca que extrai dados de arquivos
from tkinter import Toplevel, Label, Button #bibliotecas para poder criar uma nova janela dentro de uma aplicação, exibe textos em uma interface, utilizar botões em uma interface
from tkcalendar import Calendar #biblioteca que 
import threading  # biblioteca para executar tarefas em segundo plano e não travar a interface gráfica

# Comunicação da porta serial do hardware 
porta_serial = 'COM3'  # verificar porta no gerenciador de dispositivos
baud_rate = 9600       #frequência do baud rate (mesma utilizada no firmware do arquivo .ino) 
arquivo_saida = 'dados_arduino_indefinido.txt' #nome do arquivo que 

# Nome do arquivo JSON para salvar os dados cadastrados de refrigeradores
ARQUIVO_JSON = "refrigeradores.json"

# Variáveis a serem editadas
tarifa_energia = 0.80  # valor de tarifa
potencia_nominal = 218.0  # valor de potência nominal do refrigerador em watts
tensao_nominal = 220.0    # valor de tensão nominal do refrigerador em volts
rendimento_nominal = 79.80  # valor do rendimento nominal do refrigerador em %
consumo_mensal_nominal = 55.3  # valor do consumo mensal nominal do refrigerador em kWh
limite_inferior_consumo = 52.0  # valor do limite inferior do consumo mensal nominal do refrigerador em kWh
limite_superior_consumo = 57.0  # valor do limite superior do consumo mensal nominal do refrigerador em kWh
limite_inferior_temperatura_sensor_1 = 25.0  # valor do limite inferior de temperatura do Sensor 1 em ºC
limite_superior_temperatura_sensor_1 = 27.0  # valor do limite superior de temperatura do Sensor 1 em ºC
limite_inferior_temperatura_sensor_2 = 25.0  # valor do limite inferior de temperatura do Sensor 2 em ºC
limite_superior_temperatura_sensor_2 = 27.0  # valor do limite superior de temperatura do Sensor 2 em ºC
limite_inferior_rendimento = 70.0  # valor do limite inferior de rendimento do refrigerador em %
limite_superior_rendimento = 90.0  # valor do limite superior de rendimento do refrigerador em %


horario_inicio_teste = None #variavel global que armazena o valor do início de um teste
tempo_decorrido = timedelta(0) #variavel global que armazena o valor do início de um teste
horarios_teste_personalizado = {} #variavel global que armazena os valores dos horários setados no teste personalizado

# Inicialização das variáveis globais para o rendimento
estado_atual_rendimento = None #variável global que armazena o estado atual para alerta de rendimento
horario_transicao_rendimento = None #variável global que armazena o horário que foi feita a transição de estado de rendimento

# Inicialização de variáveis globais
inicio_periodo = datetime.now() #variavel global que armazena 
arquivo_atual = None

soma_potencia = 0.0 #variavel global de inicialização para somar a potência na tela de consumo energetico
numero_amostras = 0 #variavel global de inicialização para incrementar as amostras na tela de consumo energetico
ultima_posicao = 0 #variavel global de inicialização para por armazenar a ultima posição no arquivo .xlsx
potencia_media = 0 #variavel global de inicialização para porder calcular a potência no arquivo .xlsx
consumo_mensal_estimado = 0 #variavel global de inicialização para porder calcular o consumo mensal estimado
consumo_mensal_estimado_kwh = 0 #variavel global de inicialização para porder calcular o consumo mensal estimado em quilo-watt-hora
energia_acumulada = 0.0  #variavel global de inicialização para porder calcular a energia acumulada
ultima_leitura_tempo = None  # variavel global para poder inicializar a ultima leitura a ser lida no arquivo .xlsx


contador_id = 1  # Variável global para gerar IDs únicos
dados_buffer = []  # Armazena as leituras temporariamente

# Conectar ao Arduino via porta serial
try:
    arduino = serial.Serial(porta_serial, baud_rate, timeout=1) #passando como parâmetro a porta do arduino, a frequencia do baud rate e o tempo de envio de dados
    print(f"Conectado à porta {porta_serial}") #mensagem de conexão positiva no terminal python
except serial.SerialException as e:
    print(f"Erro de conexão: {e}") #mensagem de erro de comunicação no terminal python
    exit() #fecha o software

# Variáveis para armazenar os dados vindos via serial e poder calcular a media movel
valores_potencia = [] # Lista para armazenar os valores de potência do sensor de energia
valores_temperatura = [] # Lista para armazenar os valores de temperatura do sensor de temperatura 1
valores_temperatura2 = [] # Lista para armazenar os valores de temperatura do sensor de temperatura 2
valores_tensao = [] # Lista para armazenar os valores de tensao do sensor de energia
valores_corrente = [] # Lista para armazenar os valores de corrente do sensor de energia
valores_potencia_aparente = [] # Lista para armazenar os valores calcular da potencia aparente
valores_potencia_reativa = [] # Lista para armazenar os valores calcular da potencia reativa
valores_sensor_porta = [] # Lista para armazenar os valores 0 ou 1 do sensor de porta
horarios = [] # Lista para armazenar os valores dos horarios
refrigeradores = [] # Lista para armazenar os refrigeradores cadastrados
transicoes_alertas_consumo = [] # Lista para armazenar as transições de alertas do consumo
transicoes_alertas_rendimento = [] # Lista para armazenar as transições de alertas do rendimento
transicoes_alertas_temp_sensor_1 = [] # Lista para armazenar as transições de alertas de temperatura do sensor 1
transicoes_alertas_temp_sensor_2 = [] # Lista para armazenar as transições de alertas de temperatura do sensor 2
transicoes_alertas_sensor_porta = [] # Lista para armazenar as transições de alertas do sensor de porta
horarios_pausa = []  # Lista para armazenar as transições de horarios do botão pausa
horarios_continuacao = [] # Lista para armazenar as transições de horarios do botão continuar
horarios_atualizacao = [] # Lista para armazenar as transições de horarios do botão atualizar

# Definir o tamanho da janela para a média móvel
tamanho_janela = 10  # Número de leituras para calcular a média móvel

# Função para gerar o nome do arquivo
def obter_nome_arquivo():
    """Gera o nome do arquivo com base na data e no período do teste."""
    horario_inicio_teste_formatado = horario_inicio_teste.strftime('%Y-%m-%d_%H-%M-%S') if horario_inicio_teste else "indefinido"
    return f"dados_arduino_{horario_inicio_teste_formatado}.txt"
    
# Verifica se é necessário criar um novo arquivo
def verificar_novo_arquivo():
    """Verifica se é necessário criar um novo arquivo."""
    global inicio_periodo, arquivo_atual #variaveis globais que podem ser acessadas dentro ou fora dessa função

    agora = datetime.now() #armazena a data e o horario a partir do objeto
    if agora - inicio_periodo >= timedelta(minutes=1) or arquivo_atual is None: 
        inicio_periodo = agora #atualiza o horario atual
        arquivo_atual = obter_nome_arquivo() #gera um novo arquivo baseado na data e hora
        #print(f"Usando arquivo: {arquivo_atual}")

        # Cria arquivo vazio se ele não existir
        if not os.path.exists(arquivo_atual):
            open(arquivo_atual, 'w').close()
            print(f"Arquivo {arquivo_atual} criado.")  #imprime mensagem de arquivo criado no terminal python
        

def monitorar_arquivo():
    #variaveis globais que podem ser acessadas dentro ou fora dessa função
    global soma_potencia, numero_amostras, ultima_posicao, potencia_media
    global energia_acumulada, ultima_leitura_tempo
    global horario_inicio_teste, tempo_decorrido, teste_iniciado, teste_pausado,tempo_decorrido_segundos
    global tarifa_energia, consumo_mensal_estimado, consumo_mensal_estimado_kwh

    print("Executando monitorar_arquivo()...")  #imprime mensagem no terminal python chamando a função
    
    #verifica se o arquivo .xlsx existe
    try:
        nome_arquivo = "dados_extraidos.xlsx"

        # Verifica se o arquivo já existe, se não, cria um novo
        if not os.path.exists(nome_arquivo):
            #print(f"Arquivo '{nome_arquivo}' não encontrado. Criando novo arquivo...")  # Debug
            wb = xw.Book()  # Cria um novo arquivo
            sheet = wb.sheets[0] #seleciona a primeira planilha do arquivo .xlsx
            sheet.range('A1').value = ['ID', 'Potência', 'Horario', 'Delta', 'Pmed', 'Energia (Wh)', 'Energia Acumulada (Wh)']  # Cabeçalhos sendo escritos na linha A1 da planilha
            wb.save(nome_arquivo)  # Salva o arquivo
            print(f"Arquivo '{nome_arquivo}' criado com sucesso!")  #imprime mensagem de arquivo criado no terminal python 
        else:
            wb = xw.Book(nome_arquivo) #abre o arquivo .xlsx existente
            sheet = wb.sheets[0] #seleciona a primeira planilha do arquivo .xlsx

        # Lê as novas linhas do arquivo de entrada
        with open(arquivo_saida, 'r', encoding='utf-8') as arquivo: #abre o arquivo no modo leitura com caracteres especiais lidos e fecha corrente depois do arquivo ser lido
            arquivo.seek(ultima_posicao)  #move o cursor para a ultima linha para nao ler as linhas repetidas
            novas_linhas = arquivo.readlines() #lê todas as linhas da posição com inicio da posição inicial
            ultima_posicao = arquivo.tell() #continuar do ponto certo e retorna a posição atual do cursor

        #print(f"Linhas novas lidas: {len(novas_linhas)}")  # Debug
        
        #variaveis que serão utilizadas para armazenar os dados extraídos do arquivo .xlsx
        potencia_atual = None #extrai o valor de potencia / None nao tem potencia definida
        fator_potencia_atual = None #extrai o valor de do fator de potencia / None nao tem potencia definida
        tempo_atual = None #armazena o horario que a potencia foi lida
        ultima_data = None #armazena a data que a potencia foi lida
        dados_extraidos = [] #lista para armazedar todos os dados extraidos do arquivo .xlsx

        for linha in novas_linhas: #percorre cada linha do arquivo .xlsx
            linha = linha.strip() #remove os espaços indesejados
            if not linha: #linha vazia
                continue  # Ignora linhas vazias

            #print(f"Processando linha: {linha}")  # Debug

            # Verifica se a linha contém a data (horário)
            if re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", linha): #verifica se a linha esta no formato YYYY-MM-DD-HH:SS
                try:
                    ultima_data = datetime.strptime(linha, "%Y-%m-%d %H:%M:%S") #converte a string para um objeto valido
                except ValueError: #verificar se tem erro 
                    print(f"Erro ao processar tempo: {linha}")  #imprime mensagem no referente a linha que contém o erro terminal python

            # Extrai a potência
            if "Power:" in linha: #na linha tem a palavra Power?
                partes = linha.split("Power:") #separa a linha 
                if len(partes) > 1: #consigo pegar apenas o valor da potencia
                    try:
                        potencia_atual = float(partes[1].split('W')[0].strip()) #divide pela unidade watts e pega apenas o valor
                        print(f"Potência detectada: {potencia_atual} W")  #imprime mensagem no terminal com o valor da potência python
                    except ValueError: #verificar se tem erro 
                        print(f"Erro ao processar potência: {linha}")  #imprime mensagem de erro no terminal do python com o valor da linha de potência errado 
                        
            if "PF:" in linha: #na linha tem a palavra PF?
                partes = linha.split("PF:") #separa a linha 
                if len(partes) > 1: #consigo pegar apenas o valor do fator de potencia
                    try:
                        fator_potencia_atual = float(partes[1].strip()) #pega apenas o valor
                        print(f"Fator de Potência: {fator_potencia_atual}")  #imprime mensagem no terminal com o valor do fator de potencia
                    except ValueError: #verificar se tem erro 
                        print(f"Erro ao processar FP: {linha}")  #imprime mensagem no terminal com a linha que tem o valor do fator de potencia errado

        if ultima_data is not None:
            tempo_atual = ultima_data #passa um valor válido

        delta_t = 0 # variavel que armaeza o tempo decorrido  entre duas amostras 

        
        if teste_iniciado: #verifica  inicialização do teste
            if horario_inicio_teste is None: #o teste acaba de começar
                horario_inicio_teste = datetime.now()  # Define a hora inicial apenas na primeira vez
            elif not teste_pausado: #verifica se o botao de pausa foi pressionado
                tempo_decorrido += datetime.now() - horario_inicio_teste  # Acumula o tempo corretamente
                horario_inicio_teste = datetime.now()  # Atualiza para continuar a contagem

       
        tempo_decorrido_str = str(tempo_decorrido).split('.')[0]  # Converte tempo decorrido para string sem milissegundos
        tempo_decorrido_segundos = tempo_decorrido.total_seconds() #converte o tempo para segundos

       
        if tempo_decorrido_segundos > 0 and potencia_atual is not None and potencia_atual > 0:  # Evita divisão por zero e só calcula se a potência for maior que zero
            consumo_mensal_estimado = ((energia_acumulada / tempo_decorrido_segundos) * 30 * 24) # calcula o consumo mensal ao longo do tempo
            consumo_mensal_estimado_kwh = consumo_mensal_estimado / 1000 #converte o consumo para quilo-watt-hora
            custo_estimado = consumo_mensal_estimado * tarifa_energia #calcula o custo mensal por quilo-watt-hora
        else:
            #matém os valores
            consumo_mensal_estimado = consumo_mensal_estimado
            consumo_mensal_estimado_kwh = consumo_mensal_estimado_kwh
            custo_estimado = custo_estimado

        if potencia_atual is not None and tempo_atual is not None: #garante as medições válidas
            soma_potencia += potencia_atual #incrementa o valor de potência média ao longo do tempo
            numero_amostras += 1 if fator_potencia_atual is not None else 0 #incrementa as amostras com valores de fator de potencia validos
            potencia_media = soma_potencia / numero_amostras if numero_amostras > 0 else soma_potencia #se tiver uma amostra calcula a potencia media e evita divisao por zero
            
            if ultima_leitura_tempo is None: #garante que tenha uma leitura de tempo 
                ultima_leitura_tempo = tempo_atual #armazena o primeiro tempo lido
                print("Primeira leitura de tempo registrada.")
            else:
                delta_t = (tempo_atual - ultima_leitura_tempo).total_seconds() #calculo do tempo decorrido entre duas amostras
                ultima_leitura_tempo = tempo_atual #atualiza o tempo que sera referencia par a proxima medição do tempo
            
            #lista que armazena todas as medições registradas no arquivo .xlsx
            dados_extraidos.append({
                'ID': numero_amostras, #numero da sequencia da medição
                'Potencia': potencia_atual, #valor da potencia
                'Horario': tempo_atual, #data e horario da medição
                'Delta': delta_t #tempo entre as medições em segundos
            })
            
            #imprime os dados na tela de consumo energetico
            texto = (
                f"Soma da Potência: {soma_potencia:.2f} W\n"
                f"Número de Amostras: {numero_amostras}\n"
                f"Média da Potência: {potencia_media:.2f} W\n"
                f"Fator de Potência Atual: {fator_potencia_atual:.2f}\n"
                f"Energia Consumida (Integral): {energia_acumulada:.6f} Wh\n"
                f"Tempo Decorrido do Teste: {tempo_decorrido_str}\n"
                f"Tempo Decorrido do Teste em Segundos: {tempo_decorrido_segundos}\n"
                f"Consumo Mensal Estimado em Wh: {consumo_mensal_estimado:.2f} Wh\n"
                f"Consumo Mensal Estimado em kWh: {consumo_mensal_estimado_kwh:.2f} kWh\n"
                f"Custo Estimado do kWh: R$ {custo_estimado:.2f}\n"
            )
            label_resultados.config(text=texto) #exibe as informações em tempo real na tela de consumo energetico

        if dados_extraidos: #se tiver dados registrados na lista
            df = pd.read_excel(nome_arquivo) # lê as linhas existentes no Excel
            
            for dado in dados_extraidos: #lista que armazena os dados coletados
                last_row = len(df) + 2  # +2 porque os índices do Excel começam em 1 e há cabeçalhos
                
                sheet.range(f'A{last_row}').value = [dado['ID'], dado['Potencia'], dado['Horario'], dado['Delta']] #começa na célula A e escreve os dados na linha certa
                sheet.range(f'C{last_row}').number_format = 'dd-mm hh:mm:ss' #na célula C é aplicado a data e hora

                # Calcula Pmed (Média entre potências consecutivas)
                if last_row > 2:  # Só calcula a média a partir da segunda linha
                    p1 = sheet.range(f'B{last_row - 1}').value  # Potência anterior
                    p2 = dado['Potencia']  # Potência atual
                    if p1 is not None: #garante que tenha valor de potencia
                        pmed = (p1 + p2) / 2 #calcula a media entre duas potencias
                        sheet.range(f'E{last_row}').value = pmed # o valor é escrito na coluna E da linha atual
                    else:
                        sheet.range(f'E{last_row}').value = ""  # Deixar vazio se não puder calcular

                # Calcula Energia de cada intervalo
                pmed_atual = sheet.range(f'E{last_row}').value  # a potencia media é obtida a partir da coluna E
                delta_atual = dado['Delta']  # obtém o valor do tempo decorrido
                if pmed_atual is not None and delta_atual > 0: #só calcula se tiver valor de potencia e evita divisão por zero
                    energia = (pmed_atual * delta_atual) / 3600  # Converte para Wh
                    sheet.range(f'F{last_row}').value = energia #a energia consumida é escrita na coluna F do arquivo .xlsx

                    # Somando energia acumulada
                    if last_row > 2: #garante que tem dados de medição de energia
                        energia_anterior = sheet.range(f'G{last_row - 1}').value  # Energia acumulada anterior na célula G
                        energia_acumulada = (energia_anterior if energia_anterior else 0) + energia  #se a energia anterir for None assume 0 e soma  ao valor anterior para acumular a energia
                        sheet.range(f'G{last_row}').value = energia_acumulada #a energia acumulada é armazenada na coluna G do arquivo .xlsx
                    else:
                        sheet.range(f'G{last_row}').value = energia  # Primeira entrada

            wb.save()  # Salva o arquivo
            print(f"Arquivo '{nome_arquivo}' atualizado com os novos dados.")  #imprime mensagem no terminal com o nome do arquivo criado

    except Exception as e: # verifica erro no try
        print(f"Erro inesperado: {e}") #exibe mensagem de erro no terminal python

    janela.after(1000, monitorar_arquivo)  # Chama novamente após 1s

def salvar_dados(linha):
    """Salva uma linha de dados no arquivo atual."""
    verificar_novo_arquivo() #verifica se ja tem um arquivo e cria se necessário
    with open(arquivo_atual, 'a') as arquivo:  #abre o arquivo para adicionar os dados no final
        arquivo.write(f"{linha}\n") #escreve a linha recebendo e adiciona uma nova linha
        
def salvar_linha_em_arquivo(linha):
    """Salva a linha no arquivo apropriado."""
    verificar_novo_arquivo() #verifica se ja tem um arquivo e cria se necessário
    with open(arquivo_atual, 'a') as arquivo: #abre o arquivo para adicionar os dados no final
        arquivo.write(f"{linha}\n") #escreve a linha recebendo e adiciona uma nova linha
        arquivo.flush()
        
def gerar_relatorio():
    """Gera um relatório contendo os dados do teste. Salva as informações contidas no arquivo .txt"""
    pausas = "\n".join(horarios_pausa) if horarios_pausa else "Nenhuma pausa registrada." #Captura a lista dos horários de pausa
    continuacoes = "\n".join(horarios_continuacao) if horarios_continuacao else "Nenhuma continuação registrada." #Captura a lista dos horários de continuação
    atualizacoes = "\n".join(horarios_atualizacao) if horarios_atualizacao else "Nenhuma atualização registrada." #Captura a lista dos horários de atualização

    # Captura os dados relevantes do teste
    refrigerador_testado = item_testado_label.cget("text") #captura o nome do refrigerador cadastrado pelo label da tela do analisador
    data_hora_inicio = horario_inicio_formatado or "Indefinido" #captura o horario e data de inicio de teste da tela do analisador
    data_hora_fim = horario_finalizar or "Indefinido" #captura o horario e data de fim de teste da tela do analisador
    energia_consumida = energia_label.cget("text") #captura o valor da média móvel da energia consumida pelo label da tela do analisador
    custo_total = custo_teste_label.cget("text") #captura o valor da média móvel do custo total da energia consumida pelo label da tela do analisador
    rendimento = rendimento_label.cget("text") #captura o valor da média móvel do rendimento pelo label da tela do analisador
    erro_absoluto_rendimento = erro_absoluto_rendimento_label.cget("text") #captura o valor da média móvel de erro absoluto do rendimento pelo label da tela do analisador
    erro_relativo_rendimento = erro_relativo_rendimento_label.cget("text") #captura o valor da média móvel de erro relativo do rendimento pelo label da tela do analisador
    consumo_mensal = consumo_mensal_label.cget("text") #captura o valor da média móvel do consumo mensal pelo label da tela do analisador
    erro_absoluto_consumo = erro_absoluto_consumo_label.cget("text") #captura o valor da média móvel de erro absoluto do consumo pelo label da tela do analisador
    erro_relativo_consumo = erro_relativo_consumo_label.cget("text") #captura o valor da média móvel de erro relativo do consumo pelo label da tela do analisador
    custo_mensal = custo_mensal_label.cget("text") #captura o valor da média móvel do custo mensal pelo label da tela do analisador

    # Captura as transições de alertas
    transicoes_consumo = "\n".join(transicoes_alertas_consumo) if transicoes_alertas_consumo else "Nenhuma transição de consumo registrada." #Captura a lista de transições de alertas de consumo
    transicoes_rendimento = "\n".join(transicoes_alertas_rendimento) if transicoes_alertas_rendimento else "Nenhuma transição de rendimento registrada." #Captura a lista de transições de alertas de rendimento
    transicoes_temp1 = "\n".join(transicoes_alertas_temp_sensor_1) if transicoes_alertas_temp_sensor_1 else "Nenhuma transição de temperatura do Sensor 1 registrada." #Captura a lista de transições de alertas de temperatura do sensor 1
    transicoes_temp2 = "\n".join(transicoes_alertas_temp_sensor_2) if transicoes_alertas_temp_sensor_2 else "Nenhuma transição de temperatura do Sensor 2 registrada." #Captura a lista de transições de alertas de temperatura do sensor 2
    transicoes_sensor_porta = "\n".join(transicoes_alertas_sensor_porta) if transicoes_alertas_sensor_porta else "Nenhuma transição do sensor de porta registrada." #Captura a lista de transições de alertas do sensor de porta 

    # Cria o conteúdo do relatório no arquivo .txt
    conteudo_relatorio = f"""
    Relatório de Teste - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} 
    ---------------------------------------------------
    Refrigerador Testado: {refrigerador_testado}
    Início do Teste: {data_hora_inicio}
    Fim do Teste: {data_hora_fim}
    
    Horários de Pausa:
    {pausas}

    Horários de Continuação:
    {continuacoes}

    Horários de Atualização:
    {atualizacoes}

    Energia Consumida: {energia_consumida}
    Custo Total: {custo_total}

    Rendimento: {rendimento}
    Erro Absoluto de Rendimento: {erro_absoluto_rendimento}
    Erro Relativo de Rendimento: {erro_relativo_rendimento}

    Consumo Mensal Estimado: {consumo_mensal}
    Erro Absoluto do Consumo: {erro_absoluto_consumo}
    Erro Relativo do Consumo: {erro_relativo_consumo}
    Custo Mensal Estimado: {custo_mensal}

    ---------------------------------------------------
    Transições de Alertas:

    Consumo:
    {transicoes_consumo}

    Rendimento:
    {transicoes_rendimento}

    Temperatura Sensor 1:
    {transicoes_temp1}

    Temperatura Sensor 2:
    {transicoes_temp2}

    Sensor de Porta:
    {transicoes_sensor_porta}
    ---------------------------------------------------
    """

    # Salva o relatório em um arquivo de texto cujo nome tem o valor da data e do horario atual
    nome_arquivo = f"relatorio_teste_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(nome_arquivo, 'w') as arquivo: #abre o arquivo no modo escrita
        arquivo.write(conteudo_relatorio) #escreve o conteudo do relatorio criado no arquivo .txt

    print(f"Relatório salvo como {nome_arquivo}") #imprime mensagem no terminal python
    messagebox.showinfo("Relatório Gerado", f"O relatório foi salvo como {nome_arquivo}") #mensagem na tela quando o relatorio é gerado

#Método responsável pelo teste personalizado
def abrir_tela_teste_personalizado(): #abre a tela do teste personalizado
    def iniciar_teste_personalizado(): #função para iniciar o teste personalizado 
        global horarios_teste_personalizado #armazena numa variavel global dentro e fora desse método os horarios configurados pelo usuario

        # Verificar se um item está selecionado na lista
        selecionado = lista_refrigeradores.curselection() #captura o indice do refrigerador selecionado na lista
        if not selecionado: #senao for selecionado nenhum refrigerador
            messagebox.showwarning("Atenção", "Você precisa selecionar um refrigerador antes de configurar o teste personalizado!") #emite uma mensagem na tela
            return #evita a execução do restante do código

        dia_selecionado = calendario.get_date() #obtem a data selecionada pelo usuario
        horario_inicio = entrada_inicio.get() #obtem o horario de inicio de teste que foi digitado no campo
        horario_fim = entrada_fim.get() #obtem o horario de fim de teste que foi digitado no camp

        if not horario_inicio or not horario_fim: #senão for escrito corretamente o horario de inicio ou fim
            messagebox.showwarning("Erro", "Por favor, insira os horários de início e fim.")  #emite uma mensagem na tel
            return #evita a execução do restante do código

        horarios_teste_personalizado = { #cria um pacote de dados
            "dia": dia_selecionado, #armazena o dia 
            "inicio": horario_inicio, #armazena o horario de inicio de teste 
            "fim": horario_fim #armazena o horario de fim de teste
        }

        # Atualizar os labels na tela principal
        dia_programado_label.config(text=f"Dia Programado: {dia_selecionado}") #na tela do analisador exibe a informação de dia programado
        horario_inicio_programado_label.config(text=f"Horário de Início: {horario_inicio}") #na tela do analisador exibe a informação de horario de inicio programado
        horario_fim_programado_label.config(text=f"Horário de Fim: {horario_fim}") #na tela do analisador exibe a informação de horario de fim programado

        print(f"Horários Configurados: {horarios_teste_personalizado}") #imprime mensagem no terminal python com o pacote de dados
        janela_personalizada.destroy() #fecha a janela de teste personalizado

        # Iniciar a verificação do horário programado
        verificar_horario_teste() #chama a função que verifica se o horario programado chegou

    janela_personalizada = Toplevel(janela) #é uma janela secundária que abre para configurar o teste personalizado
    janela_personalizada.title("Configurar Teste Personalizado") #nome da janela

    Label(janela_personalizada, text="Selecione o dia:").pack(pady=5) #cria o campo de dia no calendario na janela secundaria com espaçamento no eixo x
    calendario = Calendar(janela_personalizada, selectmode="day", date_pattern="dd/mm/yyyy") #define o formato de data no campo do calendario
    calendario.pack(pady=10) #espaçamento no eixo y entre os campos

    Label(janela_personalizada, text="Horário de Início (HH:MM):").pack(pady=5) #cria o campo de Horario de inicio de teste personalizado no calendario na janela secundaria
    entrada_inicio = tk.Entry(janela_personalizada, width=10) #campo entrada para colocar o horario de inicio de teste personalizado
    entrada_inicio.pack(pady=5) #espaçamento no eixo y entre os campos

    Label(janela_personalizada, text="Horário de Fim (HH:MM):").pack(pady=5) #cria o campo de Horario de fim de teste personalizado no calendario na janela secundaria
    entrada_fim = tk.Entry(janela_personalizada, width=10) #campo entrada para colocar o horario de fim de teste personalizado
    entrada_fim.pack(pady=5) #espaçamento no eixo y entre os campos

    Button(janela_personalizada, text="Iniciar Teste", command=iniciar_teste_personalizado).pack(pady=10) #cria o botão na janela secundario para iniciar o teste personalizado com as informações salvas
    Button(janela_personalizada, text="Cancelar", command=janela_personalizada.destroy).pack(pady=5) #cria o botão na janela secundario para cancelar o teste personalizado e nao salva nada

#Método responsável que verifica o horario de teste periodicamente
def verificar_horario_teste():
    global horarios_teste_personalizado, teste_iniciado #variaveis globais a serem utilizadas nesse método e fora dele

    try:
        #Recupera os horários programados vindos do pacote de dados 
        dia = horarios_teste_personalizado.get('dia') #obtém o dia do teste personalizado
        inicio = horarios_teste_personalizado.get('inicio') #obtém o horário de início do teste personalizado
        fim = horarios_teste_personalizado.get('fim') #obtém o horário de fim do teste personalizado

        horario_inicio_dt = datetime.strptime(f"{dia} {inicio}", "%d/%m/%Y %H:%M") #converte dia e inicio do teste personalizado para o objeto datetime
        horario_fim_dt = datetime.strptime(f"{dia} {fim}", "%d/%m/%Y %H:%M") #converte dia e fim do teste personalizado para o objeto datetime
    except (ValueError, TypeError): #tratamento de erros durante a conversão de dados de data e horario
        tempo_restante_label.config(text="Tempo Restante: Configuração inválida") #se tiver erro exibe mensagem
        return #evita a execução do restante do código

    agora = datetime.now() #passa para a variavel agora a data e o horario atual 

    if not teste_iniciado and agora >= horario_inicio_dt: # Verificar se é hora de iniciar o teste apenas uma vez
        tempo_restante_label.config(text="Tempo Restante: Iniciando...") #altera o texto da label e informa na tela que o horario programado foi detectado
        iniciar_teste() #função que inicia o teste de medição do refrigerador
    
    if teste_iniciado and agora >= horario_fim_dt: # Verificar se é hora de finalizar o teste apenas uma vez
        finalizar_teste() #função que finaliza o teste de medição do refrigerador
        tempo_restante_label.config(text="Tempo Restante: Teste finalizado.")
        return #evita a execução do restante do código

    # Atualizar o tempo restante para o próximo evento (contagem regressiva)
    proximo_evento = horario_fim_dt if teste_iniciado else horario_inicio_dt #qual evento deve ser monitorado?
    tempo_restante = (proximo_evento - agora).total_seconds() #calcula o tempo restante até o proximo evento

    if tempo_restante > 0: #se o tempo for maior que 0 o evento ainda nao chegou
        horas, resto = divmod(tempo_restante, 3600)  # o tempo restante é dividido em horas e e segundos que restam
        minutos, segundos = divmod(resto, 60) #converte segundos em minutos e segundos finais
        tempo_restante_label.config(
            text=f"Tempo Restante: {int(horas):02d}:{int(minutos):02d}:{int(segundos):02d}"
        ) # o texto da label é atualizado e exibido em HORAS:MINUTOS:SEGUNDOS
        janela.after(1000, verificar_horario_teste)  # Chama novamente após 1s

#Método que carrega os refrigeradores do arquivo JSON, se existir
def carregar_refrigeradores():
    global refrigeradores #variavel global para ser utilizada aqui ou fora do método
    if os.path.exists(ARQUIVO_JSON): #verifica se o arquivo json esta criado
        with open(ARQUIVO_JSON, "r") as arquivo: #abre o arquivo JSON para ler os dados
            refrigeradores = json.load(arquivo) #os dados são carregados do arquivo JSON e armazena na variavel refrigeradores

#Método que salva os refrigeradores no arquivo JSON
def salvar_refrigeradores():
    with open(ARQUIVO_JSON, "w") as arquivo: #abre o arquivo JSON para escrever os dados
        json.dump(refrigeradores, arquivo, indent=4) # os dados são salvos na variavel refrigeradores com 4 espaços de indentação

#Método que abre a tela de cadastro
def abrir_tela_cadastro():
    def salvar_refrigerador(): #método que salva o refrigerador cadastrado
        nome = entrada_nome.get() #obtém o nome do refrigerador digitado 
        modelo = entrada_modelo.get() #obtém o modelo do refrigerador digitado 
        capacidade = entrada_capacidade.get() #obtém a capacidade do refrigerador digitado 

        if nome and modelo and capacidade: #nome modelo e capacidade foram preenchidos ?
            refrigeradores.append({"nome": nome, "modelo": modelo, "capacidade": capacidade}) #os dados são armazenados numa lista
            salvar_refrigeradores() #chama o método que salva os refrigeradores no arquivo JSON
            messagebox.showinfo("Sucesso", "Refrigerador cadastrado com sucesso!") #emite mensagem na tela confirmando o cadastro do refrigerador
            janela_cadastro.destroy() #fecha a tela de cadastro
            atualizar_lista() #chama o método que atualiza a lista de refrigeradores cadastrados na tela de cadastro
        else:
            messagebox.showwarning("Erro", "Todos os campos devem ser preenchidos.") #emite mensagem de erro tela indicando que o usuario deve preencher todos os campos

    def cancelar_cadastro(): #método que cancela um cadastrod e refrigerador e não salva os dados
        janela_cadastro.destroy() #fecha a tela de cadastro

    janela_cadastro = tk.Toplevel(janela) # Criar uma nova janela para cadastro de refrigerador
    janela_cadastro.title("Cadastrar Refrigerador") #titulo da tela de cadastro

    tk.Label(janela_cadastro, text="Nome:").grid(row=0, column=0, padx=10, pady=5) #cria um rótulo do nome e um posicionamento
    entrada_nome = tk.Entry(janela_cadastro) #cria um campo de entrada de nome 
    entrada_nome.grid(row=0, column=1, padx=10, pady=5) #posicionamento do campo de entrada de nome

    tk.Label(janela_cadastro, text="Modelo:").grid(row=1, column=0, padx=10, pady=5) #cria um rótulo do modelo e um posicionamento
    entrada_modelo = tk.Entry(janela_cadastro) #cria um campo de entrada de modelo
    entrada_modelo.grid(row=1, column=1, padx=10, pady=5) #posicionamento do campo de entrada de modelo

    tk.Label(janela_cadastro, text="Capacidade (L):").grid(row=2, column=0, padx=10, pady=5) #cria um rótulo da capacidade em litros e um posicionamento
    entrada_capacidade = tk.Entry(janela_cadastro) #cria um campo de entrada de capacidade
    entrada_capacidade.grid(row=2, column=1, padx=10, pady=5) #posicionamento do campo de entrada de capacidade

    tk.Button(janela_cadastro, text="Salvar", command=salvar_refrigerador).grid(row=3, column=0, padx=10, pady=10) #cria o botão na tela de cadastro para salvar os dados cadastrados e um posicionamento
    tk.Button(janela_cadastro, text="Cancelar", command=cancelar_cadastro).grid(row=3, column=1, padx=10, pady=10) #cria o botão na tela de cadastro para cancelar e não salva os dados e um posicionamento

    # Adicionar os botões de editar e excluir dentro da janela de cadastro
    tk.Button(janela_cadastro, text="Editar Refrigerador", command=abrir_tela_edicao).grid(row=4, column=0, padx=10, pady=10) #cria o botão na tela de cadastro para editar os dados cadastrados e um posicionamento
    tk.Button(janela_cadastro, text="Excluir Refrigerador", command=excluir_refrigerador).grid(row=4, column=1, padx=10, pady=10) #cria o botão na tela de cadastro para excluir os dados cadastrados e um posicionamento

#    
def abrir_tela_edicao():
    selecionado = lista_refrigeradores.curselection()
    if not selecionado:
        messagebox.showwarning("Atenção", "Selecionar um refrigerador para editar!")
        return

    idx = selecionado[0]
    refrigerador = refrigeradores[idx]

    def salvar_edicao():
        nome = entrada_nome.get()
        modelo = entrada_modelo.get()
        capacidade = entrada_capacidade.get()

        if nome and modelo and capacidade:
            refrigeradores[idx] = {"nome": nome, "modelo": modelo, "capacidade": capacidade}
            salvar_refrigeradores()
            messagebox.showinfo("Sucesso", "Refrigerador editado com sucesso!")
            janela_edicao.destroy()
            atualizar_lista()
        else:
            messagebox.showwarning("Erro", "Todos os campos devem ser preenchidos.")

    janela_edicao = tk.Toplevel(janela)
    janela_edicao.title("Editar Refrigerador")

    tk.Label(janela_edicao, text="Nome:").grid(row=0, column=0, padx=10, pady=5)
    entrada_nome = tk.Entry(janela_edicao)
    entrada_nome.insert(0, refrigerador['nome'])
    entrada_nome.grid(row=0, column=1, padx=10, pady=5)

    tk.Label(janela_edicao, text="Modelo:").grid(row=1, column=0, padx=10, pady=5)
    entrada_modelo = tk.Entry(janela_edicao)
    entrada_modelo.insert(0, refrigerador['modelo'])
    entrada_modelo.grid(row=1, column=1, padx=10, pady=5)

    tk.Label(janela_edicao, text="Capacidade (L):").grid(row=2, column=0, padx=10, pady=5)
    entrada_capacidade = tk.Entry(janela_edicao)
    entrada_capacidade.insert(0, refrigerador['capacidade'])
    entrada_capacidade.grid(row=2, column=1, padx=10, pady=5)

    tk.Button(janela_edicao, text="Salvar", command=salvar_edicao).grid(row=3, column=0, padx=10, pady=10)
    tk.Button(janela_edicao, text="Cancelar", command=janela_edicao.destroy).grid(row=3, column=1, padx=10, pady=10)
    
def excluir_refrigerador():
    selecionado = lista_refrigeradores.curselection()
    if not selecionado:
        messagebox.showwarning("Atenção", "Selecione um refrigerador para excluir!")
        return

    idx = selecionado[0]
    resposta = messagebox.askyesno("Confirmação", "Tem certeza que deseja excluir este refrigerador?")
    if resposta:
        del refrigeradores[idx]
        salvar_refrigeradores()
        atualizar_lista()
        messagebox.showinfo("Sucesso", "Refrigerador excluído com sucesso!")

def atualizar_lista():
    """Atualiza a lista de refrigeradores na interface."""
    lista_refrigeradores.delete(0, tk.END)
    for idx, refri in enumerate(refrigeradores, start=1):
        lista_refrigeradores.insert(tk.END, f"{idx}. {refri['nome']} - {refri['modelo']} ({refri['capacidade']}L)")

# Função para calcular a média móvel de uma lista
def media_movel(valores):
    if len(valores) < tamanho_janela:
        return sum(valores) / len(valores) if valores else 0.0
    else:
        return sum(valores[-(tamanho_janela):]) / tamanho_janela

# Variáveis de controle de teste
teste_iniciado = False
horario_inicio_teste = None
tempo_decorrido = timedelta(0)
horario_inicio_formatado = ""  # Variável para manter a data e hora fixas
teste_pausado = False

# Variáveis para armazenar o horário da última transição
horario_transicao_sensor_1 = None
estado_atual_sensor_1 = None

horario_transicao_sensor_2 = None
estado_atual_sensor_2 = None

# Variáveis para armazenar o horário e o estado atual do consumo
horario_transicao_consumo = None
estado_atual_consumo = None

# Variáveis globais para armazenar estado e horário da última atualização
horario_transicao_atualizar = None
estado_atual_atualizar = None

# Variáveis para armazenar o horário e o estado atual do Sensor de Porta
horario_transicao_sensor_porta = None
estado_atual_sensor_porta = None

# Variáveis globais para armazenar data e horário de "Pausar", "Continuar" e "Finalizar"
horario_continuar = ""
horario_pausar = ""
horario_finalizar = ""


def iniciar_teste():
    """Inicia o teste, verificando se há itens cadastrados e selecionados."""
    global teste_iniciado, horario_inicio_teste, horario_inicio_formatado, tempo_decorrido

    # Zerar os valores de energia, custo_teste e os labels de pausar e finalizar ao iniciar um novo teste
    energia_label.config(text="Energia: 0.000000 kWh")
    custo_teste_label.config(text="Custo Total: R$ 0.00")
    pausar_label.config(text="Pausado em: N/A")
    finalizar_label.config(text="Finalizado em: N/A")
    
    # Zerar variáveis relacionadas ao tempo
    tempo_decorrido = timedelta(0)
    horario_inicio_teste = None
    
    # Verifica se há refrigeradores cadastrados
    if not refrigeradores:
        messagebox.showwarning("Atenção", "Você precisa cadastrar pelo menos um refrigerador antes de iniciar o teste!")
        return

    # Verifica se um item está selecionado na lista
    selecionado = lista_refrigeradores.curselection()
    if not selecionado:
        messagebox.showwarning("Atenção", "Selecione um refrigerador antes de iniciar o teste!")
        return

    # Extração do índice selecionado
    idx = selecionado[0]  # Pega o primeiro índice da tupla retornada
    print(f"Índice selecionado: {idx}")  # Para depuração, remova após verificar

    if not teste_iniciado:
        # Configuração inicial do teste
        teste_iniciado = True
        horario_inicio_teste = datetime.now()
        horario_inicio_formatado = horario_inicio_teste.strftime('%d-%m-%Y %H:%M:%S')

        # Atualiza o label com o índice e detalhes do refrigerador
        refrigerador = refrigeradores[idx]
        item_testado_label.config(
            text=f"Item testado: {idx + 1}. {refrigerador['nome']} - {refrigerador['modelo']}"
        )

        atualizar_dados()
        #messagebox.showinfo("Início do Teste", "Teste iniciado com sucesso!")

        # Atualizar estados dos botões
        pausar_button.config(state=tk.NORMAL)
        finalizar_button.config(state=tk.NORMAL)
        continuar_button.config(state=tk.DISABLED)



 
# Configuração da janela principal
janela = tk.Tk()
janela.title("Cadastro de Refrigeradores")

# Carregar os refrigeradores salvos
carregar_refrigeradores()

tk.Button(janela, text="Cadastrar Refrigerador", command=abrir_tela_cadastro).pack(pady=10)

lista_refrigeradores = tk.Listbox(janela, width=50, height=10)
lista_refrigeradores.pack(pady=10)
atualizar_lista()

#tk.Button(janela, text="Iniciar Teste", command=iniciar_teste).pack(pady=10) 
# Adicionar o botão de Iniciar Teste Personalizado ao lado de Iniciar Teste
tk.Button(janela, text="Iniciar Teste", command=iniciar_teste).pack(side=tk.LEFT, padx=5, pady=10)
tk.Button(janela, text="Iniciar Teste Personalizado", command=abrir_tela_teste_personalizado).pack(side=tk.LEFT, padx=5, pady=10)

def continuar_teste():
    """Retoma o teste após ter sido pausado."""
    global teste_iniciado, horario_inicio_teste, horario_continuar, horarios_continuacao
    if not teste_iniciado:
        teste_iniciado = True
        horario_inicio_teste = datetime.now()
        horario_continuar = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
        continuar_label.config(text=f"Continuado em: {horario_continuar}")

        # Salvar o horário de continuação na lista
        horarios_continuacao.append(horario_continuar)

        pausar_button.config(state=tk.NORMAL)
        continuar_button.config(state=tk.DISABLED)
        #messagebox.showinfo("Teste Retomado", "O teste foi retomado com sucesso!")
        
def pausar_teste():
    """Pausa o teste."""
    global teste_iniciado, tempo_decorrido, horario_pausar, horarios_pausa
    if teste_iniciado:
        teste_iniciado = False
        tempo_decorrido += datetime.now() - horario_inicio_teste
        horario_pausar = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
        pausar_label.config(text=f"Pausado em: {horario_pausar}")

        # Salvar o horário de pausa na lista
        horarios_pausa.append(horario_pausar)

        pausar_button.config(state=tk.DISABLED)
        finalizar_button.config(state=tk.NORMAL)
        continuar_button.config(state=tk.NORMAL)

        
# Chamar a função ao finalizar o teste
def finalizar_teste():
    global teste_iniciado, tempo_decorrido, horario_inicio_teste, horario_finalizar
    if teste_iniciado:
        tempo_decorrido += datetime.now() - horario_inicio_teste
    teste_iniciado = False
    horario_inicio_teste = None
    horario_finalizar = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    finalizar_label.config(text=f"Finalizado em: {horario_finalizar}")

    #messagebox.showinfo("Teste Finalizado", "O teste foi finalizado com sucesso!")

    # Gerar o relatório ao finalizar o teste
    gerar_relatorio()

    # Atualizar estados dos botões
    pausar_button.config(state=tk.DISABLED)
    finalizar_button.config(state=tk.DISABLED)
    continuar_button.config(state=tk.DISABLED)

def atualizar_tempo_decorrido():
    if teste_iniciado:
        tempo_atual = datetime.now() - horario_inicio_teste + tempo_decorrido
    else:
        tempo_atual = tempo_decorrido

    # Exibe o tempo decorrido e a data/hora de início, que fica fixa
    tempo_decorrido_label.config(text=f"Tempo Decorrido: {str(tempo_atual).split('.')[0]} | Iniciado em: {horario_inicio_formatado}")
    janela.after(1000, atualizar_tempo_decorrido)

def verificar_histerese(consumo_mensal_kWh):
    global horario_transicao_consumo, estado_atual_consumo
    horario_atual = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    novo_estado = None

    if consumo_mensal_kWh < limite_inferior_consumo:
        novo_estado = "abaixo"
        status_label_alerta.config(text=f"Alerta: Consumo abaixo da média! {horario_transicao_consumo or horario_atual}", fg="blue")
    elif consumo_mensal_kWh > limite_superior_consumo:
        novo_estado = "acima"
        status_label_alerta.config(text=f"Alerta: Consumo acima da média! {horario_transicao_consumo or horario_atual}", fg="red")
    else:
        novo_estado = "dentro"
        status_label_alerta.config(text=f"Consumo dentro da média esperada. {horario_transicao_consumo or horario_atual}", fg="green")

    # Atualiza o horário de transição e registra a transição
    if novo_estado != estado_atual_consumo:
        estado_atual_consumo = novo_estado
        transicoes_alertas_consumo.append(f"Transição de Consumo: {novo_estado} em {horario_atual}")
        horario_transicao_consumo = horario_atual

 
def verificar_rendimento(rendimento_potencia):
    global horario_transicao_rendimento, estado_atual_rendimento
    horario_atual = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    novo_estado = None

    if rendimento_potencia < limite_inferior_rendimento:
        novo_estado = "abaixo"
        status_label_rendimento.config(
            text=f"Alerta: Rendimento abaixo do limite! {horario_transicao_rendimento or horario_atual}",
            fg="blue"
        )
    elif rendimento_potencia > limite_superior_rendimento:
        novo_estado = "acima"
        status_label_rendimento.config(
            text=f"Alerta: Rendimento acima do limite! {horario_transicao_rendimento or horario_atual}",
            fg="red"
        )
    else:
        novo_estado = "dentro"
        status_label_rendimento.config(
            text=f"Rendimento dentro do limite esperado. {horario_transicao_rendimento or horario_atual}",
            fg="green"
        )

    # Atualiza o horário de transição e registra a transição
    if novo_estado != estado_atual_rendimento:
        estado_atual_rendimento = novo_estado
        transicoes_alertas_rendimento.append(f"Transição de Rendimento: {novo_estado} em {horario_atual}")
        horario_transicao_rendimento = horario_atual


def verificar_temperatura_sensor_1(media_temperatura):
    global horario_transicao_sensor_1, estado_atual_sensor_1
    horario_atual = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    novo_estado = None

    if media_temperatura < limite_inferior_temperatura_sensor_1:
        novo_estado = "abaixo"
        status_label_temperatura_sensor_1.config(text=f"Alerta: Temperatura do Sensor 1 abaixo da média! {horario_transicao_sensor_1 or horario_atual}", fg="blue")
    elif media_temperatura > limite_superior_temperatura_sensor_1:
        novo_estado = "acima"
        status_label_temperatura_sensor_1.config(text=f"Alerta: Temperatura do Sensor 1 acima da média! {horario_transicao_sensor_1 or horario_atual}", fg="red")
    else:
        novo_estado = "dentro"
        status_label_temperatura_sensor_1.config(text=f"Temperatura do Sensor 1 dentro da média esperada. {horario_transicao_sensor_1 or horario_atual}", fg="green")

    # Atualiza o horário de transição e registra a transição
    if novo_estado != estado_atual_sensor_1:
        estado_atual_sensor_1 = novo_estado
        transicoes_alertas_temp_sensor_1.append(f"Transição de Temperatura Sensor 1: {novo_estado} em {horario_atual}")
        horario_transicao_sensor_1 = horario_atual

def verificar_temperatura_sensor_2(media_temperatura2):
    global horario_transicao_sensor_2, estado_atual_sensor_2
    horario_atual = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    novo_estado = None

    if media_temperatura2 < limite_inferior_temperatura_sensor_2:
        novo_estado = "abaixo"
        status_label_temperatura_sensor_2.config(text=f"Alerta: Temperatura do Sensor 2 abaixo da média! {horario_transicao_sensor_2 or horario_atual}", fg="blue")
    elif media_temperatura2 > limite_superior_temperatura_sensor_2:
        novo_estado = "acima"
        status_label_temperatura_sensor_2.config(text=f"Alerta: Temperatura do Sensor 2 acima da média! {horario_transicao_sensor_2 or horario_atual}", fg="red")
    else:
        novo_estado = "dentro"
        status_label_temperatura_sensor_2.config(text=f"Temperatura do Sensor 2 dentro da média esperada. {horario_transicao_sensor_2 or horario_atual}", fg="green")

    # Atualiza o horário de transição e registra a transição
    if novo_estado != estado_atual_sensor_2:
        estado_atual_sensor_2 = novo_estado
        transicoes_alertas_temp_sensor_2.append(f"Transição de Temperatura Sensor 2: {novo_estado} em {horario_atual}")
        horario_transicao_sensor_2 = horario_atual
        
def verificar_sensor_porta(valor_sensor_porta):
    global horario_transicao_sensor_porta, estado_atual_sensor_porta
    horario_atual = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    novo_estado = None

    if valor_sensor_porta == 1:  # Porta aberta
        novo_estado = "aberta"
        sensor_porta_label.config(
            text=f"Alerta: Porta aberta! {horario_transicao_sensor_porta or horario_atual}",
            fg="red"
        )
    elif valor_sensor_porta == 0.0:  # Porta fechada
        novo_estado = "fechada"
        sensor_porta_label.config(
            text=f"Alerta: Porta fechada. {horario_transicao_sensor_porta or horario_atual}",
            fg="green"
        )
    else:
        print(f"Valor inesperado do sensor: {valor_sensor_porta}")
        return

    # Atualiza o estado e registra a transição
    if novo_estado != estado_atual_sensor_porta:
        estado_atual_sensor_porta = novo_estado
        transicoes_alertas_sensor_porta.append(f"Transição: Porta {novo_estado} em {horario_atual}")
        horario_transicao_sensor_porta = horario_atual
        
def calcular_energia():
    global tempo_decorrido, horario_inicio_teste
    if valores_potencia:  # Verifica se há leituras de potência
        if teste_iniciado:
            # Certifique-se de que horario_inicio_teste foi inicializado
            if horario_inicio_teste is None:
                horario_inicio_teste = datetime.now()

            # Atualiza o tempo decorrido
            tempo_decorrido += datetime.now() - horario_inicio_teste
            horario_inicio_teste = datetime.now()  # Atualiza o horário inicial

        # Calcula o tempo em segundos e a energia
        tempo_em_segundos = tempo_decorrido.total_seconds()
        media_potencia = media_movel(valores_potencia)  # Usar a média móvel da potência
        energia = (media_potencia * tempo_em_segundos) / (3600 * 1000)  # Energia em kWh

        # Adiciona uma verificação para ver os valores de energia e potência
        #print(f"Tempo decorrido: {tempo_em_segundos} s, Potência média: {media_potencia} W, Energia: {energia} kWh")

        energia_label.config(text=f"Energia: {energia:.6f} kWh")

        # Cálculo do custo com base na tarifa de energia
        custo_teste = energia * tarifa_energia
        custo_teste_label.config(text=f"Custo Total: R$ {custo_teste:.8f}")
    else:
        energia_label.config(text="Energia (kWh): N/A")
        custo_teste_label.config(text="Custo Total: N/A")

# Função para extrair valores de diferentes tipos das leituras
def extrair_valor(linha, tipo):
    try:
        if tipo == "Power":
            valor_str = linha.replace("Power:", "").replace("W", "").strip()
        elif tipo == "Temperatura":
            valor_str = linha.replace("Temperatura:", "").replace("*C", "").strip()
        elif tipo == "Temperatura2":
            valor_str = linha.replace("Temperatura2:", "").replace("*C", "").strip()
        elif tipo == "Voltage":
            valor_str = linha.replace("Voltage:", "").replace("V", "").strip()
        elif tipo == "Current":
            valor_str = linha.replace("Current:", "").replace("A", "").strip()
        elif tipo == "SensorPorta":
            valor_str = linha.replace("SensorPorta:", "").strip()
        return float(valor_str)
    except ValueError:
        print(f"Erro ao converter valor: {linha}")
        return None

# Função para calcular o rendimento comparando valores médios com nominais
def calcular_rendimento():
    global rendimento_absoluto, rendimento_relativo, estado_atual_rendimento, horario_transicao_rendimento

    if valores_potencia:  # Verifica se há leituras na lista
        # Calcula a média móvel da potência
        media_potencia = media_movel(valores_potencia)

        # Cálculo do rendimento: comparando a potência média com a potência nominal
        rendimento_potencia = (media_potencia / potencia_nominal) * 100 if potencia_nominal != 0 else 0

        # Calcula os erros absolutos e relativos em relação ao rendimento nominal
        rendimento_absoluto = abs(rendimento_potencia - rendimento_nominal)
        rendimento_relativo = (rendimento_absoluto / rendimento_nominal) * 100 if rendimento_nominal != 0 else 0

        # Atualiza os labels de rendimento
        rendimento_label.config(text=f"Rendimento: {rendimento_potencia:.2f}%")
        erro_absoluto_rendimento_label.config(text=f"Diferença Absoluta do Rendimento: {rendimento_absoluto:.2f}%")
        erro_relativo_rendimento_label.config(text=f"Porcentagem Relativa do Rendimento: {rendimento_relativo:.2f}%")

        # Verificar se o rendimento está fora dos limites e exibir alertas
        verificar_rendimento(rendimento_potencia)
    else:
        # Atualiza os labels com valores padrão se não houver leituras
        rendimento_label.config(text="Rendimento: N/A")
        erro_absoluto_rendimento_label.config(text="Diferença Absoluta do Rendimento: N/A")
        erro_relativo_rendimento_label.config(text="Porcentagem Relativa do Rendimento: N/A")


# Função para calcular o consumo mensal estimado com base na potência média
def calcular_consumo_mensal():
    global consumo_absoluto, consumo_relativo
    if valores_potencia:  # Verifica se há leituras de potência
        media_potencia = media_movel(valores_potencia)  # Usar a média móvel
        horas_por_dia = 24  # Supondo uso contínuo por 24 horas
        dias_por_mes = 30  # Aproximação para um mês
        consumo_diario_kWh = (media_potencia / 1000) * horas_por_dia  # Converter watts para kWh
        consumo_mensal_kWh = consumo_diario_kWh * dias_por_mes  # Consumo mensal estimado

        # Verificar alarmes de histerese
        verificar_histerese(consumo_mensal_kWh)

        # Cálculos de erro para o consumo
        consumo_absoluto = abs(consumo_mensal_kWh - consumo_mensal_nominal)
        consumo_relativo = (consumo_absoluto / consumo_mensal_nominal) * 100 if consumo_mensal_nominal != 0 else 0

        consumo_mensal_label.config(text=f"Consumo Mensal Estimado: {consumo_mensal_kWh:.2f} kWh")
        erro_absoluto_consumo_label.config(text=f"Diferença Absoluta do do Consumo: {consumo_absoluto:.2f} kWh")
        erro_relativo_consumo_label.config(text=f"Porcentagem Relativa do do Consumo: {consumo_relativo:.2f} %")

        # Calcular o custo mensal com base no consumo e na tarifa
        custo_mensal = consumo_mensal_kWh * tarifa_energia
        custo_mensal_label.config(text=f"Custo Mensal Estimado: R$ {custo_mensal:.2f}")

        # Calcular a energia total
        calcular_energia()
    else:
        consumo_mensal_label.config(text="Consumo Mensal Estimado: N/A")
        custo_mensal_label.config(text="Custo Mensal Estimado: N/A")
        erro_absoluto_consumo_label.config(text="Consumo Erro Absoluto: N/A")
        erro_relativo_consumo_label.config(text="Consumo Erro Relativo: N/A")
        energia_label.config(text="Energia (Wh): N/A")


# Função para calcular e atualizar as médias utilizando a média móvel
def calcular_medias():
    global sensorporta  # Garantir que a variável global seja acessível
    if valores_potencia:
        media_potencia = media_movel(valores_potencia)
        media_temperatura = media_movel(valores_temperatura)
        media_temperatura2 = media_movel(valores_temperatura2)
        #media_energia = media_movel(valores_energia)
        media_tensao = media_movel(valores_tensao)
        media_corrente = media_movel(valores_corrente)
        media_potencia_aparente = media_movel(valores_potencia_aparente)
        media_potencia_reativa = media_movel(valores_potencia_reativa)
    else:
        #media_potencia = media_temperatura = media_temperatura2 = media_energia = media_tensao = media_corrente = 0.0
        media_potencia = media_temperatura = media_temperatura2 = media_tensao = media_corrente = 0.0

        media_potencia_aparente = media_potencia_reativa = 0.0

    # Atualizar os labels de médias na interface
    media_potencia_label.config(text=f"Média Potência: {media_potencia:.2f} W")
    media_temperatura_label.config(text=f"Média Temperatura: {media_temperatura:.2f} °C")
    media_temperatura2_label.config(text=f"Média Temperatura2: {media_temperatura2:.2f} °C")
    #media_energia_label.config(text=f"Média Energia: {media_energia:.2f} Wh")
    media_tensao_label.config(text=f"Média Tensão: {media_tensao:.2f} V")
    media_corrente_label.config(text=f"Média Corrente: {media_corrente:.2f} A")
    media_potencia_aparente_label.config(text=f"Média Potência Aparente: {media_potencia_aparente:.2f} VA")
    media_potencia_reativa_label.config(text=f"Média Potência Reativa: {media_potencia_reativa:.2f} Var")

    # Calcular e exibir as temperatuas dos sensores
    verificar_temperatura_sensor_1(media_temperatura)
    verificar_temperatura_sensor_2(media_temperatura2)
    
    verificar_sensor_porta(sensorporta)
    
    # Calcular e exibir o rendimento
    calcular_rendimento()

    # Calcular e exibir o consumo mensal estimado e o custo
    calcular_consumo_mensal()

# Função para adicionar valores ao gráfico e somar para calcular as médias
#def adicionar_valores_grafico(potencia, temperatura, temperatura2, energia, tensao, corrente):
def adicionar_valores_grafico(potencia, temperatura, temperatura2, tensao, corrente, sensorporta):
    potencia_aparente = tensao * corrente  # S = V * I
    if potencia_aparente != 0:
        fator_de_potencia = potencia / potencia_aparente  # FP = P / S
    else:
        fator_de_potencia = 0
    potencia_reativa = potencia_aparente * math.sqrt(1 - fator_de_potencia**2) if fator_de_potencia <= 1 else 0

    valores_potencia.append(potencia)
    valores_temperatura.append(temperatura)
    valores_temperatura2.append(temperatura2)
    #valores_energia.append(energia)
    valores_tensao.append(tensao)
    valores_corrente.append(corrente)
    valores_potencia_aparente.append(potencia_aparente)
    valores_potencia_reativa.append(potencia_reativa)
    valores_sensor_porta.append(sensorporta)
    horarios.append(datetime.now().strftime("%H:%M:%S"))

def atualizar_dados():
    global sensorporta, contador_id, dados_buffer

    if teste_iniciado and arduino.in_waiting > 0:
        linha = arduino.readline().decode('utf-8').strip()

        if linha:
            texto_area.insert(tk.END, f"{linha}\n")
            texto_area.see(tk.END)

            # Adicionar linha ao buffer de dados
            dados_buffer.append(linha)

            # Inicializa valores padrões para evitar erros em leituras incompletas
            temperatura = valores_temperatura[-1] if valores_temperatura else 0.0
            temperatura2 = valores_temperatura2[-1] if valores_temperatura2 else 0.0
            tensao = valores_tensao[-1] if valores_tensao else 0.0
            corrente = valores_corrente[-1] if valores_corrente else 0.0
            sensorporta = valores_sensor_porta[-1] if valores_sensor_porta else 0.0

            # Processa os dados recebidos e armazena as leituras mais recentes
            if linha.startswith("Power:"):
                potencia = extrair_valor(linha, "Power")
                if potencia is not None:
                    adicionar_valores_grafico(potencia, temperatura, temperatura2, tensao, corrente, sensorporta)

            elif linha.startswith("Temperatura:"):
                temperatura = extrair_valor(linha, "Temperatura")
                if temperatura is not None:
                    adicionar_valores_grafico(
                        valores_potencia[-1] if valores_potencia else 0.0,
                        temperatura, temperatura2, tensao, corrente, sensorporta
                    )

            elif linha.startswith("Temperatura2:"):
                temperatura2 = extrair_valor(linha, "Temperatura2")
                if temperatura2 is not None:
                    adicionar_valores_grafico(
                        valores_potencia[-1] if valores_potencia else 0.0,
                        temperatura, temperatura2, tensao, corrente, sensorporta
                    )

            elif linha.startswith("Voltage:"):
                tensao = extrair_valor(linha, "Voltage")
                if tensao is not None:
                    adicionar_valores_grafico(
                        valores_potencia[-1] if valores_potencia else 0.0,
                        temperatura, temperatura2, tensao, corrente, sensorporta
                    )

            elif linha.startswith("Current:"):
                corrente = extrair_valor(linha, "Current")
                if corrente is not None:
                    adicionar_valores_grafico(
                        valores_potencia[-1] if valores_potencia else 0.0,
                        temperatura, temperatura2, tensao, corrente, sensorporta
                    )

            elif linha.startswith("SensorPorta:"):
                #print(f"Recebido do Sensor Porta: {linha}")
                sensorporta = extrair_valor(linha, "SensorPorta")
                if sensorporta is not None:
                    adicionar_valores_grafico(
                        valores_potencia[-1] if valores_potencia else 0.0,
                        temperatura, temperatura2, tensao, corrente, sensorporta
                    )
                    sensor_porta_label.config(text=f"Sensor Porta: {sensorporta:.2f}")

            # Se a linha contém "PF:", significa que o conjunto de leituras está completo
            if "PF:" in linha:
                # Gerar horário e ID
                horario_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                # Criar bloco formatado para salvar no arquivo
                bloco_dados = f"ID= {contador_id}\n{horario_atual}\n" + "\n".join(dados_buffer) + "\n\n"

                # Salvar no arquivo
                with open(arquivo_saida, 'a') as arquivo:
                    arquivo.write(bloco_dados)
                    arquivo.flush()

                # Limpar buffer e incrementar ID para a próxima leitura
                dados_buffer.clear()
                contador_id += 1

    janela.after(100, atualizar_dados)  # Repetir a função a cada 100ms

    calcular_medias()  # Atualizar os cálculos das médias após processar os dados

# Função para atualizar as variáveis com base nos valores inseridos
def atualizar_variaveis():
    global tarifa_energia, potencia_nominal, tensao_nominal, rendimento_nominal
    global consumo_mensal_nominal, limite_inferior_consumo, limite_superior_consumo
    global limite_inferior_temperatura_sensor_1, limite_superior_temperatura_sensor_1
    global limite_inferior_temperatura_sensor_2, limite_superior_temperatura_sensor_2
    global limite_inferior_rendimento, limite_superior_rendimento
    global horario_transicao_atualizar, estado_atual_atualizar
    global horarios_atualizacao, transicoes_alertas_consumo

    horario_atual = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    novo_estado = None

    # Lista para registrar todas as alterações realizadas
    parametros_alterados = []

    try:
        # Função para verificar e atualizar os parâmetros
        def atualizar_parametro(nome, entrada, valor_antigo):
            valor_novo = float(entrada.get())
            if valor_novo != valor_antigo:
                parametros_alterados.append(f"{nome}: {valor_antigo} -> {valor_novo}")
                # Adiciona um alerta com o valor alterado
                transicoes_alertas_consumo.append(
                    f"Alteração no parâmetro '{nome}': {valor_antigo} -> {valor_novo} em {horario_atual}"
                )
            return valor_novo

        # Atualizar e registrar cada variável configurável
        tarifa_energia = atualizar_parametro("Tarifa Energia", tarifa_entry, tarifa_energia)
        potencia_nominal = atualizar_parametro("Potência Nominal", potencia_entry, potencia_nominal)
        tensao_nominal = atualizar_parametro("Tensão Nominal", tensao_entry, tensao_nominal)
        rendimento_nominal = atualizar_parametro("Rendimento Nominal", rendimento_entry, rendimento_nominal)
        consumo_mensal_nominal = atualizar_parametro("Consumo Mensal", consumo_entry, consumo_mensal_nominal)
        limite_inferior_consumo = atualizar_parametro("Limite Inferior Consumo", limite_inferior_entry, limite_inferior_consumo)
        limite_superior_consumo = atualizar_parametro("Limite Superior Consumo", limite_superior_entry, limite_superior_consumo)
        limite_inferior_temperatura_sensor_1 = atualizar_parametro(
            "Limite Inferior Temperatura Sensor 1", limite_inferior_temperatura_sensor_1_entry, limite_inferior_temperatura_sensor_1
        )
        limite_superior_temperatura_sensor_1 = atualizar_parametro(
            "Limite Superior Temperatura Sensor 1", limite_superior_temperatura_sensor_1_entry, limite_superior_temperatura_sensor_1
        )
        limite_inferior_temperatura_sensor_2 = atualizar_parametro(
            "Limite Inferior Temperatura Sensor 2", limite_inferior_temperatura_sensor_2_entry, limite_inferior_temperatura_sensor_2
        )
        limite_superior_temperatura_sensor_2 = atualizar_parametro(
            "Limite Superior Temperatura Sensor 2", limite_superior_temperatura_sensor_2_entry, limite_superior_temperatura_sensor_2
        )
        limite_inferior_rendimento = atualizar_parametro(
            "Limite Inferior Rendimento", limite_inferior_rendimento_entry, limite_inferior_rendimento
        )
        limite_superior_rendimento = atualizar_parametro(
            "Limite Superior Rendimento", limite_superior_rendimento_entry, limite_superior_rendimento
        )

        # Salva o horário da atualização
        horarios_atualizacao.append(horario_atual)

        # Atualiza o estado de sucesso e exibe uma mensagem
        novo_estado = "sucesso"
        status_label.config(text=f"Variáveis atualizadas com sucesso! {horario_atual}", fg="green")

    except ValueError:
        # Em caso de erro, registra o estado e exibe uma mensagem
        novo_estado = "erro"
        status_label.config(text=f"Erro: Verifique os valores inseridos. {horario_atual}", fg="red")

    # Atualiza o estado e horário das alterações
    estado_atual_atualizar = novo_estado
    horario_transicao_atualizar = horario_atual

    # Adiciona uma mensagem geral aos alertas
    if parametros_alterados:
        transicoes_alertas_consumo.append(
            f"Atualizações realizadas em {horario_atual}: {', '.join(parametros_alterados)}"
        )




# Configuração da interface Tkinter
janela = tk.Tk()
janela.title("Analisador de Consumo Energético de Refrigeradores em Tempo Real")

# Layout simétrico com Grid
janela.columnconfigure([0, 4], weight=0)

# Botões de controle
#iniciar_button = tk.Button(janela, text="Iniciar Teste", command=iniciar_teste)
#iniciar_button.grid(row=0, column=13, padx=10, pady=5)

continuar_button = tk.Button(janela, text="Continuar Teste", command=continuar_teste, state=tk.DISABLED)
continuar_button.grid(row=9, column=13, padx=10, pady=5)

pausar_button = tk.Button(janela, text="Pausar Teste", command=pausar_teste, state=tk.DISABLED)
pausar_button.grid(row=10, column=13, padx=10, pady=5)

finalizar_button = tk.Button(janela, text="Finalizar Teste", command=finalizar_teste, state=tk.DISABLED)
finalizar_button.grid(row=11, column=13, padx=10, pady=5)

# Label para exibir o horário em que o botão "Pausar" foi pressionado
pausar_label = tk.Label(janela, text="Pausado em: N/A", font=("Arial", 10))
pausar_label.grid(row=1, column=13, padx=10, pady=5)

# Label para exibir o horário em que o botão "Continuar" foi pressionado
continuar_label = tk.Label(janela, text="Continuado em: N/A", font=("Arial", 10))
continuar_label.grid(row=2, column=13, padx=10, pady=5)

# Label para exibir o horário em que o botão "Finalizar" foi pressionado
finalizar_label = tk.Label(janela, text="Finalizado em: N/A", font=("Arial", 10))
finalizar_label.grid(row=3, column=13, padx=10, pady=5)

# Mostrar tempo decorrido
tempo_decorrido_label = tk.Label(janela, text="Tempo Decorrido: 00:00:00", font=("Arial", 10))
#tempo_decorrido_label.grid(row=1, column=0, columnspan=2, padx=10, pady=5)
tempo_decorrido_label.grid(row=0, column=13, padx=10, pady=5)

# Label para indicar o item da lista que está sendo testado
item_testado_label = tk.Label(janela, text="Item testado: N/A", font=("Arial", 10))
item_testado_label.grid(row=0, column=0, padx=10, pady=5)

# Área de texto para exibir os dados recebidos
texto_area = ScrolledText(janela, wrap=tk.WORD, width=60, height=10, font=("Arial", 10))
#texto_area.grid(row=2, column=0, columnspan=2, padx=10, pady=10)
texto_area.grid(row=18, column=0, padx=10, pady=10)


# Labels para exibir médias (organizados em duas colunas)
media_temperatura_label = tk.Label(janela, text="Média Temperatura: N/A", font=("Arial", 10))
media_temperatura_label.grid(row=2, column=0, padx=10, pady=5)

media_temperatura2_label = tk.Label(janela, text="Média Temperatura2: N/A", font=("Arial", 10))
media_temperatura2_label.grid(row=3, column=0, padx=10, pady=5)

media_tensao_label = tk.Label(janela, text="Média Tensão: N/A", font=("Arial", 10))
media_tensao_label.grid(row=4, column=0, padx=10, pady=5)

media_corrente_label = tk.Label(janela, text="Média Corrente: N/A", font=("Arial", 10))
media_corrente_label.grid(row=5, column=0, padx=10, pady=5)

media_potencia_label = tk.Label(janela, text="Média Potência: N/A", font=("Arial", 10))
media_potencia_label.grid(row=6, column=0, padx=10, pady=5)

#media_energia_label = tk.Label(janela, text="Média Energia: N/A", font=("Arial", 10))
#media_energia_label.grid(row=8, column=0, padx=10, pady=5)

media_potencia_aparente_label = tk.Label(janela, text="Média Potência Aparente: N/A", font=("Arial", 10))
media_potencia_aparente_label.grid(row=7, column=0, padx=10, pady=5)

media_potencia_reativa_label = tk.Label(janela, text="Média Potência Reativa: N/A", font=("Arial", 10))
media_potencia_reativa_label.grid(row=8, column=0, padx=10, pady=5)

# Label para exibir o rendimento
rendimento_label = tk.Label(janela, text="Rendimento: N/A", font=("Arial", 10))
rendimento_label.grid(row=9, column=0, padx=10, pady=5)

# Label para exibir o erro absoluto de rendimento
erro_absoluto_rendimento_label = tk.Label(janela, text="Diferença Absoluta do Rendimento: N/A", font=("Arial", 10))
erro_absoluto_rendimento_label.grid(row=10, column=0, padx=10, pady=5)

# Label para exibir o erro relativo de rendimento
erro_relativo_rendimento_label = tk.Label(janela, text="Porcentagem Relativa do Rendimento: N/A", font=("Arial", 10))
erro_relativo_rendimento_label.grid(row=11, column=0, padx=10, pady=5)

# Label para exibir o consumo mensal estimado
consumo_mensal_label = tk.Label(janela, text="Consumo Mensal Estimado: N/A", font=("Arial", 10))
consumo_mensal_label.grid(row=12, column=0, padx=10, pady=5)

# Label para exibir o erro absoluto de consumo mensal
erro_absoluto_consumo_label = tk.Label(janela, text="Diferença Absoluta do Consumo: N/A", font=("Arial", 10))
erro_absoluto_consumo_label.grid(row=13, column=0, padx=10, pady=5)

# Label para exibir o erro relativo de consumo mensal
erro_relativo_consumo_label = tk.Label(janela, text="Porcentagem Relativa do Consumo: N/A", font=("Arial", 10))
erro_relativo_consumo_label.grid(row=14, column=0, padx=10, pady=5)

# Label para exibir o custo mensal estimado
custo_mensal_label = tk.Label(janela, text="Custo Mensal Estimado: N/A", font=("Arial", 10))
custo_mensal_label.grid(row=15, column=0, padx=10, pady=5)

# Adicionar o cálculo de energia na interface Tkinter
energia_label = tk.Label(janela, text="Energia Consumida: N/A", font=("Arial", 10))
energia_label.grid(row=16, column=0, padx=10, pady=5)

# Adicionar o cálculo de custo na interface Tkinter
custo_teste_label = tk.Label(janela, text="Custo Total da Energia: N/A", font=("Arial", 10))
custo_teste_label.grid(row=17, column=0, padx=10, pady=5)

# Campos para definir as variáveis ajustáveis (usando Grid)
tk.Label(janela, text="Tarifa Energia (R$/kWh):").grid(row=1, column=9, padx=10, pady=5)
tarifa_entry = tk.Entry(janela)
tarifa_entry.insert(0, str(tarifa_energia))
tarifa_entry.grid(row=1, column=10, padx=10, pady=5)

tk.Label(janela, text="Potência Nominal (W):").grid(row=2, column=9, padx=10, pady=5)
potencia_entry = tk.Entry(janela)
potencia_entry.insert(0, str(potencia_nominal))
potencia_entry.grid(row=2, column=10, padx=10, pady=5)

tk.Label(janela, text="Tensão Nominal (V):").grid(row=3, column=9, padx=10, pady=5)
tensao_entry = tk.Entry(janela)
tensao_entry.insert(0, str(tensao_nominal))
tensao_entry.grid(row=3, column=10, padx=10, pady=5)

tk.Label(janela, text="Rendimento Nominal (%):").grid(row=4, column=9, padx=10, pady=5)
rendimento_entry = tk.Entry(janela)
rendimento_entry.insert(0, str(rendimento_nominal))
rendimento_entry.grid(row=4, column=10, padx=10, pady=5)

tk.Label(janela, text="Consumo Mensal Nominal (kWh):").grid(row=5, column=9, padx=10, pady=5)
consumo_entry = tk.Entry(janela)
consumo_entry.insert(0, str(consumo_mensal_nominal))
consumo_entry.grid(row=5, column=10, padx=10, pady=5)

# Campos para definir os limites de histerese
tk.Label(janela, text="Limite Inferior do Consumo Mensal Nominal(kWh):").grid(row=6, column=9, padx=10, pady=5)
limite_inferior_entry = tk.Entry(janela)
limite_inferior_entry.insert(0, str(limite_inferior_consumo))
limite_inferior_entry.grid(row=6, column=10, padx=10, pady=5)

tk.Label(janela, text="Limite Superior do Consumo Mensal Nominal (kWh):").grid(row=7, column=9, padx=10, pady=5)
limite_superior_entry = tk.Entry(janela)
limite_superior_entry.insert(0, str(limite_superior_consumo))
limite_superior_entry.grid(row=7, column=10, padx=10, pady=5)

tk.Label(janela, text="Limite Inferior Sensor Temperatura 1 (ºC):").grid(row=8, column=9, padx=10, pady=5)
limite_inferior_temperatura_sensor_1_entry = tk.Entry(janela)
limite_inferior_temperatura_sensor_1_entry.insert(0, str(limite_inferior_temperatura_sensor_1))
limite_inferior_temperatura_sensor_1_entry.grid(row=8, column=10, padx=10, pady=5)

tk.Label(janela, text="Limite Superior Sensor Temperatura 1 (ºC):").grid(row=9, column=9, padx=10, pady=5)
limite_superior_temperatura_sensor_1_entry = tk.Entry(janela)
limite_superior_temperatura_sensor_1_entry.insert(0, str(limite_superior_temperatura_sensor_1))
limite_superior_temperatura_sensor_1_entry.grid(row=9, column=10, padx=10, pady=5)

tk.Label(janela, text="Limite Inferior Sensor Temperatura 2 (ºC):").grid(row=10, column=9, padx=10, pady=5)
limite_inferior_temperatura_sensor_2_entry = tk.Entry(janela)
limite_inferior_temperatura_sensor_2_entry.insert(0, str(limite_inferior_temperatura_sensor_2))
limite_inferior_temperatura_sensor_2_entry.grid(row=10, column=10, padx=10, pady=5)

tk.Label(janela, text="Limite Superior Sensor Temperatura 2 (ºC):").grid(row=11, column=9, padx=10, pady=5)
limite_superior_temperatura_sensor_2_entry = tk.Entry(janela)
limite_superior_temperatura_sensor_2_entry.insert(0, str(limite_superior_temperatura_sensor_2))
limite_superior_temperatura_sensor_2_entry.grid(row=11, column=10, padx=10, pady=5)

# Limite inferior do rendimento (%)
tk.Label(janela, text="Limite Inferior do Rendimento (%):").grid(row=12, column=9, padx=10, pady=5)
limite_inferior_rendimento_entry = tk.Entry(janela)
limite_inferior_rendimento_entry.insert(0, str(limite_inferior_rendimento))
limite_inferior_rendimento_entry.grid(row=12, column=10, padx=10, pady=5)

# Limite superior do rendimento (%)
tk.Label(janela, text="Limite Superior do Rendimento (%):").grid(row=13, column=9, padx=10, pady=5)
limite_superior_rendimento_entry = tk.Entry(janela)
limite_superior_rendimento_entry.insert(0, str(limite_superior_rendimento))
limite_superior_rendimento_entry.grid(row=13, column=10, padx=10, pady=5)

# Botão para atualizar as variáveis
atualizar_button = tk.Button(janela, text="Atualizar Variáveis", command=atualizar_variaveis)
atualizar_button.grid(row=0, column=9, padx=10, pady=10)

# Status da atualização
status_label = tk.Label(janela, text="", font=("Arial", 10))
#status_label.grid(row=0, column=10, padx=10, pady=5)
status_label.grid(row=17, column=13, padx=10, pady=5)

# Status da atualização Alertas
status_label_alerta = tk.Label(janela, text="", font=("Arial", 10))
#status_label_alerta.grid(row=0, column=14, padx=10, pady=5)
status_label_alerta.grid(row=12, column=13, padx=10, pady=5)

# Status da atualização Alertas Sensor de temperatura 1
status_label_temperatura_sensor_1 = tk.Label(janela, text="", font=("Arial", 10))
#status_label_temperatura_sensor_1.grid(row=1, column=14, padx=10, pady=5)
status_label_temperatura_sensor_1.grid(row=13, column=13, padx=10, pady=5)

# Status da atualização Alertas Sensor de temperatura 2
status_label_temperatura_sensor_2 = tk.Label(janela, text="", font=("Arial", 10))
#status_label_temperatura_sensor_2.grid(row=2, column=14, padx=10, pady=5)
status_label_temperatura_sensor_2.grid(row=14, column=13, padx=10, pady=5)

# Status da atualização Alertas Rendimento
status_label_rendimento = tk.Label(janela, text="", font=("Arial", 10))
#status_label_rendimento.grid(row=3, column=14, padx=10, pady=5)
status_label_rendimento.grid(row=15, column=13, padx=10, pady=5)

# Status da atualização Alertas Sensor de Porta
sensor_porta_label = tk.Label(janela, text="", font=("Arial", 10))
#sensor_porta_label.grid(row=4, column=14, padx=10, pady=5)
sensor_porta_label.grid(row=16, column=13, padx=10, pady=5)

##############################################################################################################
# Criar labels para exibir os horários programados
dia_programado_label = tk.Label(janela, text="Dia Programado: N/A", font=("Arial", 10))
dia_programado_label.grid(row=4, column=13, padx=10, pady=5)

horario_inicio_programado_label = tk.Label(janela, text="Horário de Início: N/A", font=("Arial", 10))
horario_inicio_programado_label.grid(row=5, column=13, padx=10, pady=5)

horario_fim_programado_label = tk.Label(janela, text="Horário de Fim: N/A", font=("Arial", 10))
horario_fim_programado_label.grid(row=6, column=13, padx=10, pady=5)

# Criar um label para mostrar o tempo restante para o início do teste
tempo_restante_label = tk.Label(janela, text="Tempo Restante: N/A", font=("Arial", 10))
tempo_restante_label.grid(row=7, column=13, padx=10, pady=5)
##############################################################################################################

#sensor_porta_label = tk.Label(janela, text="Sensor Porta: N/A", font=("Arial", 10))
#sensor_porta_label.grid(row=20, column=0, padx=10, pady=5)


# Configuração da interface gráfica
janela = tk.Tk()
janela.title("Tela de Monitor de Consumo Energético")

# Label para exibir os resultados
label_resultados = tk.Label(janela, text="Aguardando dados...", font=("Arial", 14), justify="left")
label_resultados.pack(pady=20)

# Inicia o monitoramento do arquivo
janela.after(1000, monitorar_arquivo)

# Atualizar o tempo decorrido
atualizar_tempo_decorrido()

# Iniciar a interface
janela.mainloop()

# Fechar a conexão serial ao encerrar a aplicação
arduino.close()

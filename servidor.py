import os
from flask import Flask, request, render_template, redirect, url_for
import numpy as np

# --- CONFIGURAÇÃO ---
PASTA_DOS_ROSTOS = "faces_registradas"
LIMITE_DE_RECONHECIMENTO = 2500 

app = Flask(__name__)

# --- Variável Global "Ponte" ---
# Esta variável é a "ponte" entre o seu navegador e a ESP32.
# Ela vai guardar o nome da próxima pessoa a ser registada.
g_proximo_nome_a_registar = None
# --------------------------------

@app.route("/")
def ola_mundo():
    # Vamos redirecionar a página principal para o nosso novo painel de admin
    return redirect(url_for('painel_admin'))

# --- ROTA 1: MOSTRAR A PÁGINA DE ADMIN ---
@app.route('/admin')
def painel_admin():
    # Esta função simplesmente renderiza o ficheiro admin.html que criámos
    return render_template('admin.html')

# --- ROTA 2: RECEBER O NOME DO ADMIN (O SEU NAVEGADOR CHAMA ESTA) ---
@app.route('/iniciar_registo', methods=['POST'])
def iniciar_registo():
    global g_proximo_nome_a_registar
    # Pega o nome que você digitou no formulário
    nome_da_pessoa = request.form.get('nome')
    
    if not nome_da_pessoa:
        return "Erro: O nome não pode estar vazio.", 400
    
    # "Arma" o sistema: guarda o nome na nossa variável global
    g_proximo_nome_a_registar = nome_da_pessoa
    
    print(f"***** REGISTO INICIADO: Próximo rosto será salvo como '{nome_da_pessoa}' *****")
    
    # Redireciona o seu navegador de volta para a página de admin
    return redirect(url_for('painel_admin'))

# --- ROTA 3: RECEBER OS DADOS DA CÂMERA (A ESP32 CHAMA ESTA) ---
@app.route('/registar_rosto', methods=['POST'])
def registar_rosto():
    global g_proximo_nome_a_registar

    # Verifica se o sistema está "armado" (se um nome foi definido no /iniciar_registo)
    if g_proximo_nome_a_registar is None:
        print("ERRO: Recebi um pedido de registo da ESP32, mas nenhum nome foi preparado no /admin.")
        return "Erro: Nenhum registo foi iniciado no servidor. Vá para a página /admin primeiro.", 400
    
    nome_da_pessoa = g_proximo_nome_a_registar
    dados_do_rosto = request.data
    
    if not os.path.exists(PASTA_DOS_ROSTOS):
        os.makedirs(PASTA_DOS_ROSTOS)
    
    nome_do_ficheiro = f"{nome_da_pessoa}.face"
    caminho_completo = os.path.join(PASTA_DOS_ROSTOS, nome_do_ficheiro)

    with open(caminho_completo, 'wb') as f:
        f.write(dados_do_rosto)
    
    print(f"Sucesso! Assinatura para '{nome_da_pessoa}' (tamanho: {len(dados_do_rosto)} bytes) salva.")
    
    # "Desarma" o sistema para o próximo registo
    g_proximo_nome_a_registar = None
    
    return f"Rosto de {nome_da_pessoa} registado com sucesso!", 200

# --- ROTA 4: RECONHECER (Permanece igual) ---
@app.route('/reconhecer_rosto', methods=['POST'])
def reconhecer_rosto():
    rosto_a_verificar_bytes = request.data
    if not rosto_a_verificar_bytes or len(rosto_a_verificar_bytes) == 0:
        return "Erro: Nenhum dado de rosto foi recebido para verificação.", 400

    try:
        # Tenta carregar o rosto. Se o tamanho for 0, pode dar erro.
        rosto_a_verificar = np.frombuffer(rosto_a_verificar_bytes, dtype=np.int8)

        nome_do_rosto_mais_parecido = "Desconhecido"
        menor_distancia = float('inf') 

        # Verifica se a pasta de rostos existe antes de tentar ler
        if not os.path.exists(PASTA_DOS_ROSTOS):
            os.makedirs(PASTA_DOS_ROSTOS)

        # Percorre todos os ficheiros de rostos já guardados
        for nome_do_ficheiro in os.listdir(PASTA_DOS_ROSTOS):
            if not nome_do_ficheiro.endswith(".face"):
                continue # Ignora outros ficheiros

            caminho_completo = os.path.join(PASTA_DOS_ROSTOS, nome_do_ficheiro)
            
            with open(caminho_completo, 'rb') as f:
                rosto_guardado_bytes = f.read()
                
                # Garante que os ficheiros têm o mesmo tamanho para comparar
                if len(rosto_guardado_bytes) != len(rosto_a_verificar_bytes):
                    print(f"Aviso: Ignorando ficheiro {nome_do_ficheiro} (tamanho incompatível)")
                    continue
                    
                rosto_guardado = np.frombuffer(rosto_guardado_bytes, dtype=np.int8)
                
                distancia = np.linalg.norm(rosto_a_verificar - rosto_guardado)
                
                if distancia < menor_distancia:
                    menor_distancia = distancia
                    nome_do_rosto_mais_parecido = os.path.splitext(nome_do_ficheiro)[0] # Pega o nome sem a extensão .face

        if menor_distancia < LIMITE_DE_RECONHECIMENTO:
            print(f"Rosto reconhecido como: {nome_do_rosto_mais_parecido} (Distância: {menor_distancia})")
            return nome_do_rosto_mais_parecido, 200
        else:
            print(f"Rosto desconhecido. Mais parecido com: {nome_do_rosto_mais_parecido} (Distância: {menor_distancia})")
            return "Rosto Desconhecido", 200

    except Exception as e:
        print(f"Ocorreu um erro durante o reconhecimento: {e}")
        return "Erro interno no servidor", 500


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
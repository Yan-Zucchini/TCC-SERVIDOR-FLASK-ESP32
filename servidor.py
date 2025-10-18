import os
from flask import Flask, request
import numpy as np # Importamos a biblioteca numpy

# --- CONFIGURAÇÃO ---
PASTA_DOS_ROSTOS = "faces_registadas"
# Esta é a nossa 'margem de tolerância'. Se a 'distância' entre dois rostos for menor que este valor,
# consideramos que são a mesma pessoa. Pode ajustar este valor depois de alguns testes.
LIMITE_DE_RECONHECIMENTO = 2500

app = Flask(__name__)

@app.route("/")
def ola_mundo():
    return "Olá, Mundo! O nosso servidor Flask está a funcionar!"

@app.route("/registar_rosto", methods=['POST'])
def registar_rosto():
    nome_da_pessoa = request.args.get('nome')
    if not nome_da_pessoa:
        return "Erro: O nome da pessoa é necessário.", 400

    dados_do_rosto = request.data
    if not dados_do_rosto:
        return "Erro: Nenhum dado de rosto foi recebido.", 400

    if not os.path.exists(PASTA_DOS_ROSTOS):
        os.makedirs(PASTA_DOS_ROSTOS)
    
    nome_do_ficheiro = f"{nome_da_pessoa}.face"
    caminho_completo = os.path.join(PASTA_DOS_ROSTOS, nome_do_ficheiro)

    with open(caminho_completo, 'wb') as f:
        f.write(dados_do_rosto)
    
    print(f"Sucesso! Assinatura para '{nome_da_pessoa}' salva.")
    return f"Rosto de {nome_da_pessoa} registado com sucesso!", 200

# --- NOSSA NOVA ROTA PARA RECONHECER ROSTOS ---
@app.route('/reconhecer_rosto', methods=['POST'])
def reconhecer_rosto():
    rosto_a_verificar_bytes = request.data
    if not rosto_a_verificar_bytes:
        return "Erro: Nenhum dado de rosto foi recebido para verificação.", 400

    try:
        # 1. Carrega a assinatura do rosto recebido para um formato que o numpy entende
        rosto_a_verificar = np.frombuffer(rosto_a_verificar_bytes, dtype=np.int8)

        # 2. Prepara-se para procurar o rosto mais parecido
        nome_do_rosto_mais_parecido = "Desconhecido"
        menor_distancia = float('inf') # Começamos com uma distância infinita

        # 3. Percorre todos os ficheiros de rostos já guardados
        for nome_do_ficheiro in os.listdir(PASTA_DOS_ROSTOS):
            caminho_completo = os.path.join(PASTA_DOS_ROSTOS, nome_do_ficheiro)
            
            with open(caminho_completo, 'rb') as f:
                rosto_guardado_bytes = f.read()
                rosto_guardado = np.frombuffer(rosto_guardado_bytes, dtype=np.int8)
                
                # 4. Calcula a 'distância' entre o rosto a verificar e o rosto guardado
                distancia = np.linalg.norm(rosto_a_verificar - rosto_guardado)
                
                # 5. Se esta distância for a menor que encontrámos até agora, guardamos o nome
                if distancia < menor_distancia:
                    menor_distancia = distancia
                    nome_do_rosto_mais_parecido = os.path.splitext(nome_do_ficheiro)[0]

        # 6. No final, verifica se o rosto mais parecido está dentro da nossa margem de tolerância
        if menor_distancia < LIMITE_DE_RECONHECIMENTO:
            print(f"Rosto reconhecido como: {nome_do_rosto_mais_parecido} (Distância: {menor_distancia})")
            return nome_do_rosto_mais_parecido, 200
        else:
            print(f"Rosto desconhecido. Mais parecido com: {nome_do_rosto_mais_parecido}, mas a distância ({menor_distancia}) é muito alta.")
            return "Rosto Desconhecido", 200

    except Exception as e:
        print(f"Ocorreu um erro durante o reconhecimento: {e}")
        return "Erro interno no servidor", 500


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
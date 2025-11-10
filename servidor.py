import os
from flask import Flask, request, render_template, redirect, url_for, flash
import numpy as np

# --- CONFIGURAÇÃO ---
PASTA_DOS_ROSTOS = "faces_registradas"
LIMITE_DE_RECONHECIMENTO = 4500 # Mantemos o seu limite que funcionou

app = Flask(__name__)
app.secret_key = 'chave_secreta_pode_ser_qualquer_coisa' 

# --- Variável Global "Ponte" ---
g_proximo_nome_a_registar = None
# --------------------------------

@app.route("/")
def ola_mundo():
    return redirect(url_for('painel_admin'))

# --- ROTA c: MOSTRAR A PÁGINA DE ADMIN (COM LEITURA DE ROSTOS) ---
@app.route('/admin')
def painel_admin():
    lista_de_nomes = []
    
    if not os.path.exists(PASTA_DOS_ROSTOS):
        os.makedirs(PASTA_DOS_ROSTOS) 

    for nome_do_ficheiro in os.listdir(PASTA_DOS_ROSTOS):
        if nome_do_ficheiro.endswith(".face"):
            nome_limpo = os.path.splitext(nome_do_ficheiro)[0]
            lista_de_nomes.append(nome_limpo)
            
    lista_de_nomes.sort() 
    
    return render_template('admin.html', lista_rostos=lista_de_nomes)

# --- ROTA 2: RECEBER O NOME DO ADMIN (O SEU NAVEGADOR CHAMA ESTA) ---
@app.route('/iniciar_registo', methods=['POST'])
def iniciar_registo():
    global g_proximo_nome_a_registar
    nome_da_pessoa = request.form.get('nome')
    
    if not nome_da_pessoa:
        flash("Erro: O nome não pode estar vazio.", "error")
        return redirect(url_for('painel_admin'))
    
    nome_do_ficheiro = f"{nome_da_pessoa}.face"
    caminho_completo = os.path.join(PASTA_DOS_ROSTOS, nome_do_ficheiro)
    if os.path.exists(caminho_completo):
        flash(f"Erro: Já existe um rosto registado com o nome '{nome_da_pessoa}'.", "error")
        return redirect(url_for('painel_admin'))

    g_proximo_nome_a_registar = nome_da_pessoa
    
    print(f"***** REGISTO INICIADO: Próximo rosto será salvo como '{nome_da_pessoa}' *****")
    flash(f"Pronto para registar '{nome_da_pessoa}'. Vá à câmera e clique em 'Enroll Face'.", "info")
    
    return redirect(url_for('painel_admin'))


# ==================================================================
# --- ROTA 3 ATUALIZADA: REGISTAR ROSTO (COM FALLBACK) ---
# ==================================================================
@app.route('/registar_rosto', methods=['POST'])
def registar_rosto():
    global g_proximo_nome_a_registar
    dados_do_rosto = request.data
    nome_da_pessoa = None

    if not dados_do_rosto or len(dados_do_rosto) == 0:
        print("Erro: Recebi um pedido de registo sem dados.")
        return "Erro: Nenhum dado de rosto foi recebido.", 400
    
    if not os.path.exists(PASTA_DOS_ROSTOS):
        os.makedirs(PASTA_DOS_ROSTOS)

    # 1. Verifica se um nome foi preparado pelo admin
    if g_proximo_nome_a_registar is not None:
        nome_da_pessoa = g_proximo_nome_a_registar
        g_proximo_nome_a_registar = None # Desarma o sistema
    else:
        # 2. Se não foi, gera um nome automático "userX"
        print("Aviso: Nenhum nome preparado no /admin. A gerar nome de utilizador automático.")
        i = 0
        while True:
            nome_teste = f"user{i}"
            caminho_teste = os.path.join(PASTA_DOS_ROSTOS, f"{nome_teste}.face")
            if not os.path.exists(caminho_teste):
                nome_da_pessoa = nome_teste # Encontrámos um nome vago
                break
            i += 1
        print(f"Nome automático gerado: {nome_da_pessoa}")

    # 3. Salva o ficheiro
    caminho_completo = os.path.join(PASTA_DOS_ROSTOS, f"{nome_da_pessoa}.face")

    # (A verificação de duplicado para o nome do admin já foi feita na Rota 2)
    # Mas vamos adicionar uma para o caso do "userX" por segurança
    if os.path.exists(caminho_completo):
         print(f"Erro: O ficheiro para '{nome_da_pessoa}' já existe (fallback).")
         return f"Erro: O nome '{nome_da_pessoa}' já está registado.", 400

    try:
        with open(caminho_completo, 'wb') as f:
            f.write(dados_do_rosto)
        
        print(f"Sucesso! Assinatura para '{nome_da_pessoa}' (tamanho: {len(dados_do_rosto)} bytes) salva.")
        flash(f"Rosto '{nome_da_pessoa}' registado com sucesso!", "success")
        return f"Rosto de {nome_da_pessoa} registado com sucesso!", 200

    except Exception as e:
        print(f"Ocorreu um erro ao salvar o ficheiro: {e}")
        flash("Erro interno ao salvar o ficheiro.", "error")
        return "Erro interno no servidor ao salvar o ficheiro.", 500
# ==================================================================
# --- FIM DA ROTA 3 ATUALIZADA ---
# ==================================================================


# --- ROTA 4: RECONHECER (Permanece igual) ---
@app.route('/reconhecer_rosto', methods=['POST'])
def reconhecer_rosto():
    rosto_a_verificar_bytes = request.data
    if not rosto_a_verificar_bytes or len(rosto_a_verificar_bytes) == 0:
        return "Erro: Nenhum dado de rosto foi recebido para verificação.", 400

    try:
        rosto_a_verificar = np.frombuffer(rosto_a_verificar_bytes, dtype=np.int8)

        nome_do_rosto_mais_parecido = "Desconhecido"
        menor_distancia = float('inf') 

        if not os.path.exists(PASTA_DOS_ROSTOS):
            os.makedirs(PASTA_DOS_ROSTOS)

        for nome_do_ficheiro in os.listdir(PASTA_DOS_ROSTOS):
            if not nome_do_ficheiro.endswith(".face"):
                continue 

            caminho_completo = os.path.join(PASTA_DOS_ROSTOS, nome_do_ficheiro)
            
            with open(caminho_completo, 'rb') as f:
                rosto_guardado_bytes = f.read()
                
                if len(rosto_guardado_bytes) != len(rosto_a_verificar_bytes):
                    print(f"Aviso: Ignorando ficheiro {nome_do_ficheiro} (tamanho incompatível)")
                    continue
                    
                rosto_guardado = np.frombuffer(rosto_guardado_bytes, dtype=np.int8)
                
                distancia = np.linalg.norm(rosto_a_verificar - rosto_guardado)
                
                if distancia < menor_distancia:
                    menor_distancia = distancia
                    nome_do_rosto_mais_parecido = os.path.splitext(nome_do_ficheiro)[0]

        if menor_distancia < LIMITE_DE_RECONHECIMENTO:
            print(f"Rosto reconhecido como: {nome_do_rosto_mais_parecido} (Distância: {menor_distancia})")
            return nome_do_rosto_mais_parecido, 200
        else:
            print(f"Rosto desconhecido. Mais parecido com: {nome_do_rosto_mais_parecido} (Distância: {menor_distancia})")
            return "Rosto Desconhecido", 200

    except Exception as e:
        print(f"Ocorreu um erro durante o reconhecimento: {e}")
        return "Erro interno no servidor", 500

# --- ROTA 5: APAGAR UM ROSTO (CRUD - DELETE) ---
@app.route('/apagar_rosto/<nome>', methods=['POST'])
def apagar_rosto(nome):
    try:
        nome_do_ficheiro = f"{nome}.face"
        caminho_completo = os.path.join(PASTA_DOS_ROSTOS, nome_do_ficheiro)
        
        if os.path.exists(caminho_completo):
            os.remove(caminho_completo)
            print(f"Rosto '{nome}' apagado com sucesso.")
            flash(f"Rosto '{nome}' apagado com sucesso.", "success")
        else:
            print(f"Erro: Rosto '{nome}' não encontrado para apagar.")
            flash(f"Erro: Rosto '{nome}' não encontrado.", "error")
            
    except Exception as e:
        print(f"Ocorreu um erro ao apagar o ficheiro: {e}")
        flash(f"Erro ao apagar o ficheiro: {e}", "error")

    return redirect(url_for('painel_admin'))

# --- ROTA 6: RENOMEAR UM ROSTO (CRUD - UPDATE) ---
@app.route('/renomear_rosto/<nome_antigo>', methods=['POST'])
def renomear_rosto(nome_antigo):
    novo_nome = request.form.get('novo_nome')

    if not novo_nome:
        flash("Erro: O novo nome não pode estar vazio.", "error")
        return redirect(url_for('painel_admin'))

    if novo_nome == nome_antigo:
        flash("Aviso: O novo nome é igual ao antigo.", "info")
        return redirect(url_for('painel_admin'))

    ficheiro_antigo = os.path.join(PASTA_DOS_ROSTOS, f"{nome_antigo}.face")
    ficheiro_novo = os.path.join(PASTA_DOS_ROSTOS, f"{novo_nome}.face")

    if not os.path.exists(ficheiro_antigo):
        flash(f"Erro: O rosto '{nome_antigo}' não foi encontrado.", "error")
        return redirect(url_for('painel_admin'))
        
    if os.path.exists(ficheiro_novo):
        flash(f"Erro: O nome '{novo_nome}' já está a ser utilizado.", "error")
        return redirect(url_for('painel_admin'))

    try:
        os.rename(ficheiro_antigo, ficheiro_novo)
        print(f"Rosto '{nome_antigo}' renomeado para '{novo_nome}'.")
        flash(f"Rosto '{nome_antigo}' renomeado para '{novo_nome}' com sucesso!", "success")
    except Exception as e:
        print(f"Ocorreu um erro ao renomear: {e}")
        flash(f"Erro ao renomear: {e}", "error")

    return redirect(url_for('painel_admin'))


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
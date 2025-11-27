# Importa a biblioteca 'os', que permite interagir com o sistema operativo (ex: criar pastas, apagar ficheiros, verificar se existem).
import os

# Do pacote 'flask', importa todas as ferramentas específicas que vamos usar.
from flask import Flask, request, render_template, redirect, url_for, flash 

# Flask: É a classe principal que usamos para criar a nossa aplicação web.
# request: É um objeto que guarda os dados de um pedido que acabou de chegar do navegador ou da ESP32 (ex: dados de formulário, ficheiros, ou os bytes do rosto).
# render_template: É a função que carrega um ficheiro .html da pasta 'templates', processa-o e o envia para o navegador.
# redirect: É uma função que diz ao navegador do utilizador: "Vá para este outro URL".
# url_for: É um assistente que constrói um URL para nós, em vez de termos de escrever a string (ex: "/admin") manualmente.
# flash: É a função que nos permite criar mensagens de notificação temporárias (ex: "Sucesso!", "Erro!").

# Importa a biblioteca 'numpy' e dá-lhe o "apelido" de 'np' para ser mais rápido de a chamar.
import numpy as np 

# --- CONFIGURAÇÃO ---

# Define uma variável global constante que guarda o nome da pasta onde as assinaturas de rosto serão guardadas.
PASTA_DOS_ROSTOS = "faces_registradas" 

# Define a nossa "régua" de tolerância. É a distância matemática máxima para um rosto ser considerado uma correspondência.
LIMITE_DE_RECONHECIMENTO = 4500 

# Cria a instância principal da nossa aplicação web. '__name__' é uma variável especial do Python que diz ao Flask onde ele está.
app = Flask(__name__) 

# Define uma "chave secreta" para o Flask. Isto é obrigatório para a função 'flash()' funcionar, pois ela usa sessões seguras.
app.secret_key = 'chave_secreta_pode_ser_qualquer_coisa' 

# --- Variável Global "Ponte" ---

# Cria uma variável global que irá funcionar como uma "ponte" de memória entre o painel de admin e a ESP32.
# 'None' é a palavra do Python para "vazio" ou "nulo".
g_proximo_nome_a_registar = None 
# --------------------------------

# '@app.route' é um "decorador" do Flask. Ele liga a função que vem abaixo a um URL específico.
@app.route("/") 
# Define a função 'ola_mundo' que será executada quando alguém aceder ao URL principal (ex: http://localhost:5000/).
def ola_mundo(): 
    # Diz ao navegador do utilizador para ser redirecionado para o URL associado à função 'painel_admin' (ou seja, "/admin").
    return redirect(url_for('painel_admin')) 

# --- ROTA 1: MOSTRAR A PÁGINA DE ADMIN (COM LEITURA DE ROSTOS) ---
@app.route('/admin') # Liga esta função ao URL /admin.
def painel_admin(): # Define a função 'painel_admin'.
    lista_de_nomes = [] # Cria uma lista vazia que irá guardar os nomes dos rostos que encontrarmos.
    
    # Verifica se a pasta (definida na nossa constante) NÃO existe no disco.
    if not os.path.exists(PASTA_DOS_ROSTOS): 
        os.makedirs(PASTA_DOS_ROSTOS) # Se não existir, cria a pasta.

    # Pede à biblioteca 'os' para listar todos os ficheiros e pastas dentro do caminho 'PASTA_DOS_ROSTOS'.
    for nome_do_ficheiro in os.listdir(PASTA_DOS_ROSTOS): 
        # Para cada ficheiro, verifica se o nome dele termina com ".face".
        if nome_do_ficheiro.endswith(".face"): 
            # Se terminar, usa 'os.path.splitext' para separar o nome da extensão (ex: "Yanzuc.face" -> ["Yanzuc", ".face"]).
            # [0] pega apenas a primeira parte (o nome "Yanzuc").
            nome_limpo = os.path.splitext(nome_do_ficheiro)[0] 
            lista_de_nomes.append(nome_limpo) # Adiciona o nome limpo à nossa lista.
            
    lista_de_nomes.sort() # Organiza a lista de nomes em ordem alfabética.
    
    # Chama a função 'render_template' para carregar o 'admin.html'.
    # Também "injeta" a nossa 'lista_de_nomes' numa variável chamada 'lista_rostos' que o código HTML poderá usar.
    return render_template('admin.html', lista_rostos=lista_de_nomes) 

# --- ROTA 2: RECEBER O NOME DO ADMIN (O SEU NAVEGADOR CHAMA ESTA) ---
# Define a rota '/iniciar_registo' e especifica que ela só aceita pedidos do tipo 'POST' (enviados por um formulário).
@app.route('/iniciar_registo', methods=['POST']) 
def iniciar_registo(): # Define a função.
    global g_proximo_nome_a_registar # Avisa o Python que esta função pretende alterar a variável global que criámos no topo.
    
    # Pega o valor do campo de formulário <input name="nome"> que foi enviado no pedido.
    nome_da_pessoa = request.form.get('nome') 
    
    # Verifica se o nome_da_pessoa está vazio (se o utilizador não digitou nada).
    if not nome_da_pessoa: 
        flash("Erro: O nome não pode estar vazio.", "error") # Cria uma mensagem de erro para ser mostrada no HTML.
        return redirect(url_for('painel_admin')) # Manda o utilizador de volta para a página de admin.
    
    # Cria o nome de ficheiro completo (ex: "Yanzuc.face").
    nome_do_ficheiro = f"{nome_da_pessoa}.face" 
    # Junta o nome da pasta com o nome do ficheiro (ex: "faces_registadas/Yanzuc.face").
    caminho_completo = os.path.join(PASTA_DOS_ROSTOS, nome_do_ficheiro) 
    
    # Verifica se um ficheiro com este nome JÁ EXISTE na pasta.
    if os.path.exists(caminho_completo): 
        flash(f"Erro: Já existe um rosto registado com o nome '{nome_da_pessoa}'.", "error") # Cria uma mensagem de erro.
        return redirect(url_for('painel_admin')) # Manda o utilizador de volta.

    # A "ponte": guarda o nome que recebemos do formulário na nossa variável global.
    g_proximo_nome_a_registar = nome_da_pessoa 
    
    # Imprime uma mensagem no terminal do servidor (o seu terminal) para sabermos que funcionou.
    print(f"***** REGISTO INICIADO: Próximo rosto será salvo como '{nome_da_pessoa}' *****") 
    # Cria uma mensagem "info" para o utilizador, que aparecerá no topo da página de admin.
    flash(f"Pronto para registar '{nome_da_pessoa}'. Vá à câmera e clique em 'Enroll Face'.", "info") 
    
    # Manda o navegador do utilizador de volta para a página de admin.
    return redirect(url_for('painel_admin')) 


# ==================================================================
# --- ROTA 3 ATUALIZADA: REGISTAR ROSTO (COM FALLBACK) ---
# ==================================================================
@app.route('/registar_rosto', methods=['POST']) # A rota que a ESP32 chama para enviar a assinatura do rosto.
def registar_rosto(): # Define a função.
    global g_proximo_nome_a_registar # Avisa que vamos usar (e modificar) a variável global.
    dados_do_rosto = request.data # Pega os dados binários brutos (os 9408 bytes) que a ESP32 enviou no corpo (data) do pedido.
    nome_da_pessoa = None # Inicia a variável de nome como "vazia".

    # Se a ESP32 enviou um pedido sem dados, ou com dados de tamanho 0, rejeita.
    if not dados_do_rosto or len(dados_do_rosto) == 0: 
        print("Erro: Recebi um pedido de registo sem dados.") # Imprime um erro no terminal.
        return "Erro: Nenhum dado de rosto foi recebido.", 400 # Retorna uma mensagem de erro 400 (Bad Request) para a ESP32.
    
    # Garante que a pasta existe (caso tenha sido apagada manualmente).
    if not os.path.exists(PASTA_DOS_ROSTOS): 
        os.makedirs(PASTA_DOS_ROSTOS) # Cria a pasta.

    # 1. Verifica se um nome foi preparado pelo admin
    # Se a nossa variável global NÃO estiver "vazia" (None)...
    if g_proximo_nome_a_registar is not None: 
        nome_da_pessoa = g_proximo_nome_a_registar # ...usa esse nome (ex: "Yanzuc").
        g_proximo_nome_a_registar = None # E "desarma" o sistema, limpando a variável para o próximo registo.
    else: 
        # 2. Se a variável global ESTAVA "vazia", gera um nome automático "userX"
        print("Aviso: Nenhum nome preparado no /admin. A gerar nome de utilizador automático.") # Imprime um aviso no terminal.
        i = 0 # Inicia um contador 'i' em 0.
        while True: # Inicia um loop infinito (que só será quebrado com 'break').
            nome_teste = f"user{i}" # Cria um nome de teste (ex: "user0", "user1", etc.).
            caminho_teste = os.path.join(PASTA_DOS_ROSTOS, f"{nome_teste}.face") # Cria um caminho de ficheiro de teste.
            if not os.path.exists(caminho_teste): # Verifica se um ficheiro com este nome NÃO existe.
                nome_da_pessoa = nome_teste # Se não existir, encontrámos um nome vago! Usamos este.
                break # Quebra o loop infinito.
            i += 1 # Se "user0" já existia, incrementa o 'i' (i=1) e o loop tenta "user1".
        print(f"Nome automático gerado: {nome_da_pessoa}") # Imprime no terminal qual nome foi gerado.

    # 3. Salva o ficheiro
    caminho_completo = os.path.join(PASTA_DOS_ROSTOS, f"{nome_da_pessoa}.face") # Cria o caminho final para salvar o ficheiro.

    # Verificação de segurança para o caso do 'userX' (a de nome de admin já foi feita na Rota 2).
    if os.path.exists(caminho_completo): 
         print(f"Erro: O ficheiro para '{nome_da_pessoa}' já existe (fallback).") # Log de erro.
         return f"Erro: O nome '{nome_da_pessoa}' já está registado.", 400 # Retorna erro 400 para a ESP32.

    try: # Inicia um bloco "try...except" para apanhar erros de escrita no disco.
        # Abre o ficheiro no caminho completo em modo 'wb' (write binary / escrita binária).
        with open(caminho_completo, 'wb') as f: 
            f.write(dados_do_rosto) # Escreve os bytes brutos da assinatura no ficheiro.
        
        print(f"Sucesso! Assinatura para '{nome_da_pessoa}' (tamanho: {len(dados_do_rosto)} bytes) salva.") # Log de sucesso.
        flash(f"Rosto '{nome_da_pessoa}' registado com sucesso!", "success") # Cria uma notificação de sucesso para a página /admin.
        return f"Rosto de {nome_da_pessoa} registado com sucesso!", 200 # Retorna uma mensagem de sucesso 200 (OK) para a ESP32.

    except Exception as e: # Se algo der errado ao tentar salvar o ficheiro.
        print(f"Ocorreu um erro ao salvar o ficheiro: {e}") # Imprime o erro no terminal.
        flash("Erro interno ao salvar o ficheiro.", "error") # Cria uma notificação de erro.
        return "Erro interno no servidor ao salvar o ficheiro.", 500 # Retorna um erro 500 (Server Error) para a ESP32.
# ==================================================================
# --- FIM DA ROTA 3 ATUALIZADA ---
# ==================================================================


# --- ROTA 4: RECONHECER (Permanece igual) ---
@app.route('/reconhecer_rosto', methods=['POST']) # Define a rota que a ESP32 chama para reconhecer um rosto.
def reconhecer_rosto(): # Define a função.
    rosto_a_verificar_bytes = request.data # Pega os bytes da assinatura do rosto que a ESP32 acabou de ver.
    
    # Se não recebeu dados, retorna um erro.
    if not rosto_a_verificar_bytes or len(rosto_a_verificar_bytes) == 0: 
        return "Erro: Nenhum dado de rosto foi recebido para verificação.", 400

    try: # Inicia um bloco "try...except" para apanhar erros de matemática ou de leitura de ficheiros.
        
        # 1. Carrega a assinatura do rosto recebido para um formato que o numpy entende
        # Converte os bytes brutos (b'...') num vetor de números (dtype=np.int8) para o cálculo.
        rosto_a_verificar = np.frombuffer(rosto_a_verificar_bytes, dtype=np.int8) 

        # 2. Prepara-se para procurar o rosto mais parecido
        nome_do_rosto_mais_parecido = "Desconhecido" # Começa assumindo que não conhece o rosto.
        menor_distancia = float('inf') # Inicia a "menor distância" como um número infinito.

        # Garante que a pasta existe (caso o servidor tenha sido iniciado sem rostos registados).
        if not os.path.exists(PASTA_DOS_ROSTOS): 
            os.makedirs(PASTA_DOS_ROSTOS) # Cria a pasta.

        # 3. Percorre todos os ficheiros de rostos já guardados
        for nome_do_ficheiro in os.listdir(PASTA_DOS_ROSTOS): # Faz um loop por cada ficheiro na pasta.
            if not nome_do_ficheiro.endswith(".face"): # Ignora qualquer ficheiro que não seja .face (ex: .DS_Store, etc.).
                continue # Pula para o próximo item do loop.

            caminho_completo = os.path.join(PASTA_DOS_ROSTOS, nome_do_ficheiro) # Monta o caminho para o ficheiro.
            
            with open(caminho_completo, 'rb') as f: # Abre o ficheiro em modo 'rb' (read binary / leitura binária).
                rosto_guardado_bytes = f.read() # Lê todos os bytes do ficheiro guardado.
                
                # Garante que os ficheiros têm o mesmo tamanho para comparar (evita o erro "broadcast").
                if len(rosto_guardado_bytes) != len(rosto_a_verificar_bytes): 
                    print(f"Aviso: Ignorando ficheiro {nome_do_ficheiro} (tamanho incompatível)") # Imprime um aviso.
                    continue # Pula este ficheiro, pois ele tem um tamanho diferente.
                    
                # Converte os bytes do ficheiro guardado num vetor numpy.
                rosto_guardado = np.frombuffer(rosto_guardado_bytes, dtype=np.int8) 
                
                # 4. Calcula a 'distância' entre o rosto a verificar e o rosto guardado
                # Esta é a matemática principal: calcula a Distância Euclidiana (a norma L2) entre os dois vetores.
                distancia = np.linalg.norm(rosto_a_verificar - rosto_guardado) 
                
                # 5. Se esta distância for a menor que encontrámos até agora...
                if distancia < menor_distancia: 
                    menor_distancia = distancia # ...atualiza a 'menor_distancia'.
                    nome_do_rosto_mais_parecido = os.path.splitext(nome_do_ficheiro)[0] # ...e guarda o nome deste rosto.

        # 6. No final, verifica se o rosto mais parecido está dentro da nossa margem de tolerância
        if menor_distancia < LIMITE_DE_RECONHECIMENTO: # Se a menor distância for menor que a nossa "régua" (4500).
            print(f"Rosto reconhecido como: {nome_do_rosto_mais_parecido} (Distância: {menor_distancia})") # Log de sucesso.
            return nome_do_rosto_mais_parecido, 200 # Retorna o nome da pessoa para a ESP32.
        else: # Se a menor distância for maior que a "régua".
            print(f"Rosto desconhecido. Mais parecido com: {nome_do_rosto_mais_parecido}, mas a distância ({menor_distancia}) é muito alta.") # Log de falha.
            return "Rosto Desconhecido", 200 # Retorna "Rosto Desconhecido" para a ESP32.

    except Exception as e: # Se qualquer coisa no bloco 'try' falhar (ex: um ficheiro corrompido).
        print(f"Ocorreu um erro durante o reconhecimento: {e}") # Imprime o erro.
        return "Erro interno no servidor", 500 # Retorna um erro 500 para a ESP32.

# --- ROTA 5: APAGAR UM ROSTO (CRUD - DELETE) ---
# Esta rota usa um URL dinâmico. O <nome> na URL será passado como um argumento para a função.
@app.route('/apagar_rosto/<nome>', methods=['POST']) 
def apagar_rosto(nome): # A função recebe a variável 'nome' diretamente da URL.
    try: # Inicia um bloco try/except para o caso de erros ao apagar.
        nome_do_ficheiro = f"{nome}.face" # Cria o nome do ficheiro a ser apagado.
        caminho_completo = os.path.join(PASTA_DOS_ROSTOS, nome_do_ficheiro) # Monta o caminho.
        
        if os.path.exists(caminho_completo): # Verifica se o ficheiro realmente existe.
            os.remove(caminho_completo) # Apaga o ficheiro do disco.
            print(f"Rosto '{nome}' apagado com sucesso.") # Log de sucesso.
            flash(f"Rosto '{nome}' apagado com sucesso.", "success") # Notificação de sucesso para o admin.
        else: # Se o ficheiro não foi encontrado (ex: o utilizador recarregou a página).
            print(f"Erro: Rosto '{nome}' não encontrado para apagar.") # Log de erro.
            flash(f"Erro: Rosto '{nome}' não encontrado.", "error") # Notificação de erro.
            
    except Exception as e: # Se der um erro de permissão ou outro problema ao apagar.
        print(f"Ocorreu um erro ao apagar o ficheiro: {e}") # Log do erro.
        flash(f"Erro ao apagar o ficheiro: {e}", "error") # Notificação de erro.

    return redirect(url_for('painel_admin')) # Manda o utilizador de volta para a página de admin (que irá recarregar a lista).

# --- ROTA 6: RENOMEAR UM ROSTO (CRUD - UPDATE) ---
@app.route('/renomear_rosto/<nome_antigo>', methods=['POST']) # Rota que recebe o nome antigo pela URL.
def renomear_rosto(nome_antigo): # A função recebe o 'nome_antigo' da URL.
    novo_nome = request.form.get('novo_nome') # Pega o 'novo_nome' do formulário que foi enviado.

    if not novo_nome: # Verifica se o campo "novo nome" não está vazio.
        flash("Erro: O novo nome não pode estar vazio.", "error") # Notificação de erro.
        return redirect(url_for('painel_admin')) # Manda de volta.

    if novo_nome == nome_antigo: # Verifica se o utilizador tentou renomear para o mesmo nome.
        flash("Aviso: O novo nome é igual ao antigo.", "info") # Notificação de aviso.
        return redirect(url_for('painel_admin')) # Manda de volta.

    # Monta o caminho do ficheiro antigo e do novo ficheiro.
    ficheiro_antigo = os.path.join(PASTA_DOS_ROSTOS, f"{nome_antigo}.face") 
    ficheiro_novo = os.path.join(PASTA_DOS_ROSTOS, f"{novo_nome}.face") 

    if not os.path.exists(ficheiro_antigo): # Garante que o ficheiro antigo ainda existe.
        flash(f"Erro: O rosto '{nome_antigo}' não foi encontrado.", "error")
        return redirect(url_for('painel_admin'))
        
    if os.path.exists(ficheiro_novo): # Garante que o novo nome já não está a ser usado por outro ficheiro.
        flash(f"Erro: O nome '{novo_nome}' já está a ser utilizado.", "error")
        return redirect(url_for('painel_admin'))

    try: # Tenta fazer a operação de renomear.
        os.rename(ficheiro_antigo, ficheiro_novo) # O comando principal que renomeia o ficheiro no disco.
        print(f"Rosto '{nome_antigo}' renomeado para '{novo_nome}'.") # Log de sucesso.
        flash(f"Rosto '{nome_antigo}' renomeado para '{novo_nome}' com sucesso!", "success") # Notificação de sucesso.
    except Exception as e: # Se a renomeação falhar.
        print(f"Ocorreu um erro ao renomear: {e}") # Log de erro.
        flash(f"Erro ao renomear: {e}", "error") # Notificação de erro.

    return redirect(url_for('painel_admin')) # Manda o utilizador de volta para a página de admin.


# Esta é a construção padrão em Python para executar o código.
# A variável especial '__name__' só será "__main__" se executarmos este ficheiro diretamente (ex: "python servidor.py").
if __name__ == "__main__": 
    # O comando que inicia o servidor web do Flask.
    app.run(host='0.0.0.0', port=5000, debug=True) 
    # host='0.0.0.0': Faz o servidor ser visível na sua rede local (para a ESP32 o encontrar), não apenas no seu PC (localhost).
    # port=5000: Define a "porta" em que o servidor vai ouvir.
    # debug=True: Ativa o modo de depuração, que reinicia o servidor automaticamente sempre que você salva o ficheiro.
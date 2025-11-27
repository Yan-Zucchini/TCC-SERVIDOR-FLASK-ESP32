# Sistema de Reconhecimento Facial com ESP32 e Flask

Este projeto é um sistema completo de reconhecimento facial composto por um **Servidor Central (Python/Flask)** e um **Dispositivo de Captura (ESP32-CAM)**. Ele foi desenvolvido como parte de um Trabalho de Conclusão de Curso (TCC).

O sistema permite cadastrar rostos, gerenciar usuários via interface web e realizar o reconhecimento facial em tempo real, enviando os dados da ESP32 para o servidor processar.

## 📋 Índice

1. [Visão Geral e Arquitetura](#visão-geral-e-arquitetura)
2. [Pré-requisitos](#pré-requisitos)
3. [Instalação do Servidor](#instalação-do-servidor)
4. [Como Rodar o Projeto](#como-rodar-o-projeto)
5. [Manual de Uso (Passo a Passo)](#manual-de-uso-passo-a-passo)
6. [API e Detalhes Técnicos](#api-e-detalhes-técnicos)
7. [Resolução de Problemas](#resolução-de-problemas)

---

## 🏗 Visão Geral e Arquitetura

O sistema funciona em uma arquitetura Cliente-Servidor:

*   **Servidor (Este repositório)**:
    *   Feito em Python usando o framework **Flask**.
    *   Armazena os "moldes" (assinaturas matemáticas) dos rostos na pasta `faces_registradas`.
    *   Realiza os cálculos matemáticos (Distância Euclidiana) para comparar um rosto novo com os rostos salvos.
    *   Fornece um Painel Administrativo Web para gerenciar os usuários.

*   **Cliente (ESP32-CAM)**:
    *   Captura a imagem do rosto.
    *   Processa a imagem localmente para extrair a "assinatura" do rosto (um vetor de números).
    *   Envia apenas essa assinatura (bytes) para o servidor via Wi-Fi.

---

## 💻 Pré-requisitos

Para rodar o servidor, você precisará de um computador com:

*   **Python 3.7 ou superior** instalado.
*   Conexão de rede (Wi-Fi) onde a ESP32 também estará conectada.

---

## ⚙️ Instalação do Servidor

Siga estes passos para preparar o ambiente no seu computador:

### 1. Clonar ou Baixar o Projeto
Baixe os arquivos deste repositório para uma pasta no seu computador (ex: `TCC_Reconhecimento`).

### 2. Criar um Ambiente Virtual (Recomendado)
Para não misturar as bibliotecas do projeto com as do seu sistema, crie um ambiente virtual.
Abra o terminal (Prompt de Comando ou PowerShell) na pasta do projeto e execute:

**No Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**No Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```
*Você saberá que funcionou se aparecer `(venv)` no início da linha do terminal.*

### 3. Instalar as Dependências
Com o ambiente virtual ativado, instale as bibliotecas necessárias (Flask e Numpy) usando o arquivo `requirements.txt` que incluímos:

```bash
pip install -r requirements.txt
```

---

## 🚀 Como Rodar o Projeto

1.  Certifique-se de que seu ambiente virtual está ativado.
2.  Execute o servidor com o comando:

```bash
python servidor.py
```

3.  Você verá uma mensagem como:
    ```
    * Running on http://0.0.0.0:5000/ (Press CTRL+C to quit)
    ```
    Isso significa que o servidor está online!

4.  **Descubra o IP do seu computador**:
    *   No Windows, abra outro terminal e digite `ipconfig`. Procure por "Endereço IPv4" (ex: `192.168.1.15`).
    *   Este é o IP que você deverá configurar no código da sua ESP32.

---

## 📖 Manual de Uso (Passo a Passo)

### Acessando o Painel Administrativo
Abra o seu navegador (Chrome, Firefox, etc.) e digite:
`http://localhost:5000/admin`

Você verá a lista de rostos cadastrados (inicialmente vazia) e as opções de gerenciamento.

### Passo 1: Cadastrar um Novo Rosto
O processo de cadastro é feito em duas etapas para garantir segurança e organização:

1.  **No Painel Admin**:
    *   Digite o nome da pessoa no campo "Novo Registo".
    *   Clique em **"Iniciar Registo"**.
    *   O servidor entrará em "Modo de Espera" para aquele nome.

2.  **Na ESP32 (Dispositivo)**:
    *   Aponte a câmera para o rosto da pessoa.
    *   Pressione o botão de cadastro (ex: "Enroll Face") na ESP32.
    *   A ESP32 enviará os dados para o servidor.
    *   O servidor salvará o arquivo automaticamente como `NomeDaPessoa.face`.

### Passo 2: Reconhecimento Facial
*   Com o sistema rodando, basta posicionar um rosto na frente da ESP32.
*   A ESP32 enviará os dados para a rota de reconhecimento.
*   O servidor verificará se o rosto bate com algum arquivo salvo na pasta `faces_registradas`.
*   O resultado (Nome da pessoa ou "Desconhecido") será retornado para a ESP32.

### Gerenciamento de Usuários
No Painel Admin, você pode:
*   **Renomear**: Corrigir o nome de um usuário já cadastrado.
*   **Apagar**: Remover o registro de um usuário. O arquivo `.face` será excluído do computador.

---

## 🔧 API e Detalhes Técnicos

Se você for modificar o código da ESP32, aqui estão os "endpoints" (endereços) que o servidor disponibiliza:

### 1. `POST /registar_rosto`
*   **Objetivo**: Receber a assinatura binária de um rosto e salvar em arquivo.
*   **Corpo (Body)**: Bytes brutos (Raw data) da assinatura do rosto.
*   **Lógica**:
    *   Se o admin preparou um nome (via `/iniciar_registo`), usa esse nome.
    *   Se não, gera um nome automático (`user0`, `user1`...).

### 2. `POST /reconhecer_rosto`
*   **Objetivo**: Comparar um rosto recebido com o banco de dados.
*   **Corpo (Body)**: Bytes brutos da assinatura a ser verificada.
*   **Retorno**:
    *   `200 OK`: Corpo contém o nome da pessoa identificada.
    *   `200 OK`: Corpo contém "Rosto Desconhecido" se a distância for muito grande.

---

## ❓ Resolução de Problemas

**1. A ESP32 não consegue conectar ao servidor.**
*   Verifique se o computador e a ESP32 estão na **mesma rede Wi-Fi**.
*   Verifique se o **Firewall do Windows** não está bloqueando o Python. Tente desativar o firewall temporariamente para testar.
*   Confirme se o IP configurado na ESP32 é o IP correto do seu computador (use `ipconfig`).

**2. O servidor diz "Rosto Desconhecido" mesmo para pessoas cadastradas.**
*   A iluminação pode estar diferente. Tente cadastrar novamente no mesmo ambiente.
*   Você pode tentar aumentar o `LIMITE_DE_RECONHECIMENTO` no arquivo `servidor.py` (linha 23) se estiver muito rigoroso.

**3. Erro "Address already in use".**
*   O servidor já está rodando em outra janela. Feche todas as janelas do Python/Terminal e tente novamente.

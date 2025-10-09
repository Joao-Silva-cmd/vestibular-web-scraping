from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import pickle
import os
import time
import re

def fazer_login(driver, email, senha):
    """Faz login no site"""
    print("Fazendo login...")
    driver.get("https://app.repertorioenem.com.br/login")
    
    wait = WebDriverWait(driver, 10)
    
    campo_email = wait.until(EC.presence_of_element_located((By.ID, "inputEmailAddress")))
    campo_email.send_keys(email)
    
    campo_senha = driver.find_element(By.ID, "inputPassword")
    campo_senha.send_keys(senha)
    
    botao_login = driver.find_element(By.CSS_SELECTOR, ".btn.btn-lg.w-100.bg-purple")
    botao_login.click()
    
    time.sleep(3)
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "card-body")))
    print("Login realizado com sucesso!")

def salvar_cookies(driver, arquivo="cookies.pkl"):
    """Salva os cookies em um arquivo"""
    pickle.dump(driver.get_cookies(), open(arquivo, "wb"))
    print(f"Cookies salvos em {arquivo}")

def carregar_cookies(driver, arquivo="cookies.pkl"):
    """Carrega cookies de um arquivo"""
    if os.path.exists(arquivo):
        cookies = pickle.load(open(arquivo, "rb"))
        for cookie in cookies:
            driver.add_cookie(cookie)
        print("Cookies carregados!")
        return True
    return False

def verificar_login(driver):
    """Verifica se ainda está logado"""
    try:
        driver.find_element(By.CLASS_NAME, "card-body")
        return True
    except:
        return False

def tem_conteudo_util(html):
    """Verifica se o HTML tem texto ou imagem"""
    # Remover tags para verificar texto
    texto_limpo = re.sub(r'<[^>]+>', '', html).strip()
    
    # Verificar se tem texto significativo (mais que espaços/quebras)
    tem_texto = len(texto_limpo) > 0
    
    # Verificar se tem imagem
    tem_imagem = '<img' in html.lower() or 'src=' in html.lower()
    
    return tem_texto or tem_imagem

def limpar_html(html):
    """Remove elementos vazios do HTML"""
    # Aqui você pode adicionar limpezas adicionais se necessário
    return html

def extrair_questoes(driver, url):
    """Extrai enunciados e alternativas de uma página"""
    print(f"Acessando: {url}")
    driver.get(url)
    time.sleep(3)
    
    questoes_html = []
    
    # Pegar todos os enunciados
    enunciados = driver.find_elements(By.CSS_SELECTOR, ".mb-0.mx-2.ck-content.highlighter-context")
    
    print(f"  - {len(enunciados)} enunciados encontrados")
    
    for i, enunciado in enumerate(enunciados, 1):
        # Verificar se o enunciado tem conteúdo útil
        enunciado_html = enunciado.get_attribute('outerHTML')
        
        if not tem_conteudo_util(enunciado_html):
            print(f"    Questão {i}: Enunciado vazio, pulando...")
            continue
        
        questao_completa = '<div class="questao">\n'
        questao_completa += f'<h3>Questão {i}</h3>\n'
        
        # Adicionar enunciado
        questao_completa += '<div class="enunciado">\n'
        questao_completa += enunciado_html + '\n'
        questao_completa += '</div>\n'
        
        # Tentar encontrar as alternativas dessa questão
        try:
            # Navegar para o elemento pai (card)
            elemento_pai = enunciado.find_element(By.XPATH, "./ancestor::div[contains(@class, 'card')]")
            
            # Dentro desse card, procurar o container d-flex
            container_d_flex = elemento_pai.find_element(By.CSS_SELECTOR, ".d-flex.flex-wrap.justify-content-between")
            
            # Pegar a div ms-0 que vem DEPOIS do d-flex (não dentro dele)
            # A div ms-0 está no mesmo nível ou após o d-flex
            try:
                # Tentar pegar o próximo elemento irmão ou dentro do container pai
                div_ms0 = container_d_flex.find_element(By.XPATH, "./following-sibling::div[contains(@class, 'ms-0')]")
            except:
                # Se não encontrar como irmão, procurar dentro do d-flex
                div_ms0 = container_d_flex.find_element(By.CSS_SELECTOR, ".ms-0")
            
            # Pegar o HTML da div ms-0
            alternativas_html = div_ms0.get_attribute('outerHTML')
            
            # Verificar se tem conteúdo útil
            if tem_conteudo_util(alternativas_html):
                questao_completa += '<div class="alternativas">\n'
                questao_completa += alternativas_html + '\n'
                questao_completa += '</div>\n'
                print(f"    Questão {i}: Alternativas extraídas")
            else:
                print(f"    Questão {i}: Alternativas vazias, não incluídas")
                
        except Exception as e:
            print(f"    Questão {i}: Erro ao buscar alternativas - {e}")
        
        questao_completa += '</div>\n<hr>\n'
        questoes_html.append(questao_completa)
    
    return questoes_html

def salvar_html(todas_questoes, arquivo="questoes_extraidas.html"):
    """Salva todas as questões em um arquivo HTML puro"""
    html_completo = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Questões Extraídas</title>
</head>
<body>
<h1>Questões ENEM 2014</h1>
"""
    
    # Adicionar cada questão
    for questao_html in todas_questoes:
        html_completo += questao_html
    
    html_completo += """
</body>
</html>"""
    
    with open(arquivo, "w", encoding="utf-8") as f:
        f.write(html_completo)
    
    print(f"\nArquivo salvo: {arquivo}")
    print(f"Total de questões extraídas: {len(todas_questoes)}")

# ============ CÓDIGO PRINCIPAL ============

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

try:
    # Fazer login (com sistema de cookies)
    driver.get("https://app.repertorioenem.com.br")
    time.sleep(2)
    
    cookies_carregados = carregar_cookies(driver)
    
    if cookies_carregados:
        driver.refresh()
        time.sleep(2)
        
        if verificar_login(driver):
            print("Sessão ainda válida! Pulando login...")
        else:
            print("Sessão expirada. Fazendo login novamente...")
            fazer_login(driver, "laionp98@gmail.com", "00uLisses00!")
            salvar_cookies(driver)
    else:
        print("Nenhum cookie encontrado. Fazendo primeiro login...")
        fazer_login(driver, "laionp98@gmail.com", "00uLisses00!")
        salvar_cookies(driver)
    
    # URLs das 8 páginas
    base_url = "https://app.repertorioenem.com.br/questions/list?search=1&institution%5B0%5D=1&year%5B0%5D=2014&pages=25&order_by=2&page="
    
    todas_questoes = []
    
    # Extrair de 8 páginas
    print("\n=== INICIANDO EXTRAÇÃO ===\n")
    for pagina in range(1, 9):
        url = base_url + str(pagina)
        questoes_pagina = extrair_questoes(driver, url)
        todas_questoes.extend(questoes_pagina)
        print(f"Página {pagina}: {len(questoes_pagina)} questões extraídas\n")
    
    # Salvar tudo em um único arquivo HTML
    salvar_html(todas_questoes)
    
    print("\n=== EXTRAÇÃO CONCLUÍDA ===")
    
finally:
    driver.quit()
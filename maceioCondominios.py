# Importação das dependencias
import requests
import pandas as pd
import json
import time
from bs4 import BeautifulSoup
import logging
from typing import List, Dict, Optional
import os
from datetime import datetime
import re
import urllib.parse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class MaceioCondominiosScraperReal:
    """
    Classe para baixar dados REAIS de condomínios de prédios da cidade de Maceió
    usando fontes oficiais e públicas
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('maceio_condominios_real.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Criar diretório para dados
        self.data_dir = 'dados_condominios_maceio_real'
        os.makedirs(self.data_dir, exist_ok=True)
        
        # URLs reais descobertas
        self.urls_reais = {
            'portal_cidadao': 'https://www.online.maceio.al.gov.br/',
            'sefaz_maceio': 'https://online.maceio.al.gov.br/',
            'transparencia_estado': 'https://transparencia.al.gov.br/',
            'ibge_api': 'https://servicodados.ibge.gov.br/api/v1/',
            'dados_abertos_br': 'https://dados.gov.br/dados/conjuntos-dados'
        }
    
    def configurar_selenium(self) -> webdriver.Chrome:
        """
        Configura o driver Selenium para sites que requerem JavaScript
        """
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            return driver
        except Exception as e:
            self.logger.error(f"Erro ao configurar Selenium: {e}")
            return None
    
    def buscar_dados_portal_cidadao(self) -> List[Dict]:
        """
        Busca dados do Portal do Cidadão de Maceió (dados REAIS)
        """
        self.logger.info("Buscando dados do Portal do Cidadão de Maceió")
        condominios = []

        try:
            # Acessar serviços de ficha cadastral
            url_ficha = f"{self.urls_reais['portal_cidadao']}1/ver_servico/69/unidade/ficha+cadastral+de+imoveis/"
            
            response = self.session.get(url_ficha, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                self.logger.info("Acesso ao portal do cidadão realizado com sucesso")
                # Buscar formulários de consulta disponíveis
                forms = soup.find_all('form')
                for form in forms:
                    action = form.get('action', '')
                    if 'imovel' in action.lower() or 'cadastr' in action.lower():
                        self.logger.info(f"Encontrado formulário de consulta: {action}")
                # Buscar links para serviços relacionados a imoveis
                links_servicos = soup.find_all('a', href=True)
                servicos_imoveis = []

                for link in links_servicos:
                    texto = link.get_text().lower()
                    href = link['href']

                    if any(palavra in texto for palavra in ['inóvel', 'imovel', 'cadastr', 'iptu', 'predial']):
                        servicos_imoveis.append({
                            'servico': link.get_text().strip(),
                            'url': href,
                            'tipo': 'consulta_imovel'
                        })
                condominios.extend(servicos_imoveis)
                self.logger.info(f"Encontrados {len(servicos_imoveis)} serviços relacionados a imoveis")

        except Exception as e:
            self.logger.error(f"Erro ao acessar Portal do Cidadão: {e}")
    
    def buscar_dados_sefaz_maceio(self) -> List[Dict]:
        """
        Busca dados da SEFAZ de Maceió (Sistema de IPTU - dados REAIS)
        """
        self.logger.info("Buscando dados da SEFAZ Maceió...")
        dados_imoveis = []
        
        try:
            # URL do sistema de IPTU
            url_iptu = f"{self.urls_reais['sefaz_maceio']}n/iptu2022/"
            
            response = self.session.get(url_iptu, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Analisar estrutura do sistema de IPTU
                forms = soup.find_all('form')
                inputs = soup.find_all('input')
                selects = soup.find_all('select')
                
                sistema_info = {
                    'url': url_iptu,
                    'tipo': 'sistema_iptu',
                    'status': 'ativo',
                    'formularios_disponiveis': len(forms),
                    'campos_consulta': []
                }
                
                # Extrair campos de consulta disponíveis
                for input_field in inputs:
                    if input_field.get('name'):
                        sistema_info['campos_consulta'].append({
                            'campo': input_field.get('name'),
                            'tipo': input_field.get('type', 'text'),
                            'placeholder': input_field.get('placeholder', '')
                        })
                
                dados_imoveis.append(sistema_info)
                self.logger.info("Sistema de IPTU mapeado com sucesso")
                
                # Tentar acessar página de busca de inscrição
                url_busca = f"{self.urls_reais['portal_cidadao']}6/ver_servico/21/unidade/buscar+inscri%C3%A7ao+imobiliaria/"
                response_busca = self.session.get(url_busca, timeout=10)
                
                if response_busca.status_code == 200:
                    dados_imoveis.append({
                        'url': url_busca,
                        'tipo': 'busca_inscricao',
                        'status': 'disponivel'
                    })
        
        except Exception as e:
            self.logger.error(f"Erro ao acessar SEFAZ: {e}")
        
        return dados_imoveis
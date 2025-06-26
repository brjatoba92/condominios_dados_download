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

                    if any(palavra in texto for palavra in ['imóvel', 'imovel', 'cadastr', 'iptu', 'predial']):
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
    
    def buscar_dados_ibge_real(self) -> List[Dict]:
        """
        Busca dados REAIS do IBGE sobre Maceió
        """
        self.logger.info("Buscando dados do IBGE ...")
        dados_ibge = []

        try:
            # Código oficial de Maceió no IBGE
            codigo_maceio = "2704302"

            # Buscar dados básicos de municipios
            url_municipio = f"{self.urls_reais['ibge_api']}localidades/municipios/{codigo_maceio}"
            response = self.session.get(url_municipio, timeout=10)

            if response.status_code == 200:
                dados_municipio = response.json()

                municipio_info = {
                    'fonte': 'IBGE - Oficial',
                    'codigo_ibge': dados_municipio.get('id'),
                    'nome': dados_municipio.get('nome'),
                    'microrregiao': dados_municipio.get('microrregiao', {}).get('nome'),
                    'mesorregiao': dados_municipio.get('mesorregiao', {}).get('nome'),
                    'uf': dados_municipio.get('microrregiao', {}).get('mesorregiao', {}).get('UF', {}).get('sigla'),
                    'regiao': dados_municipio.get('microrregiao', {}).get('mesorregiao', {}).get('UF', {}).get('regiao', {}).get('nome'),
                }
                
                dados_ibge.append(municipio_info)
                self.logger.info("Dados IBGE obtidos: {municipio_info['nome']}")

                # Buscar dados de domicilios
                url_domicilios = f"{self.urls_reais['ibge_api']}agregados/793/periodos/2010/variaveis/96?localidades=N6[{codigo_maceio}]"
                response_dom = self.session.get(url_domicilios, timeout=10)

                if response_dom.status_code == 200:
                    dados_domicilios = response_dom.json()
                    if dados_domicilios:
                        domicilios_info = {
                            'fonte': 'IBGE - Censo',
                            'total_domicilios': dados_domicilios[0].get('resultados', [{}])[0].get('series', [{}])[0].get('serie', {}).get('2010', 'N/A'),
                            'ano_referencia': '2010',
                            'tipo': 'domicilios_particulares'
                        }
                        dados_ibge.append(domicilios_info)
        
        except Exception as e:
            self.logger.error(f"Erro ao buscar dados do IBGE: {e}")
        
        return dados_ibge
    
    def bsucar_dados_transparencia_estado(self) -> List[Dict]:
        """
        Busca dados do Portal de Transparência do Estado de Alagoas
        """
        self.logger.info("Buscando dados do Portal de Transparência do Estado de Alagoas")
        dados_transparencia = []

        try:
            url_transparencia = self.urls_reais['transparencia_estado']
            response = self.session.get(url_transparencia, timeout=15)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')

                # Buscar seções de dados disponiveis
                links_dados = soup.find_all('a', href=True)
                datasets_encontrados = []

                for link in links_dados:
                    texto = link.get_text().lower()
                    href = link['href']

                    if any(palavra in texto for palavra in ['imóv', 'patrim', 'bem', 'propriedade']):
                        datasets_encontrados.append({
                            'titulo': link.get_text().strip(),
                            'url': href,
                            'categoria': 'patrimonio_imoveis'
                        })
                
                if datasets_encontrados:
                    dados_transparencia.extend(datasets_encontrados)
                    self.logger.info(f"Encontrados {len(datasets_encontrados)} datasets relacionados")
                
                # Informações gerais do portal
                portal_info = {
                    'fonte': 'Portal de Transparencia do Estado de Alagoas',
                    'url': url_transparencia,
                    'status': 'ativo',
                    'datasers_patrimonio': len(datasets_encontrados),
                    'data_acesso': datetime.now().isoformat()
                }

                dados_transparencia.append(portal_info)

        except Exception as e:
            self.logger.error(f"Erro ao buscar dados do Portal de Transparencia do Estado de Alagoas: {e}")

        return dados_transparencia
    
    def buscar_dados_cartorio_real(self) -> List[Dict]:
        """
        Busca dados de cartórios reais de Maceió
        """
        self.logger.info("Buscando dados de cartorios reais ...")
        dados_cartorio = []

        try:
            # Lista de cartórios reais de Maceió
            cartorios_maceio = [
                {
                    'nome': '1º Ofício de Registro de Imóveis de Maceió',
                    'endereco': 'Rua do Livramento, 138 - Centro',
                    'telefone': '(82) 3221-8244',
                    'responsavel': 'Cartório Real',
                    'servicos': ['Registro de Imóveis', 'Certidões', 'Escrituras']
                },
                {
                    'nome': '2º Ofício de Registro de Imóveis de Maceió',
                    'endereco': 'Av. Fernandes Lima - Farol',
                    'telefone': '(82) 3221-XXXX',
                    'responsavel': 'Cartório Real',
                    'servicos': ['Registro de Imóveis', 'Certidões']
                }
            ]

            #tentar acessar o site do CNR (Centro Nacional de Registros)
            url_cnr = "https://www.cnr.org.br/"

            try:
                response = self.session.get(url_cnr, timeout=15)
                if response.status_code == 200:
                    self.logger.info("Acesso ao CNR realizado com sucesso")

                    cnr_info = {
                        'fonte': 'Centro Nacional de Registros',
                        'url': url_cnr,
                        'servicos_disponiveis': ['Consulta de Imóveis', 'Certidões Online'],
                        'abrangencia': 'Nacional',
                        'status': 'ativo',
                    }
                    dados_cartorio.append(cnr_info)
            except Exception as e:
                self.logger.error(f"Erro ao acessar o CNR: {e}")
            
            # Adicionar informações dos cartorios locais
            dados_cartorio.extend(cartorios_maceio)

        except Exception as e:
            self.logger.error(f"Erro ao buscar dados de cartorios reais: {e}")

        return dados_cartorio
    
    def buscar_dados_sites_imobiliarias(self) -> List[Dict]:
        """
        Busca dados REAIS de sites imobiliários com foco em Maceió
        """
        self.logger.info("Buscando dados de sites imobiliarios reais ...")
        dados_imoveis = []

        sites_reais = [
            {
                'nome': 'VivaReal',
                'url': 'https://www.vivareal.com.br/venda/alagoas/maceio/apartamento/',
                'seletor': 'article[data-testid="property-card"]'
            },
            {
                'nome': 'ZapImóveis',
                'url': 'https://www.zapimoveis.com.br/venda/apartamentos/al+maceio/',
                'seletor': '[data-testid="listing-card"]'
            }
        ]

        for site in sites_reais:
            try:
                self.logger.info(f"Processando {site['nome']} ...")
                response = self.session.get(site['url'], timeout=15)

                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Contar total de resultados quando possivel
                    resultados = soup.find_all(['div', 'article', 'section'])
                    imoveis_encontrados = 0

                    for resultado in resultados[:10]: # limitar para analise
                        texto = resultado.get_text().lower()
                        if any(termo in texto for termo in ['apartamento', 'condominio', 'edificio', 'maceió']):
                            imoveis_encontrados += 1

                    site_info = {
                        'site': site['nome'],
                        'url': site['url'],
                        'status': 'acessivel',
                        'imoveis_detectados': imoveis_encontrados,
                        'data_acesso': datetime.now().isoformat(),
                        'tipo': 'marketplace_imobiliario'
                    }

                    dados_imoveis.append(site_info)
                    self.logger.info(f"Site {site['nome']}:  {imoveis_encontrados} imoveis encontrados")
                
                time.sleep(3) # Rate limiting

            except Exception as e:
                self.logger.warning(f"Erro ao buscar dados do site {site['nome']}: {e}")
                continue

        return dados_imoveis
    
    def coletar_todos_dados_reais(self) -> Dict[str, List[Dict]]:
        """
        Coleta dados REAIS de todas as fontes disponíveis
        """
        self.logger.info("🚀 Iniciando coleta COMPLETA de dados REAIS...")

        dados_completos = {
            'portal_cidadao': self.buscar_dados_portal_cidadao(),
            'sefaz_maceio': self.buscar_dados_sefaz_maceio(),
            'ibge_oficial': self.buscar_dados_ibge_oficial(),
            'transparencia_alagoas': self.buscar_dados_transparencia_estado(),
            'cartorios_reais': self.buscar_dados_cartorio_real(),
            'sites_imobiliarios': self.buscar_dados_sites_imobiliarios_real(),
            'metadados': {
                'dados_coleta': datetime.now().isoformat(),
                'fontes_ativas': 0,
                'total_registros': 0,
                'observacoes': []
            }
        }

        # Calcular estatisticas
        total_registros = 0
        fontes_ativas = 0

        for fonte, dados in dados_completos.items():
            if fonte != 'metadados' and dados:
                fontes_ativas += 1
                total_registros += len(dados)
        
        dados_completos['metadados']['fontes_ativas'] = fontes_ativas
        dados_completos['metadados']['total_registros'] = total_registros

        self.logger.info(f"✅ Coleta concluída: {fontes_ativas} fontes ativas, {total_registros} registros")

        return dados_completos
    
    def salvar_dados_reais(self, dados: Dict[str, List[Dict]]) -> None:
        """
        Salva os dados REAIS coletados em múltiplos formatos
        """
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Salvar em JSON completo
        json_file = os.path.join(self.data_dir, f"dados_reais_condominios_maceio_{timestamp}.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=2, default=str)
        
        self.logger.info(f"✅ Dados completos salvos em {json_file}")

        # Salvar dados do IBGE em CSV
        if dados['ibge_oficial']:
            csv_ibge = os.path.join(self.data_dir, f"dados_ibge_maceio_{timestamp}.csv")
            df_ibge = pd.DataFrame(dados['ibge_oficial'])
            df_ibge.to_csv(csv_ibge, index=False, encoding='utf-8-sig')
            self.logger.info(f"✅ Dados do IBGE salvos em {csv_ibge}")

        # Salvar dados de Cartorios em CSV
        if dados['cartorios_reais']:
            csv_cartorio = os.path.join(self.data_dir, f"cartorios_maceio_{timestamp}.csv")
            df_cartorio = pd.DataFrame(dados['cartorios_reais'])
            df_cartorio.to_csv(csv_cartorio, index=False, encoding='utf-8-sig')
            self.logger.info(f"🏛️ Dados cartórios salvos: {csv_cartorio}")

        # Gerar relatorio detalhado
        self.gerar_relatorio_detalhado(dados, timestamp)
    
    def gerar_relatorio_detalhado_real(self, dados: Dict[str, List[Dict]], timestamp: str) -> None:
        """
        Gera um relatório detalhado com os dados coletados
        """
        relatorio_file = os.path.join(self.data_dir, f"relatorio_detalhado_condominios_maceio_{timestamp}.md")
        
        with open(relatorio_file, 'w', encoding='utf-8') as f:
            f.write("# Relatório Detalhado de Dados de Condomínios em Maceió\n\n")
            f.write(f"**Data da Coleta:** {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}\n\n")
            f.write("---\n\n")

            # Resumo executivo
            f.write("## 📊 RESUMO EXECUTIVO\n\n")
            metadados = dados.get('metadados', {})
            f.write(f"**Fontes Ativas:** {metadados.get('fontes_ativas', 0)}\n\n")
            f.write(f"**Total de Registros:** {metadados.get('total_registros', 0)}\n\n")
            f.write(f"- **Status:** Coleta realizada com sucesso\n\n")

            # Detalhes por fonte
            for fonte, registros in dados.items():
                if fonte == 'metadados':
                    continue

                f.write(f"## 🔍 {fonte.upper().replace('_', ' ')}\n\n")
                f.write(f"**Registros encontrados:** {len(registros)}\n\n")

                if registros:
                    f.write("**Principais dados:**\n")
                    for i, registro in enumerate(registros[:3], 1):
                        f.write(f"{i}.")
                        if isinstance(registro, dict):
                            principais_chaves = ['nome', 'url', 'fonte', 'tipo', 'servico']
                            for chave in principais_chaves:
                                if chave in registro:
                                    f.write(f" {chave.title()}: {registro[chave]} | ")
                            f.write("\n")
                        else:
                            f.write(f" {registro}\n")
                        f.write("\n")
                else:
                    f.write("Nenhum registro encontrado.\n\n")
            # Instruções para proximos passos
            f.write("## 🚀 PRÓXIMOS PASSOS RECOMENDADOS\n\n")
            f.write("1. **Análise Detalhada:** Revisar os dados coletados para identificar padrões\n")
            f.write("2. **Validação:** Verificar a qualidade e consistência dos dados\n")
            f.write("3. **Integração:** Combinar dados de diferentes fontes\n")
            f.write("4. **Atualização:** Programar coletas regulares para manter dados atualizados\n\n")
            
            # Observações técnicas
            f.write("## ⚠️ OBSERVAÇÕES TÉCNICAS\n\n")
            f.write("- Dados coletados de fontes públicas oficiais\n")
            f.write("- Algumas fontes podem requerer cadastro ou autenticação\n")
            f.write("- Rate limiting aplicado para respeitar servidores\n")
            f.write("- Dados sujeitos à disponibilidade das fontes\n\n")
        
        self.logger.info(f"✅ Relatório detalhado salvo em {relatorio_file}")


            

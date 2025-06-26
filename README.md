# 🏢 Maceió Condomínios Scraper

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Este projeto é um coletor de dados REAIS de condomínios de prédios na cidade de Maceió, Alagoas, utilizando fontes oficiais e públicas.

## 📌 Visão Geral

O `MaceioCondominiosScraperReal` é uma ferramenta Python que coleta e consolida dados sobre condomínios de diversas fontes públicas, incluindo:

- Portal do Cidadão de Maceió
- SEFAZ Maceió (Sistema de IPTU)
- IBGE (dados oficiais)
- Portal de Transparência do Estado de Alagoas
- Cartórios de Registro de Imóveis
- Sites imobiliários (VivaReal, ZapImóveis)

## ✨ Funcionalidades

- **Coleta automatizada** de dados de múltiplas fontes
- **Processamento e limpeza** dos dados coletados
- **Exportação** em múltiplos formatos (JSON, CSV)
- **Geração de relatórios** detalhados em Markdown
- **Logging completo** para monitoramento
- **Configuração flexível** para diferentes cenários

## 📦 Instalação

1. Clone este repositório:
   ```bash
   git clone https://github.com/brjatoba92/condominios_dados_download.git
   cd condominios_dados_download
   ```

2. Crie um ambiente virtual (recomendado):
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # ou
   venv\Scripts\activate  # Windows
   ```

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

## 🚀 Uso

Execute o script principal:
```bash
python maceio_condominios_scraper.py
```

Após a execução, os dados serão salvos no diretório `dados_condominios_maceio_real/` com os seguintes arquivos:
- `dados_reais_condominios_maceio_<TIMESTAMP>.json` - Dados completos em JSON
- `dados_ibge_maceio_<TIMESTAMP>.csv` - Dados do IBGE em CSV
- `cartorios_maceio_<TIMESTAMP>.csv` - Dados de cartórios em CSV
- `relatorio_detalhado_real_<TIMESTAMP>.md` - Relatório detalhado em Markdown

## 🛠️ Dependências

- Python 3.8+
- Bibliotecas principais:
  - `requests`
  - `beautifulsoup4`
  - `pandas`
  - `selenium`
  - `lxml`

## 🤝 Contribuição

Contribuições são bem-vindas! Siga estes passos:

1. Faça um fork do projeto
2. Crie sua branch (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 📧 Contato

Para dúvidas ou sugestões, entre em contato:

- [E-mail](mailto:brunojatobadev@gmail.com)
- [LinkedIn](https://www.linkedin.com/in/brunojatoba/)

---

**Nota:** Este projeto é destinado apenas para fins educacionais e de pesquisa. Certifique-se de cumprir os Termos de Serviço de cada fonte de dados utilizada.
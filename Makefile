# Makefile da Scientific Systems Exploration Platform (SSEP)
PYTHON = .venv/bin/python

.PHONY: help status user user-falsified engineer scientist design reproduce falsify test verify demo

help:
	@echo "Central de Administracao SSEP (Camadas L1 a L7)"
	@echo "Comandos disponiveis:"
	@echo "  make status         - Exibe resumo do grafo epistemico"
	@echo "  make user           - Executa simulacao em regime validado (1000 uM ATP, 0 pN carga)"
	@echo "  make user-falsified - Executa simulacao sob forca (alerta Epistemic Firewall)"
	@echo "  make engineer       - Inspeciona entidades moleculares e parametros"
	@echo "  make scientist      - Inspeciona proveniencia ponta a ponta e conflitos"
	@echo "  make design         - Calcula proposta de desenho experimental discriminatorio"
	@echo "  make reproduce      - Executa pipeline de reproducao sobre Dataset A"
	@echo "  make falsify        - Executa pipeline de falsificacao sobre Dataset B"
	@echo "  make test           - Executa suite de testes automatizados (pytest)"
	@echo "  make verify         - Executa auditoria formal de integridade e dados"
	@echo "  make demo           - Executa bateria de demonstracao completa"

status:
	@$(PYTHON) manage.py status

user:
	@$(PYTHON) manage.py user --preset-valid

user-falsified:
	@$(PYTHON) manage.py user --preset-falsified

engineer:
	@$(PYTHON) manage.py engineer

scientist:
	@$(PYTHON) manage.py scientist

design:
	@$(PYTHON) manage.py design

reproduce:
	@$(PYTHON) manage.py reproduce

falsify:
	@$(PYTHON) manage.py falsify

test:
	@$(PYTHON) manage.py test

verify:
	@$(PYTHON) manage.py verify

demo:
	@$(PYTHON) manage.py demo
